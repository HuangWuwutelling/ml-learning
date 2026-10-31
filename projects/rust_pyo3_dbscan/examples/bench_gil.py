"""Does PyO3's `Python::detach` actually buy us parallelism here?

The GIL is held for the whole duration of a `#[pymethods]` function unless the
binding explicitly releases it. Stage 1's `fit` is ~705 ms at n=5000, so if we
held the GIL every concurrent caller would queue behind the first one and
threading would buy nothing.

The measurement, stated so the numbers are unambiguous:

    t_serial   = wall time for K fits, one after another on the main thread
    t_parallel = wall time for the SAME K fits spread over T threads
    speedup    = t_serial / t_parallel

    speedup ~= T   -> the fits overlapped; the GIL was released
    speedup ~= 1   -> they serialised; the GIL was held

The work is identical in both cases, so the only variable is overlap.

Run with:
    python examples/bench_gil.py
"""

import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

# __file__ = <repo>/projects/rust_pyo3_dbscan/examples/bench_gil.py
# parents[3] = <repo>, which is where `models/dbscan.py` lives.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import rust_pyo3_dbscan
from models.dbscan import DBSCAN as PyDbscan

N_PER_CLUSTER = 100
SEED = 42
MAX_THREADS = 8

# Section A only. Each fit must last long enough that thread scheduling noise
# does not dominate: DBSCAN is O(n^2), so n=2000 lands around 85 ms per fit on
# this box, and MAX_THREADS of them take ~0.7 s serially. At n=300 the whole
# serial run is under 5 ms and every speedup figure is noise.
N_GIL = 2000


def make_blobs(n_per=N_PER_CLUSTER, std=0.5):
    rng = np.random.default_rng(SEED)
    return np.vstack(
        [rng.normal(loc=c, scale=std, size=(n_per, 2)) for c in ((0.0, 0.0), (5.0, 5.0), (-5.0, 5.0))]
    ).astype(np.float64)


def run_serial(x, k, eps, min_pts):
    t0 = time.perf_counter()
    for _ in range(k):
        m = rust_pyo3_dbscan.Dbscan(eps=eps, min_pts=min_pts)
        m.fit(x)
    return time.perf_counter() - t0


def run_parallel(x, k, threads, eps, min_pts):
    # Each task builds its own Dbscan: a pyclass is not required to be
    # thread-safe, and sharing one would measure the wrong thing.
    def one(_):
        m = rust_pyo3_dbscan.Dbscan(eps=eps, min_pts=min_pts)
        m.fit(x)
        return m.n_clusters

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(one, range(k)))
    return time.perf_counter() - t0


def bench_gil():
    """Section A — parallel scaling.

    Size matters more than anything else here. DBSCAN's `region_query` is
    O(n^2), so each fit must be long enough (tens of ms) that thread scheduling
    noise does not swamp the measurement. At n=300 a fit is ~0.8 ms and the
    whole serial run is ~6 ms — every number there is noise.
    """
    x = make_blobs(n_per=N_GIL // 3)
    n = len(x)
    k = MAX_THREADS
    eps, min_pts = 1.0, 5
    repeats = 3

    print("=" * 62)
    print(f"A. GIL release — n={n}, {k} fits total, eps={eps}, min_pts={min_pts}")
    print(f"   {os.cpu_count()} CPUs, best of {repeats} runs")
    print("=" * 62)

    # One untimed fit so the first timed run does not pay lazy page faults.
    run_serial(x, 1, eps, min_pts)

    t_serial = min(run_serial(x, k, eps, min_pts) for _ in range(repeats))
    print(f"serial (1 thread)        {t_serial * 1000:8.1f} ms   speedup 1.00x")

    for threads in (2, 4, 8):
        t_par = min(run_parallel(x, k, threads, eps, min_pts) for _ in range(repeats))
        speedup = t_serial / t_par
        print(
            f"parallel ({threads} threads){'':10}{t_par * 1000:8.1f} ms"
            f"   speedup {speedup:.2f}x"
        )
    print()
    print("Read: speedup ~= thread count => GIL released (fits overlapped).")
    print("      speedup ~= 1.0            => GIL held (fits serialised).")
    print()


NATIVE_BENCH = Path(__file__).resolve().parents[2] / "rust_dbscan/target/release/examples/benchmark.exe"


def _time_native_csv(csv_path):
    """Run the Stage 1 binary on `csv_path`, return fit time in ms.

    Returns None if the binary has not been built yet — section B degrades to a
    Python-vs-PyO3 comparison instead of failing.
    """
    if not NATIVE_BENCH.exists():
        print(f"  (native binary not built: {NATIVE_BENCH})")
        print("   build it with: cd projects/rust_dbscan && cargo build --release --example benchmark")
        return None
    out = subprocess.run(
        [str(NATIVE_BENCH), str(csv_path)], capture_output=True, text=True, check=True
    ).stdout
    # Rust's Duration Debug prints ns/µs/ms/s. Longest-first, or "1.9µs"
    # matches as value 1.9 with unit "s" and comes back 1000x too large.
    m = re.search(r"Rust DBSCAN fit:\s*([\d.]+)(ns|µs|ms|s)", out)
    if not m:
        return None
    return float(m.group(1)) * {"ns": 1e-6, "µs": 1e-3, "ms": 1.0, "s": 1000.0}[m.group(2)]


def bench_latency():
    """Section B — what does the Python->PyO3 hop actually cost?

    All three rows run on *the same numpy array*. The array is written to CSV
    and handed to the Stage 1 binary, because that binary's own generator uses
    a different RNG (StdRng + Box-Muller vs numpy's PCG64 + ziggurat) and its
    numbers were recorded on a different day. Comparing across those would
    measure the machine's mood, not the FFI.
    """
    print("=" * 62)
    print("B. Single-fit latency — all three on identical input")
    print("=" * 62)
    print(f"{'n':>7} {'Python':>12} {'PyO3':>12} {'Rust native':>13} {'FFI cost':>10}")

    with tempfile.TemporaryDirectory() as tmp:
        for target in (5000, 10000):
            x = make_blobs(n_per=target // 3)
            n = len(x)  # 3 * (target // 3), so report what was actually built

            csv_path = Path(tmp) / f"blobs_{n}.csv"
            np.savetxt(csv_path, x, delimiter=",", fmt="%.17g")

            t0 = time.perf_counter()
            PyDbscan(eps=1.0, min_pts=5).fit(x)
            t_py = (time.perf_counter() - t0) * 1000

            m = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5)
            t0 = time.perf_counter()
            m.fit(x)
            t_pyo3 = (time.perf_counter() - t0) * 1000

            native = _time_native_csv(csv_path)
            if native is None:
                print(f"{n:>7} {t_py:>10.0f} ms {t_pyo3:>10.0f} ms {'n/a':>11} {'n/a':>10}")
                continue

            ffi = t_pyo3 / native
            print(
                f"{n:>7} {t_py:>10.0f} ms {t_pyo3:>10.0f} ms {native:>11.0f} ms"
                f" {ffi:>9.2f}x"
            )

    print()
    print("'FFI cost' = PyO3 / Rust native, same data, same session. 1.00x would")
    print("mean the binding is free; the excess is the numpy->Array2 copy plus")
    print("call overhead, and it is paid once per fit against O(n^2) work.")
    print()


if __name__ == "__main__":
    bench_gil()
    bench_latency()

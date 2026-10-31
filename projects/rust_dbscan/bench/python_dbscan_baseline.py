"""Stage 1 baseline: same DBSCAN fit timing, in pure Python/numpy.

Generates the same 5000 / 10000 point 2D 3-Gaussian datasets as
`examples/benchmark.rs`, then times the fit step. Run from
`projects/rust_dbscan/` with:

    python bench/python_dbscan_baseline.py

The Python DBSCAN lives at `../../models/dbscan.py` (via sys.path injection).
"""
import sys
import time
import numpy as np

# Make the Python DBSCAN importable from the repo root.
sys.path.insert(0, "../..")
from models.dbscan import DBSCAN

SEED = 42


def gaussian_cluster(rng, n, mean, sigma):
    return rng.normal(loc=mean, scale=sigma, size=(n, 2))


def dataset_3clusters(n, seed):
    rng = np.random.default_rng(seed)
    n_per = n // 3
    a = gaussian_cluster(rng, n_per, [0.0, 0.0], 0.5)
    b = gaussian_cluster(rng, n_per, [5.0, 5.0], 0.5)
    c = gaussian_cluster(rng, n_per, [-5.0, 5.0], 0.5)
    return np.concatenate([a, b, c], axis=0)


def main():
    for n in (5000, 10000):
        x = dataset_3clusters(n, SEED)
        print(f"\n=== n={n} 2D 3-Gaussian clusters ===")
        model = DBSCAN(eps=1.0, min_pts=5)

        # Warm-up
        _ = model.fit(x)

        start = time.perf_counter()
        _ = model.fit(x)
        elapsed = time.perf_counter() - start
        print(f"  Python DBSCAN fit: {elapsed*1000:.1f} ms")
        print(
            f"  n_clusters={model.n_clusters_} n_noise={model.n_noise_}"
        )


if __name__ == "__main__":
    main()

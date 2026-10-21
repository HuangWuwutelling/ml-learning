//! Stage 1 benchmark: DBSCAN clustering timing on a synthetic dataset.
//!
//! Generates 5000 / 10000 points in 2D (3 Gaussians) and times the `fit` step.
//! Run with:
//!
//! ```bash
//! cargo run --release --example benchmark              # built-in dataset
//! cargo run --release --example benchmark data.csv     # your own n x 2 CSV
//! ```
//!
//! Compare against the Python equivalent in
//! `bench/python_dbscan_baseline.py`. The CSV mode exists because the built-in
//! generator uses `StdRng` + Box-Muller while numpy uses `PCG64` + ziggurat:
//! statistically the same distribution, but a different array, so a timing
//! comparison across the two is not like-for-like. Stage 2 drives the CSV mode
//! to measure the Python->PyO3 hop against this exact input.

use ndarray::Array2;
use rand::Rng;
use rand::rngs::StdRng;
use rand::SeedableRng;
use rust_dbscan::Dbscan;
use std::time::Instant;

const SEED: u64 = 42;

/// Sample `n` points from a 2D Gaussian with the given mean and standard
/// deviation, using the Box-Muller transform.
fn gaussian_cluster(rng: &mut StdRng, n: usize, mean: [f64; 2], sigma: f64) -> Vec<[f64; 2]> {
    let mut out = Vec::with_capacity(n);
    for _ in 0..n {
        let u1: f64 = rng.gen_range(1e-12..1.0);
        let u2: f64 = rng.gen_range(0.0..1.0);
        let r = (-2.0 * u1.ln()).sqrt();
        let theta = 2.0 * std::f64::consts::PI * u2;
        let z0 = r * theta.cos();
        let z1 = r * theta.sin();
        out.push([mean[0] + sigma * z0, mean[1] + sigma * z1]);
    }
    out
}

fn dataset_3clusters(n: usize, seed: u64) -> Array2<f64> {
    let mut rng = StdRng::seed_from_u64(seed);
    let n_per = n / 3;
    let a = gaussian_cluster(&mut rng, n_per, [0.0, 0.0], 0.5);
    let b = gaussian_cluster(&mut rng, n_per, [5.0, 5.0], 0.5);
    let c = gaussian_cluster(&mut rng, n_per, [-5.0, 5.0], 0.5);
    let mut flat = Vec::with_capacity(n_per * 3 * 2);
    for p in a.into_iter().chain(b).chain(c) {
        flat.push(p[0]);
        flat.push(p[1]);
    }
    let rows = flat.len() / 2;
    Array2::from_shape_vec((rows, 2), flat).expect("shape ok")
}

/// Load an `n x 2` CSV of floats, no header. Used so this benchmark can be
/// driven from Python on *exactly* the same array the PyO3 path sees — a
/// like-for-like FFI-overhead number needs identical input, and the built-in
/// generator uses a different RNG than numpy so its timings are not comparable.
fn load_csv_2d(path: &str) -> Array2<f64> {
    let text = std::fs::read_to_string(path).expect("read csv");
    let rows: Vec<[f64; 2]> = text
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|line| {
            let mut it = line.split(',');
            let x: f64 = it.next().expect("col 0").trim().parse().expect("f64 col 0");
            let y: f64 = it.next().expect("col 1").trim().parse().expect("f64 col 1");
            [x, y]
        })
        .collect();
    let flat: Vec<f64> = rows.iter().flat_map(|r| [r[0], r[1]]).collect();
    Array2::from_shape_vec((rows.len(), 2), flat).expect("shape ok")
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    // `benchmark <path.csv>` times one fit on data produced elsewhere. Used by
    // `projects/rust_pyo3_dbscan/examples/bench_gil.py` section B.
    if let Some(path) = args.get(1) {
        let x = load_csv_2d(path);
        println!("=== csv {} (n={}) ===", path, x.nrows());
        let start = Instant::now();
        let model = Dbscan::new(1.0, 5).fit(x).expect("fit ok");
        println!("  Rust DBSCAN fit: {:?}", start.elapsed());
        println!(
            "  n_clusters={}, n_noise={}",
            model.n_clusters(),
            model.n_noise()
        );
        return;
    }

    for &n in &[5000usize, 10000usize] {
        let x = dataset_3clusters(n, SEED);
        println!("\n=== n={n} 2D 3-Gaussian clusters ===");

        // Warm-up
        let _ = Dbscan::new(1.0, 5).fit(x.clone()).expect("warmup ok");

        let start = Instant::now();
        let model = Dbscan::new(1.0, 5).fit(x).expect("fit ok");
        let elapsed = start.elapsed();
        println!("  Rust DBSCAN fit: {elapsed:?}");
        println!(
            "  n_clusters={}, n_noise={}",
            model.n_clusters(),
            model.n_noise()
        );
    }
}

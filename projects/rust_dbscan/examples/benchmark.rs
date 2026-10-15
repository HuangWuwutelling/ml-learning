//! Stage 1 benchmark: DBSCAN clustering timing on a synthetic dataset.
//!
//! Generates 5000 / 10000 points in 2D (3 Gaussians) and times the `fit` step.
//! Run with:
//!
//! ```bash
//! cargo run --release --example benchmark
//! ```
//!
//! Compare against the Python equivalent in
//! `bench/python_dbscan_baseline.py`.

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

fn main() {
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

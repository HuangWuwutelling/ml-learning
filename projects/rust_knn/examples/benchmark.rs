//! Stage 1 benchmark: KNN predict timing on a synthetic dataset.
//!
//! Generates 5000 random 2D points (3 classes) and 500 query points, then
//! times the predict step. Run with:
//!
//! ```bash
//! cargo run --release --example benchmark
//! ```
//!
//! Compare against the Python equivalent in
//! `projects/rust_knn/bench/python_knn_baseline.py` (kept outside the crate
//! root because Python scripts don't belong in a Rust package).

use ndarray::{s, Array1, Array2};
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;
use rust_knn::Knn;
use std::time::Instant;

const N_TRAIN: usize = 5_000;
const N_QUERY: usize = 500;
const N_FEATURES: usize = 8;
const N_CLASSES: i64 = 3;
const K: usize = 5;
const SEED: u64 = 42;

fn main() {
    let mut rng = StdRng::seed_from_u64(SEED);
    let x_train: Array2<f64> = Array2::from_shape_fn((N_TRAIN, N_FEATURES), |_| {
        rng.gen_range(-1.0..1.0)
    });
    let y_train: Array1<i64> = Array1::from_shape_fn(N_TRAIN, |_| {
        rng.gen_range(0..N_CLASSES)
    });
    let x_query: Array2<f64> = Array2::from_shape_fn((N_QUERY, N_FEATURES), |_| {
        rng.gen_range(-1.0..1.0)
    });

    let model = Knn::new(K).fit(x_train, y_train).expect("fit ok");

    // Warm-up
    let _ = model.predict(&x_query).expect("predict ok");

    let start = Instant::now();
    let preds = model.predict(&x_query).expect("predict ok");
    let elapsed = start.elapsed();

    println!("Rust KNN predict (release build):");
    println!("  n_train={} n_query={} n_features={} k={}",
        N_TRAIN, N_QUERY, N_FEATURES, K);
    println!("  elapsed: {:?}", elapsed);
    println!("  per query: {:?}", elapsed / N_QUERY as u32);
    println!("  predicted {} labels (first 5: {:?})",
        preds.len(), preds.slice(s![..5.min(preds.len())]));
}

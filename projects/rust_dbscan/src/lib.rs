//! DBSCAN clustering — Rust port of `ml_playground.models.dbscan`.
//!
//! Stage 1 of 副线 3 (Rust 渐进式学习). The Python reference is at
//! `../../models/dbscan.py` and is registered in `projects/ml_playground/core.py`
//! with default `eps=0.5, min_pts=5, dataset=make_moons`.
//!
//! Differences from the Python version:
//! - Returns `Result<Self, String>` from `fit` instead of mutating in place — Rust
//!   has no exceptions.
//! - Labels fetched via [`Dbscan::labels`] which returns `&[i64]` (use the
//!   `Result` to surface "not fitted yet").
//! - `labels[i]` encoding: `>=0` cluster id, `-1` noise, `-2` unvisited (internal).
//! - `n_clusters` / `n_noise` as getter methods, not Python attributes.

use ndarray::Array2;

const UNVISITED: i64 = -2;
const NOISE: i64 = -1;

/// DBSCAN clustering result.
///
/// Build with [`Dbscan::new`], then call [`Dbscan::fit`] to run clustering.
/// After fit, fetch labels via [`Dbscan::labels`], cluster count via
/// [`Dbscan::n_clusters`], noise count via [`Dbscan::n_noise`].
#[derive(Debug, Clone)]
pub struct Dbscan {
    eps: f64,
    min_pts: usize,
    labels_: Option<Vec<i64>>,
    n_clusters_: usize,
    n_noise_: usize,
}

impl Dbscan {
    /// Build a DBSCAN model with the given hyperparameters. Does not run
    /// clustering until [`Dbscan::fit`] is called.
    pub fn new(eps: f64, min_pts: usize) -> Self {
        Self {
            eps,
            min_pts,
            labels_: None,
            n_clusters_: 0,
            n_noise_: 0,
        }
    }

    /// The eps radius used by this model.
    pub fn eps(&self) -> f64 {
        self.eps
    }

    /// The min_pts threshold used by this model.
    pub fn min_pts(&self) -> usize {
        self.min_pts
    }

    /// Run DBSCAN clustering on `x` (n × d). Returns `Err` for invalid
    /// hyperparameters (eps ≤ 0 or non-finite, min_pts == 0).
    pub fn fit(mut self, x: Array2<f64>) -> Result<Self, String> {
        if !self.eps.is_finite() || self.eps <= 0.0 {
            return Err(format!("eps must be > 0 (got {})", self.eps));
        }
        if self.min_pts == 0 {
            return Err("min_pts must be >= 1".to_string());
        }

        let n = x.nrows();
        let mut labels: Vec<i64> = vec![UNVISITED; n];
        let mut cluster_id: i64 = 0;

        for i in 0..n {
            if labels[i] != UNVISITED {
                continue;
            }
            let neighbors = self.region_query(&x, i);
            if neighbors.len() < self.min_pts {
                labels[i] = NOISE;
                continue;
            }
            // Core point: open a new cluster and queue neighbours (except self)
            // as seeds for density-reachable expansion.
            labels[i] = cluster_id;
            let mut seeds: Vec<usize> = Vec::with_capacity(neighbors.len());
            for &j in &neighbors {
                if j != i {
                    seeds.push(j);
                }
            }

            // Expand the cluster by draining the seed queue.
            while let Some(j) = seeds.pop() {
                if labels[j] >= 0 {
                    continue; // already in some cluster
                }
                if labels[j] == NOISE {
                    // Border point: flip from provisional noise to this cluster.
                    labels[j] = cluster_id;
                    continue;
                }
                // labels[j] == UNVISITED: classify and expand if it's also a core.
                labels[j] = cluster_id;
                let new_neighbors = self.region_query(&x, j);
                if new_neighbors.len() >= self.min_pts {
                    for &nn in &new_neighbors {
                        if labels[nn] < 0 && !seeds.contains(&nn) {
                            seeds.push(nn);
                        }
                    }
                }
            }
            cluster_id += 1;
        }

        self.n_clusters_ = cluster_id as usize;
        self.n_noise_ = labels.iter().filter(|&&l| l == NOISE).count();
        self.labels_ = Some(labels);
        Ok(self)
    }

    /// Cluster labels after `fit`. Returns `Err` if the model has not been
    /// fitted yet.
    pub fn labels(&self) -> Result<&[i64], String> {
        let v = self
            .labels_
            .as_ref()
            .ok_or("not fitted: call fit() first".to_string())?;
        Ok(v.as_slice())
    }

    /// Number of clusters discovered (0 if not fitted).
    pub fn n_clusters(&self) -> usize {
        self.n_clusters_
    }

    /// Number of noise points (–1 labels) discovered (0 if not fitted).
    pub fn n_noise(&self) -> usize {
        self.n_noise_
    }

    /// Indices of all training points within `eps` of `x[i]`. Naive O(n) scan —
    /// no KD-tree or Ball-Tree. The intent is to compare Rust vs Python loop
    /// overhead on the same algorithm; spatial-acceleration work belongs in
    /// Stage 2/3.
    fn region_query(&self, x: &Array2<f64>, i: usize) -> Vec<usize> {
        let row_i = x.row(i);
        let eps2 = self.eps * self.eps;
        let mut out = Vec::with_capacity(x.nrows());
        for j in 0..x.nrows() {
            let row_j = x.row(j);
            let d2: f64 = row_i
                .iter()
                .zip(row_j.iter())
                .map(|(a, b)| {
                    let d = a - b;
                    d * d
                })
                .sum();
            if d2 <= eps2 {
                out.push(j);
            }
        }
        out
    }
}

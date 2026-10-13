//! k-Nearest Neighbors classifier — Rust port of `ml_playground.models.knn`.
//!
//! Stage 1 of 副线 3 (Rust 渐进式学习). The Python reference lives at
//! `../../models/knn.py` and is registered in `projects/ml_playground/core.py`
//! with default `k=5`, `weights="uniform"`, `metric="euclidean"`.
//!
//! Differences from the Python version:
//! - Returns `Result<Self, String>` from `fit` and `Result<Array1, String>` from
//!   `predict` instead of raising — Rust has no exceptions.
//! - Builder pattern: `Knn::new(k).with_weights(...).with_metric(...).fit(x, y)?`
//!   instead of positional `__init__` kwargs.
//! - `i64` labels (Python uses `np.unique` over arbitrary hashable types; for
//!   Stage 1 we restrict to integer class labels, which is enough for iris
//!   and the toy tests).
//! - Tie-breaking: when k votes for two or more classes are equal, the smallest
//!   class label wins. The Python `np.argmax` over the same `classes_` order
//!   does the same thing; this is just spelled out.

use ndarray::{Array1, Array2, ArrayView1};
use std::collections::HashMap;

/// How to weight each of the k nearest neighbors when voting.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Weights {
    /// Every neighbor counts as 1.
    Uniform,
    /// Closer neighbors count more, weight = 1 / (distance + 1e-8).
    Distance,
}

/// Distance metric between a query point and a training point.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Metric {
    /// √Σ(aᵢ − bᵢ)²
    Euclidean,
    /// Σ|aᵢ − bᵢ|
    Manhattan,
}

/// k-Nearest Neighbors classifier.
///
/// Construct with [`Knn::new`], optionally chain [`Knn::with_weights`] and
/// [`Knn::with_metric`], then call [`Knn::fit`] to train and [`Knn::predict`]
/// to classify.
#[derive(Debug)]
pub struct Knn {
    k: usize,
    weights: Weights,
    metric: Metric,
    x_train: Option<Array2<f64>>,
    y_train: Option<Array1<i64>>,
    /// Sorted unique class labels from the most recent `fit`. Used for stable
    /// tie-breaking (smallest class wins).
    classes: Vec<i64>,
}

impl Knn {
    /// Build a KNN with default uniform weights and Euclidean distance.
    pub fn new(k: usize) -> Self {
        Self {
            k,
            weights: Weights::Uniform,
            metric: Metric::Euclidean,
            x_train: None,
            y_train: None,
            classes: Vec::new(),
        }
    }

    /// Override the weights. Builder pattern, so chain it before `fit`.
    pub fn with_weights(mut self, w: Weights) -> Self {
        self.weights = w;
        self
    }

    /// Override the distance metric. Builder pattern, so chain it before `fit`.
    pub fn with_metric(mut self, m: Metric) -> Self {
        self.metric = m;
        self
    }

    /// Train on `x` (n × d) and integer labels `y` (n).
    ///
    /// Returns `Err` if k is 0, k > n, or x.nrows() != y.len().
    pub fn fit(mut self, x: Array2<f64>, y: Array1<i64>) -> Result<Self, String> {
        if self.k == 0 {
            return Err("k must be >= 1".to_string());
        }
        if x.nrows() != y.len() {
            return Err(format!(
                "X has {} rows but y has {} elements",
                x.nrows(),
                y.len()
            ));
        }
        if self.k > x.nrows() {
            return Err(format!(
                "k={} is greater than the number of training samples ({})",
                self.k,
                x.nrows()
            ));
        }
        // Sorted unique classes — used for stable tie-breaking.
        let mut classes: Vec<i64> = y.iter().copied().collect();
        classes.sort_unstable();
        classes.dedup();
        self.classes = classes;
        self.x_train = Some(x);
        self.y_train = Some(y);
        Ok(self)
    }

    /// Predict integer labels for queries `x` (n × d).
    ///
    /// Returns `Err` if the model has not been fitted yet, or if `x` has the
    /// wrong number of features.
    pub fn predict(&self, x: &Array2<f64>) -> Result<Array1<i64>, String> {
        let x_train = self
            .x_train
            .as_ref()
            .ok_or("not fitted: call fit() first")?;
        let y_train = self
            .y_train
            .as_ref()
            .ok_or("not fitted: call fit() first")?;
        if x.ncols() != x_train.ncols() {
            return Err(format!(
                "X has {} features but the training set had {}",
                x.ncols(),
                x_train.ncols()
            ));
        }
        let n = x.nrows();
        let mut preds = Array1::zeros(n);
        for i in 0..n {
            let row = x.row(i);
            let dists = self.distances_to_train(&row, x_train);
            preds[i] = self.vote(&dists, y_train);
        }
        Ok(preds)
    }

    /// Distance from one query row to every row of the training set.
    fn distances_to_train(&self, row: &ArrayView1<f64>, train: &Array2<f64>) -> Array1<f64> {
        let mut d = Array1::zeros(train.nrows());
        for j in 0..train.nrows() {
            let tr = train.row(j);
            d[j] = match self.metric {
                Metric::Euclidean => row
                    .iter()
                    .zip(tr.iter())
                    .map(|(a, b)| (a - b) * (a - b))
                    .sum::<f64>()
                    .sqrt(),
                Metric::Manhattan => row
                    .iter()
                    .zip(tr.iter())
                    .map(|(a, b)| (a - b).abs())
                    .sum(),
            };
        }
        d
    }

    /// Take the k nearest neighbors and pick the class with the highest vote.
    /// Ties are broken by `self.classes` order (smallest class wins).
    fn vote(&self, dists: &Array1<f64>, y_train: &Array1<i64>) -> i64 {
        let k = self.k.min(dists.len());
        // select_nth_unstable_by panics if k >= slice.len(), so we skip the
        // partition when k == n (in that case every index is a "top-k" winner).
        let top_k: Vec<usize> = if k < dists.len() {
            let mut idx: Vec<usize> = (0..dists.len()).collect();
            idx.select_nth_unstable_by(k, |a, b| {
                dists[*a]
                    .partial_cmp(&dists[*b])
                    .unwrap_or(std::cmp::Ordering::Equal)
            });
            idx[..k].to_vec()
        } else {
            (0..dists.len()).collect()
        };

        // Tally weighted votes per class.
        let mut counts: HashMap<i64, f64> = HashMap::new();
        for i in top_k {
            let weight = match self.weights {
                Weights::Uniform => 1.0,
                // 1e-8 prevents division by zero when the query point equals
                // a training point (distance = 0).
                Weights::Distance => 1.0 / (dists[i] + 1e-8),
            };
            *counts.entry(y_train[i]).or_insert(0.0) += weight;
        }

        // Pick the class with the highest score. Walking self.classes in sorted
        // order means the smallest class wins ties (matches np.argmax over a
        // sorted class list).
        let mut best_class = self.classes[0];
        let mut best_score = f64::NEG_INFINITY;
        for &c in &self.classes {
            let s = counts.get(&c).copied().unwrap_or(0.0);
            if s > best_score {
                best_score = s;
                best_class = c;
            }
        }
        best_class
    }
}

//! Integration tests for the KNN classifier.

use ndarray::{array, Array1, Array2};
use rust_knn::{Knn, Metric, Weights};

/// Two clearly separated clusters: 5 points near (0, 0) labelled 0, 5 points
/// near (10, 10) labelled 1.
fn train_x() -> Array2<f64> {
    array![
        [0.0, 0.0],
        [0.1, 0.2],
        [-0.1, 0.1],
        [0.2, -0.1],
        [-0.2, 0.0],
        [10.0, 10.0],
        [10.1, 10.2],
        [9.9, 9.8],
        [10.2, 9.9],
        [9.8, 10.1],
    ]
}

fn train_y() -> Array1<i64> {
    array![0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
}

#[test]
fn fits_and_predicts_cluster_centers() {
    let model = Knn::new(3).fit(train_x(), train_y()).expect("fit ok");
    let queries = array![[0.0, 0.0], [10.0, 10.0]];
    let preds = model.predict(&queries).expect("predict ok");
    assert_eq!(preds, array![0, 1]);
}

#[test]
fn predict_at_training_point_returns_that_label() {
    let model = Knn::new(3).fit(train_x(), train_y()).unwrap();
    // Querying a training point: that point itself is one of the k=3 nearest
    // neighbors (distance 0) so its label dominates the vote.
    let queries = array![[0.1, 0.2], [10.1, 10.2]];
    let preds = model.predict(&queries).unwrap();
    assert_eq!(preds, array![0, 1]);
}

#[test]
fn rejects_wrong_feature_dim() {
    let model = Knn::new(3).fit(train_x(), train_y()).unwrap();
    let bad = array![[0.0, 0.0, 0.0]]; // 3 features vs 2 in training
    assert!(model.predict(&bad).is_err());
}

#[test]
fn rejects_k_greater_than_n_train() {
    let res = Knn::new(11).fit(train_x(), train_y());
    assert!(res.is_err());
    let msg = res.unwrap_err();
    assert!(msg.contains("k=11"), "error should mention k=11, got: {msg}");
}

#[test]
fn rejects_predict_before_fit() {
    let model = Knn::new(3);
    let queries = array![[0.0, 0.0]];
    let err = model.predict(&queries).unwrap_err();
    assert!(err.contains("not fitted"), "got: {err}");
}

#[test]
fn rejects_mismatched_x_y_lengths() {
    let x = array![[0.0, 0.0], [1.0, 1.0]];
    let y = array![0]; // only 1 label, 2 rows
    let err = Knn::new(1).fit(x, y).unwrap_err();
    assert!(err.contains("2 rows"), "got: {err}");
    assert!(err.contains("1 elements"), "got: {err}");
}

#[test]
fn rejects_zero_k() {
    let err = Knn::new(0).fit(train_x(), train_y()).unwrap_err();
    assert!(err.contains("k must be >= 1"), "got: {err}");
}

#[test]
fn euclidean_distance_basic_correctness() {
    // 1-D: train at x=0, query at x=3. Distance 3, k=1 → predicts train label.
    let x = array![[0.0]];
    let y = array![42];
    let model = Knn::new(1).fit(x, y).unwrap();
    let q = array![[3.0]];
    assert_eq!(model.predict(&q).unwrap()[0], 42);
}

#[test]
fn manhattan_metric_picks_correct_neighbor() {
    // 2 points: (0,0)→0 and (2,2)→1.
    let x = array![[0.0, 0.0], [2.0, 2.0]];
    let y = array![0, 1];
    let eu = Knn::new(1)
        .with_metric(Metric::Euclidean)
        .fit(x.clone(), y.clone())
        .unwrap();
    let man = Knn::new(1)
        .with_metric(Metric::Manhattan)
        .fit(x.clone(), y.clone())
        .unwrap();
    // (0.5, 0.5) is closer to (0,0) under both metrics.
    let q = array![[0.5, 0.5]];
    assert_eq!(eu.predict(&q).unwrap()[0], 0);
    assert_eq!(man.predict(&q).unwrap()[0], 0);
    // (1.5, 1.5) is closer to (2,2) under both metrics.
    let q = array![[1.5, 1.5]];
    assert_eq!(eu.predict(&q).unwrap()[0], 1);
    assert_eq!(man.predict(&q).unwrap()[0], 1);
}

#[test]
fn distance_weights_favour_close_neighbor() {
    // 2 train points: (0,0)→0 and (1,0)→1.
    let x = array![[0.0, 0.0], [1.0, 0.0]];
    let y = array![0, 1];
    let uniform = Knn::new(2).fit(x.clone(), y.clone()).unwrap();
    let weighted = Knn::new(2)
        .with_weights(Weights::Distance)
        .fit(x.clone(), y.clone())
        .unwrap();
    // Query at (0.99, 0): uniform gives 1 vote each → class 0 wins by sorted
    // tie-break. Distance weighting gives (1,0) ≈ 100x more weight → class 1.
    let q = array![[0.99, 0.0]];
    assert_eq!(uniform.predict(&q).unwrap()[0], 0);
    assert_eq!(weighted.predict(&q).unwrap()[0], 1);
}

#[test]
fn three_class_problem() {
    // Three clusters along the x-axis, far apart.
    let x = array![
        [0.0],
        [0.1],
        [-0.1],
        [10.0],
        [10.1],
        [9.9],
        [20.0],
        [20.1],
        [19.9],
    ];
    let y = array![0, 0, 0, 1, 1, 1, 2, 2, 2];
    let model = Knn::new(3).fit(x, y).unwrap();
    let q = array![[0.0], [10.0], [20.0]];
    let preds = model.predict(&q).unwrap();
    assert_eq!(preds, array![0, 1, 2]);
}

#[test]
fn predict_on_larger_batch_returns_one_per_row() {
    let model = Knn::new(3).fit(train_x(), train_y()).unwrap();
    let q = array![
        [0.0, 0.0],
        [0.1, 0.1],
        [10.0, 10.0],
        [10.1, 10.1],
        [5.0, 5.0], // ambiguous, will be classified to one of the two
    ];
    let preds = model.predict(&q).unwrap();
    assert_eq!(preds.len(), 5);
    // First two are clearly near the (0,0) cluster.
    assert_eq!(preds[0], 0);
    assert_eq!(preds[1], 0);
    // Next two are clearly near the (10,10) cluster.
    assert_eq!(preds[2], 1);
    assert_eq!(preds[3], 1);
}

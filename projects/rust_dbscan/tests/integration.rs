//! Integration tests for DBSCAN clustering.

use ndarray::{arr2, Array2};
use rust_dbscan::Dbscan;

#[test]
fn separates_two_clusters() {
    // Two clearly separated point groups: cluster A near (0,0), cluster B near (10,10).
    let x = arr2(&[
        [0.0, 0.0],
        [0.1, 0.1],
        [-0.1, 0.0],
        [0.05, -0.05],
        [10.0, 10.0],
        [10.1, 10.1],
        [9.9, 9.95],
        [10.05, 10.0],
    ]);
    let m = Dbscan::new(0.5, 3).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 2);
    let labels = m.labels().expect("labels");
    let la: std::collections::HashSet<i64> = labels[..4].iter().copied().collect();
    let lb: std::collections::HashSet<i64> = labels[4..].iter().copied().collect();
    assert_eq!(la.len(), 1, "first half should be one cluster");
    assert_eq!(lb.len(), 1, "second half should be one cluster");
    assert_ne!(la, lb, "two clusters should have different ids");
}

#[test]
fn separates_three_clusters() {
    let x = arr2(&[
        // cluster 0
        [0.0],
        [0.1],
        [-0.1],
        // cluster 1
        [10.0],
        [10.1],
        [9.9],
        // cluster 2
        [20.0],
        [20.1],
        [19.9],
    ]);
    let m = Dbscan::new(0.5, 2).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 3);
}

#[test]
fn all_points_are_noise_when_eps_too_small() {
    let x = arr2(&[
        [0.0, 0.0],
        [0.1, 0.0],
        [-0.1, 0.0],
        [5.0, 5.0],
        [5.1, 5.0],
        [4.9, 5.0],
    ]);
    let m = Dbscan::new(0.05, 2).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 0);
    assert_eq!(m.n_noise(), 6);
}

#[test]
fn single_huge_cluster_when_eps_too_large() {
    let x = arr2(&[
        [0.0, 0.0],
        [0.1, 0.1],
        [-0.1, 0.1],
        [5.0, 5.0],
        [5.1, 5.0],
        [4.9, 5.0],
        [-3.0, -3.0],
        [-3.1, -2.9],
    ]);
    let m = Dbscan::new(100.0, 2).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 1);
    assert_eq!(m.n_noise(), 0);
}

#[test]
fn isolated_point_between_clusters_becomes_noise() {
    // Two tight clusters separated by a gap larger than eps. A single point
    // sits in the gap with no neighbour within eps, so DBSCAN marks it as
    // noise (-1) rather than absorbing it into either cluster.
    let x = arr2(&[
        // cluster A near x=0
        [0.0],
        [0.1],
        [-0.1],
        [0.05],
        // cluster B near x=1
        [1.0],
        [1.1],
        [0.9],
        [1.05],
        // isolated point in the gap
        [0.5],
    ]);
    let m = Dbscan::new(0.3, 3).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 2);
    assert_eq!(m.n_noise(), 1);
    let labels = m.labels().expect("labels");
    assert_eq!(labels[8], -1);
}

#[test]
fn n_clusters_and_n_noise_fields_correct() {
    let x = arr2(&[
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [10.0, 10.0],
        [10.0, 10.0],
        [10.0, 10.0],
        // isolated noise
        [100.0, 100.0],
    ]);
    let m = Dbscan::new(0.5, 3).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 2);
    assert_eq!(m.n_noise(), 1);
    let labels = m.labels().expect("labels");
    assert_eq!(labels[6], -1);
}

#[test]
fn duplicate_points_do_not_break_clustering() {
    // Five points at the exact same location should cluster together, not break
    // the algorithm with duplicate distances.
    let x = arr2(&[
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [10.0, 10.0],
        [10.0, 10.0],
        [10.0, 10.0],
        [10.0, 10.0],
        [10.0, 10.0],
    ]);
    let m = Dbscan::new(0.5, 3).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 2);
    assert_eq!(m.n_noise(), 0);
    let labels = m.labels().expect("labels");
    let first_cluster: std::collections::HashSet<i64> = labels[..5].iter().copied().collect();
    let second_cluster: std::collections::HashSet<i64> = labels[5..].iter().copied().collect();
    assert_eq!(first_cluster.len(), 1);
    assert_eq!(second_cluster.len(), 1);
    assert_ne!(first_cluster, second_cluster);
}

#[test]
fn labels_before_fit_returns_error() {
    let m = Dbscan::new(0.5, 5);
    let err = m.labels().unwrap_err();
    assert!(err.contains("not fitted"), "got: {err}");
}

#[test]
fn single_point_with_min_pts_one_self_clusters() {
    let x: Array2<f64> = arr2(&[[1.5, -2.5]]);
    let m = Dbscan::new(0.1, 1).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 1);
    assert_eq!(m.n_noise(), 0);
    let labels = m.labels().expect("labels");
    assert_eq!(labels[0], 0);
}

#[test]
fn empty_input_is_handled() {
    let x: Array2<f64> = Array2::zeros((0, 2));
    let m = Dbscan::new(0.5, 3).fit(x).expect("fit ok");
    assert_eq!(m.n_clusters(), 0);
    assert_eq!(m.n_noise(), 0);
    let labels = m.labels().expect("labels");
    assert!(labels.is_empty());
}

#[test]
fn rejects_invalid_hyperparameters() {
    let x: Array2<f64> = arr2(&[[0.0, 0.0], [1.0, 1.0]]);
    assert!(Dbscan::new(0.0, 3).fit(x.clone()).is_err());
    assert!(Dbscan::new(-1.0, 3).fit(x.clone()).is_err());
    assert!(Dbscan::new(f64::NAN, 3).fit(x.clone()).is_err());
    assert!(Dbscan::new(0.5, 0).fit(x).is_err());
}

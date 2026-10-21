"""Python-side tests for the PyO3 binding.

The important one is `test_labels_match_python_reference`: Stage 2 claims to be
a drop-in replacement for `models/dbscan.py`, so the only assertion that really
matters is that both implementations assign identical labels to every point.

Run with:
    pytest tests/test_from_python.py -v
"""

import numpy as np
import pytest

import rust_pyo3_dbscan
from models.dbscan import DBSCAN as PyDbscan


def make_blobs(n_per=200, centers=((0.0, 0.0), (5.0, 5.0), (-5.0, 5.0)), std=0.5, seed=42):
    """Three well-separated 2-D Gaussians — the Stage 1 benchmark dataset.

    Uses a private Generator rather than the global seed so the test does not
    depend on call order.
    """
    rng = np.random.default_rng(seed)
    return np.vstack(
        [rng.normal(loc=c, scale=std, size=(n_per, 2)) for c in centers]
    ).astype(np.float64)


# --------------------------------------------------------------------------
# Alignment with the pure-Python reference — the load-bearing test
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "eps,min_pts",
    [
        (1.0, 5),  # the benchmark setting: three clean clusters
        (0.5, 5),  # tighter: still 3 clusters, fewer border points
        (2.0, 10),  # looser core requirement: chains the clusters together
        (0.3, 3),  # tight enough to produce noise points
    ],
)
def test_labels_match_python_reference(eps, min_pts):
    x = make_blobs()
    py = PyDbscan(eps=eps, min_pts=min_pts).fit_predict(x)
    rust = rust_pyo3_dbscan.Dbscan(eps=eps, min_pts=min_pts).fit_predict(x)
    np.testing.assert_array_equal(np.asarray(rust), py)


def test_counts_match_python_reference():
    x = make_blobs()
    py = PyDbscan(eps=1.0, min_pts=5).fit(x)
    m = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5)
    m.fit(x)
    assert m.n_clusters == py.n_clusters_
    assert m.n_noise == py.n_noise_


def test_fit_predict_agrees_with_fit_then_labels():
    """`fit_predict` is documented as fit + labels; prove it is not a shortcut."""
    x = make_blobs()
    a = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5)
    a.fit(x)
    b = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5)
    np.testing.assert_array_equal(a.labels(), b.fit_predict(x))


# --------------------------------------------------------------------------
# Hyperparameter pass-through
# --------------------------------------------------------------------------


def test_eps_is_readable_and_defaults_match_python():
    assert rust_pyo3_dbscan.Dbscan().eps == 0.5
    assert rust_pyo3_dbscan.Dbscan().min_pts == 5
    assert rust_pyo3_dbscan.Dbscan(eps=1.5, min_pts=9).eps == 1.5
    assert rust_pyo3_dbscan.Dbscan(eps=1.5, min_pts=9).min_pts == 9


def test_hyperparameters_reach_the_algorithm():
    """A huge eps must merge everything into one cluster; min_pts matters too."""
    x = make_blobs()
    m = rust_pyo3_dbscan.Dbscan(eps=100.0, min_pts=5)
    m.fit(x)
    assert m.n_clusters == 1

    sparse = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=400)
    sparse.fit(x)
    assert sparse.n_clusters == 0
    assert sparse.n_noise == 600


# --------------------------------------------------------------------------
# Error paths — Rust Result/Err mapped onto Python exceptions
# --------------------------------------------------------------------------


@pytest.mark.parametrize("bad_eps", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_eps_raises_value_error(bad_eps):
    with pytest.raises(ValueError):
        rust_pyo3_dbscan.Dbscan(eps=bad_eps, min_pts=5)


def test_zero_min_pts_raises_value_error():
    with pytest.raises(ValueError):
        rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=0)


def test_labels_before_fit_raises_value_error():
    with pytest.raises(ValueError, match="not fitted"):
        rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5).labels()


def test_counts_before_fit_are_zero_not_an_error():
    """Mirrors Stage 1, where n_clusters/n_noise are plain getters defaulting to 0."""
    m = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5)
    assert m.n_clusters == 0
    assert m.n_noise == 0


def test_wrong_dtype_is_rejected():
    x = np.zeros((10, 2), dtype=np.int32)
    with pytest.raises((TypeError, ValueError)):
        rust_pyo3_dbscan.Dbscan().fit(x)


def test_wrong_ndim_is_rejected():
    x = np.zeros(10, dtype=np.float64)  # 1-D, not (n, d)
    with pytest.raises((TypeError, ValueError)):
        rust_pyo3_dbscan.Dbscan().fit(x)


# --------------------------------------------------------------------------
# Edge cases Stage 1 covers in Rust
# --------------------------------------------------------------------------


def test_empty_input():
    m = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5)
    m.fit(np.zeros((0, 2)))
    assert m.labels() == []
    assert m.n_clusters == 0
    assert m.n_noise == 0


def test_single_point_with_min_pts_one():
    m = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=1)
    m.fit(np.array([[0.0, 0.0]]))
    assert m.labels() == [0]
    assert m.n_clusters == 1


def test_duplicate_points_do_not_break_clustering():
    x = np.repeat(np.array([[0.0, 0.0], [1.0, 1.0]]), 10, axis=0)
    py = PyDbscan(eps=0.5, min_pts=3).fit_predict(x)
    rust = rust_pyo3_dbscan.Dbscan(eps=0.5, min_pts=3).fit_predict(x)
    np.testing.assert_array_equal(np.asarray(rust), py)


def test_input_is_not_mutated_by_fit():
    x = make_blobs()
    before = x.copy()
    rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5).fit(x)
    np.testing.assert_array_equal(x, before)

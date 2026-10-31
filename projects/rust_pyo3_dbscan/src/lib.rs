//! PyO3 bindings for the Stage 1 `rust_dbscan` crate.
//!
//! Stage 2 of 副线 3 (Rust 渐进式学习). The point of this crate is the binding
//! layer, not the algorithm: `Dbscan` below is a thin `#[pyclass]` wrapper that
//! forwards to `rust_dbscan::Dbscan` unchanged.
//!
//! Four things this file is here to demonstrate (see
//! `docs/superpowers/specs/rust-stage2-3/2026-10-21-pyo3-candle-design.md` §1.3):
//!
//! 1. `#[pyclass]` / `#[pymethods]` / `#[new]` — a Rust struct becomes a Python
//!    class with a normal constructor signature.
//! 2. `PyReadonlyArray2<f64>` — NumPy interop. Extracting it validates dtype,
//!    ndim and contiguity for us; we then move the data into an `Array2<f64>`.
//! 3. `Python::detach` — **GIL release**. Stage 1's `fit` takes ~705 ms at
//!    n=5000. Holding the GIL across that makes every concurrent caller
//!    serialise behind us; releasing it is what makes PyO3 worth the FFI.
//! 4. `Result<_, String>` → `PyErr` — mapping Rust errors onto Python exceptions
//!    that callers can actually catch.
//!
//! An honest note on zero-copy: `rust_dbscan::Dbscan::fit` takes `Array2<f64>`
//! **by value**, so the NumPy buffer has to be copied once regardless of what
//! the binding does. `as_array()` is a zero-copy *view*, but `fit` consumes it.
//! We keep Stage 1's signature and pay one O(n·d) copy — negligible next to the
//! O(n²) clustering itself. See design doc §1.5.

use ndarray::Array2;
use numpy::PyReadonlyArray2;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Python-callable DBSCAN.
///
/// Mirrors the Python reference (`models/dbscan.py`) so the two are drop-in
/// replacements for each other:
///
/// ```python
/// import numpy as np, rust_pyo3_dbscan
///
/// m = rust_pyo3_dbscan.Dbscan(eps=1.0, min_pts=5)
/// m.fit(np.random.rand(500, 2))
/// print(m.n_clusters, m.n_noise)
/// ```
#[pyclass(name = "Dbscan", module = "rust_pyo3_dbscan")]
struct DbscanPy {
    /// `None` until `fit` succeeds — mirrors Stage 1's "not fitted" state so we
    /// can raise a Python `ValueError` instead of returning garbage.
    inner: Option<rust_dbscan::Dbscan>,
    eps: f64,
    min_pts: usize,
}

#[pymethods]
impl DbscanPy {
    /// Validate hyperparameters up front rather than at `fit` time, so a bad
    /// value fails where it was written instead of one call later.
    #[new]
    #[pyo3(signature = (eps=0.5, min_pts=5))]
    fn new(eps: f64, min_pts: usize) -> PyResult<Self> {
        if !eps.is_finite() || eps <= 0.0 {
            return Err(PyValueError::new_err(format!(
                "eps must be > 0 (got {eps})"
            )));
        }
        if min_pts == 0 {
            return Err(PyValueError::new_err("min_pts must be >= 1"));
        }
        Ok(Self {
            inner: None,
            eps,
            min_pts,
        })
    }

    /// Run DBSCAN clustering on an `(n, d)` array.
    ///
    /// The GIL is released for the duration of the fit. The array is copied out
    /// of NumPy first (Stage 1's `fit` consumes it by value), and that copy
    /// happens while we still hold the GIL.
    #[pyo3(signature = (x))]
    fn fit(&mut self, py: Python<'_>, x: PyReadonlyArray2<'_, f64>) -> PyResult<()> {
        let owned: Array2<f64> = x.as_array().to_owned();
        let model = rust_dbscan::Dbscan::new(self.eps, self.min_pts);

        let fitted = py
            .detach(|| model.fit(owned))
            .map_err(PyValueError::new_err)?;

        self.inner = Some(fitted);
        Ok(())
    }

    /// Cluster labels: `>= 0` is a cluster id, `-1` is noise.
    ///
    /// Returns a Python list. Stage 1's labels are `&[i64]`; for the benchmark
    /// sizes here (n ≤ 10k) the conversion is not the bottleneck, and
    /// `numpy.asarray(model.labels())` on the Python side is one call.
    fn labels(&self) -> PyResult<Vec<i64>> {
        self.inner
            .as_ref()
            .ok_or_else(|| PyValueError::new_err("not fitted: call fit() first"))?
            .labels()
            .map(|l| l.to_vec())
            .map_err(PyValueError::new_err)
    }

    /// Fit then return labels in one call, like the Python reference's
    /// `fit_predict`.
    #[pyo3(signature = (x))]
    fn fit_predict(&mut self, py: Python<'_>, x: PyReadonlyArray2<'_, f64>) -> PyResult<Vec<i64>> {
        self.fit(py, x)?;
        self.labels()
    }

    /// Number of clusters discovered (0 before `fit`).
    #[getter]
    fn n_clusters(&self) -> usize {
        self.inner.as_ref().map_or(0, |m| m.n_clusters())
    }

    /// Number of noise points discovered (0 before `fit`).
    #[getter]
    fn n_noise(&self) -> usize {
        self.inner.as_ref().map_or(0, |m| m.n_noise())
    }

    /// The eps radius this model was built with.
    #[getter]
    fn eps(&self) -> f64 {
        self.eps
    }

    /// The min_pts threshold this model was built with.
    #[getter]
    fn min_pts(&self) -> usize {
        self.min_pts
    }
}

/// `import rust_pyo3_dbscan` → this module.
#[pymodule]
fn rust_pyo3_dbscan(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<DbscanPy>()?;
    Ok(())
}

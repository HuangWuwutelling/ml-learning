pub mod config;
pub mod error;
pub mod model;
pub mod routes;
pub mod schema;

use std::sync::{Arc, OnceLock};
use std::time::Instant;

use axum::routing::{get, post};
use axum::Router;
use tower_http::trace::TraceLayer;

use crate::config::Config;
use crate::model::Embedder;

/// Shared state handed to every handler. `Clone` because axum clones it into
/// each request; every field is cheap to clone on purpose (Config is all owned
/// scalars and paths, the Instant is a pointer-sized counter, the OnceLock is
/// an Arc).
#[derive(Clone)]
pub struct AppState {
    pub config: Arc<Config>,
    started_at: Instant,
    embedder: Arc<OnceLock<Arc<Embedder>>>,
}

impl AppState {
    pub fn new(config: Config) -> Self {
        Self {
            config: Arc::new(config),
            started_at: Instant::now(),
            embedder: Arc::new(OnceLock::new()),
        }
    }

    /// None until the background load task lands. Handlers must treat this as
    /// "not ready yet", never as an error worth hiding behind a default.
    pub fn embedder(&self) -> Option<&Arc<Embedder>> {
        self.embedder.get()
    }

    pub fn model_loaded(&self) -> bool {
        self.embedder.get().is_some()
    }

    /// Set once, by the loader. A second call returns the value that won the
    /// race rather than panicking, so a duplicate load is a no-op.
    pub fn install_embedder(&self, embedder: Arc<Embedder>) -> Result<(), Arc<Embedder>> {
        self.embedder.set(embedder)
    }

    pub fn uptime_s(&self) -> f64 {
        self.started_at.elapsed().as_secs_f64()
    }
}

pub fn app(state: AppState) -> Router {
    Router::new()
        .route("/healthz", get(routes::health::healthz))
        .route("/readyz", get(routes::health::readyz))
        .route("/v1/embeddings", post(routes::embed::embeddings))
        // TraceLayer goes after .route() so it sees the matched route name, and
        // before .with_state() so it wraps the routes but not the 404 fallback.
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}
pub mod config;
pub mod routes;
pub mod schema;

use std::time::Instant;

use axum::routing::get;
use axum::Router;
use tower_http::trace::TraceLayer;

use crate::config::Config;

/// Shared state handed to every handler. `Clone` because axum clones it into
/// each request; every field here is cheap to clone on purpose (Config is a
/// SocketAddr + a Duration, the Instant is a pointer-sized counter).
#[derive(Clone, Debug)]
pub struct AppState {
    pub config: Config,
    started_at: Instant,
    pub model_loaded: bool,
}

impl AppState {
    pub fn new(config: Config) -> Self {
        Self {
            config,
            started_at: Instant::now(),
            // Step 7 ships no model, so there is nothing to wait for and the
            // instance is ready the moment it binds. Step 8 sets this false at
            // startup and flips it once the weights finish loading, which is
            // what makes /readyz worth having.
            model_loaded: true,
        }
    }

    pub fn uptime_s(&self) -> f64 {
        self.started_at.elapsed().as_secs_f64()
    }
}

pub fn app(state: AppState) -> Router {
    Router::new()
        .route("/healthz", get(routes::health::healthz))
        .route("/readyz", get(routes::health::readyz))
        // TraceLayer goes after .route() so it sees the matched route name, and
        // before .with_state() so it wraps the routes but not the 404 fallback.
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}
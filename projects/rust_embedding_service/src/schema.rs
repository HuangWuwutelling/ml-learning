use serde::Serialize;

/// GET /healthz — "is this process alive?"
///
/// Deliberately says nothing about the model. A liveness probe that fails gets
/// the container restarted, and restarting would not fix a model that is merely
/// slow to load.
#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: &'static str,
    pub uptime_s: f64,
}

/// GET /readyz — "should traffic be routed here yet?"
///
/// Separate from /healthz because loading weights is slow enough that a rolling
/// deploy would otherwise send requests to a process that cannot answer them.
#[derive(Debug, Serialize)]
pub struct ReadyResponse {
    pub status: &'static str,
    pub model_loaded: bool,
}
use axum::extract::State;
use axum::Json;

use crate::schema::{HealthResponse, ReadyResponse};
use crate::AppState;

pub async fn healthz(State(state): State<AppState>) -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok",
        uptime_s: state.uptime_s(),
    })
}

pub async fn readyz(State(state): State<AppState>) -> Json<ReadyResponse> {
    Json(ReadyResponse {
        status: if state.model_loaded {
            "ready"
        } else {
            "loading"
        },
        model_loaded: state.model_loaded,
    })
}
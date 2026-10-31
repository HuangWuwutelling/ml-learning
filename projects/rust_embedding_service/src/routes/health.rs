use axum::extract::State;
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;

use crate::schema::{HealthResponse, ReadyResponse};
use crate::AppState;

pub async fn healthz(State(state): State<AppState>) -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok",
        uptime_s: state.uptime_s(),
    })
}

/// 503 while the weights load, 200 after.
///
/// The status code is the load-bearing part. A Kubernetes readinessProbe
/// treats any 2xx as "route traffic here", so answering 200 with
/// `{"status": "loading"}` in the body would advertise the instance as ready
/// for the entire load window — the exact failure this endpoint exists to
/// prevent. The body is for humans; the code is for the probe.
pub async fn readyz(State(state): State<AppState>) -> Response {
    let ready = state.model_loaded();
    let body = Json(ReadyResponse {
        status: if ready { "ready" } else { "loading" },
        model_loaded: ready,
    });
    let status = if ready {
        StatusCode::OK
    } else {
        StatusCode::SERVICE_UNAVAILABLE
    };
    (status, body).into_response()
}
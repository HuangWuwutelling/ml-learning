use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;

/// OpenAI's error envelope: `{"error": {"message": ..., "type": ...}}`.
/// Same reasoning as the success schema — if we are claiming OpenAI
/// compatibility, errors have to look like OpenAI's too, or SDK retry logic
/// that keys on the error type will not recognise them.
#[derive(Debug)]
pub enum AppError {
    /// Client sent something the service will not act on.
    BadRequest(String),
    /// The weights are still loading, or failed to load. 503 rather than 500:
    /// this is the retryable condition, and a load balancer should route
    /// around it instead of treating the instance as broken.
    ModelUnavailable,
    Inference(String),
}

impl AppError {
    pub fn bad_request(msg: impl Into<String>) -> Self {
        AppError::BadRequest(msg.into())
    }

    fn parts(&self) -> (StatusCode, &'static str, String) {
        match self {
            AppError::BadRequest(m) => (
                StatusCode::BAD_REQUEST,
                "invalid_request_error",
                m.clone(),
            ),
            AppError::ModelUnavailable => (
                StatusCode::SERVICE_UNAVAILABLE,
                "model_unavailable",
                "model is still loading; retry shortly".to_string(),
            ),
            AppError::Inference(m) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "inference_error",
                m.clone(),
            ),
        }
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, kind, message) = self.parts();
        (status, Json(serde_json::json!({ "error": { "message": message, "type": kind } })))
            .into_response()
    }
}
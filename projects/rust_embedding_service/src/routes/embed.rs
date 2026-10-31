use std::sync::Arc;

use axum::extract::State;
use axum::Json;

use crate::error::AppError;
use crate::schema::{EmbedData, EmbedRequest, EmbedResponse, EmbedUsage};
use crate::AppState;

pub async fn embeddings(
    State(state): State<AppState>,
    Json(request): Json<EmbedRequest>,
) -> Result<Json<EmbedResponse>, AppError> {
    let texts = request.input.into_texts();
    if texts.is_empty() {
        return Err(AppError::bad_request(
            "`input` must contain at least one string",
        ));
    }

    let embedder = state
        .embedder()
        .ok_or(AppError::ModelUnavailable)?
        .clone();

    if let Some(requested) = &request.model {
        if requested != embedder.name() {
            return Err(AppError::bad_request(format!(
                "this server serves only {:?}, got {requested:?}",
                embedder.name()
            )));
        }
    }

    // candle inference is CPU-bound and synchronous. Called directly here it
    // would park the runtime worker for the whole forward pass and stall every
    // other connection on that worker -- with a 0.5B model that is hundreds of
    // milliseconds of frozen health checks. spawn_blocking moves it onto the
    // blocking threadpool where it belongs.
    let worker = Arc::clone(&embedder);
    let output = tokio::task::spawn_blocking(move || worker.embed(texts))
        .await
        .map_err(|e| AppError::Inference(format!("embedding task failed: {e}")))?
        .map_err(|e| AppError::Inference(e.to_string()))?;

    Ok(Json(EmbedResponse {
        model: embedder.name().to_string(),
        dimensions: embedder.dimensions(),
        data: output
            .vectors
            .into_iter()
            .enumerate()
            .map(|(index, embedding)| EmbedData { index, embedding })
            .collect(),
        usage: EmbedUsage {
            prompt_tokens: output.prompt_tokens,
            total_tokens: output.prompt_tokens,
        },
    }))
}
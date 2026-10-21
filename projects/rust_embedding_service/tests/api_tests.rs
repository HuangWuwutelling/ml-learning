use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode};
use rust_embedding_service::{app, config::Config, AppState};
use tower::ServiceExt;

fn state() -> AppState {
    AppState::new(Config::default())
}

/// Drive one request through the Router without binding a port. This is the
/// reason the router lives in the lib: `tests/` cannot see `main.rs`, and a
/// test that binds :8080 would collide with a running dev server.
async fn send(uri: &str) -> (StatusCode, Vec<u8>) {
    let response = app(state())
        .oneshot(Request::get(uri).body(Body::empty()).unwrap())
        .await
        .expect("router should not error");
    let status = response.status();
    let bytes = to_bytes(response.into_body(), usize::MAX)
        .await
        .expect("body should read");
    (status, bytes.to_vec())
}

async fn get_json(uri: &str) -> (StatusCode, serde_json::Value) {
    let (status, bytes) = send(uri).await;
    let value = serde_json::from_slice(&bytes)
        .unwrap_or_else(|e| panic!("{uri} returned a non-JSON body: {e}"));
    (status, value)
}

#[tokio::test]
async fn healthz_is_ok_and_reports_uptime() {
    let (status, body) = get_json("/healthz").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(body["status"], "ok");
    // Uptime starts at 0 and only grows; just assert it is a real number.
    assert!(body["uptime_s"].as_f64().is_some_and(|s| s >= 0.0));
}

#[tokio::test]
async fn readyz_is_ok_with_no_model_to_wait_for() {
    let (status, body) = get_json("/readyz").await;
    assert_eq!(status, StatusCode::OK);
    // Step 7 ships no model, so the instance is ready as soon as it binds.
    // Step 8 flips model_loaded to false at startup and back once the weights
    // load — this assertion is the one that will fail on purpose then.
    assert_eq!(body["status"], "ready");
    assert_eq!(body["model_loaded"], true);
}

/// Pins the negative space so step 8's /v1/embeddings landing is a real
/// behavioural change with a test that notices, not just a new file.
#[tokio::test]
async fn embeddings_route_does_not_exist_yet() {
    let (status, _) = send("/v1/embeddings").await;
    assert_eq!(status, StatusCode::NOT_FOUND);
}
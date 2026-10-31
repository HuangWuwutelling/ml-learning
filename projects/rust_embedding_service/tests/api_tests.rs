use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode};
use rust_embedding_service::{app, config::Config, AppState};
use tower::ServiceExt;

/// These tests never load the model: doing so means mmap-ing ~1 GB of weights
/// and running a 24-layer forward pass, which is not what a routing test should
/// cost. Real inference is covered by `examples/bench_http.rs` (step 9).
fn state() -> AppState {
    AppState::new(Config::default())
}

/// Drive one request through the Router without binding a port. This is the
/// reason the router lives in the lib: `tests/` cannot see `main.rs`, and a
/// test that binds :8080 would collide with a running dev server.
async fn send(request: Request<Body>) -> (StatusCode, Vec<u8>) {
    let response = app(state())
        .oneshot(request)
        .await
        .expect("router should not error");
    let status = response.status();
    let bytes = to_bytes(response.into_body(), usize::MAX)
        .await
        .expect("body should read");
    (status, bytes.to_vec())
}

async fn get(uri: &str) -> (StatusCode, serde_json::Value) {
    let (status, bytes) = send(Request::get(uri).body(Body::empty()).unwrap()).await;
    let value = serde_json::from_slice(&bytes)
        .unwrap_or_else(|e| panic!("{uri} returned a non-JSON body: {e}"));
    (status, value)
}

async fn post_json(uri: &str, body: serde_json::Value) -> (StatusCode, serde_json::Value) {
    let request = Request::post(uri)
        .header("content-type", "application/json")
        .body(Body::from(body.to_string()))
        .unwrap();
    let (status, bytes) = send(request).await;
    let value = serde_json::from_slice(&bytes)
        .unwrap_or_else(|e| panic!("{uri} returned a non-JSON body: {e}"));
    (status, value)
}

#[tokio::test]
async fn healthz_is_ok_and_reports_uptime() {
    let (status, body) = get("/healthz").await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(body["status"], "ok");
    // Uptime starts at 0 and only grows; just assert it is a real number.
    assert!(body["uptime_s"].as_f64().is_some_and(|s| s >= 0.0));
}

/// 503, not 200-with-a-loading-body: a 2xx here tells a readiness probe to
/// route traffic to an instance that cannot serve a single embedding.
#[tokio::test]
async fn readyz_is_503_until_the_model_lands() {
    let (status, body) = get("/readyz").await;
    assert_eq!(status, StatusCode::SERVICE_UNAVAILABLE);
    assert_eq!(body["status"], "loading");
    assert_eq!(body["model_loaded"], false);
}

/// /healthz must NOT share /readyz's failure mode. The process is alive and
/// serving; only the model is missing, and restarting would not help.
#[tokio::test]
async fn healthz_stays_200_while_the_model_loads() {
    let (status, _) = get("/healthz").await;
    assert_eq!(status, StatusCode::OK);
}

#[tokio::test]
async fn embeddings_are_503_until_the_model_lands() {
    let (status, body) = post_json("/v1/embeddings", serde_json::json!({"input": "生态环境法典"})).await;
    assert_eq!(status, StatusCode::SERVICE_UNAVAILABLE);
    assert_eq!(body["error"]["type"], "model_unavailable");
}

/// Input validation runs before the model check, so a malformed request is a
/// client error even on a cold instance. Getting this order wrong would turn
/// every typo into a 503 and send clients into pointless retry loops.
#[tokio::test]
async fn empty_batch_is_a_client_error_not_a_503() {
    let (status, body) = post_json("/v1/embeddings", serde_json::json!({"input": []})).await;
    assert_eq!(status, StatusCode::BAD_REQUEST);
    assert_eq!(body["error"]["type"], "invalid_request_error");
}

#[tokio::test]
async fn unknown_route_is_404() {
    let (status, _) = send(Request::get("/nope").body(Body::empty()).unwrap()).await;
    assert_eq!(status, StatusCode::NOT_FOUND);
}
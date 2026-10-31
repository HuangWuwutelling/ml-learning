use std::sync::Arc;

use rust_embedding_service::model::Embedder;
use rust_embedding_service::{app, config::Config, AppState};
use tokio::net::TcpListener;

/// Resolve on Ctrl-C, or on SIGTERM so `docker stop` and Kubernetes pod
/// deletion shut down as cleanly as a keyboard interrupt does.
async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install Ctrl-C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("failed to install SIGTERM handler")
            .recv()
            .await;
    };

    // Windows has no SIGTERM arriving the way it does on Unix; Ctrl-C covers it.
    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }
    tracing::info!("shutdown signal received");
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    let config = Config::from_env();

    // Bind before loading. A liveness probe that cannot connect during startup
    // gets the container killed at exactly the moment it is doing the slow
    // work it was started to do. So: port first, weights second, /readyz
    // honest about which phase we are in.
    let listener = TcpListener::bind(config.addr).await?;
    tracing::info!(addr = %config.addr, "listening");

    let state = AppState::new(config.clone());
    let server = app(state.clone());

    let loader = tokio::task::spawn_blocking({
        let config = config.clone();
        let state = state.clone();
        move || {
            if !config.model_dir.join("model.safetensors").exists() {
                tracing::error!(
                    dir = %config.model_dir.display(),
                    "no model.safetensors there; set EMBED_MODEL_DIR. \
                     /readyz will stay 503 and every /v1/embeddings will fail."
                );
                return;
            }
            match Embedder::load(&config.model_dir, config.model_name.clone(), config.max_tokens) {
                Ok(embedder) => {
                    tracing::info!(
                        model = %embedder.name(),
                        dimensions = embedder.dimensions(),
                        max_tokens = config.max_tokens,
                        "model loaded"
                    );
                    if state.install_embedder(Arc::new(embedder)).is_err() {
                        tracing::warn!("another loader already installed a model");
                    }
                }
                Err(err) => {
                    // Not fatal to the process, but it *is* fatal to the
                    // service: /readyz stays 503 forever, which is the honest
                    // signal. Exiting would be equally honest and easier to
                    // alert on; that is a Stage 9 decision.
                    tracing::error!(%err, "model load failed; /readyz will stay 503");
                }
            }
        }
    });

    axum::serve(listener, server)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    loader.await.ok();
    tracing::info!("shutdown complete");
    Ok(())
}
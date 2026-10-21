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
    let state = AppState::new(config.clone());
    let listener = TcpListener::bind(config.addr).await?;
    tracing::info!(addr = %config.addr, "listening");

    axum::serve(listener, app(state))
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    tracing::info!("shutdown complete");
    Ok(())
}
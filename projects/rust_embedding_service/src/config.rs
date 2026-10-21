use std::net::SocketAddr;
use std::time::Duration;

/// Runtime configuration. Every field has a working default so the service
/// boots with no environment set up, but each is overridable — a container
/// that forgets one env var should fall back to localhost, not refuse to
/// start.
#[derive(Debug, Clone)]
pub struct Config {
    pub addr: SocketAddr,
    /// How long in-flight requests get after a shutdown signal before axum
    /// stops waiting for them.
    pub shutdown_grace: Duration,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            addr: SocketAddr::from(([127, 0, 0, 1], 8080)),
            shutdown_grace: Duration::from_secs(10),
        }
    }
}

impl Config {
    pub fn from_env() -> Self {
        let d = Self::default();
        Self {
            addr: env_parse("EMBED_ADDR").unwrap_or(d.addr),
            shutdown_grace: env_parse("EMBED_SHUTDOWN_GRACE_SECS")
                .map(Duration::from_secs)
                .unwrap_or(d.shutdown_grace),
        }
    }
}

/// A malformed env var must not take the service down: log it and use the
/// default. The alternative is a container that refuses to boot because of a
/// typo in a variable nobody reads until the day it matters.
fn env_parse<T: std::str::FromStr>(key: &str) -> Option<T> {
    let raw = std::env::var(key).ok()?;
    match raw.parse() {
        Ok(v) => Some(v),
        Err(_) => {
            tracing::warn!(key, value = %raw, "unparseable env var, falling back to default");
            None
        }
    }
}
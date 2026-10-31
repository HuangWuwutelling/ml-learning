use std::net::SocketAddr;
use std::path::PathBuf;
use std::time::Duration;

use crate::model::default_model_dir;

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
    /// Directory holding config.json / model.safetensors / tokenizer.json.
    pub model_dir: PathBuf,
    /// Reported back as the `model` field. Also the value a client must send
    /// back to be accepted.
    pub model_name: String,
    /// Per-input token cap. The model's own limit is 32768, but a 32k-token
    /// forward pass on CPU is minutes, not milliseconds — a service that will
    /// not refuse a pathological input is a service that will fall over on one.
    pub max_tokens: usize,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            addr: SocketAddr::from(([127, 0, 0, 1], 8080)),
            shutdown_grace: Duration::from_secs(10),
            model_dir: default_model_dir().unwrap_or_default(),
            model_name: "Qwen2.5-0.5B".to_string(),
            max_tokens: 512,
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
            model_dir: env_str("EMBED_MODEL_DIR").map(Into::into).unwrap_or(d.model_dir),
            model_name: env_str("EMBED_MODEL_NAME").unwrap_or(d.model_name),
            max_tokens: env_parse("EMBED_MAX_TOKENS").unwrap_or(d.max_tokens),
        }
    }
}

/// A malformed env var must not take the service down: log it and use the
/// default. The alternative is a container that refuses to boot because of a
/// typo in a variable nobody reads until the day it matters.
fn env_parse<T: std::str::FromStr>(key: &str) -> Option<T> {
    let raw = env_str(key)?;
    match raw.parse() {
        Ok(v) => Some(v),
        Err(_) => {
            tracing::warn!(key, value = %raw, "unparseable env var, falling back to default");
            None
        }
    }
}

fn env_str(key: &str) -> Option<String> {
    std::env::var(key).ok().filter(|v| !v.trim().is_empty())
}
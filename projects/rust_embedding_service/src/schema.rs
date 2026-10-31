use serde::{Deserialize, Serialize};

/// GET /healthz — "is this process alive?"
///
/// Deliberately says nothing about the model. A liveness probe that fails gets
/// the container restarted, and restarting would not fix a model that is merely
/// slow to load.
#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: &'static str,
    pub uptime_s: f64,
}

/// GET /readyz — "should traffic be routed here yet?"
///
/// Separate from /healthz because loading weights is slow enough that a rolling
/// deploy would otherwise send requests to a process that cannot answer them.
#[derive(Debug, Serialize)]
pub struct ReadyResponse {
    pub status: &'static str,
    pub model_loaded: bool,
}

/// OpenAI's /v1/embeddings accepts a bare string or an array; every client in
/// the wild sends one or the other, so accept both rather than forcing callers
/// to normalise.
#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum EmbedInput {
    Single(String),
    Batch(Vec<String>),
}

impl EmbedInput {
    pub fn into_texts(self) -> Vec<String> {
        match self {
            EmbedInput::Single(s) => vec![s],
            EmbedInput::Batch(v) => v,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct EmbedRequest {
    pub input: EmbedInput,
    /// Accepted for client compatibility, but this server serves exactly one
    /// model and a mismatch is rejected rather than ignored -- silently
    /// ignoring it is how two clients end up comparing embeddings produced by
    /// different models and reporting nonsense similarity.
    #[serde(default)]
    pub model: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct EmbedData {
    pub index: usize,
    pub embedding: Vec<f32>,
}

#[derive(Debug, Serialize)]
pub struct EmbedUsage {
    pub prompt_tokens: usize,
    pub total_tokens: usize,
}

/// Deliberately mirrors OpenAI's response shape so any OpenAI SDK works by
/// changing base_url. That is the whole point of picking this schema over a
/// private one.
#[derive(Debug, Serialize)]
pub struct EmbedResponse {
    pub model: String,
    pub dimensions: usize,
    pub data: Vec<EmbedData>,
    pub usage: EmbedUsage,
}
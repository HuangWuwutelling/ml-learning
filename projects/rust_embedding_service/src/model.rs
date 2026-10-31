use std::path::{Path, PathBuf};
use std::sync::Mutex;

use candle_core::{DType, Device, IndexOp, Result, Tensor};
use candle_nn::VarBuilder;
use candle_transformers::models::qwen2::{Config, Model};
use tokenizers::{Tokenizer, TruncationParams, TruncationStrategy};

pub struct EmbedOutput {
    pub vectors: Vec<Vec<f32>>,
    pub prompt_tokens: usize,
}

/// A loaded model plus its tokenizer.
///
/// `Mutex<Model>` rather than a bare `Model`: `qwen2::Model::forward` takes
/// `&mut self` because it maintains a KV cache for autoregressive decoding.
/// See `embed()` — that cache is written on *every* forward, so concurrent
/// requests must be serialised or they read each other's keys. The mutex is a
/// correctness requirement here, not a performance limitation.
pub struct Embedder {
    model: Mutex<Model>,
    tokenizer: Tokenizer,
    dimensions: usize,
    name: String,
}

impl Embedder {
    pub fn load(dir: &Path, name: String, max_tokens: usize) -> Result<Self> {
        let device = Device::Cpu;

        let config_path = dir.join("config.json");
        let raw = std::fs::read_to_string(&config_path)
            .map_err(|e| candle_core::Error::Msg(format!("read {}: {e}", config_path.display())))?;
        let cfg: Config = serde_json::from_str(&raw).map_err(|e| {
            candle_core::Error::Msg(format!("parse {}: {e}", config_path.display()))
        })?;

        let weights = dir.join("model.safetensors");
        // SAFETY: the mapping is read-only for the life of the VarBuilder and
        // this process never writes to the safetensors file. mmap on Windows
        // requires the file to stay open, which the VarBuilder's own handle
        // guarantees — we never drop it before the tensors are used.
        let vb = unsafe {
            VarBuilder::from_mmaped_safetensors(&[weights], DType::F32, &device)
                .map_err(|e| candle_core::Error::Msg(e.to_string()))?
        };
        // `Model::new` calls `vb.pp("model")` itself, so hand it the root
        // builder -- passing an already-prefixed one looks for
        // "model.model.embed_tokens.weight" and fails at load.
        let model = Model::new(&cfg, vb)?;

        let tokenizer_path = dir.join("tokenizer.json");
        let mut tokenizer = Tokenizer::from_file(&tokenizer_path).map_err(|e| {
            candle_core::Error::Msg(format!("load {}: {e}", tokenizer_path.display()))
        })?;
        tokenizer
            .with_truncation(Some(TruncationParams {
                max_length: max_tokens,
                strategy: TruncationStrategy::LongestFirst,
                ..Default::default()
            }))
            .map_err(|e| {
                candle_core::Error::Msg(format!(
                    "set truncation to {max_tokens} tokens: {e}"
                ))
            })?;

        Ok(Self {
            model: Mutex::new(model),
            tokenizer,
            dimensions: cfg.hidden_size,
            name,
        })
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn dimensions(&self) -> usize {
        self.dimensions
    }

    pub fn embed(&self, texts: Vec<String>) -> Result<EmbedOutput> {
        // add_special_tokens = false: Qwen2 has no BOS convention, and adding
        // one would change which token ends up last.
        let mut rows: Vec<Vec<u32>> = Vec::with_capacity(texts.len());
        let mut prompt_tokens = 0usize;
        for text in &texts {
            let encoding = self
                .tokenizer
                .encode(text.as_str(), false)
                .map_err(|e| candle_core::Error::Msg(e.to_string()))?;
            if encoding.is_empty() {
                return Err(candle_core::Error::Msg(format!(
                    "input tokenized to zero tokens: {text:?}"
                )));
            }
            prompt_tokens += encoding.len();
            rows.push(encoding.get_ids().to_vec());
        }

        // candle 0.11's Tensor::new infers the shape from the nested vec, so
        // (batch, seq_len) falls out of the data instead of being passed in.
        let input_ids = Tensor::new(pad_right(&rows), &Device::Cpu)?;

        let mut model = self
            .model
            .lock()
            .map_err(|_| candle_core::Error::Msg("model mutex poisoned".to_string()))?;

        let forward = model.forward(&input_ids, 0, None);
        // Unconditional, and before the `?`. qwen2's Attention::forward ends
        // with `self.kv_cache = Some(...)` on every call, including the first,
        // and the next call `cat`s the previous keys onto the new ones. Because
        // the cache only ever grows, k_len can never equal q_len again after
        // the first request, so the failure is immediate and loud: reusing an
        // Embedder without this line panics on the *second* request with
        // `shape mismatch in broadcast_add` (measured: a 7-token query leaves a
        // 7-token cache, the next 104-token input sees k_len 111 vs q_len 104).
        model.clear_kv_cache();
        let xs = forward?;

        let mut vectors = Vec::with_capacity(rows.len());
        for i in 0..rows.len() {
            let last = rows[i].len() - 1;
            let mut v = xs.i((i, last))?.flatten_all()?.to_vec1::<f32>()?;
            l2_normalize(&mut v);
            vectors.push(v);
        }

        Ok(EmbedOutput {
            vectors,
            prompt_tokens,
        })
    }
}

/// Right-pad every row to the longest sequence in the batch. Callers gather at
/// `row.len() - 1`, i.e. each row's own last real token, not `seq_len - 1`.
///
/// Padding with 0 is safe here and only here because attention is causal: a
/// token at position p attends to positions <= p, and pads live to the right of
/// every real token, so no real token ever attends to a pad. With bidirectional
/// (BERT-style) models this reasoning breaks and an explicit attention mask is
/// mandatory.
fn pad_right(rows: &[Vec<u32>]) -> Vec<Vec<u32>> {
    let seq_len = rows.iter().map(Vec::len).max().unwrap_or(1).max(1);
    let mut padded = Vec::with_capacity(rows.len());
    for row in rows {
        let mut r = row.clone();
        r.resize(seq_len, 0);
        padded.push(r);
    }
    padded
}

fn l2_normalize(v: &mut [f32]) {
    let norm = v.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        for x in v.iter_mut() {
            *x /= norm;
        }
    }
}

/// Qwen2.5-0.5B-Instruct is already in this machine's HF cache. The snapshot
/// directory is named after a content hash that changes if the model is ever
/// re-downloaded, so resolve it rather than hardcoding a path that rots.
pub fn default_model_dir() -> Option<PathBuf> {
    let snapshots = PathBuf::from(r"D:\Workspace\.cache\huggingface\hub")
        .join("models--Qwen--Qwen2.5-0.5B-Instruct")
        .join("snapshots");
    std::fs::read_dir(snapshots)
        .ok()?
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .find(|dir| dir.join("model.safetensors").exists())
}
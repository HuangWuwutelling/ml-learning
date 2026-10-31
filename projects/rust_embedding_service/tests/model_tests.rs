//! Real inference against Qwen2.5-0.5B-Instruct.
//!
//! `#[ignore]`d because it mmaps ~1 GB of weights and runs 24 transformer
//! layers on CPU. Run it explicitly:
//!
//! ```bash
//! cargo test --release --test model_tests -- --ignored --nocapture
//! ```
//!
//! Use `--release`: the debug build of a 0.5B model is slow enough to make
//! this suite take minutes, and every number below is a correctness check
//! rather than a timing one, so an optimised build is strictly better.

use rust_embedding_service::model::{default_model_dir, Embedder};

fn embedder() -> Option<Embedder> {
    let dir = std::env::var("EMBED_MODEL_DIR")
        .ok()
        .map(std::path::PathBuf::from)
        .or_else(default_model_dir)?;
    Some(Embedder::load(&dir, "Qwen2.5-0.5B".to_string(), 512).expect("model should load"))
}

fn cosine(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b).map(|(x, y)| x * y).sum();
    let na = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let nb = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    dot / (na * nb)
}

#[test]
#[ignore = "mmaps ~1 GB of weights; run explicitly"]
fn embedding_is_896_dim_and_l2_normalised() {
    let Some(e) = embedder() else {
        eprintln!("skipping: no local Qwen2.5-0.5B weights found");
        return;
    };
    let out = e.embed(vec!["生态环境法典自2026年1月1日起施行".to_string()]).unwrap();
    assert_eq!(out.vectors.len(), 1);
    assert_eq!(out.vectors[0].len(), 896);
    assert!(out.prompt_tokens > 0);

    let norm = out.vectors[0].iter().map(|x| x * x).sum::<f32>().sqrt();
    assert!((norm - 1.0).abs() < 1e-5, "expected unit norm, got {norm}");
}

/// The load-bearing test.
///
/// `qwen2::Attention::forward` ends with an unconditional
/// `self.kv_cache = Some(...)`, so a model reused across requests without
/// `clear_kv_cache()` concatenates request N's keys onto request N+1. Because
/// the cache only grows, `k_len` can never match `q_len` again after the first
/// request — this fails loudly on the second call rather than returning
/// quietly-wrong vectors, which was the initial assumption here and turned out
/// to be wrong when the line was commented out and this test re-run:
/// `shape mismatch in broadcast_add, lhs: [1, 14, 104, 111], rhs: [1, 1, 104, 104]`
/// (14 heads, q_len 104, k_len 111 = 104 stale + 7).
///
/// Worth pinning either way: the loud panic is a property of *this* candle
/// version's shape check, not a guarantee the API makes.
#[test]
#[ignore = "mmaps ~1 GB of weights; run explicitly"]
fn repeated_embedding_is_not_contaminated_by_an_intervening_request() {
    let Some(e) = embedder() else {
        eprintln!("skipping: no local Qwen2.5-0.5B weights found");
        return;
    };

    let query = "排污许可证延续需要重新申请吗";
    let distractor = "《固体废物污染环境防治法》第四十二条规定的处罚幅度".repeat(8);

    let first = e.embed(vec![query.to_string()]).unwrap().vectors.remove(0);

    // A different-length request in between. Without cache clearing this is
    // already enough to blow up: the stale cache is concatenated onto it.
    e.embed(vec![distractor]).unwrap();

    let again = e.embed(vec![query.to_string()]).unwrap().vectors.remove(0);

    let sim = cosine(&first, &again);
    assert!(
        sim > 0.9999,
        "same input gave cosine {sim} after an intervening request -- \
         the KV cache is leaking across requests"
    );
}

#[test]
#[ignore = "mmaps ~1 GB of weights; run explicitly"]
fn different_texts_produce_different_vectors() {
    let Some(e) = embedder() else {
        eprintln!("skipping: no local Qwen2.5-0.5B weights found");
        return;
    };
    let out = e
        .embed(vec![
            "排污单位应当按证排污".to_string(),
            "今天天气很好适合散步".to_string(),
        ])
        .unwrap();
    let sim = cosine(&out.vectors[0], &out.vectors[1]);
    assert!(sim < 0.999, "unrelated sentences collapsed to cosine {sim}");
}

/// Batching pads short rows out to the longest row in the batch. With causal
/// attention that must be a no-op mathematically, but different tensor shapes
/// can select different matmul kernels, so this asserts high similarity rather
/// than bit equality.
#[test]
#[ignore = "mmaps ~1 GB of weights; run explicitly"]
fn batching_matches_one_at_a_time() {
    let Some(e) = embedder() else {
        eprintln!("skipping: no local Qwen2.5-0.5B weights found");
        return;
    };
    let long = "生态环境部应当组织制定生态环境监测规范".to_string();
    let short = "罚款".to_string();

    let batched = e.embed(vec![short.clone(), long.clone()]).unwrap().vectors;
    let alone = e.embed(vec![short]).unwrap().vectors.remove(0);

    let sim = cosine(&batched[0], &alone);
    assert!(sim > 0.999, "padded batch diverged from single: cosine {sim}");
}
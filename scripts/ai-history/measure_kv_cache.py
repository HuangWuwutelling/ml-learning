"""Measure KV cache size and decode speed on local Qwen2.5-0.5B-Instruct (CPU).

Run from repo root:
    HF_HUB_OFFLINE=1 python scripts/ai-history/measure_kv_cache.py

The hub cache must already hold the snapshots:
    <HF_HOME>/hub/models--Qwen--Qwen2.5-0.5B-Instruct
    <HF_HOME>/hub/models--Qwen--Qwen2.5-7B-Instruct
Only drop HF_HUB_OFFLINE when downloading is actually needed, and set
HF_ENDPOINT=https://hf-mirror.com for that run.

Outputs JSON next to this script: scripts/ai-history/kv_cache_measure.json
Sections:
  cache        - [S] local measurement: KV cache bytes and prefill time per seq len
  decode       - [S] local measurement: decode time with and without cache
  official_cfg - [C] calculated from official config.json in the local HF cache
"""
import glob
import json
import os
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
REF_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
HF_HOME = os.environ.get("HF_HOME", r"D:\Workspace\.cache\huggingface")
# the hub cache is <HF_HOME>/hub; passing HF_HOME itself makes transformers
# start a fresh download instead of reusing the cached snapshot
CACHE_DIR = os.environ.get("HF_HUB_CACHE", os.path.join(HF_HOME, "hub"))
OUT_PATH = Path(__file__).resolve().parent / "kv_cache_measure.json"

SEQ_LENS = [128, 512, 2048]
DECODE_PROMPT_TOKENS = 512
DECODE_NEW_TOKENS = 8
THREADS = 4
CTX_LEN = 32768  # fallback only; each model's config.json gives the real value
REPEAT_TEXT = "The quick brown fox jumps over the lazy dog. " * 400


def cache_tensors(past_key_values):
    """Return [(key, value), ...] from a Cache object or a legacy tuple of tuples."""
    tensors = []
    if hasattr(past_key_values, "layers"):
        for layer in past_key_values.layers:
            tensors.append((getattr(layer, "keys", None), getattr(layer, "values", None)))
    elif hasattr(past_key_values, "key_cache"):
        for k, v in zip(past_key_values.key_cache, past_key_values.value_cache):
            tensors.append((k, v))
    else:
        for k, v in past_key_values:
            tensors.append((k, v))
    return tensors


def cache_bytes(past_key_values):
    total = 0
    for k, v in cache_tensors(past_key_values):
        for t in (k, v):
            if t is not None:
                total += t.numel() * t.element_size()
    return total


def find_config(model_id):
    """Locate the official config.json inside the hub cache.

    Only the hub cache (<HF_HOME>/hub) counts. An earlier version also
    searched the models--* folders directly under HF_HOME, which held the
    leftovers of a run that pointed transformers at HF_HOME instead of
    HF_HOME/hub; those folders are gone now, and searching them only
    widened the chance of reading a config from an arbitrary directory.
    Whatever is found is recorded as `source` in the JSON, so the number
    always names the exact file it was read from.
    """
    folder = "models--" + model_id.replace("/", "--")
    hits = glob.glob(str(Path(CACHE_DIR) / folder / "snapshots" / "*" / "config.json"))
    return hits[0] if hits else None


def official_config_block():
    """[C] KV cache footprint per model, computed from official config.json."""
    out = {}
    for model_id in (MODEL_ID, REF_MODEL_ID):
        path = find_config(model_id)
        if not path:
            out[model_id] = {"error": "config.json not found in local cache"}
            continue
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
        layers = cfg["num_hidden_layers"]
        kv_heads = cfg["num_key_value_heads"]
        head_dim = cfg["hidden_size"] // cfg["num_attention_heads"]
        ctx_len = cfg.get("max_position_embeddings") or CTX_LEN
        entry = {
            "source": path,
            "num_hidden_layers": layers,
            "num_attention_heads": cfg["num_attention_heads"],
            "num_key_value_heads": kv_heads,
            "hidden_size": cfg["hidden_size"],
            "head_dim": head_dim,
            "max_position_embeddings": cfg.get("max_position_embeddings"),
            "dtype": cfg.get("torch_dtype"),
            "formula": "2 (K and V) * layers * kv_heads * head_dim * dtype_bytes",
            "per_token_bytes": {},
            "ctx_bytes": {},
        }
        for label, nbytes in (("float32", 4), ("bfloat16", 2)):
            per_token = 2 * layers * kv_heads * head_dim * nbytes
            entry["per_token_bytes"][label] = per_token
            entry["ctx_bytes"][label] = {
                "ctx_len": ctx_len,
                "bytes": per_token * ctx_len,
                "mib": round(per_token * ctx_len / 1024 / 1024, 1),
            }
        out[model_id] = entry
    return out


def main():
    torch.set_num_threads(THREADS)
    tok = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=CACHE_DIR)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, cache_dir=CACHE_DIR, dtype=torch.float32
    )
    model.eval()

    cfg = model.config
    result = {
        "model": MODEL_ID,
        "device": "cpu",
        "threads": THREADS,
        "dtype": "float32",
        "config": {
            "num_hidden_layers": cfg.num_hidden_layers,
            "num_attention_heads": cfg.num_attention_heads,
            "num_key_value_heads": cfg.num_key_value_heads,
            "hidden_size": cfg.hidden_size,
            "max_position_embeddings": cfg.max_position_embeddings,
            "dtype": str(cfg.dtype),
        },
        "cache": [],
        "decode": {},
    }

    with torch.no_grad():
        # warmup: the very first forward in a cold process pays for paging in
        # the 1 GB weight file and for building the CPU primitive cache (about
        # 108 s on this machine), so prefill times are only comparable after
        # one throwaway pass
        warm_ids = torch.tensor([tok(REPEAT_TEXT).input_ids[:32]])
        model(warm_ids, use_cache=True, logits_to_keep=1)

        for n in SEQ_LENS:
            ids = torch.tensor([tok(REPEAT_TEXT).input_ids[:n]])
            assert ids.shape[1] == n, f"need {n} tokens, got {ids.shape[1]}"
            t0 = time.perf_counter()
            # logits_to_keep=1: skip the lm_head projection for every position
            # (a 2048-token forward would otherwise allocate 1.2 GB of logits)
            out = model(ids, use_cache=True, logits_to_keep=1)
            prefill_s = time.perf_counter() - t0

            past = out.past_key_values
            total_bytes = cache_bytes(past)
            tensors = cache_tensors(past)
            shape = list(tensors[0][0].shape) if tensors and tensors[0][0] is not None else None
            actual_len = shape[2] if shape else n

            result["cache"].append({
                "seq_len": n,
                "prefill_s": round(prefill_s, 3),
                "cache_bytes": total_bytes,
                "cache_mib": round(total_bytes / 1024 / 1024, 3),
                "bytes_per_token": total_bytes // actual_len,
                "tensor_shape": shape,
                "num_layers_with_cache": len(tensors),
            })
            print(f"seq_len={n} prefill={prefill_s:.2f}s "
                  f"cache={total_bytes / 1024 / 1024:.2f} MiB "
                  f"per_token={total_bytes // actual_len} shape={shape}", flush=True)

        # decode speed: same prompt, greedy, cache on vs off
        prompt_ids = tok(REPEAT_TEXT).input_ids[:DECODE_PROMPT_TOKENS]
        ids = torch.tensor([prompt_ids])

        for use_cache in (True, False):
            warm = torch.tensor([tok(REPEAT_TEXT).input_ids[:32]])
            model.generate(warm, max_new_tokens=2, do_sample=False, use_cache=use_cache)

            t0 = time.perf_counter()
            gen = model.generate(
                ids,
                max_new_tokens=DECODE_NEW_TOKENS,
                do_sample=False,
                use_cache=use_cache,
                pad_token_id=tok.eos_token_id,
            )
            elapsed = time.perf_counter() - t0
            key = "cache_on" if use_cache else "cache_off"
            result["decode"][key] = {
                "use_cache": use_cache,
                "elapsed_s": round(elapsed, 3),
                "new_tokens": DECODE_NEW_TOKENS,
                "tok_per_s": round(DECODE_NEW_TOKENS / elapsed, 4),
                "total_tokens_in_seq": len(gen[0]),
                "output_ids": gen[0][-DECODE_NEW_TOKENS:].tolist(),
            }
            print(f"use_cache={use_cache} elapsed={elapsed:.2f}s "
                  f"tok_per_s={DECODE_NEW_TOKENS / elapsed:.3f}", flush=True)

    on = result["decode"]["cache_on"]["elapsed_s"]
    off = result["decode"]["cache_off"]["elapsed_s"]
    result["decode"]["speedup_cache_on"] = round(off / on, 2)

    result["official_cfg"] = official_config_block()
    for model_id, entry in result["official_cfg"].items():
        if "per_token_bytes" in entry:
            ctx = entry["ctx_bytes"]["bfloat16"]["ctx_len"]
            print(f"cfg {model_id}: per_token f32={entry['per_token_bytes']['float32']} B, "
                  f"bf16={entry['per_token_bytes']['bfloat16']} B, "
                  f"ctx{ctx} bf16={entry['ctx_bytes']['bfloat16']['mib']} MiB", flush=True)

    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"written: {OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()

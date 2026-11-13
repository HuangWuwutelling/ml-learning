"""Measure symmetric group-wise int4 quantization on local Qwen2.5-0.5B-Instruct (CPU).

Run from repo root:
    HF_HUB_OFFLINE=1 python scripts/ai-history/measure_ai_13_quant.py

The hub cache must already hold the snapshots:
    <HF_HOME>/hub/models--Qwen--Qwen2.5-0.5B-Instruct
    <HF_HOME>/hub/models--Qwen--Qwen2.5-7B-Instruct
Only drop HF_HUB_OFFLINE when downloading is actually needed, and set
HF_ENDPOINT=https://hf-mirror.com for that run.

What this measures
  - the byte budget of the weights: 16-bit, 4-bit on the linear layers only,
    and 4-bit on everything
  - the accuracy cost of that quantization, as perplexity on a fixed text

What gets quantized: the linear weights of the transformer blocks (q/k/v/o
and gate/up/down projections). The embedding table, the output head and the
RMS norms are left in 16-bit, which is what the real 4-bit runtimes do -
llama.cpp ships --leave-output-tensor and --token-embedding-type for exactly
those two tensors. Quantizing the embedding as well destroys the model and
tells you nothing about quantization.

The scheme is the simplest one there is: symmetric, round-to-nearest, one fp16
scale per group of 128 weights. It is NOT GPTQ / AWQ / NF4. Quantized weights
are dequantized back to fp32 in place, so the model runs in the same dtype as
the baseline and the perplexity difference is the quantization cost alone.

Outputs JSON next to this script: scripts/ai-history/quant_measure.json
"""
import glob
import json
import math
import os
import sys
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
REF_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
HF_HOME = os.environ.get("HF_HOME", r"D:\Workspace\.cache\huggingface")
# the hub cache is <HF_HOME>/hub; passing HF_HOME itself makes transformers
# start a fresh download instead of reusing the cached snapshot
CACHE_DIR = os.environ.get("HF_HUB_CACHE", os.path.join(HF_HOME, "hub"))
OUT_PATH = Path(__file__).resolve().parent / "quant_measure.json"

GROUP = 128          # weights per scale factor
THREADS = 4
QMAX = 7             # 4-bit symmetric: levels are -8..7, scale = absmax / 7
LINEAR_SUFFIXES = (
    "q_proj.weight", "k_proj.weight", "v_proj.weight", "o_proj.weight",
    "gate_proj.weight", "up_proj.weight", "down_proj.weight",
)

# Fixed corpus for the perplexity number. Kept inside the script so the
# measurement is reproducible without any external file, and so the number
# always refers to the same text.
TEXT = (
    "环境监测站点的日常工作是按周期采集样品并记录数据。"
    "水样要记录采样点位、采样时间、水温和流量，"
    "pH 值要在现场测定，因为样品离开原位后平衡会被打破。"
    "每个批次至少带一份平行样，平行样之间的偏差超出控制限时整批数据要作废重采。"
    "实验室分析重金属时，消解这一步决定结果的上限，"
    "容器里残留的清洗液会污染低浓度样品，"
    "所以容器要用硝酸浸泡后用去离子水冲洗三遍。"
    "数据上报前要经过三级审核，"
    "审核人要看校准曲线、空白样和加标回收率，"
    "任何一项不合格这批数据都不能进入数据库。"
    "监测结果还要和周边污染源的位置做比对，"
    "只有浓度和污染源的空间分布对得上，"
    "才能判断这次异常是排放造成的还是采样过程造成的。"
    "这套流程里每一步都会留下记录，"
    "记录的缺失会让一个正常数字变得无法解释。"
)
PROMPT = "用两句话说清楚在线监测和手工采样的区别。"


def is_quantizable(name):
    """Only the linear weights of the transformer blocks get quantized."""
    return name.endswith(LINEAR_SUFFIXES)


def find_snapshot_file(model_id, filename):
    """Locate a file inside the hub cache snapshot of a model.

    Only the hub cache (<HF_HOME>/hub) counts. Whatever is found is recorded
    as `source` in the JSON, so the number always names the exact file it was
    read from.
    """
    folder = "models--" + model_id.replace("/", "--")
    hits = glob.glob(str(Path(CACHE_DIR) / folder / "snapshots" / "*" / filename))
    return hits[0] if hits else None


def read_index(model_id):
    """Read the official safetensors index of a checkpoint from the hub cache.

    The index carries the exact storage size of the weights
    (metadata.total_size) and the name of every tensor in the checkpoint
    (weight_map). For a bf16 checkpoint, total_size / 2 is the parameter
    count - that is the authoritative number, and it is what the byte
    account below is checked against.
    """
    path = find_snapshot_file(model_id, "model.safetensors.index.json")
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        "path": path,
        "total_size": data.get("metadata", {}).get("total_size"),
        "tensor_names": sorted(data.get("weight_map", {}).keys()),
    }


def byte_budget(tensors):
    """Storage budget for a list of (name, numel, is_quantized) tensors.

    tensors: list of (name, numel, quantizable)

    16-bit     - every weight stored in 2 bytes
    4-bit lin  - linear weights at 4 bit + one fp16 scale per group, the rest
                 (embedding, output head, norms) stays at 16-bit
    4-bit all  - everything at 4 bit, one fp16 scale per group
    """
    nq = sum(n for _, n, q in tensors if q)
    nk = sum(n for _, n, q in tensors if not q)
    gq = sum(math.ceil(n / GROUP) for _, n, q in tensors if q)
    gk = sum(math.ceil(n / GROUP) for _, n, q in tensors if not q)
    total = nq + nk
    fp16 = total * 2
    lin = nq * 4 // 8 + gq * 2 + nk * 2
    allq = total * 4 // 8 + (gq + gk) * 2
    return {
        "param_count": total,
        "quantized_param_count": nq,
        "kept_param_count": nk,
        "num_groups_quantized": gq,
        "bytes_fp32": total * 4,
        "bytes_fp16": fp16,
        "bytes_int4_linear_g128": lin,
        "bytes_int4_all_g128": allq,
        "bits_per_weight_int4_linear_g128": lin * 8 / total,
        "bits_per_weight_int4_all_g128": allq * 8 / total,
        "ratio_int4_linear_over_fp16": fp16 / lin,
        "ratio_int4_all_over_fp16": fp16 / allq,
    }


def model_tensor_nums_from_config(cfg):
    """[C] per-tensor parameter counts of a Qwen2 model, read off the config.

    head_dim is not a config field: it is hidden_size // num_attention_heads.
    A bias-free Qwen2 block holds q/k/v/o projections, gate/up/down projections
    and two RMS norms.
    """
    hidden = cfg["hidden_size"]
    heads = cfg["num_attention_heads"]
    kv_heads = cfg["num_key_value_heads"]
    inter = cfg["intermediate_size"]
    vocab = cfg["vocab_size"]
    layers = cfg["num_hidden_layers"]

    head_dim = hidden // heads
    kv_dim = kv_heads * head_dim

    tensors = [("model.embed_tokens.weight", vocab * hidden, False)]
    if not cfg.get("tie_word_embeddings"):
        tensors.append(("lm_head.weight", vocab * hidden, False))
    tensors.append(("model.norm.weight", hidden, False))
    for i in range(layers):
        p = f"model.layers.{i}."
        tensors += [
            (p + "self_attn.q_proj.weight", hidden * hidden, True),
            (p + "self_attn.k_proj.weight", hidden * kv_dim, True),
            (p + "self_attn.v_proj.weight", hidden * kv_dim, True),
            (p + "self_attn.o_proj.weight", hidden * hidden, True),
            (p + "mlp.gate_proj.weight", hidden * inter, True),
            (p + "mlp.up_proj.weight", hidden * inter, True),
            (p + "mlp.down_proj.weight", inter * hidden, True),
            (p + "input_layernorm.weight", hidden, False),
            (p + "post_attention_layernorm.weight", hidden, False),
            # Qwen2 keeps a bias on q/k/v and none on o. This is not a config
            # switch: Qwen2Config has no attention_bias argument at all, and
            # Qwen2Attention hardcodes bias=True for q/k/v. The 0.5B checkpoint
            # carries them and so does the 7B one - the official safetensors
            # index lists q/k/v_proj.bias x28 for Qwen2.5-7B-Instruct. Biases
            # are never quantized.
            (p + "self_attn.q_proj.bias", hidden, False),
            (p + "self_attn.k_proj.bias", kv_dim, False),
            (p + "self_attn.v_proj.bias", kv_dim, False),
        ]
    return tensors, head_dim, kv_dim


def quantize_group(g):
    """Symmetric round-to-nearest int4 on one group of weights.

    scale = absmax / 7, levels -8..7, so 0 is exactly representable and the
    group's peak lands on +-7. Returns (scale, dequantized values).
    """
    absmax = g.abs().amax()
    scale = absmax / QMAX if float(absmax) > 0 else torch.tensor(1.0)
    q = torch.clamp(torch.round(g / scale), -QMAX, QMAX)
    return scale, q * scale


def quantize_tensor_(w):
    """In-place symmetric group-wise int4 on a float tensor.

    Writes the dequantized values back into w (fp32 storage is kept), and
    returns the number of scale factors this tensor needs.
    """
    flat = w.data.reshape(-1)
    n = flat.numel()
    pad = (-n) % GROUP
    if pad:
        flat = torch.cat([flat, torch.zeros(pad, dtype=flat.dtype)])
    g = flat.view(-1, GROUP)
    absmax = g.abs().amax(dim=1, keepdim=True)
    scale = torch.where(absmax > 0, absmax / QMAX, torch.ones_like(absmax))
    q = torch.clamp(torch.round(g / scale), -QMAX, QMAX)
    flat = (q * scale).reshape(-1)[:n]
    w.data.copy_(flat.view_as(w.data))
    return g.shape[0]


def perplexity(model, tok, text):
    """Exponentiated mean next-token cross entropy over the whole text."""
    ids = tok(text, return_tensors="pt").input_ids
    with torch.no_grad():
        logits = model(ids).logits[:, :-1, :].float()
    targets = ids[:, 1:]
    ce = torch.nn.functional.cross_entropy(
        logits.reshape(-1, logits.size(-1)), targets.reshape(-1), reduction="mean"
    )
    return float(torch.exp(ce)), int(ids.shape[1])


def sample(model, tok, prompt, max_new_tokens=48):
    ids = tok(prompt, return_tensors="pt").input_ids
    with torch.no_grad():
        gen = model.generate(
            ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tok.eos_token_id,
        )
    return tok.decode(gen[0][ids.shape[1]:], skip_special_tokens=True)


def pick_demo_groups(model):
    """Two real groups from a mid-layer down_proj weight.

    `normal` is the group whose peak is the median over all groups, `outlier`
    is the group with the largest peak. For each group we keep the original
    values, the scale the group's peak implies, and the dequantized values,
    so the figure can show the step size and the error.
    """
    cands = [(n, p) for n, p in model.named_parameters()
             if n.endswith("mlp.down_proj.weight")]
    name, w = cands[len(cands) // 2]

    flat = w.data.reshape(-1)
    n = flat.numel()
    pad = (-n) % GROUP
    if pad:
        flat = torch.cat([flat, torch.zeros(pad, dtype=flat.dtype)])
    g = flat.view(-1, GROUP)
    absmax = g.abs().amax(dim=1)

    order = torch.argsort(absmax)
    normal_idx = int(order[order.numel() // 2])
    outlier_idx = int(order[-1])

    def entry(idx):
        grp = g[idx]
        scale, deq = quantize_group(grp)
        err = (deq - grp).abs()
        levels = torch.clamp(torch.round(grp / scale), -QMAX, QMAX)
        # Two worked examples, so the article can show the whole arithmetic of
        # a single weight instead of asking the reader to trust a formula:
        #   peak    - the largest value of the group, it fixes the scale
        #   max_err - the weight the quantization hurts the most
        peak_i = int(grp.abs().argmax())
        err_i = int(err.argmax())

        def step(i):
            v = float(grp[i])
            return {
                "index": i,
                "value": v,
                "ratio": v / float(scale),
                "level": int(levels[i]),
                "dequant": float(deq[i]),
                "err": float(err[i]),
            }

        return {
            "group_index": idx,
            "absmax": float(grp.abs().amax()),
            "scale": float(scale),
            "values": [float(x) for x in grp.tolist()],
            "dequant": [float(x) for x in deq.tolist()],
            "max_abs_err": float(err.max()),
            "mean_abs_err": float(err.mean()),
            "outlier_pos": int(grp.abs().argmax()),
            # how many weights of this group are smaller than half a step and
            # therefore land on level 0, and how many of the 16 levels are used
            "n_zero_levels": int((levels == 0).sum()),
            "levels_used": sorted({int(x) for x in levels.tolist()}),
            "half_step": float(scale) / 2,
            "worked_example": {"peak": step(peak_i), "max_err": step(err_i)},
        }

    stats = {
        "median": float(absmax.median()),
        "p90": float(absmax.quantile(0.90)),
        "p99": float(absmax.quantile(0.99)),
        "max": float(absmax.max()),
        "num_groups": int(absmax.numel()),
    }
    stats["max_over_median"] = stats["max"] / stats["median"] if stats["median"] else 0.0

    return {
        "tensor": name,
        "group_size": GROUP,
        "absmax_stats": stats,
        "normal": entry(normal_idx),
        "outlier": entry(outlier_idx),
    }


def main():
    torch.set_num_threads(THREADS)
    tok = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=CACHE_DIR)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, cache_dir=CACHE_DIR, dtype=torch.float32
    )
    model.eval()

    # --- baseline: fp32 weights ------------------------------------------------
    with torch.no_grad():
        # warmup: the first forward in a cold process pays for paging in the
        # weight file and for building the CPU primitive cache, so it is not
        # comparable with later passes
        warm = tok("测试", return_tensors="pt").input_ids
        model(warm)

    ppl_fp32, n_tok = perplexity(model, tok, TEXT)
    sample_fp32 = sample(model, tok, PROMPT)
    print(f"baseline ppl_fp32={ppl_fp32:.4f} tokens={n_tok}", flush=True)

    # --- capture the demo groups before they get quantized --------------------
    group_demo = pick_demo_groups(model)

    # --- quantize the linear weights only -------------------------------------
    tensors = []
    for name, p in model.named_parameters():
        if not p.is_floating_point():
            continue
        tensors.append((name, p.numel(), is_quantizable(name)))
    for name, p in model.named_parameters():
        if p.is_floating_point() and is_quantizable(name):
            quantize_tensor_(p)

    budget = byte_budget(tensors)
    n_quant_tensors = sum(1 for _, _, q in tensors if q)
    kept_suffixes = sorted({n.split(".")[-2] + "." + n.split(".")[-1]
                            for n, _, q in tensors if not q})
    budget["quantized_tensor_count"] = n_quant_tensors
    budget["kept_tensor_suffixes"] = kept_suffixes
    print(f"params={budget['param_count']} quantized_tensors={n_quant_tensors} "
          f"kept={kept_suffixes} "
          f"fp16={budget['bytes_fp16']} int4lin={budget['bytes_int4_linear_g128']} "
          f"int4all={budget['bytes_int4_all_g128']} "
          f"ratio_lin={budget['ratio_int4_linear_over_fp16']:.3f} "
          f"ratio_all={budget['ratio_int4_all_over_fp16']:.3f}", flush=True)

    # --- quantized model -------------------------------------------------------
    ppl_int4, _ = perplexity(model, tok, TEXT)
    sample_int4 = sample(model, tok, PROMPT)
    print(f"quantized ppl_int4={ppl_int4:.4f} "
          f"ppl_ratio={ppl_int4 / ppl_fp32:.4f}", flush=True)
    for key in ("normal", "outlier"):
        g = group_demo[key]
        we = g["worked_example"]
        print(f"group_demo[{key}] tensor={group_demo['tensor']} "
              f"absmax={g['absmax']:.6f} scale={g['scale']:.6f} "
              f"half_step={g['half_step']:.6f} "
              f"n_zero_levels={g['n_zero_levels']}/{len(g['values'])} "
              f"levels_used={len(g['levels_used'])} "
              f"peak(idx={we['peak']['index']},v={we['peak']['value']:.6f},"
              f"level={we['peak']['level']}) "
              f"max_err(idx={we['max_err']['index']},v={we['max_err']['value']:.6f},"
              f"level={we['max_err']['level']},err={we['max_err']['err']:.6f})",
              flush=True)
    print(f"group_demo max_over_median="
          f"{group_demo['absmax_stats']['max_over_median']:.2f}", flush=True)

    # --- 7B account from the official config.json ------------------------------
    weights_07b = {}
    cfg_path = find_snapshot_file(REF_MODEL_ID, "config.json")
    if cfg_path:
        cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
        cfg_tensors, head_dim, kv_dim = model_tensor_nums_from_config(cfg)
        budget_07b = byte_budget(cfg_tensors)
        budget_07b["source"] = cfg_path
        budget_07b["head_dim"] = head_dim
        budget_07b["kv_dim"] = kv_dim
        budget_07b["tie_word_embeddings"] = bool(cfg.get("tie_word_embeddings"))
        budget_07b["config"] = {
            "hidden_size": cfg["hidden_size"],
            "num_attention_heads": cfg["num_attention_heads"],
            "num_key_value_heads": cfg["num_key_value_heads"],
            "num_hidden_layers": cfg["num_hidden_layers"],
            "intermediate_size": cfg["intermediate_size"],
            "vocab_size": cfg["vocab_size"],
            "max_position_embeddings": cfg.get("max_position_embeddings"),
            "dtype": cfg.get("torch_dtype"),
        }

        # cross-check against the official safetensors index: its total_size is
        # the exact storage size of the checkpoint, so total_size / 2 is the
        # parameter count. If the derived count disagrees, the config reading
        # above is wrong and the numbers must not go into the article.
        index = read_index(REF_MODEL_ID)
        if index and index.get("total_size"):
            derived_bytes = budget_07b["param_count"] * 2
            budget_07b["index_source"] = index["path"]
            budget_07b["index_total_size"] = index["total_size"]
            budget_07b["index_total_size_matches"] = (derived_bytes == index["total_size"])
            budget_07b["index_param_count"] = index["total_size"] // 2
            print(f"cfg 7B params={budget_07b['param_count']} "
                  f"fp16={budget_07b['bytes_fp16']} "
                  f"int4lin={budget_07b['bytes_int4_linear_g128']} "
                  f"int4all={budget_07b['bytes_int4_all_g128']} "
                  f"index_match={budget_07b['index_total_size_matches']} "
                  f"(derived {derived_bytes} vs index {index['total_size']})", flush=True)
        else:
            print("cfg 7B: safetensors index not in local cache, no cross-check",
                  flush=True)

        weights_07b = budget_07b
    else:
        weights_07b = {"error": "config.json not found in local cache"}
        print("cfg 7B: config.json not found in local cache", flush=True)

    result = {
        "env": {
            "model": MODEL_ID,
            "device": "cpu",
            "threads": THREADS,
            "dtype": "float32",
            "transformers": transformers.__version__,
            "torch": torch.__version__,
            "python": sys.version.split()[0],
            "text_chars": len(TEXT),
            "group_size": GROUP,
            "scheme": "symmetric, round-to-nearest, one fp16 scale per group",
            "quantized": "linear weights only (q/k/v/o, gate/up/down)",
            "kept": "embedding, output head, RMS norms stay in 16-bit",
        },
        "weights_05b": budget,
        "weights_07b": weights_07b,
        "perplexity": {
            "text_chars": len(TEXT),
            "tokens": n_tok,
            "ppl_fp32": ppl_fp32,
            "ppl_int4_linear_g128": ppl_int4,
            "ppl_ratio": ppl_int4 / ppl_fp32,
            "sample_fp32": sample_fp32,
            "sample_int4": sample_int4,
        },
        "group_demo": group_demo,
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"written: {OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()

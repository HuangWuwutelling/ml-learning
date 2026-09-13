"""Benchmark LLM 流式输出: 20 题，TTFT + TPOT 实测."""
import asyncio
import json
import time
from pathlib import Path

from stream import generate, load_model

TEST_SET = Path(__file__).parent / "test_set.jsonl"


async def measure_one(prompt: str) -> dict:
    """测一道题：TTFT = 第一个 token 时间，总耗时，总 token 数。"""
    start = time.perf_counter()
    first_token_time = None
    token_count = 0
    async for chunk in generate(prompt):
        if chunk.startswith("data: ") and chunk.strip():
            token_count += 1
            if first_token_time is None:
                first_token_time = time.perf_counter()
    total_time = time.perf_counter() - start
    ttft = (first_token_time - start) * 1000 if first_token_time else None
    avg_tpot = ((total_time * 1000) - ttft) / (token_count - 1) if token_count > 1 and ttft else None
    return {
        "prompt": prompt[:30],
        "ttft_ms": round(ttft, 1) if ttft else None,
        "avg_tpot_ms": round(avg_tpot, 1) if avg_tpot else None,
        "total_ms": round(total_time * 1000, 1),
        "token_count": token_count,
    }


async def run_benchmark():
    load_model()
    prompts = []
    with open(TEST_SET, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            prompts.append(item["text"])

    print(f"Running benchmark on {len(prompts)} prompts...")
    results = []
    for i, prompt in enumerate(prompts, 1):
        r = await measure_one(prompt)
        results.append(r)
        print(f"[{i}/{len(prompts)}] TTFT={r['ttft_ms']}ms, TPOT={r['avg_tpot_ms']}ms, tokens={r['token_count']}")

    ttfts = [r["ttft_ms"] for r in results if r["ttft_ms"] is not None]
    tpots = [r["avg_tpot_ms"] for r in results if r["avg_tpot_ms"] is not None]
    tokens = [r["token_count"] for r in results]
    summary = {
        "n_prompts": len(results),
        "avg_ttft_ms": round(sum(ttfts) / len(ttfts), 1),
        "avg_tpot_ms": round(sum(tpots) / len(tpots), 1),
        "avg_tokens": round(sum(tokens) / len(tokens), 1),
        "results": results,
    }
    out_path = Path(__file__).parent / "bench_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nSummary: avg TTFT={summary['avg_ttft_ms']}ms, avg TPOT={summary['avg_tpot_ms']}ms, avg tokens={summary['avg_tokens']}")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())

"""Benchmark 3 个 Structured Output 方法在 test_set.jsonl 上的表现.

输出 eval_results.json: 3 方法 × {total, valid_count, correct_count, schema_validity, accuracy}.

predict 函数本身在 structured_output.py，模型加载和 tokenizer 都在那里做。
本模块只负责遍历测试集 + 统计指标 + 落盘。
"""
import json
from pathlib import Path
from structured_output import predict_prompt_only, predict_response_format, predict_tool_choice


def run_benchmark():
    """跑 3 方法在 test_set.jsonl 上，记录 schema_validity + accuracy."""
    test_path = Path(__file__).parent / "test_set.jsonl"
    results = {}
    methods = {
        "prompt_only": predict_prompt_only,
        "response_format": predict_response_format,
        "tool_choice": predict_tool_choice,
    }

    for name, fn in methods.items():
        valid_count = 0
        correct_count = 0
        total = 0
        with open(test_path, encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                pred = fn(item["text"])
                total += 1
                if pred is not None:
                    valid_count += 1
                    if pred == item["label"]:
                        correct_count += 1
        results[name] = {
            "total": total,
            "valid_count": valid_count,
            "correct_count": correct_count,
            "schema_validity": round(valid_count / total, 4),
            "accuracy": round(correct_count / total, 4),
        }
        print(f"{name}: schema_validity={results[name]['schema_validity']}, accuracy={results[name]['accuracy']}")

    out_path = Path(__file__).parent / "eval_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results saved: {out_path}")
    return results


if __name__ == "__main__":
    run_benchmark()

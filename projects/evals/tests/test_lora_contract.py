"""lora_finetune（环境违法严重程度识别）的契约测试。

只读留出集、预测产物与 `eval_results.json`，钉住 README 里那两个对外数字
（29.4% → 91.2%）真的能从产物里算出来，而不是抄在 README 上。
"""
from collections import Counter

from conftest import (LORA_DIR, module_functions, read_json, read_jsonl,
                      read_text)

TEST_SET = LORA_DIR / "test_set.jsonl"
BASE_PRED = LORA_DIR / "base_predictions.jsonl"
LORA_PRED = LORA_DIR / "lora_predictions.jsonl"
EVAL_RESULTS = LORA_DIR / "eval_results.json"
ADAPTER_CONFIG = LORA_DIR / "lora_adapter" / "adapter_config.json"
STRUCTURED_OUTPUT = LORA_DIR / "structured_output.py"

LABELS = {"高", "中", "低"}


def test_holdout_set_structure():
    """留出集 34 条，标签分布 高 4 / 中 9 / 低 21，文本不重复。"""
    records = read_jsonl(TEST_SET)
    assert len(records) == 34
    counts = Counter(r["label"] for r in records)
    assert set(counts) <= LABELS
    assert counts == Counter({"低": 21, "中": 9, "高": 4})
    assert len({r["text"] for r in records}) == 34, '留出集里有重复题目'


def test_predictions_match_the_two_headline_numbers():
    """微调前 10/34（29.4%），微调后 31/34（91.2%）。"""
    base = read_jsonl(BASE_PRED)
    lora = read_jsonl(LORA_PRED)
    assert len(base) == len(lora) == 34
    assert sum(r["true"] == r["pred"] for r in base) == 10
    assert sum(r["true"] == r["pred"] for r in lora) == 31


def test_readme_numbers_agree_with_artifacts():
    """README 上写的两个百分比必须和产物算出来的一致。"""
    readme = read_text(LORA_DIR / "README.md")
    assert "29.4%" in readme, 'README 缺微调前的 29.4%'
    assert "91.2%" in readme, 'README 缺微调后的 91.2%'


def test_prediction_rows_have_the_same_shape():
    """预测文件每行都要有 text/true/pred，且 true 与留出集对得上。"""
    holdout = {r["text"]: r["label"] for r in read_jsonl(TEST_SET)}
    for path in (BASE_PRED, LORA_PRED):
        for row in read_jsonl(path):
            assert row["pred"] in LABELS, f'{path} 有非法预测标签 {row["pred"]}'
            assert row["true"] in LABELS, f'{path} 有非法真实标签 {row["true"]}'
            assert holdout[row["text"]] == row["true"], f'{path} 的真实标签与留出集不一致'


def test_eval_results_contract():
    """三组对照都是 34 题，schema 全合法，准确率与 correct_count 对得上。"""
    results = read_json(EVAL_RESULTS)
    assert set(results) == {"prompt_only", "response_format", "tool_choice"}
    for name, row in results.items():
        assert row["total"] == 34, f'{name} 的题数不是 34'
        assert row["valid_count"] == 34, f'{name} 有解析不了的输出'
        assert row["schema_validity"] == 1.0, f'{name} 的 schema 合法率不是 100%'
        assert abs(row["accuracy"] - row["correct_count"] / 34) < 1e-4, f'{name} 准确率对不上'
    counts = [results[k]["correct_count"] for k in ("prompt_only", "response_format", "tool_choice")]
    assert counts == [7, 7, 12], '三组对照的题数变了'


def test_three_structured_output_methods_share_one_signature():
    """三种让输出可解析的写法，函数签名必须一致，方便横向替换。"""
    funcs = module_functions(STRUCTURED_OUTPUT)
    predicts = {k: v for k, v in funcs.items() if k.startswith("predict_")}
    assert set(predicts) == {"predict_prompt_only", "predict_response_format", "predict_tool_choice"}
    assert len({tuple(v) for v in predicts.values()}) == 1, '三种方法的签名不一致'


def test_adapter_config_is_lora_on_the_expected_base_model():
    """LoRA 适配器挂在 Qwen2.5-0.5B-Instruct 上，秩 16。"""
    config = read_json(ADAPTER_CONFIG)
    assert config["peft_type"] == "LORA"
    assert config["base_model_name_or_path"] == "Qwen/Qwen2.5-0.5B-Instruct"
    assert config["r"] == 16
    assert config["use_rslora"] is False

"""
Evaluate LoRA adapter vs base model on environment violation classification test set.

Outputs:
  - eval_results.json: accuracy, per-class precision/recall/F1
  - base_predictions.jsonl: base model predictions
  - lora_predictions.jsonl: lora model predictions
  - confusion matrix data for plotting
"""
import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from structured_output import predict_prompt_only, predict_response_format, predict_tool_choice, Severity  # noqa: F401

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
ADAPTER_DIR = os.path.join(os.path.dirname(__file__), "lora_adapter")
TEST_PATH = os.path.join(os.path.dirname(__file__), "test_set.jsonl")

LABELS = ["高", "中", "低"]


def build_prompt(text: str) -> str:
    return (
        f"<|im_start|>system\n你是一名环境合规审核员，请根据违规描述判断严重程度。"
        f"严重程度分为三级：高、中、低。严格只回复一个汉字。<|im_end|>\n"
        f"<|im_start|>user\n{text}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def evaluate(*args, **kwargs):
    """占位：Task 2 将用 run_benchmark 重写主入口."""
    raise NotImplementedError("eval 重构中，见 Task 2 run_benchmark")


def per_class_metrics(y_true, y_pred):
    metrics = {}
    for lbl in LABELS:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lbl and p == lbl)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lbl and p == lbl)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lbl and p != lbl)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        metrics[lbl] = {"precision": prec, "recall": rec, "f1": f1, "support": y_true.count(lbl)}
    return metrics


def confusion_matrix_data(y_true, y_pred):
    """Return 3x3 matrix: rows=true, cols=pred."""
    matrix = [[0]*3 for _ in range(3)]
    for t, p in zip(y_true, y_pred):
        ti = LABELS.index(t)
        pi = LABELS.index(p)
        matrix[ti][pi] += 1
    return matrix


if __name__ == "__main__":
    evaluate()

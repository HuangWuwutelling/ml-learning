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


def predict_label(model, tokenizer, text: str) -> str:
    """Greedy decode, take first character of output, map to known label."""
    prompt = build_prompt(text)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=4,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    gen = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    # Take first non-whitespace char; if it's a known label, return it; else "中" (fallback)
    for ch in gen.strip():
        if ch in LABELS:
            return ch
    return "中"


def evaluate(model, tokenizer, items):
    correct = 0
    y_true, y_pred = [], []
    preds = []
    for it in items:
        true = it["label"]
        pred = predict_label(model, tokenizer, it["text"])
        y_true.append(true)
        y_pred.append(pred)
        preds.append({"text": it["text"], "true": true, "pred": pred})
        if pred == true:
            correct += 1
    acc = correct / len(items)
    return acc, y_true, y_pred, preds


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


def main():
    print("Loading test set...")
    items = []
    with open(TEST_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    print(f"Test samples: {len(items)}")

    print("Loading base model (4-bit)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, quantization_config=bnb_config, device_map="auto", trust_remote_code=True,
    )
    tok = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    print("Evaluating BASE model...")
    base_acc, base_true, base_pred, base_preds = evaluate(base, tok, items)
    base_metrics = per_class_metrics(base_true, base_pred)
    base_cm = confusion_matrix_data(base_true, base_pred)
    print(f"Base accuracy: {base_acc:.3f}")

    with open(os.path.join(os.path.dirname(__file__), "base_predictions.jsonl"), "w", encoding="utf-8") as f:
        for p in base_preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print("Loading LoRA adapter...")
    lora_model = PeftModel.from_pretrained(base, ADAPTER_DIR)
    print("Evaluating LORA model...")
    lora_acc, lora_true, lora_pred, lora_preds = evaluate(lora_model, tok, items)
    lora_metrics = per_class_metrics(lora_true, lora_pred)
    lora_cm = confusion_matrix_data(lora_true, lora_pred)
    print(f"LoRA accuracy: {lora_acc:.3f}")

    with open(os.path.join(os.path.dirname(__file__), "lora_predictions.jsonl"), "w", encoding="utf-8") as f:
        for p in lora_preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    results = {
        "test_size": len(items),
        "base": {"accuracy": base_acc, "per_class": base_metrics, "confusion_matrix": base_cm},
        "lora": {"accuracy": lora_acc, "per_class": lora_metrics, "confusion_matrix": lora_cm},
        "improvement": lora_acc - base_acc,
    }
    with open(os.path.join(os.path.dirname(__file__), "eval_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nImprovement: {lora_acc - base_acc:+.3f}")
    print("Done!")


if __name__ == "__main__":
    main()

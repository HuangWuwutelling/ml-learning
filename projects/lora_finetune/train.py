"""
LoRA fine-tuning of Qwen2.5-0.5B-Instruct for environment violation severity classification.

Dataset: data/env_violations.jsonl  (text, label) -- 150 samples
Output: projects/lora_finetune/lora_adapter/

Hardware: designed for 4GB VRAM (QLoRA 4-bit).
"""
import os
import json
import torch
import random
from datasets import load_dataset
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType


# ── Config ──
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "env_violations.jsonl")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "lora_adapter")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

SEED = 42
EPOCHS = 8
BATCH_SIZE = 2
GRAD_ACCUM = 4
LR = 2e-4
MAX_SEQ_LEN = 128
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

random.seed(SEED)
torch.manual_seed(SEED)


# ── Data ──
SYSTEM_PROMPT = "你是一名环境合规审核员，请根据违规描述判断严重程度。严重程度分为三级：高、中、低。严格只回复一个汉字。"

def build_prompt(text: str) -> str:
    """Full chat prompt ending with assistant prefix (model continues with label)."""
    return (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{text}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def build_full_text(text: str, label: str) -> str:
    return build_prompt(text) + f"{label}<|im_end|>"


def load_and_split(path: str, test_ratio: float = 0.2):
    """Load jsonl, split into train/test."""
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    random.shuffle(items)
    n_test = int(len(items) * test_ratio)
    return items[n_test:], items[:n_test]


# ── Main ──
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    print("Loading data...")
    train_items, test_items = load_and_split(DATA_PATH)
    print(f"Train: {len(train_items)}  Test: {len(test_items)}")
    # Save test set for evaluation
    with open(os.path.join(os.path.dirname(__file__), "test_set.jsonl"), "w", encoding="utf-8") as f:
        for it in test_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Tokenizing...")
    def tokenize_fn(item):
        full_text = build_full_text(item["text"], item["label"])
        prompt_text = build_prompt(item["text"])
        full_ids = tokenizer(full_text, truncation=True, max_length=MAX_SEQ_LEN, padding="max_length")["input_ids"]
        prompt_ids = tokenizer(prompt_text, truncation=True, max_length=MAX_SEQ_LEN)["input_ids"]
        prompt_len = len(prompt_ids)

        # Mask the prompt part in labels (-100 = ignore in loss)
        labels = list(full_ids)
        for i in range(min(prompt_len, len(labels))):
            labels[i] = -100
        return {
            "input_ids": full_ids,
            "attention_mask": [1 if t != tokenizer.pad_token_id else 0 for t in full_ids],
            "labels": labels,
        }

    train_data = [tokenize_fn(it) for it in train_items]

    print("Loading model with 4-bit quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Collator: pad input_ids, attention_mask, labels
    def collator(batch):
        max_len = max(len(b["input_ids"]) for b in batch)
        pad_id = tokenizer.pad_token_id
        out = {"input_ids": [], "attention_mask": [], "labels": []}
        for b in batch:
            pad_n = max_len - len(b["input_ids"])
            out["input_ids"].append(b["input_ids"] + [pad_id] * pad_n)
            out["attention_mask"].append(b["attention_mask"] + [0] * pad_n)
            out["labels"].append(b["labels"] + [-100] * pad_n)
        return {k: torch.tensor(v) for k, v in out.items()}

    training_args = TrainingArguments(
        output_dir=LOG_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR,
        logging_steps=5,
        save_strategy="no",
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        fp16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        report_to="none",
        seed=SEED,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        data_collator=collator,
    )

    print("Training...")
    trainer.train()

    print(f"Saving adapter to {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Done!")


if __name__ == "__main__":
    main()

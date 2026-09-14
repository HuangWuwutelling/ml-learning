"""Qwen2.5-0.5B-Instruct 加载与生成（非流式）。"""
import os

MODEL_NAME = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
USE_4BIT = os.environ.get("LLM_4BIT", "0") == "1"

_tokenizer = None
_model = None


def load_model():
    """加载模型（启动时调用一次）。"""
    global _tokenizer, _model
    if _model is not None:
        return _tokenizer, _model
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    import torch

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    kwargs = {"trust_remote_code": True}
    if USE_4BIT:
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16
        )
        kwargs["device_map"] = "auto"
    else:
        kwargs["torch_dtype"] = torch.float16
        kwargs["device_map"] = "auto"
    _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, **kwargs)
    return _tokenizer, _model


def generate(system: str, user: str, max_new_tokens: int = 256) -> str:
    """非流式生成 LLM 输出。

    Args:
        system: system prompt。
        user: user message。
        max_new_tokens: 最大生成 token 数。

    Returns:
        LLM 输出文本（不含 prompt）。
    """
    tokenizer, model = load_model()
    import torch

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
            top_p=1.0,
            pad_token_id=tokenizer.eos_token_id,
        )
    output_text = tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return output_text
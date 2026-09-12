"""Structured Output 3 方法实现，给 lora_finetune eval 用.

本机 transformers 直推 Qwen2.5-0.5B-Instruct (CPU)。3 个 predict 函数都返回
Severity.label 字符串，失败时返回 None。

注意：在 OpenAI/Anthropic 上，方法 2/3 分别对应 response_format / tool_choice；
在 transformers 直推场景下，两者都是「prompt + parse + Pydantic」的不同实现。
"""
import json
import re
from typing import Literal
import torch
from pydantic import BaseModel, ValidationError
from transformers import AutoModelForCausalLM, AutoTokenizer

class Severity(BaseModel):
    label: Literal['高', '中', '低']

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

# 3 个方法各自专属的 system prompt
SYSTEM_PROMPT_M1 = "你是环境违法等级分类器。只输出一个词：高、中 或 低。"
SYSTEM_PROMPT_M2 = (
    "你是环境违法等级分类器。\n"
    "严格按 JSON 格式输出：{\"label\": \"高\"} 或 {\"label\": \"中\"} 或 {\"label\": \"低\"}。\n"
    "不要输出其他内容。"
)
SYSTEM_PROMPT_M3 = (
    "你是环境违法等级分类器。调用 classify_severity 函数，参数 label 填 高/中/低。\n"
    "输出格式：<tool_call>{\"name\": \"classify_severity\", \"arguments\": {\"label\": \"高\"}}</tool_call>"
)

# 模型 + tokenizer 全局加载（3 函数共享）
_model = None
_tokenizer = None

def _load_model():
    global _model, _tokenizer
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float32)
        _model.eval()
    return _model, _tokenizer

def _generate(system_prompt: str, user_text: str, max_new_tokens: int = 32) -> str:
    """共用推理逻辑：拼 chat template + greedy generate + decode."""
    model, tokenizer = _load_model()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,  # do_sample=False 时 temperature 忽略
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = outputs[0][inputs.input_ids.shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

def _parse_simple(raw: str) -> str | None:
    """方法 1 的解析：匹配 高/中/低 三字之一，失败返回 None."""
    m = re.search(r'[高中低]', raw)
    if m is None:
        return None
    candidate = m.group(0)
    try:
        return Severity(label=candidate).label
    except ValidationError:
        return None

def _parse_json_pydantic(raw: str) -> str | None:
    """方法 2 的解析：尝试 JSON 解析 + Pydantic 验证."""
    try:
        data = json.loads(raw)
        return Severity(**data).label
    except (json.JSONDecodeError, ValidationError):
        # 容错：截取首个 {...} 块
        m = re.search(r'\{\s*"label"\s*:\s*"([^"]+)"\s*\}', raw)
        if m:
            try:
                return Severity(label=m.group(1)).label
            except ValidationError:
                return None
        return None

def _parse_tool_call_pydantic(raw: str) -> str | None:
    """方法 3 的解析：从 <tool_call>...</tool_call> 提取 arguments，Pydantic 验证."""
    m = re.search(r'<tool_call>\s*(\{.*?\})\s*</tool_call>', raw, re.DOTALL)
    if m is None:
        # 容错：无 wrapper 直接匹配 {"name":..., "arguments":...}
        m = re.search(r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{\s*"label"\s*:\s*"([^"]+)"\s*\}\s*\}', raw)
        if m is None:
            return None
        try:
            return Severity(label=m.group(1)).label
        except ValidationError:
            return None
    try:
        data = json.loads(m.group(1))
        return Severity(**data["arguments"]).label
    except (json.JSONDecodeError, ValidationError, KeyError):
        return None

def predict_prompt_only(text: str) -> str | None:
    """方法 1（prompt + parse）：最简 system prompt，regex 提取第一字。"""
    raw = _generate(SYSTEM_PROMPT_M1, text, max_new_tokens=8)
    return _parse_simple(raw)

def predict_response_format(text: str) -> str | None:
    """方法 2（response_format 模拟）：强制 JSON 输出 + Pydantic 验证。"""
    raw = _generate(SYSTEM_PROMPT_M2, text, max_new_tokens=32)
    return _parse_json_pydantic(raw)

def predict_tool_choice(text: str) -> str | None:
    """方法 3（tool_choice 模拟）：function call 格式 + Pydantic 验证 arguments。"""
    raw = _generate(SYSTEM_PROMPT_M3, text, max_new_tokens=64)
    return _parse_tool_call_pydantic(raw)
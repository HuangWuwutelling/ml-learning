"""LLM 流式生成：transformers TextIteratorStreamer -> SSE 格式."""
import asyncio
import os
from threading import Thread
from typing import AsyncIterator

# 模型只加载一次（启动期）
MODEL_NAME = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
USE_4BIT = os.environ.get("LLM_4BIT", "0") == "1"

_tokenizer = None
_model = None


def load_model():
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
        # 不用 device_map="auto"：内存不够时它会静默把权重卸载到磁盘，
        # 逐 token 速度掉到 1/8 却不报错，测出来的数全是垃圾。直接加载，装不下就报错。
    _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, **kwargs)

    offloaded = [n for n, p in _model.named_parameters() if p.device.type == "meta"]
    if offloaded:
        raise RuntimeError(
            f"{len(offloaded)} 个参数被卸载到 meta device，测速结果不可用，先腾出内存再跑"
        )
    return _tokenizer, _model


async def format_sse_from(prompt: str, token_iter) -> AsyncIterator[str]:
    """把上游 token 迭代器包装成 SSE 格式。跳过空字符串。支持 sync/async 迭代器。"""
    if hasattr(token_iter, "__aiter__"):
        async for tok in token_iter:
            if tok:
                yield f"data: {tok}\n\n"
    else:
        for tok in token_iter:
            if tok:
                yield f"data: {tok}\n\n"
            await asyncio.sleep(0)


async def generate(prompt: str) -> AsyncIterator[str]:
    """主入口：LLM 生成 + SSE 格式化。"""
    tokenizer, model = load_model()
    from transformers import TextIteratorStreamer

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    generation_kwargs = dict(
        **inputs,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        streamer=streamer,
    )
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    async for chunk in format_sse_from(prompt, streamer):
        yield chunk
    thread.join()

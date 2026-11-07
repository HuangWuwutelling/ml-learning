"""复核 context_recall 的 judge：把 RAGAS 内部那一步的原始输出打出来

RAGAS 的 LLMContextRecall 只有一步：把 GT 当 answer 交给 LLM，让它逐句判断
「能否由检索到的上下文支撑」，每条给 attributed 0/1 和 reason。这个脚本用
同一套 prompt、同一个模型（deepseek-chat, temp=0）重跑这一步，把 statement /
attributed / reason 全部打出来，用来判断零分是「检索真没召回」还是「judge 判错」。

用法：
    cd 环境法律法规智能问答系统
    .venv-rag/Scripts/python.exe ../scripts/llm/ragas/probe_context_recall.py \
        --result ../scripts/llm/ragas/results/ragas_20260921_120654.json
"""

import argparse
import asyncio
import json
import os
import sys
import types
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "环境法律法规智能问答系统").is_dir():
            return p
    raise SystemExit(f"ERROR: 从 {start} 向上找不到 环境法律法规智能问答系统/")


REPO_ROOT = _find_repo_root(SCRIPT_DIR)
RAG_PROJECT = REPO_ROOT / "环境法律法规智能问答系统"


# === 同 run_ragas_eval.py：ragas.llms.base 硬 import 已被 langchain-community 移除的
# vertexai 子模块，导入前先塞桩模块，否则 import ragas 直接 ModuleNotFoundError ===
def _stub_removed_langchain_modules():
    for module_path in [
        "langchain_community.chat_models.vertexai",
    ]:
        if module_path not in sys.modules:
            mod = types.ModuleType(module_path)

            class _Stub:
                def __init__(self, *a, **kw):
                    raise NotImplementedError(
                        f"{module_path} 已被 langchain-community 日落，这里只是导入桩"
                    )

            mod.ChatVertexAI = _Stub
            sys.modules[module_path] = mod


_stub_removed_langchain_modules()

from dotenv import load_dotenv  # noqa: E402

load_dotenv(RAG_PROJECT / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")


def make_judge_llm():
    from langchain_openai import ChatOpenAI
    from ragas.llms import LangchainLLMWrapper

    base_llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=DEEPSEEK_API_KEY,
        openai_api_base=f"{DEEPSEEK_API_BASE}/v1",
        temperature=0.0,
        max_retries=3,
        timeout=60,
    )
    return LangchainLLMWrapper(langchain_llm=base_llm)


async def probe(llm, question, contexts, ground_truth):
    from ragas.metrics._context_recall import (
        ContextRecallClassificationPrompt,
        QCA,
    )

    prompt = ContextRecallClassificationPrompt()
    out = await prompt.generate(
        data=QCA(
            question=question,
            context="\n".join(contexts),
            answer=ground_truth,
        ),
        llm=llm,
    )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True, help="已有评测结果 JSON（提供题目/上下文/GT）")
    ap.add_argument("--only", type=int, nargs="*", help="只跑这几道（题号，从 1 开始）")
    args = ap.parse_args()

    if not DEEPSEEK_API_KEY:
        sys.exit("ERROR: DEEPSEEK_API_KEY 未配置")

    path = Path(args.result)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))

    llm = make_judge_llm()
    print(f"结果文件: {path.name}  检索模式: {data.get('retrieval_mode')}\n")

    for i, e in enumerate(data["details"], 1):
        if not e.get("in_scope", True):
            continue
        if args.only and i not in args.only:
            continue

        stored = e["scores"]["context_recall"]
        print("=" * 78)
        print(f"Q{i}  已存判定 recall={stored}")
        print(f"问题: {e['question']}")
        print(f"GT  : {e['ground_truth']}")

        out = asyncio.run(probe(llm, e["question"], e["contexts"], e["ground_truth"]))
        cls = out.classifications
        n = len(cls)
        num = sum(1 for c in cls if c.attributed)
        print(f"--> judge 返回 {n} 条判定，attributed=1 的 {num} 条，复算 recall={num / n if n else float('nan'):.3f}")
        for j, c in enumerate(cls, 1):
            print(f"    [{j}] attributed={c.attributed}")
            print(f"        陈述: {c.statement}")
            print(f"        理由: {c.reason}")
        print()


if __name__ == "__main__":
    main()

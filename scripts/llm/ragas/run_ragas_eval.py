"""
RAGAS 评测脚本：对 环境法律法规智能问答系统 跑 RAGAS 4 个核心指标。

依赖（先装到 env 法规项目的 side venv）:
    cd 环境法律法规智能问答系统
    .venv-rag/Scripts/python.exe -m pip install -r ../scripts/llm/ragas/requirements-ragas.txt

关键决策:
    - 同一个 DEEPSEEK_API_KEY 既当回答模型又当 judge（降低成本，便于复现）
    - 每题前重置 _history，避免多轮对话污染评测
    - 共享 embedding model + vector store，避免反复加载 BGE
    - judge LLM temperature=0，保证评分稳定

用法（从 环境法律法规智能问答系统/ 目录下跑，用 .venv-rag 的 python）:
    # 全量跑（含 RAGAS 评分）
    .venv-rag/Scripts/python.exe ../scripts/llm/ragas/run_ragas_eval.py

    # 指定检索模式（dense | hybrid | hybrid_rerank，默认取 RETRIEVAL_MODE 否则 dense）
    .venv-rag/Scripts/python.exe ../scripts/llm/ragas/run_ragas_eval.py --mode hybrid
    .venv-rag/Scripts/python.exe ../scripts/llm/ragas/run_ragas_eval.py --mode hybrid_rerank

    # 只跑 RAG 不评分（先看 RAG 输出对不对）
    .venv-rag/Scripts/python.exe ../scripts/llm/ragas/run_ragas_eval.py --dry-run

    # 调试用，只跑前 3 题
    .venv-rag/Scripts/python.exe ../scripts/llm/ragas/run_ragas_eval.py --limit 3

输出:
    scripts/llm/ragas/results/ragas_<时间戳>.json  （机器可读）
    scripts/llm/ragas/results/ragas_<时间戳>.md    （人看的表格）
"""

import os
import sys
import json
import math
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# === 抑制 chromadb 匿名埋点通知 ===
# 必须在任何 chromadb import 之前设置，否则 chromadb 在 import 时就缓存上报开关了
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# === 路径处理 ===
SCRIPT_DIR = Path(__file__).resolve().parent


def _find_repo_root(start: Path) -> Path:
    """向上找到含「环境法律法规智能问答系统/」的那层，就是仓库根

    原先写的是 SCRIPT_DIR.parent.parent，脚本从 scripts/ragas/ 挪到
    scripts/llm/ragas/ 之后就指错了目录（指到 scripts/ 去了），因此改成
    按锚点找，脚本在仓库内挪位置不会再失效。
    """
    for p in [start, *start.parents]:
        if (p / "环境法律法规智能问答系统").is_dir():
            return p
    raise SystemExit(f"ERROR: 从 {start} 向上找不到 环境法律法规智能问答系统/")


PROJECT_ROOT = _find_repo_root(SCRIPT_DIR)  # ml-learning/
RAG_PROJECT = PROJECT_ROOT / "环境法律法规智能问答系统"

# === 在所有 import 之前：ragas.llms.base 在模块加载时硬 import vertexai 子模块，
# 但 langchain-community 0.4+ 已把 chat_models.vertexai 移走（日落）。
# 我们用桩模块让它安静通过（我们用的是 OpenAI 路径，不会触发 VertexAI 调用）。
def _stub_removed_langchain_modules():
    import types

    def _ensure(module_path: str, attrs: dict):
        if module_path not in sys.modules:
            mod = types.ModuleType(module_path)
            for k, v in attrs.items():
                setattr(mod, k, v)
            sys.modules[module_path] = mod

    _ensure(
        "langchain_community.chat_models.vertexai",
        {"ChatVertexAI": object},
    )
    _ensure("langchain_community.llms", {"VertexAI": object})


_stub_removed_langchain_modules()

# 把 env 法规项目根加进 sys.path，让 src.* 可被 import
sys.path.insert(0, str(RAG_PROJECT))

from dotenv import load_dotenv

# 在 import 任何 src.* 之前加载 .env
load_dotenv(RAG_PROJECT / ".env")

# === 强制 CHROMA_DB_PATH 为绝对路径（避免 cwd 影响） ===
os.environ["CHROMA_DB_PATH"] = str(RAG_PROJECT / "data" / "chroma_db")

# === 配置 ===
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | {level} | {message}")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")

DEFAULT_TESTSET = SCRIPT_DIR / "testset.jsonl"
RESULTS_DIR = SCRIPT_DIR / "results"
TOP_K = int(os.getenv("TOP_K", "5"))

METRIC_NAMES = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


# === 共享 engine（避免反复加载 BGE 嵌入模型） ===
_engine_singleton = None


def get_engine():
    """懒加载并重置历史"""
    global _engine_singleton
    if _engine_singleton is None:
        # chromadb 0.5.5 + 较新 sqlite3 的兼容补丁：max_seqid() 偶尔返 int 不是 bytes。
        # _decode_seq_id 假设 bytes 会调 len() 崩。先 patch 模块属性。
        try:
            import chromadb.segment.impl.metadata.sqlite as _sqlite_mod

            _original = _sqlite_mod._decode_seq_id

            def _safe_decode(seq_id):
                if isinstance(seq_id, int):
                    return seq_id
                return _original(seq_id)

            _sqlite_mod._decode_seq_id = _safe_decode
        except Exception:
            pass  # 即便补丁失败也继续，可能环境本身没问题

        from src.rag.qa_engine import QAEngine

        _engine_singleton = QAEngine()
        n = _engine_singleton.vector_store.count()
        logger.info(f"向量库加载完成：{n} 个 chunk")
    _engine_singleton._history = []  # 每题前清空，避免多轮污染
    return _engine_singleton


# === 数据准备 ===
def load_testset(path: Path) -> list:
    """加载 jsonl 测试集"""
    with open(path, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]
    logger.info(f"已加载 {len(cases)} 个测试用例 from {path.name}")
    return cases


def run_rag_one(engine, question: str, top_k: int = TOP_K) -> dict:
    """对单个问题跑 RAG，不污染历史"""
    contexts = engine.retrieve(question, top_k=top_k)
    if not contexts:
        return {
            "answer": "未找到相关的法律法规内容，请尝试换个问题。",
            "contexts": [],
            "sources": [],
        }
    prompt = engine.build_prompt(question, contexts, history=[])
    answer_text = engine.query_deepseek(prompt)
    sources = list(
        set(
            c["metadata"].get("law_name", "")
            for c in contexts
            if c["metadata"].get("law_name")
        )
    )
    return {
        "answer": answer_text,
        "contexts": [c["content"] for c in contexts],
        "sources": sources,
    }


def run_rag_all(testset: list, top_k: int, limit: int | None) -> list:
    """跑全部测试用例"""
    engine = get_engine()
    rag_results = []
    cases = testset[:limit] if limit else testset
    for i, case in enumerate(cases, 1):
        logger.info(f"[{i}/{len(cases)}] {case['question'][:50]}")
        rag_results.append(run_rag_one(engine, case["question"], top_k=top_k))
    return rag_results


def build_dataset(testset: list, rag_results: list):
    """组装 RAGAS 0.2.x 输入：字段名遵循新规范（user_input/response/retrieved_contexts/reference）"""
    from ragas import EvaluationDataset
    from datasets import Dataset

    data = {
        "user_input": [c["question"] for c in testset],
        "retrieved_contexts": [r["contexts"] for r in rag_results],
        "response": [r["answer"] for r in rag_results],
        "reference": [c.get("ground_truth", "") for c in testset],
    }
    hf_ds = Dataset.from_dict(data)
    return EvaluationDataset.from_hf_dataset(hf_ds)


def make_judge_llm():
    """构造 DeepSeek judge LLM（ragas 0.2.x 改名 LangchainLLMWrapper）"""
    if not DEEPSEEK_API_KEY:
        sys.exit(
            "ERROR: DEEPSEEK_API_KEY 未配置。请在 环境法律法规智能问答系统/.env 中配置。"
        )

    from ragas.llms import LangchainLLMWrapper
    from langchain_openai import ChatOpenAI

    base_llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=DEEPSEEK_API_KEY,
        openai_api_base=f"{DEEPSEEK_API_BASE}/v1",
        temperature=0.0,
        max_retries=3,
        timeout=60,
    )
    return LangchainLLMWrapper(langchain_llm=base_llm)


def make_embeddings():
    """构造本地 BGE embeddings（避免依赖 OpenAI API key）

    拆出后用 langchain-huggingface 独立包的 HuggingFaceEmbeddings（替代被日落的
    langchain-community 版），ragas 0.2.x 自带的是抽象类，再用
    LangchainEmbeddingsWrapper 包一下交给 evaluate。
    """
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    bge = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    return LangchainEmbeddingsWrapper(embeddings=bge)


def run_ragas_eval(eval_ds, has_ground_truth: bool):
    """跑 RAGAS 4 个核心指标"""
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

    judge_llm = make_judge_llm()
    embeddings = make_embeddings()

    metrics_to_run = []
    for m in [faithfulness, answer_relevancy, context_precision, context_recall]:
        if m is context_recall and not has_ground_truth:
            logger.warning("没有 ground_truth，跳过 context_recall")
            continue
        m.llm = judge_llm
        # answer_relevancy 需要 metric.embeddings（不只是 evaluate() 里的全局参数）
        # 断言在 _answer_relevance.py:100
        if m is answer_relevancy:
            m.embeddings = embeddings
        metrics_to_run.append(m)

    logger.info(f"RAGAS 评分中（共 {len(metrics_to_run)} 个指标）...")
    # 注意：ragas 0.2.x 默认会硬试图连 OpenAI embeddings API，需要显式传本地 embeddings 绕开
    result = evaluate(eval_ds, metrics=metrics_to_run, embeddings=embeddings)
    return result


# === 输出 ===
def extract_metric(result, name: str) -> float | None:
    """从 RAGAS Result 提取单个指标

    result[name] 返回该指标每题的分数 list（不是均值）。
    用 nanmean 处理 NaN（个别题失败的情况）。
    """
    try:
        scores = result[name]  # List[float]，每题一个
        import numpy as np
        return float(np.nanmean(scores))
    except (KeyError, TypeError, ValueError):
        return None


def write_outputs(testset, rag_results, result, dry_run: bool, top_k: int, mode: str):
    """写 JSON + Markdown 报告"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = RESULTS_DIR / f"ragas_{timestamp}"

    metrics = {}
    for m in METRIC_NAMES:
        if not dry_run and result is not None:
            metrics[m] = extract_metric(result, m)
        else:
            metrics[m] = None

    # 每题分数。原先只落均值，导致「排除超纲题后只剩 N 题」这类子集说法事后
    # 没法复算，只能靠手算或重跑。存下来之后任意子集都能独立算。
    per_question = {m: None for m in METRIC_NAMES}
    if not dry_run and result is not None:
        for m in METRIC_NAMES:
            try:
                per_question[m] = [
                    None if s is None or (isinstance(s, float) and math.isnan(s)) else float(s)
                    for s in result[m]
                ]
            except (KeyError, TypeError, ValueError):
                per_question[m] = None

    # in_scope 子集均值：文章里「排除超纲题，剩下 N 题的改善」就是这一栏
    in_scope_idx = [i for i, c in enumerate(testset) if c.get("in_scope", True)]
    metrics_in_scope = {}
    for m in METRIC_NAMES:
        scores = per_question.get(m)
        vals = [scores[i] for i in in_scope_idx if scores and i < len(scores) and scores[i] is not None]
        metrics_in_scope[m] = sum(vals) / len(vals) if vals else None

    # 检索指纹：题目 + 检索到的上下文原文一起哈希。
    # context_precision / context_recall 只依赖这两样（不看生成的答案），所以
    # 指纹相同 → 这两个指标可比；指纹不同 → 检索结果真的变了，指标差异不能
    # 当成评分抖动。answer 那侧因为 DeepSeek temperature=0.3，每次都会变，不纳入。
    retrieval_fingerprint = hashlib.md5(
        json.dumps(
            [[c["question"], r["contexts"]] for c, r in zip(testset, rag_results)],
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()[:12]

    summary = {
        "timestamp": timestamp,
        "n_questions": len(testset),
        "top_k": top_k,
        "retrieval_mode": mode,
        "retrieval_fingerprint": retrieval_fingerprint,
        "judge_model": "deepseek-chat (via langchain-openai, temp=0)" if not dry_run else None,
        "metrics": metrics,
        "n_in_scope": len(in_scope_idx),
        "metrics_in_scope": metrics_in_scope,
        "details": [
            {
                "question": c["question"],
                "ground_truth": c.get("ground_truth"),
                "in_scope": c.get("in_scope", True),
                "category": c.get("category", ""),
                "answer": r["answer"],
                "contexts": r["contexts"],
                "n_contexts": len(r["contexts"]),
                "sources": r["sources"],
                "scores": {
                    m: (per_question[m][i] if per_question.get(m) and i < len(per_question[m]) else None)
                    for m in METRIC_NAMES
                },
            }
            for i, (c, r) in enumerate(zip(testset, rag_results))
        ],
    }

    with open(f"{base}.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Markdown
    md = [
        "# RAGAS 评测结果",
        "",
        f"- 时间：{timestamp}",
        f"- 题目：{len(testset)}",
        f"- top_k：{top_k}",
        f"- 检索模式：{mode}",
        f"- 检索指纹：`{retrieval_fingerprint}`（同指纹 = 两个 run 检索到的东西完全一样）",
        f"- judge：{'deepseek-chat' if not dry_run else '（dry-run，无评分）'}",
        "",
    ]
    if not dry_run and any(v is not None for v in metrics.values()):
        md.extend(
            [
                "## 四指标",
                "",
                "| 指标 | 分数 | 含义 |",
                "|---|---|---|",
            ]
        )
        meanings = {
            "faithfulness": "答案是否忠于上下文",
            "answer_relevancy": "答案是否切题",
            "context_precision": "检索结果中相关 chunk 占比",
            "context_recall": "检索覆盖标准答案的比例",
        }
        for name in METRIC_NAMES:
            v = metrics[name]
            md.append(
                f"| {name} | {v:.3f} | {meanings[name]} |"
                if v is not None
                else f"| {name} | n/a | {meanings[name]} |"
            )
        md.append("")

        # in_scope 子集：全量均值会被超纲题拉低，剔掉之后才是「检索算法能改善的部分」
        if len(in_scope_idx) != len(testset):
            md.extend(
                [
                    f"## 四指标（只看 in_scope，{len(in_scope_idx)}/{len(testset)} 题）",
                    "",
                    "| 指标 | 全量 | in_scope |",
                    "|---|---|---|",
                ]
            )
            for name in METRIC_NAMES:
                a, b = metrics[name], metrics_in_scope[name]
                fmt = lambda x: f"{x:.3f}" if x is not None else "n/a"
                md.append(f"| {name} | {fmt(a)} | {fmt(b)} |")
            md.append("")

    md.append("## 详细（每题）")
    md.append("")
    for i, d in enumerate(summary["details"], 1):
        md.append(f"### {i}. {d['question']}")
        if d["in_scope"]:
            md.append(f"- **GT**: {d['ground_truth'] or '（人工未填）'}")
        else:
            md.append("- **GT**: （超出范围，预期系统应识别）")
        ans = d["answer"]
        if len(ans) > 200:
            ans = ans[:200] + "..."
        md.append(f"- **答案**: {ans}")
        sc = d.get("scores") or {}
        md.append(
            "- **分数**: "
            + " | ".join(
                f"{m} {sc[m]:.3f}" if sc.get(m) is not None else f"{m} n/a" for m in METRIC_NAMES
            )
        )
        md.append(
            f"- **Top-k chunks**: {d['n_contexts']} | sources: {', '.join(d['sources']) or '无'}"
        )
        if d["category"]:
            md.append(f"- **类别**: {d['category']}")
        md.append("")

    with open(f"{base}.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    logger.info(f"输出: {base}.json / {base}.md")


# === 主流程 ===
def main():
    parser = argparse.ArgumentParser(description="RAGAS 评测：环境法规 RAG 系统")
    parser.add_argument(
        "--testset",
        type=Path,
        default=DEFAULT_TESTSET,
        help=f"测试集 jsonl（默认 {DEFAULT_TESTSET}）",
    )
    parser.add_argument("--top-k", type=int, default=TOP_K, help=f"RAG 检索 top_k（默认 {TOP_K}）")
    parser.add_argument(
        "--mode",
        default=os.getenv("RETRIEVAL_MODE", "dense"),
        choices=["dense", "hybrid", "hybrid_rerank"],
        help="检索模式（默认取 RETRIEVAL_MODE 环境变量，否则 dense）",
    )
    parser.add_argument("--limit", type=int, default=None, help="只跑前 N 题（调试用）")
    parser.add_argument("--dry-run", action="store_true", help="只跑 RAG 不评分（先看 RAG 输出对不对）")
    args = parser.parse_args()

    # 必须在 src.config 首次 import 之前设好：Config 的模式是类属性，import 时就定值，
    # 之后再改环境变量不生效。src.* 全部是懒加载，这里设了才赶得上。
    os.environ["RETRIEVAL_MODE"] = args.mode

    if not args.testset.exists():
        sys.exit(f"ERROR: 测试集 {args.testset} 不存在")

    testset = load_testset(args.testset)
    if args.limit:
        testset = testset[: args.limit]
    logger.info(f"检索模式：{args.mode}")

    # 1. 跑 RAG
    rag_results = run_rag_all(testset, args.top_k, args.limit)

    result = None
    if not args.dry_run:
        # 2. 组装 RAGAS dataset
        eval_ds = build_dataset(testset, rag_results)
        has_gt = any(c.get("ground_truth") for c in testset)
        # 3. 跑 RAGAS
        result = run_ragas_eval(eval_ds, has_gt)
    else:
        logger.warning("dry-run 模式：跳过 RAGAS 评分")

    # 4. 输出
    write_outputs(testset, rag_results, result, args.dry_run, args.top_k, args.mode)

    if result is not None:
        # 简洁打印四指标
        print("\n===== RAGAS 评分 =====")
        for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            v = extract_metric(result, m)
            if v is not None:
                print(f"  {m:25s}: {v:.3f}")
        print("======================\n")


if __name__ == "__main__":
    main()

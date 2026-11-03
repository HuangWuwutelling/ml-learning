"""env-rag（生态环境法典智能问答系统）的契约测试。

对应 ADR-0003：默认检索模式保持 dense；改了就是推翻决策，不是调参。
"""
import importlib.util
from pathlib import Path

import pytest

from conftest import RAG_DIR, env_default, read_jsonl, read_text

CONFIG = RAG_DIR / "src" / "config.py"
EVAL_SET = RAG_DIR / "data" / "eval" / "eval_set_v1.jsonl"
HYBRID = RAG_DIR / "src" / "rag" / "hybrid.py"


def test_default_retrieval_mode_is_dense():
    """默认档位是 dense。改这个值等于推翻 ADR-0003，必须先改 ADR。"""
    assert env_default(read_text(CONFIG), "RETRIEVAL_MODE") == "dense"


def test_retrieval_constants():
    """检索参数默认值是公开契约的一部分，改了会影响复现。"""
    src = read_text(CONFIG)
    assert env_default(src, "RETRIEVAL_CANDIDATES") == "50"
    assert env_default(src, "RRF_K") == "60"
    assert env_default(src, "TOP_K") == "5"
    assert env_default(src, "CHUNK_SIZE") == "500"
    assert env_default(src, "CHUNK_OVERLAP") == "50"
    assert env_default(src, "RERANKER_MODEL_NAME") == "BAAI/bge-reranker-v2-m3"


def test_eval_set_v1_structure():
    """30 条评测题，id 连续唯一，五个必填字段都不空。"""
    records = read_jsonl(EVAL_SET)
    assert len(records) == 30
    ids = [r["id"] for r in records]
    assert len(set(ids)) == 30
    assert ids == [f"q{i:03d}" for i in range(1, 31)]
    for r in records:
        for field in ("query", "ground_truth", "reference", "category"):
            assert str(r.get(field, "")).strip(), f'{r["id"]} 的 {field} 为空'
    assert len({r["category"] for r in records}) >= 5, '分类维度太少，测不出检索差异'


def _load_hybrid():
    """单独加载 hybrid.py，绕开 `rag` 包的 __init__，只用 loguru 这一个轻依赖。"""
    pytest.importorskip("loguru", reason="loguru 未安装，RRF 行为测试跳过")
    spec = importlib.util.spec_from_file_location("rag_hybrid_contract", Path(HYBRID))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rrf_fuse_uses_rank_reciprocal():
    """RRF 分数 = sum(1/(k+rank))，rank 从 1 开始。"""
    hybrid = _load_hybrid()
    dense = [{"content": "A"}, {"content": "B"}]
    bm25 = [{"content": "B"}]
    fused = {item["content"]: item["score"] for item in hybrid.rrf_fuse(dense, bm25, k=60)}
    assert fused["A"] == pytest.approx(1 / 61)
    assert fused["B"] == pytest.approx(1 / 62 + 1 / 61)


def test_rrf_fuse_merges_duplicate_content():
    """同一段内容两路都命中时分数相加，不出现两条。"""
    hybrid = _load_hybrid()
    doc = {"content": "同一条", "metadata": {"src": "a"}}
    fused = hybrid.rrf_fuse([doc], [dict(doc)])
    assert len(fused) == 1
    assert fused[0]["score"] == pytest.approx(2 / 61)


def test_rrf_fuse_truncates_to_top_n():
    """top_n 截断生效，超出的部分不进结果。"""
    hybrid = _load_hybrid()
    dense = [{"content": f"doc{i}"} for i in range(10)]
    assert len(hybrid.rrf_fuse(dense, [], top_n=3)) == 3


def test_rrf_fuse_handles_empty_input():
    """两路都空时返回空列表，不抛异常。"""
    hybrid = _load_hybrid()
    assert hybrid.rrf_fuse([], []) == []

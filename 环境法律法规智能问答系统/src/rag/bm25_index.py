"""
BM25 索引构建（离线一次性）

把 ChromaDB 里所有 chunks 取出，用 jieba 切词后建 BM25 索引，
保存为 pickle。QAEngine 启动时加载，避免每次重建。
"""
import os
import pickle
import jieba
from loguru import logger

from src.data.processor import VectorStore
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document


# 索引文件存放路径（与 chroma_db 同级）
INDEX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "bm25_index.pkl",
)


def chinese_preprocess(text: str) -> list[str]:
    """中文预处理：jieba 切词 + 过滤空白"""
    return [t for t in jieba.cut(text) if t.strip()]


def build_bm25_index(top_k: int = 50) -> BM25Retriever:
    """从 ChromaDB 拉所有 chunks，构建 BM25 索引并持久化

    Args:
        top_k: 索引召回宽度，存进 pickle 后可改

    Returns:
        构建好的 BM25Retriever 实例
    """
    logger.info("开始构建 BM25 索引...")
    vs = VectorStore()
    raw = vs.collection.get(include=["documents", "metadatas"])
    docs_text = raw["documents"]
    metas = raw["metadatas"]

    logger.info(f"从 ChromaDB 取出 {len(docs_text)} 个 chunks")

    # 包成 langchain Document，metadata 保留以便回溯
    documents = [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(docs_text, metas)
    ]

    bm25 = BM25Retriever.from_documents(
        documents,
        preprocess_func=chinese_preprocess,
    )
    bm25.k = top_k  # 召回宽度

    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(bm25, f)
    logger.info(f"BM25 索引已保存到 {INDEX_PATH}（top_k={top_k}）")

    return bm25


def load_bm25_index() -> BM25Retriever:
    """加载已持久化的 BM25 索引，文件缺失或反序列化失败时自动重建

    存的是 pickle 后的 langchain retriever 对象，跨 langchain 版本可能反
    序列化失败。重建只需要读一遍 ChromaDB，不贵，所以这里直接兜底重建，
    不把异常抛给调用方。
    """
    if not os.path.exists(INDEX_PATH):
        logger.warning(f"BM25 索引文件不存在: {INDEX_PATH}，自动构建")
        return build_bm25_index()
    try:
        with open(INDEX_PATH, "rb") as f:
            bm25 = pickle.load(f)
    except Exception as e:
        logger.warning(f"BM25 索引反序列化失败（{type(e).__name__}: {e}），重建")
        return build_bm25_index()
    logger.info(f"BM25 索引加载完成（top_k={bm25.k}）")
    return bm25


if __name__ == "__main__":
    build_bm25_index(top_k=50)

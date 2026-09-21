"""
三层检索：向量召回 + BM25 召回 + RRF 融合 + Cross-Encoder 重排

对应 articles/llm/13_向量数据库进阶_Hybrid_Rerank.md。三种模式：

    dense          只走向量检索（基线）
    hybrid         向量 + BM25 两路召回，RRF 融合
    hybrid_rerank  hybrid 之后再过一遍 bge-reranker-v2-m3 精排

RRF（Reciprocal Rank Fusion）只用排名换算分数，两路检索的分数尺度不同也能
直接合并，不需要归一化，也不需要调权重。
"""

from typing import Any, Dict, List

from loguru import logger


def doc_to_item(doc) -> Dict[str, Any]:
    """把 langchain 的 Document 转成与 VectorStore.search 一致的 dict 结构"""
    return {
        "content": doc.page_content,
        "metadata": doc.metadata or {},
    }


def rrf_fuse(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = 60,
    top_n: int = 50,
) -> List[Dict[str, Any]]:
    """RRF 融合：按排名倒数加权求和

    分数 = sum(1 / (k + rank))，rank 从 1 开始。同一段内容在两路都出现就
    把两个分数相加，只在一路出现就只计一路。

    用 content 字符串本身当 key，不用 hash(content)：Python 的 str hash
    每个进程加随机盐，跨进程不稳定，拿来当标识会出问题。
    """
    scores: Dict[str, float] = {}
    items: Dict[str, Dict[str, Any]] = {}

    for rank, item in enumerate(dense_results, start=1):
        key = item["content"]
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        items.setdefault(key, item)

    for rank, item in enumerate(bm25_results, start=1):
        key = item["content"]
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        items.setdefault(key, item)

    ranked = sorted(scores, key=lambda key: -scores[key])[:top_n]
    return [{**items[key], "score": scores[key]} for key in ranked]


class Reranker:
    """Cross-Encoder 精排，懒加载（首次调用才载入模型）"""

    def __init__(self, model_name: str, max_length: int = 512):
        self.model_name = model_name
        self.max_length = max_length
        self._model = None

    def _lazy_load(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            logger.info(f"正在加载重排模型: {self.model_name}")
            self._model = CrossEncoder(self.model_name, max_length=self.max_length)
            logger.info("重排模型加载完成")

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """对候选重新打分排序，返回前 top_k 条

        Cross-Encoder 的输入是 (query, doc) 原文对，不要再加 BGE 的 query
        前缀，那个前缀是给 Bi-Encoder 用的。
        """
        if not candidates:
            return []

        self._lazy_load()
        pairs = [(query, c["content"]) for c in candidates]
        scores = self._model.predict(pairs)

        # 只按分数排，不把 dict 拉进比较：两段内容完全相同时 sorted 会比到
        # dict 上，抛 TypeError
        order = sorted(range(len(candidates)), key=lambda i: -float(scores[i]))
        return [
            {**candidates[i], "score": float(scores[i])}
            for i in order[:top_k]
        ]

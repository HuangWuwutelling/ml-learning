"""
RAG问答引擎：检索增强生成
"""

import os
import json
from typing import List, Optional
from loguru import logger
import requests

from src.config import config
from src.data.processor import VectorStore


class EmbeddingModel:
    """嵌入模型封装"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL_NAME
        self._model = None

    def _lazy_load(self):
        if self._model is None:
            # 使用国内镜像加速模型下载
            os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
            from sentence_transformers import SentenceTransformer
            logger.info(f"正在加载嵌入模型: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, trust_remote_code=True)
            logger.info("嵌入模型加载完成")

    def encode(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为向量"""
        self._lazy_load()
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def encode_query(self, text: str) -> List[float]:
        """将查询文本转换为向量"""
        self._lazy_load()
        # BGE模型需要为query添加指令前缀
        emb = self._model.encode(f"为这个句子生成表示以用于检索相关文章：{text}")
        return emb.tolist()


class QAEngine:
    """RAG问答引擎"""

    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()
        # 连续对话历史，每项是 {"role": "user"/"assistant", "content": "..."}
        self._history: List[dict] = []

    def retrieve(self, query: str, top_k: int = None) -> List[dict]:
        """检索相关文档片段"""
        query_embedding = self.embedding_model.encode_query(query)
        results = self.vector_store.search(query_embedding, top_k=top_k)
        return results

    def build_prompt(self, query: str, contexts: List[dict], history: List[dict] = None) -> str:
        """构建LLM提示词"""
        context_text = "\n\n---\n\n".join([
            f"[来源：{c['metadata'].get('law_name', '未知')}]\n{c['content']}"
            for c in contexts
        ])

        # 拼接对话历史
        history_block = ""
        if history:
            turns = []
            for h in history:
                role = "用户" if h["role"] == "user" else "助手"
                turns.append(f"{role}：{h['content']}")
            history_block = "\n\n--- 对话历史 ---\n" + "\n".join(turns)

        prompt = f"""你是一个专业的环境法律法规智能助手。请根据以下提供的法律法规内容，准确回答用户的问题。

要求：
1. 仅基于提供的法律法规内容进行回答，不要编造法条
2. 如果提供的内容不足以回答问题，请明确说明
3. 引用具体法条时，注明出处（法律名称）
4. 回答应当准确、简洁、专业
5. 注意结合对话历史理解用户的连续提问，代词指代等内容需根据上文判断{history_block}

--- 相关法律法规内容 ---
{context_text}

--- 用户问题 ---
{query}

--- 回答 ---"""

        return prompt

    def query_deepseek(self, prompt: str) -> str:
        """调用DeepSeek API"""
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的环境法律法规智能助手，回答准确、简洁、专业。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
        }

        try:
            resp = requests.post(
                f"{config.DEEPSEEK_API_BASE}/v1/chat/completions",
                headers=config.deepseek_headers,
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            result = resp.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应内容: {e.response.text}")
            return f"抱歉，AI服务暂时不可用（{str(e)}），请稍后再试。"

    def answer(self, query: str, top_k: int = None) -> dict:
        """完整问答流程：检索 -> 生成"""
        # 检索
        contexts = self.retrieve(query, top_k=top_k)

        if not contexts:
            self._history.append({"role": "user", "content": query})
            self._history.append({"role": "assistant", "content": "未找到相关的法律法规内容，请尝试换个问题。"})
            self._trim_history()
            return {
                "query": query,
                "answer": "未找到相关的法律法规内容，请尝试换个问题。",
                "contexts": [],
                "sources": []
            }

        # 构建提示并调用LLM（传入历史）
        prompt = self.build_prompt(query, contexts, history=self._history)
        self._history.append({"role": "user", "content": query})
        answer_text = self.query_deepseek(prompt)
        self._history.append({"role": "assistant", "content": answer_text})
        self._trim_history()

        # 提取来源
        sources = list(set([
            c['metadata'].get('law_name', '未知来源')
            for c in contexts
            if c['metadata'].get('law_name')
        ]))

        return {
            "query": query,
            "answer": answer_text,
            "sources": sources,
            "contexts": [
                {
                    "content": c["content"][:200] + "..." if len(c["content"]) > 200 else c["content"],
                    "law_name": c["metadata"].get("law_name", "未知"),
                    "relevance": round((1 - c["distance"]) * 100, 1) if c.get("distance") else 0
                }
                for c in contexts[:3]
            ]
        }

    def _trim_history(self):
        """裁剪对话历史，保留最近 N 轮"""
        max_rounds = config.MAX_HISTORY_ROUNDS
        while len(self._history) > max_rounds * 2:
            self._history.pop(0)
            self._history.pop(0)

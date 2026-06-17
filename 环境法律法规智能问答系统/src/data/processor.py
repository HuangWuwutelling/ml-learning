"""
文档处理模块：文本分块、向量化并存入向量数据库
"""

import os
import re
import hashlib
from typing import List, Dict, Any

from loguru import logger
import chromadb
from chromadb.config import Settings

from src.config import config


class TextProcessor:
    """文本分块与处理"""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """将文本按章节和条款切分成块"""
        if chunk_size is None:
            chunk_size = config.CHUNK_SIZE
        if overlap is None:
            overlap = config.CHUNK_OVERLAP

        # 先按章节拆分（第X章）
        sections = re.split(r'(第[一二三四五六七八九十百千]+章\s*[^\n]*)', text)
        # 如果没找到章节，直接用全文
        if len(sections) <= 1:
            sections = [text]

        chunks = []
        for i in range(1 if len(sections) <= 1 else 0, len(sections), 2 if len(sections) > 1 else 1):
            if len(sections) > 1:
                section_header = sections[i] if i < len(sections) else ""
                section_body = sections[i + 1] if i + 1 < len(sections) else ""
                section_text = section_header + "\n" + section_body
            else:
                section_text = sections[i]

            # 再按条款拆分（每条条款作为独立段落）
            articles = re.split(r'(第[一二三四五六七八九十百千]+[条])', section_text)

            paragraphs = []
            for j in range(0, len(articles) - 1, 2):
                article_text = articles[j] + articles[j + 1]
                paragraphs.append(article_text.strip())
            if len(articles) % 2 == 1 and articles[-1].strip():
                paragraphs.append(articles[-1].strip())

            if not paragraphs:
                paragraphs = [section_text.strip()]

            # 合并短段落成块
            current = []
            current_len = 0
            for para in paragraphs:
                para_len = len(para)
                if current_len + para_len > chunk_size and current:
                    chunks.append('\n'.join(current))
                    # 保留部分内容作overlap
                    retain = []
                    retain_len = 0
                    for p in reversed(current):
                        if retain_len + len(p) < overlap:
                            retain.insert(0, p)
                            retain_len += len(p)
                        else:
                            break
                    current = retain
                    current_len = retain_len
                current.append(para)
                current_len += para_len

            if current:
                chunks.append('\n'.join(current))

        return [c.strip() for c in chunks if c.strip()]

    @staticmethod
    def extract_metadata(text: str, law_name: str = "") -> Dict[str, Any]:
        """提取文本元数据"""
        metadata = {
            "law_name": law_name,
            "source": "builtin",
        }
        # 尝试提取章节信息
        chapter_match = re.search(r'第[一二三四五六七八九十百千]+章', text)
        if chapter_match:
            metadata["chapter"] = chapter_match.group()
        # 尝试提取条款信息
        article_match = re.search(r'第[一二三四五六七八九十百千]+[条款]', text)
        if article_match:
            metadata["article"] = article_match.group()

        return metadata


class VectorStore:
    """向量数据库管理"""

    def __init__(self):
        os.makedirs(config.CHROMA_DB_PATH, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """获取或创建集合"""
        try:
            return self.client.get_collection(config.COLLECTION_NAME)
        except Exception:
            return self.client.create_collection(config.COLLECTION_NAME)

    def add_documents(self, chunks: List[str], metadatas: List[Dict[str, Any]], embeddings: List[List[float]]):
        """添加文档到向量库"""
        ids = []
        seen = set()
        for i, chunk in enumerate(chunks):
            hash_obj = hashlib.md5(f"{i}_{chunk}".encode('utf-8'))
            id_str = hash_obj.hexdigest()[:16]
            while id_str in seen:
                id_str = hashlib.md5(f"{id_str}_{i}".encode()).hexdigest()[:16]
            seen.add(id_str)
            ids.append(id_str)

        # 检查已存在的ID，避免重复
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        logger.info(f"已添加 {len(chunks)} 个文档块到向量数据库")

    def search(self, query_embedding: List[float], top_k: int = None) -> List[Dict[str, Any]]:
        """向量检索"""
        if top_k is None:
            top_k = config.TOP_K

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        documents = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                documents.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })
        return documents

    def count(self) -> int:
        """返回文档数量"""
        return self.collection.count()

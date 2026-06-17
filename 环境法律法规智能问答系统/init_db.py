"""
初始化向量数据库：读取法律文本 -> 分块 -> 向量化 -> 存入ChromaDB
"""

import sys
import io
from loguru import logger

# 解决Windows终端编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from src.config import config
from src.data.collector import get_codec_text
from src.data.processor import TextProcessor, VectorStore
from src.rag.qa_engine import EmbeddingModel


def init_database():
    """初始化向量数据库：读取法典全文 -> 分块 -> 向量化 -> 存入ChromaDB"""
    logger.info("开始初始化向量数据库...")

    # 1. 获取法典文本
    text = get_codec_text()
    logger.info(f"加载了《中华人民共和国生态环境法典》，共 {len(text):,} 字")

    # 2. 分块
    processor = TextProcessor()
    all_chunks = processor.chunk_text(text)
    all_metadatas = [{"law_name": "中华人民共和国生态环境法典", "source": "codec_2026"} for _ in all_chunks]

    logger.info(f"分块完成：共 {len(all_chunks)} 个文档片段")

    # 3. 向量化
    emb_model = EmbeddingModel()
    embeddings = emb_model.encode(all_chunks)
    logger.info(f"向量化完成：维度 {len(embeddings[0])}")

    # 4. 存入向量数据库
    store = VectorStore()
    store.add_documents(all_chunks, all_metadatas, embeddings)

    import re
    articles = re.findall(r'第[一二三四五六七八九十百千零]+条', text)

    print(f"\n✅ 向量数据库初始化完成！")
    print(f"   法律文件: 中华人民共和国生态环境法典")
    print(f"   总字数: {len(text):,} 字")
    print(f"   总条数: {len(articles)} 条")
    print(f"   文档片段: {len(all_chunks)} 个")
    print(f"   向量维度: {len(embeddings[0])}")
    print(f"   存储路径: {config.CHROMA_DB_PATH}")


if __name__ == "__main__":
    init_database()

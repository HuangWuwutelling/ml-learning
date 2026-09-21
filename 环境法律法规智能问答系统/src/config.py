import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")

    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh-v1.5")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    COLLECTION_NAME = "env_laws"

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

    TOP_K = int(os.getenv("TOP_K", "5"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

    # 检索模式：dense（默认，直接向量检索）| hybrid | hybrid_rerank
    # hybrid / hybrid_rerank 对应 articles/llm/13 里的三层检索，比 dense 慢得多：
    # 重排模型 CPU 上每对约 0.47s（batch=32），50 条候选一次十几到二十秒，
    # 整条查询在本机（8 核 CPU / 7.8GB 内存）实测 285s，演示默认走 dense
    RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "dense").strip().lower()
    RETRIEVAL_CANDIDATES = int(os.getenv("RETRIEVAL_CANDIDATES", "50"))  # 单路召回宽度
    RRF_K = int(os.getenv("RRF_K", "60"))                                # RRF 平滑常数
    RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-v2-m3")
    RERANK_MAX_LENGTH = int(os.getenv("RERANK_MAX_LENGTH", "512"))

    MAX_HISTORY_ROUNDS = int(os.getenv("MAX_HISTORY_ROUNDS", "5"))

    @property
    def deepseek_headers(self):
        return {
            "Authorization": f"Bearer {self.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }


config = Config()

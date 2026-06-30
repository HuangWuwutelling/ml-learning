import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh-v1.5")

    # 本地 ChromaDB（projects/env_agent/data/chroma_db），包含排污许可管理办法和条例
    CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "chroma_db")
    COLLECTION_NAME = "env_laws"

    TOP_K = int(os.getenv("TOP_K", "3"))


config = Config()

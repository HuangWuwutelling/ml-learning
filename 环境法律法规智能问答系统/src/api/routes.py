"""
FastAPI API路由
"""

import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from src.rag.qa_engine import QAEngine

router = APIRouter()
qa_engine = QAEngine()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[str]
    contexts: list[dict]
    elapsed_ms: int


class StatusResponse(BaseModel):
    status: str
    db_docs_count: int
    embedding_model: str


@router.get("/api/status", response_model=StatusResponse)
def get_status():
    """获取系统状态"""
    try:
        count = qa_engine.vector_store.count()
    except Exception:
        count = 0

    return StatusResponse(
        status="ok",
        db_docs_count=count,
        embedding_model=qa_engine.embedding_model.model_name
    )


@router.post("/api/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """处理用户查询"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    start = time.time()
    result = qa_engine.answer(request.query)
    elapsed = int((time.time() - start) * 1000)

    logger.info(f"查询: '{request.query}' -> 耗时{elapsed}ms, 来源: {result['sources']}")

    return QueryResponse(
        query=result["query"],
        answer=result["answer"],
        sources=result["sources"],
        contexts=result["contexts"],
        elapsed_ms=elapsed
    )

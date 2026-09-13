"""FastAPI 流式 demo: /stream?prompt=... -> SSE token stream."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from stream import generate, load_model


class StreamRequest(BaseModel):
    prompt: str

app = FastAPI(title="LLM Streaming Demo")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def startup():
    """预热模型（启动时加载到内存）。"""
    load_model()


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/stream")
async def stream_endpoint(prompt: str):
    """SSE 流式输出 LLM 生成的 token。"""
    return StreamingResponse(
        generate(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 NGINX buffering
        },
    )


@app.post("/stream")
async def stream_post(req: StreamRequest):
    """POST 版流式端点（前端 fetch 用）。"""
    return StreamingResponse(
        generate(req.prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

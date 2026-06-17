"""
环境法律法规智能问答系统 - 主入口
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 将项目根目录加入Python路径
sys.path.insert(0, str(Path(__file__).parent))

import logging

from loguru import logger
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.requests import Request

from src.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    from src.data.processor import VectorStore
    try:
        store = VectorStore()
        count = store.count()
        logger.info(f"向量数据库状态: {count} 个文档片段")
        if count == 0:
            logger.warning("向量数据库为空！请先运行 python init_db.py 初始化数据库")
    except Exception as e:
        logger.error(f"数据库检查失败: {e}")
        logger.warning("请先运行 python init_db.py 初始化数据库")
    yield


app = FastAPI(
    title="环境法律法规智能问答系统",
    description="基于RAG技术的中国环境法律智能问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 挂载静态文件
static_dir = Path(__file__).parent / "src" / "web" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 模板
templates_dir = Path(__file__).parent / "src" / "web" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# 导入并注册API路由
from src.api.routes import router as api_router
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """提供主页面"""
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    logger.info(f"启动服务: http://localhost:{config.PORT}")

    # 过滤 Uvicorn 的默认启动地址日志（显示的是 0.0.0.0，用户点不了）
    class _UvicornFilter(logging.Filter):
        def filter(self, record):
            return "Uvicorn running on" not in record.getMessage()
    logging.getLogger("uvicorn").addFilter(_UvicornFilter())

    uvicorn.run("app:app", host=config.HOST, port=config.PORT, reload=False)

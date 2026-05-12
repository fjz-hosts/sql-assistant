"""SQL 智能助手 - 主入口"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .database.history import close_history_manager
from .llm.manager import get_llm_manager
from .database.manager import get_db_manager

# 模板和静态文件路径
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    yield
    await get_llm_manager().close_all()
    await get_db_manager().close_all()
    await close_history_manager()


app = FastAPI(
    title="SQL 智能助手",
    description="自然语言转 SQL 查询工具",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Jinja2 模板
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# API 路由
app.include_router(api_router)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


def main():
    """CLI 入口"""
    import uvicorn

    # 确保控制台支持 UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 60)
    print("  SQL Assistant v1.0.0")
    print("  Natural Language -> SQL -> Results")
    print("=" * 60)
    print()
    print("  URL: http://localhost:5010")
    print("  Docs: http://localhost:5010/docs")
    print()
    print("  Configure LLM and Database in Settings (gear icon)")
    print("=" * 60)
    print()

    uvicorn.run(
        "sql_assistant.main:app",
        host="0.0.0.0",
        port=5010,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()

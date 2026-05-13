"""Schema 相关 API 路由"""

from fastapi import APIRouter

from .dependencies import get_db

router = APIRouter()


@router.post("/schema/refresh")
async def refresh_schema():
    db = get_db()
    schema = await db.refresh_schema()
    return schema


@router.get("/schema")
async def get_schema():
    db = get_db()
    schema = await db.get_schema()
    return schema
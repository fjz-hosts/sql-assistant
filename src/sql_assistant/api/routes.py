"""API 路由"""

from fastapi import APIRouter

from .query import router as query_router
from .config import router as config_router
from .conversation import router as conversation_router
from .backup import router as backup_router
from .schema import router as schema_router
from .history import router as history_router

router = APIRouter(prefix="/api")

router.include_router(query_router)
router.include_router(config_router)
router.include_router(conversation_router)
router.include_router(backup_router)
router.include_router(schema_router)
router.include_router(history_router)
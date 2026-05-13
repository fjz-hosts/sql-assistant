"""配置相关 API 路由"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from ..settings import LLMProviderConfig, DatabaseConfig

from .dependencies import get_config, get_llm, get_db
from .models import (
    LLMConfigRequest, LLMConfigResponse,
    DatabaseConfigRequest, DatabaseConfigResponse,
    TestConnectionRequest, TestConnectionResponse, TestLLMConnectionRequest,
    AppSettingsResponse,
)

router = APIRouter()


def _mask_api_key(key: str) -> str:
    if len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


@router.get("/config/llm/models")
async def get_llm_models(provider: Optional[str] = None):
    from ..settings import PROVIDER_MODELS

    if provider:
        models = PROVIDER_MODELS.get(provider, [])
        return {"provider": provider, "models": models}

    return {"models": PROVIDER_MODELS}


@router.get("/config/llm", response_model=list[LLMConfigResponse])
async def list_llm_configs():
    config = get_config()
    return [
        LLMConfigResponse(
            name=p.name, provider=p.provider, model=p.get_model(),
            enabled=p.enabled, api_key_masked=_mask_api_key(p.api_key),
        )
        for p in config.get_llm_providers()
    ]


@router.post("/config/llm")
async def save_llm_config(req: LLMConfigRequest):
    config = get_config()
    llm_config = LLMProviderConfig(**req.model_dump())
    config.add_llm_provider(llm_config)
    return {"ok": True}


@router.delete("/config/llm/{name}")
async def delete_llm_config(name: str):
    config = get_config()
    if not config.remove_llm_provider(name):
        raise HTTPException(status_code=404, detail="LLM 配置不存在")
    return {"ok": True}


@router.put("/config/llm/active/{name}")
async def set_active_llm(name: str):
    config = get_config()
    if not config.set_active_llm(name):
        raise HTTPException(status_code=404, detail="LLM 配置不存在")
    return {"ok": True}


@router.post("/config/llm/test", response_model=TestConnectionResponse)
async def test_llm_connection(req: TestLLMConnectionRequest):
    llm = get_llm()
    config_mgr = get_config()

    if req.config:
        llm_config = LLMProviderConfig(**req.config.model_dump())
        from ..llm.manager import LLMManager
        llm_manager = LLMManager()
        provider = llm_manager.get_provider(llm_config)
        result = await provider.test_connection()
    elif req.name:
        llm_config = config_mgr.get_llm_provider(req.name)
        if not llm_config:
            raise HTTPException(status_code=404, detail="LLM 配置不存在")
        from ..llm.manager import LLMManager
        llm_manager = LLMManager()
        provider = llm_manager.get_provider(llm_config)
        result = await provider.test_connection()
    else:
        result = {"success": False, "error": "请提供 LLM 配置名称或完整配置"}

    return TestConnectionResponse(
        success=result.get("success", False),
        message=result.get("message") or (result.get("data") or {}).get("message") or result.get("error") or "未知错误",
    )


@router.get("/config/database", response_model=list[DatabaseConfigResponse])
async def list_database_configs():
    config = get_config()
    return [
        DatabaseConfigResponse(
            name=db.name, db_type=db.db_type, host=db.host,
            port=db.get_port(), user=db.user,
            database=db.database, enabled=db.enabled,
        )
        for db in config.get_databases()
    ]


@router.post("/config/database")
async def save_database_config(req: DatabaseConfigRequest):
    config = get_config()
    db_config = DatabaseConfig(**req.model_dump())
    config.add_database(db_config)
    return {"ok": True}


@router.delete("/config/database/{name}")
async def delete_database_config(name: str):
    config = get_config()
    if not config.remove_database(name):
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    return {"ok": True}


@router.put("/config/database/active/{name}")
async def set_active_database(name: str):
    config = get_config()
    if not config.set_active_database(name):
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    return {"ok": True}


@router.post("/config/database/test", response_model=TestConnectionResponse)
async def test_database_connection(req: TestConnectionRequest):
    db = get_db()
    config_mgr = get_config()

    if req.config:
        db_config = DatabaseConfig(**req.config.model_dump())
        result = await db.test_connection(db_config)
    elif req.name:
        db_config = config_mgr.get_database(req.name)
        if not db_config:
            raise HTTPException(status_code=404, detail="数据库配置不存在")
        result = await db.test_connection(db_config)
    else:
        result = {"success": False, "error": "请提供数据库名称或完整配置"}

    return TestConnectionResponse(
        success=result.get("success", False),
        message=result.get("message") or (result.get("data") or {}).get("message") or result.get("error") or "未知错误",
    )


@router.get("/config/settings", response_model=AppSettingsResponse)
async def get_settings():
    config = get_config()
    settings = config.get_settings()
    return AppSettingsResponse(
        active_llm=settings.active_llm,
        active_database=settings.active_database,
        max_history_rows=settings.max_history_rows,
        llm_providers=[
            LLMConfigResponse(
                name=p.name, provider=p.provider, model=p.get_model(),
                enabled=p.enabled, api_key_masked=_mask_api_key(p.api_key),
            )
            for p in settings.llm_providers
        ],
        databases=[
            DatabaseConfigResponse(
                name=db.name, db_type=db.db_type, host=db.host,
                port=db.get_port(), user=db.user,
                database=db.database, enabled=db.enabled,
            )
            for db in settings.databases
        ],
    )
"""API 路由"""

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..settings import LLMProviderConfig, DatabaseConfig
from ..llm.prompts import SYSTEM_PROMPT, NL_TO_SQL_PROMPT
from ..database.connectors.base import QueryResult

from .dependencies import get_config, get_llm, get_db, get_history
from .models import (
    QueryRequest, QueryResponse,
    LLMConfigRequest, LLMConfigResponse,
    DatabaseConfigRequest, DatabaseConfigResponse,
    TestConnectionRequest, TestConnectionResponse,
    AppSettingsResponse, HistoryRecord, HistoryListResponse,
)

router = APIRouter(prefix="/api")


# ---- Helpers ----

def _mask_api_key(key: str) -> str:
    if len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


def _extract_sql(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _result_to_dict(result: Any) -> dict:
    if isinstance(result, QueryResult):
        return {
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
            "affected_rows": result.affected_rows,
            "sql_type": result.sql_type,
        }
    return {"value": str(result)}


# ---- Query ----

@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    config = get_config()
    llm = get_llm()
    db = get_db()
    history = get_history()

    active_llm = config.get_active_llm()
    active_db = config.get_active_database()

    if not active_llm:
        raise HTTPException(status_code=400, detail="请先在设置中配置并选择 LLM 提供商")
    if not active_db:
        raise HTTPException(status_code=400, detail="请先在设置中配置并选择数据库")

    db_type = request.db_type_override or active_db.db_type

    # 获取 schema 文本
    schema_text = await db.get_schema_text()

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(
                db_type=db_type,
                schema_context=schema_text,
            )},
            {"role": "user", "content": NL_TO_SQL_PROMPT.format(
                db_type=db_type,
                question=request.question,
            )},
        ]
        sql_text = await llm.chat(messages, temperature=0.1)
        sql_text = _extract_sql(sql_text)
    except Exception as e:
        return QueryResponse(
            success=False,
            question=request.question,
            error=f"LLM 调用失败: {e}",
        )

    try:
        result = await db.execute(sql_text)
        result_dict = _result_to_dict(result)

        history_id = await history.add_record(
            question=request.question,
            sql=sql_text,
            result=result_dict,
            db_type=db_type,
            llm_provider=active_llm.provider,
            success=True,
        )

        return QueryResponse(
            success=True,
            question=request.question,
            sql=sql_text,
            result=result_dict,
            history_id=history_id,
        )
    except Exception as e:
        history_id = await history.add_record(
            question=request.question,
            sql=sql_text,
            db_type=db_type,
            llm_provider=active_llm.provider,
            success=False,
            error_message=str(e),
        )
        return QueryResponse(
            success=False,
            question=request.question,
            sql=sql_text,
            error=f"SQL 执行失败: {e}",
            history_id=history_id,
        )


@router.post("/query/stream")
async def execute_query_stream(request: QueryRequest):
    config = get_config()
    llm = get_llm()
    db = get_db()
    history = get_history()

    active_llm = config.get_active_llm()
    active_db = config.get_active_database()

    if not active_llm:
        raise HTTPException(status_code=400, detail="请先配置 LLM")
    if not active_db:
        raise HTTPException(status_code=400, detail="请先配置数据库")

    db_type = request.db_type_override or active_db.db_type

    schema_text = await db.get_schema_text()

    async def stream():
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(
                db_type=db_type,
                schema_context=schema_text,
            )},
            {"role": "user", "content": NL_TO_SQL_PROMPT.format(
                db_type=db_type,
                question=request.question,
            )},
        ]

        full_sql = ""
        yield json.dumps({"type": "llm_start"}, ensure_ascii=False) + "\n"

        try:
            async for chunk in llm.chat_stream(messages, temperature=0.1):
                full_sql += chunk
                yield json.dumps({"type": "llm_chunk", "content": chunk}, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "content": f"LLM 调用失败: {e}"}, ensure_ascii=False) + "\n"
            return

        full_sql = _extract_sql(full_sql)
        yield json.dumps({"type": "sql", "content": full_sql}, ensure_ascii=False) + "\n"

        try:
            result = await db.execute(full_sql)
            result_dict = _result_to_dict(result)
            yield json.dumps({"type": "result", "content": result_dict}, ensure_ascii=False) + "\n"

            await history.add_record(
                question=request.question,
                sql=full_sql,
                result=result_dict,
                db_type=db_type,
                llm_provider=active_llm.provider,
                success=True,
            )
        except Exception as e:
            yield json.dumps({"type": "error", "content": f"SQL 执行失败: {e}"}, ensure_ascii=False) + "\n"
            await history.add_record(
                question=request.question,
                sql=full_sql,
                db_type=db_type,
                llm_provider=active_llm.provider,
                success=False,
                error_message=str(e),
            )

        yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


# ---- Config: LLM ----

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


# ---- Config: Database ----

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
        result = {"success": False, "message": "请提供数据库名称或完整配置"}

    return TestConnectionResponse(**result)


# ---- Schema ----

@router.post("/schema/refresh")
async def refresh_schema():
    """强制刷新当前数据库的 schema"""
    db = get_db()
    schema = await db.refresh_schema()
    return schema


@router.get("/schema")
async def get_schema():
    """获取当前数据库 schema（缓存）"""
    db = get_db()
    schema = await db.get_schema()
    return schema


# ---- Config: Settings ----

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


# ---- History ----

@router.get("/history", response_model=HistoryListResponse)
async def list_history(limit: int = 50, offset: int = 0):
    history = get_history()
    records = await history.get_records(limit=limit, offset=offset)
    total = await history.get_count()
    return HistoryListResponse(
        records=[
            HistoryRecord(
                id=r["id"], question=r["question"], sql=r["sql"],
                result_json=r.get("result_json"),
                db_type=r.get("db_type", ""), llm_provider=r.get("llm_provider", ""),
                success=bool(r.get("success", 1)),
                error_message=r.get("error_message", ""),
                created_at=r.get("created_at", ""),
            )
            for r in records
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/history/{record_id}")
async def delete_history_record(record_id: int):
    history = get_history()
    if not await history.delete_record(record_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"ok": True}


@router.delete("/history")
async def clear_history():
    history = get_history()
    count = await history.clear_history()
    return {"ok": True, "deleted": count}


@router.get("/history/{record_id}")
async def get_history_record(record_id: int):
    history = get_history()
    record = await history.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record

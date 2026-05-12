"""API 路由"""

import json
from typing import Any, Optional

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
    TestConnectionRequest, TestConnectionResponse, TestLLMConnectionRequest,
    AppSettingsResponse, HistoryRecord, HistoryListResponse,
    ConversationRequest, ConversationResponse, ConversationDetailResponse,
    ConversationListResponse, ConversationUpdateRequest,
    BackupRequest, BackupResponse, BackupInfoResponse, BackupListResponse,
    RestoreRequest, RestoreResponse,
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

        total_rows = result_dict.get("row_count", 0)
        total_pages = (total_rows + request.page_size - 1) // request.page_size if total_rows > 0 else 1

        if total_rows > 0 and request.page > 1:
            start_idx = (request.page - 1) * request.page_size
            end_idx = start_idx + request.page_size
            result_dict["rows"] = result_dict["rows"][start_idx:end_idx]
            result_dict["row_count"] = len(result_dict["rows"])

        pagination = {
            "page": request.page,
            "page_size": request.page_size,
            "total_rows": total_rows,
            "total_pages": total_pages,
        }

        history_id = await history.add_record(
            question=request.question,
            sql=sql_text,
            result=result_dict,
            db_type=db_type,
            llm_provider=active_llm.provider,
            success=True,
            conversation_id=request.conversation_id,
        )

        return QueryResponse(
            success=True,
            question=request.question,
            sql=sql_text,
            result=result_dict,
            history_id=history_id,
            conversation_id=request.conversation_id,
            pagination=pagination,
        )
    except Exception as e:
        history_id = await history.add_record(
            question=request.question,
            sql=sql_text,
            db_type=db_type,
            llm_provider=active_llm.provider,
            success=False,
            error_message=str(e),
            conversation_id=request.conversation_id,
        )
        return QueryResponse(
            success=False,
            question=request.question,
            sql=sql_text,
            error=f"SQL 执行失败: {e}",
            history_id=history_id,
            conversation_id=request.conversation_id,
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
                conversation_id=request.conversation_id,
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
                conversation_id=request.conversation_id,
            )

        yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


# ---- Conversation ----

@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(req: ConversationRequest):
    history = get_history()
    conversation_id = await history.create_conversation(title=req.title)
    conversation = await history.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=500, detail="创建对话失败")
    return ConversationResponse(**conversation)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(limit: int = 50, offset: int = 0):
    history = get_history()
    conversations = await history.get_conversations(limit=limit, offset=offset)
    total = await history.get_conversation_count()
    return ConversationListResponse(
        conversations=[ConversationResponse(**c) for c in conversations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(conversation_id: int):
    history = get_history()
    conversation = await history.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    messages = await history.get_conversation_messages(conversation_id)
    return ConversationDetailResponse(
        id=conversation["id"],
        title=conversation["title"],
        created_at=conversation.get("created_at", ""),
        updated_at=conversation.get("updated_at", ""),
        messages=[HistoryRecord(**m) for m in messages],
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: int, req: ConversationUpdateRequest):
    history = get_history()
    if not await history.update_conversation(conversation_id, req.title):
        raise HTTPException(status_code=404, detail="对话不存在")
    
    conversation = await history.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=500, detail="获取对话失败")
    return ConversationResponse(**conversation)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    history = get_history()
    if not await history.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"ok": True}


# ---- Config: LLM Models ----

@router.get("/config/llm/models")
async def get_llm_models(provider: Optional[str] = None):
    """获取 LLM 提供商支持的模型列表"""
    from ..settings import PROVIDER_MODELS
    
    if provider:
        models = PROVIDER_MODELS.get(provider, [])
        return {"provider": provider, "models": models}
    
    return {"models": PROVIDER_MODELS}


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
        result = {"success": False, "error": "请提供数据库名称或完整配置"}

    return TestConnectionResponse(
        success=result.get("success", False),
        message=result.get("message") or (result.get("data") or {}).get("message") or result.get("error") or "未知错误",
    )


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
async def list_history(limit: int = 50, offset: int = 0, conversation_id: Optional[int] = None):
    history = get_history()
    records = await history.get_records(limit=limit, offset=offset, conversation_id=conversation_id)
    total = await history.get_count(conversation_id=conversation_id)
    return HistoryListResponse(
        records=[
            HistoryRecord(
                id=r["id"],
                conversation_id=r.get("conversation_id"),
                question=r["question"],
                sql=r["sql"],
                result_json=r.get("result_json"),
                db_type=r.get("db_type", ""),
                llm_provider=r.get("llm_provider", ""),
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


# ---- Backup ----

@router.post("/backup", response_model=BackupResponse)
async def create_backup(request: BackupRequest):
    """创建数据库备份"""
    from ..database.backup import get_backup_manager, BackupConfig
    
    backup_manager = get_backup_manager()
    
    config = BackupConfig(
        backup_type=request.backup_type,
        tables=request.tables,
        include_schema=request.include_schema,
        include_data=request.include_data
    )
    
    result = await backup_manager.backup(config)
    
    return BackupResponse(
        success=result.success,
        message=result.message,
        backup_id=result.backup_id,
        backup_path=result.backup_path,
        tables_backed_up=result.tables_backed_up,
        total_records=result.total_records,
        backup_size=result.backup_size,
        backup_time=result.backup_time
    )


@router.get("/backup/list", response_model=BackupListResponse)
async def list_backups():
    """获取备份列表"""
    from ..database.backup import get_backup_manager
    
    backup_manager = get_backup_manager()
    backups = backup_manager.list_backups()
    
    return BackupListResponse(
        backups=[BackupInfoResponse(
            backup_id=b.backup_id,
            backup_type=b.backup_type,
            db_type=b.db_type,
            db_name=b.db_name,
            tables=b.tables,
            record_count=b.record_count,
            backup_time=b.backup_time,
            file_size=b.file_size
        ) for b in backups],
        total=len(backups)
    )


@router.get("/backup/{backup_id}", response_model=BackupInfoResponse)
async def get_backup_info(backup_id: str):
    """获取指定备份的详细信息"""
    from ..database.backup import get_backup_manager
    
    backup_manager = get_backup_manager()
    backup_info = backup_manager.get_backup_info(backup_id)
    
    if not backup_info:
        raise HTTPException(status_code=404, detail="备份不存在")
    
    return BackupInfoResponse(
        backup_id=backup_info.backup_id,
        backup_type=backup_info.backup_type,
        db_type=backup_info.db_type,
        db_name=backup_info.db_name,
        tables=backup_info.tables,
        record_count=backup_info.record_count,
        backup_time=backup_info.backup_time,
        file_size=backup_info.file_size
    )


@router.delete("/backup/{backup_id}")
async def delete_backup(backup_id: str):
    """删除指定备份"""
    from ..database.backup import get_backup_manager
    
    backup_manager = get_backup_manager()
    
    if not backup_manager.delete_backup(backup_id):
        raise HTTPException(status_code=404, detail="备份不存在")
    
    return {"ok": True, "message": "备份删除成功"}


@router.post("/backup/restore", response_model=RestoreResponse)
async def restore_backup(request: RestoreRequest):
    """从备份恢复数据库"""
    from ..database.backup import get_backup_manager
    
    backup_manager = get_backup_manager()
    
    result = await backup_manager.restore(
        backup_id=request.backup_id,
        restore_schema=request.restore_schema,
        restore_data=request.restore_data,
        tables=request.tables
    )
    
    return RestoreResponse(
        success=result.success,
        message=result.message,
        backup_id=result.backup_id,
        tables_restored=result.tables_restored,
        total_records=result.total_records
    )
"""历史记录相关 API 路由"""

from typing import Optional

from fastapi import APIRouter

from .dependencies import get_history
from .models import HistoryRecord, HistoryListResponse

router = APIRouter()


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
        return {"ok": False, "error": "记录不存在"}
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
        return {"error": "记录不存在"}
    return record
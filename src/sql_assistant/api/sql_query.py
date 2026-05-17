"""直接 SQL 查询 API 路由"""

from fastapi import APIRouter, HTTPException

from ..database.connectors.base import QueryResult
from ..database.security import get_security_guard

from .dependencies import get_config, get_db, get_history
from .models import DirectSQLRequest, DirectSQLResponse

router = APIRouter()


def _result_to_dict(result) -> dict:
    if isinstance(result, QueryResult):
        return {
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
            "affected_rows": result.affected_rows,
            "sql_type": result.sql_type,
        }
    return {"value": str(result)}


@router.post("/sql/execute", response_model=DirectSQLResponse)
async def execute_direct_sql(request: DirectSQLRequest):
    config = get_config()
    db = get_db()
    history = get_history()

    active_db = config.get_active_database()
    if not active_db:
        raise HTTPException(status_code=400, detail="请先在设置中配置并选择数据库")

    sql_text = request.sql.strip()
    if not sql_text:
        raise HTTPException(status_code=400, detail="SQL 语句不能为空")

    security_guard = get_security_guard()
    check_result = security_guard.check_sql_safety(sql_text)

    if not check_result.is_safe:
        return DirectSQLResponse(
            success=False,
            sql=sql_text,
            error=f"SQL 安全检查失败: {check_result.blocked_reason}",
        )

    requires_confirmation, confirmation_reason = security_guard.requires_confirmation(sql_text)

    if requires_confirmation and not request.confirmed:
        return DirectSQLResponse(
            success=False,
            sql=sql_text,
            error="此操作需要用户确认",
            requires_confirmation=True,
            confirmation_reason=confirmation_reason,
            warning=check_result.warning,
            risk_level=check_result.risk_level,
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
            question=f"[直接SQL] {sql_text[:100]}",
            sql=sql_text,
            result=result_dict,
            db_type=active_db.db_type,
            llm_provider="direct_sql",
            success=True,
            conversation_id=request.conversation_id,
        )

        return DirectSQLResponse(
            success=True,
            sql=sql_text,
            result=result_dict,
            history_id=history_id,
            conversation_id=request.conversation_id,
            pagination=pagination,
        )
    except Exception as e:
        await history.add_record(
            question=f"[直接SQL] {sql_text[:100]}",
            sql=sql_text,
            db_type=active_db.db_type,
            llm_provider="direct_sql",
            success=False,
            error_message=str(e),
            conversation_id=request.conversation_id,
        )
        return DirectSQLResponse(
            success=False,
            sql=sql_text,
            error=f"SQL 执行失败: {e}",
        )
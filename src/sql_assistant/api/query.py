"""查询相关 API 路由"""

import hashlib
import json
from typing import Any

from fastapi import APIRouter, HTTPException

from ..llm.prompts import SYSTEM_PROMPT, NL_TO_SQL_PROMPT, CONTEXT_PROMPT
from ..database.connectors.base import QueryResult
from ..database.security import get_security_guard

from .dependencies import get_config, get_llm, get_db, get_history
from .models import QueryRequest, QueryResponse, SQLPreviewResponse

router = APIRouter()

MAX_CONTEXT_MESSAGES = 10
"""最大上下文消息数量，防止 prompt 过长"""


def _extract_sql(text: str) -> str:
    """从 LLM 输出中提取 SQL 语句。

    处理多种常见格式：
    - Markdown 代码块包裹：```sql ... ```
    - 带前导注释：-- 注释\\nDELETE FROM ...
    - 带解释性前缀：以下是 SQL：\\nSELECT ...
    """
    text = text.strip()

    # 1. 提取 markdown 代码块内容
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 2. 如果提取后内容仍不以 SQL 关键字开头，尝试定位 SQL 起始行
    sql_keywords = (
        "SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE", "ALTER",
        "DROP", "TRUNCATE", "SHOW", "DESCRIBE", "EXPLAIN", "USE", "SET",
        "GRANT", "REVOKE", "BEGIN", "COMMIT", "ROLLBACK",
    )
    lines = text.split("\n")
    # 跳过前导的注释行和空行，找到第一条实际语句
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("--") or stripped.startswith("#") or stripped.startswith("/*"):
            continue
        # 检查是否以 SQL 关键字开头
        upper = stripped.upper()
        if any(upper.startswith(kw + " ") or upper == kw or upper.startswith(kw + "\t")
               for kw in sql_keywords):
            start_idx = i
            break
        else:
            # 不是 SQL 关键字也不是注释，可能是解释性文字，继续往后找
            continue

    if start_idx > 0:
        text = "\n".join(lines[start_idx:]).strip()

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


def _hash_sql(sql: str) -> str:
    return hashlib.sha256(sql.strip().encode('utf-8')).hexdigest()


async def _build_messages_with_context(
    db_type: str,
    schema_text: str,
    question: str,
    conversation_id: int = None,
) -> list[dict]:
    """构建带有对话上下文的消息列表
    
    Args:
        db_type: 数据库类型
        schema_text: 数据库 schema 文本
        question: 当前用户问题
        conversation_id: 对话 ID（可选）
    
    Returns:
        包含系统提示、上下文历史和当前问题的消息列表
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(
            db_type=db_type,
            schema_context=schema_text,
        )},
    ]
    
    # 如果有对话ID，获取历史消息作为上下文
    if conversation_id:
        history = get_history()
        context_messages = await history.get_conversation_messages(conversation_id)
        
        # 只保留最近的 MAX_CONTEXT_MESSAGES 条消息
        if context_messages:
            context_messages = context_messages[-MAX_CONTEXT_MESSAGES:]
            
            for msg in context_messages:
                # 添加用户问题
                messages.append({
                    "role": "user",
                    "content": CONTEXT_PROMPT.format(
                        question=msg["question"],
                    ),
                })
                
                # 添加助手回复（SQL结果）
                result_summary = msg.get("result_json")
                if result_summary:
                    try:
                        result_data = json.loads(result_summary)
                        rows = result_data.get("rows", [])
                        row_count = result_data.get("row_count", 0)
                        columns = result_data.get("columns", [])
                        
                        # 构建结果摘要
                        if row_count > 0 and columns:
                            summary_lines = []
                            summary_lines.append(f"执行结果: {row_count} 行数据")
                            summary_lines.append(f"列: {', '.join(str(c) for c in columns)}")
                            
                            # 如果行数较少，显示部分数据
                            if row_count <= 5:
                                for i, row in enumerate(rows[:3]):
                                    summary_lines.append(f"  行{i+1}: {', '.join(str(v) for v in row)}")
                            else:
                                summary_lines.append(f"  (显示前3行)...")
                            
                            result_text = "\n".join(summary_lines)
                        else:
                            result_text = f"执行完成，影响 {result_data.get('affected_rows', 0)} 行"
                    except:
                        result_text = f"SQL: {msg['sql']}"
                else:
                    result_text = f"SQL: {msg['sql']}"
                
                messages.append({
                    "role": "assistant",
                    "content": result_text,
                })
    
    # 添加当前问题
    messages.append({
        "role": "user",
        "content": NL_TO_SQL_PROMPT.format(
            db_type=db_type,
            question=question,
        ),
    })
    
    return messages


def _validate_request() -> tuple:
    config = get_config()
    llm = get_llm()
    db = get_db()

    active_llm = config.get_active_llm()
    active_db = config.get_active_database()

    if not active_llm:
        raise HTTPException(status_code=400, detail="请先在设置中配置并选择 LLM 提供商")
    if not active_db:
        raise HTTPException(status_code=400, detail="请先在设置中配置并选择数据库")

    return config, llm, db, active_llm, active_db


@router.post("/query/preview", response_model=SQLPreviewResponse)
async def preview_query(request: QueryRequest):
    config, llm, db, active_llm, active_db = _validate_request()
    db_type = request.db_type_override or active_db.db_type
    schema_text = await db.get_schema_text()

    try:
        messages = await _build_messages_with_context(
            db_type=db_type,
            schema_text=schema_text,
            question=request.question,
            conversation_id=request.conversation_id,
        )
        sql_text = await llm.chat(messages, temperature=0.1)
        sql_text = _extract_sql(sql_text)

        security_guard = get_security_guard()
        check_result = security_guard.check_sql_safety(sql_text)

        if not check_result.is_safe:
            return SQLPreviewResponse(
                success=False,
                error=f"SQL 安全检查失败: {check_result.blocked_reason}"
            )

        requires_confirmation, confirmation_reason = security_guard.requires_confirmation(sql_text)

        return SQLPreviewResponse(
            success=True,
            sql=sql_text,
            sql_hash=_hash_sql(sql_text),
            requires_confirmation=requires_confirmation,
            confirmation_reason=confirmation_reason,
            warning=check_result.warning,
            risk_level=check_result.risk_level
        )

    except Exception as e:
        return SQLPreviewResponse(
            success=False,
            error=f"生成 SQL 失败: {e}"
        )


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    config, llm, db, active_llm, active_db = _validate_request()
    history = get_history()
    db_type = request.db_type_override or active_db.db_type
    schema_text = await db.get_schema_text()

    sql_text = ""
    
    # 如果是确认执行（confirmed=True），直接使用前端传递的 SQL
    # 避免 LLM 非确定性导致 hash 不匹配
    if request.confirmed:
        if not request.sql:
            return QueryResponse(
                success=False,
                question=request.question,
                error="确认执行时需要提供 SQL 语句",
            )
        
        sql_text = request.sql
        
        # 如果提供了 sql_hash，验证 SQL 的完整性
        if request.sql_hash:
            expected_hash = _hash_sql(sql_text)
            if request.sql_hash != expected_hash:
                return QueryResponse(
                    success=False,
                    question=request.question,
                    sql=sql_text,
                    error="SQL 验证失败，请重新预览并确认",
                )
    else:
        # 非确认执行，正常调用 LLM 生成 SQL
        try:
            messages = await _build_messages_with_context(
                db_type=db_type,
                schema_text=schema_text,
                question=request.question,
                conversation_id=request.conversation_id,
            )
            sql_text = await llm.chat(messages, temperature=0.1)
            sql_text = _extract_sql(sql_text)
        except Exception as e:
            return QueryResponse(
                success=False,
                question=request.question,
                error=f"LLM 调用失败: {e}",
            )

    security_guard = get_security_guard()
    check_result = security_guard.check_sql_safety(sql_text)
    if not check_result.is_safe:
        return QueryResponse(
            success=False,
            question=request.question,
            sql=sql_text,
            error=f"SQL 安全检查失败: {check_result.blocked_reason}",
        )

    requires_confirmation, _ = security_guard.requires_confirmation(sql_text)

    if requires_confirmation and not request.confirmed:
        return QueryResponse(
            success=False,
            question=request.question,
            sql=sql_text,
            error="此操作需要用户确认，请预览后确认执行",
        )

    try:
        result = await db.execute(sql_text)
        full_result = _result_to_dict(result)

        total_rows = full_result.get("row_count", 0)
        total_pages = (total_rows + request.page_size - 1) // request.page_size if total_rows > 0 else 1

        history_id = await history.add_record(
            question=request.question,
            sql=sql_text,
            result=full_result,
            db_type=db_type,
            llm_provider=active_llm.provider,
            success=True,
            conversation_id=request.conversation_id,
        )

        paginated_result = {
            "columns": full_result.get("columns", []),
            "rows": full_result.get("rows", []),
            "row_count": total_rows,
            "affected_rows": full_result.get("affected_rows"),
            "sql_type": full_result.get("sql_type", ""),
        }

        pagination = {
            "page": request.page,
            "page_size": request.page_size,
            "total_rows": total_rows,
            "total_pages": total_pages,
        }

        return QueryResponse(
            success=True,
            question=request.question,
            sql=sql_text,
            result=paginated_result,
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
"""SQL执行计划分析 API"""

import json
import re
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException

from .models import (
    ExplainRequest,
    ExplainResponse,
    ExplainPlanNode,
    ExplainHistoryListResponse,
    ExplainHistoryRecord,
    ExplainStatsResponse,
)
from .dependencies import get_db, get_config
from ..database.manager import DatabaseManager
from ..database.explain import ExplainPlanManager
from ..config import ConfigManager

router = APIRouter(prefix="/explain", tags=["explain"])

# 慢查询阈值 (ms)
SLOW_QUERY_THRESHOLD = 1000


def get_explain_manager() -> ExplainPlanManager:
    return ExplainPlanManager()


@router.post("/analyze", response_model=ExplainResponse)
async def analyze_explain(
    request: ExplainRequest,
    db: DatabaseManager = Depends(get_db),
    config: ConfigManager = Depends(get_config),
    explain_manager: ExplainPlanManager = Depends(get_explain_manager),
):
    """分析SQL执行计划"""
    try:
        # 获取当前数据库连接
        db_config = config.get_active_database()
        if not db_config:
            return ExplainResponse(
                success=False,
                error="未配置活动数据库"
            )

        connector = await db.get_connector()
        if not connector:
            return ExplainResponse(
                success=False,
                error=f"无法获取数据库连接器"
            )

        db_type = db_config.db_type
        db_name = db_config.database

        # 根据数据库类型执行EXPLAIN
        if db_type == "mysql":
            result = await _explain_mysql(connector, request.sql, request.analyze)
        elif db_type == "postgresql":
            result = await _explain_postgresql(connector, request.sql, request.analyze)
        elif db_type == "sqlserver":
            result = await _explain_sqlserver(connector, request.sql)
        else:
            return ExplainResponse(
                success=False,
                error=f"不支持的数据库类型: {db_type}"
            )

        if not result["success"]:
            return ExplainResponse(
                success=False,
                error=result.get("error", "执行计划分析失败")
            )

        # 分析执行计划，生成警告和建议
        warnings = _analyze_warnings(result, db_type)
        suggestions = _generate_suggestions(result, db_type)

        # 判断是否为慢查询
        is_slow = result.get("actual_time_ms", 0) > SLOW_QUERY_THRESHOLD or \
                  result.get("estimated_cost", 0) > 10000

        # 保存到历史记录
        plan_tree = result.get("plan_tree")
        plan_id = await explain_manager.save_plan(
            sql=request.sql,
            db_type=db_type,
            db_name=db_name,
            plan_json=plan_tree.model_dump() if plan_tree else {},
            plan_text=result.get("plan_text", ""),
            estimated_cost=result.get("estimated_cost", 0.0),
            estimated_rows=result.get("estimated_rows", 0),
            actual_time_ms=result.get("actual_time_ms", 0.0),
            warnings=warnings,
            suggestions=suggestions,
            is_slow_query=is_slow
        )

        return ExplainResponse(
            success=True,
            plan_id=plan_id,
            sql=request.sql,
            db_type=db_type,
            db_name=db_name,
            plan_tree=result.get("plan_tree"),
            plan_text=result.get("plan_text", ""),
            estimated_cost=result.get("estimated_cost", 0.0),
            estimated_rows=result.get("estimated_rows", 0),
            actual_time_ms=result.get("actual_time_ms", 0.0),
            warnings=warnings,
            suggestions=suggestions,
            is_slow_query=is_slow
        )

    except Exception as e:
        return ExplainResponse(
            success=False,
            error=f"执行计划分析失败: {str(e)}"
        )


async def _explain_mysql(connector, sql: str, analyze: bool = True) -> dict:
    """MySQL EXPLAIN分析"""
    try:
        await connector.connect()

        # 使用 EXPLAIN FORMAT=JSON 获取结构化数据
        explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
        result = await connector.execute(explain_sql)

        plan_text = ""
        plan_tree = None
        estimated_cost = 0.0
        estimated_rows = 0
        actual_time_ms = 0.0

        if result.rows:
            # MySQL返回的JSON可能在多行
            plan_text = "".join(str(row[0]) for row in result.rows)
            try:
                plan_json = json.loads(plan_text)
                plan_tree = _parse_mysql_explain(plan_json)
                estimated_cost = plan_json.get("query_block", {}).get("cost_info", {}).get("query_cost", 0)
                estimated_rows = _extract_mysql_rows(plan_json)
            except json.JSONDecodeError:
                pass

        # 如果需要ANALYZE，执行实际查询获取时间
        if analyze:
            try:
                import time
                start = time.time()
                await connector.execute(f"SELECT 1 FROM ({sql}) AS t LIMIT 0")
                actual_time_ms = (time.time() - start) * 1000
            except:
                pass

        await connector.disconnect()

        return {
            "success": True,
            "plan_tree": plan_tree,
            "plan_text": plan_text,
            "estimated_cost": float(estimated_cost) if estimated_cost else 0.0,
            "estimated_rows": estimated_rows,
            "actual_time_ms": actual_time_ms
        }

    except Exception as e:
        await connector.disconnect()
        return {"success": False, "error": str(e)}


async def _explain_postgresql(connector, sql: str, analyze: bool = True) -> dict:
    """PostgreSQL EXPLAIN分析"""
    try:
        await connector.connect()

        # 使用 EXPLAIN (FORMAT JSON)
        explain_option = "EXPLAIN (FORMAT JSON"
        if analyze:
            explain_option += ", ANALYZE, BUFFERS, TIMING"
        explain_option += ")"

        explain_sql = f"{explain_option} {sql}"
        result = await connector.execute(explain_sql)

        plan_text = ""
        plan_tree = None
        estimated_cost = 0.0
        estimated_rows = 0
        actual_time_ms = 0.0

        if result.rows:
            plan_text = str(result.rows[0][0])
            try:
                plan_data = json.loads(plan_text)
                if plan_data and len(plan_data) > 0:
                    plan = plan_data[0].get("Plan", {})
                    plan_tree = _parse_postgres_plan(plan)
                    estimated_cost = plan.get("Total Cost", 0)
                    estimated_rows = plan.get("Plan Rows", 0)
                    if analyze:
                        actual_time_ms = plan.get("Actual Total Time", 0)
            except json.JSONDecodeError:
                pass

        await connector.disconnect()

        return {
            "success": True,
            "plan_tree": plan_tree,
            "plan_text": plan_text,
            "estimated_cost": float(estimated_cost),
            "estimated_rows": estimated_rows,
            "actual_time_ms": float(actual_time_ms)
        }

    except Exception as e:
        await connector.disconnect()
        return {"success": False, "error": str(e)}


async def _explain_sqlserver(connector, sql: str) -> dict:
    """SQL Server执行计划分析"""
    try:
        await connector.connect()

        # SQL Server使用 SET SHOWPLAN_XML 或实际执行统计
        setup_sql = """
        SET STATISTICS PROFILE ON;
        SET STATISTICS TIME ON;
        SET STATISTICS IO ON;
        """
        await connector.execute(setup_sql)

        result = await connector.execute(sql)

        plan_text = ""
        plan_tree = None
        estimated_rows = 0

        if result.rows and result.columns:
            # 尝试构建计划树
            plan_tree = _parse_sqlserver_plan(result.columns, result.rows)
            estimated_rows = len(result.rows)

        await connector.disconnect()

        return {
            "success": True,
            "plan_tree": plan_tree,
            "plan_text": plan_text,
            "estimated_cost": 0.0,
            "estimated_rows": estimated_rows,
            "actual_time_ms": 0.0
        }

    except Exception as e:
        await connector.disconnect()
        return {"success": False, "error": str(e)}


def _parse_mysql_explain(plan_json: dict) -> Optional[ExplainPlanNode]:
    """解析MySQL EXPLAIN JSON"""
    try:
        query_block = plan_json.get("query_block", {})
        table = query_block.get("table", {})

        if not table:
            return None

        return ExplainPlanNode(
            id=1,
            node_type=table.get("access_type", "UNKNOWN"),
            table_name=table.get("table_name"),
            access_type=table.get("access_type"),
            key=table.get("key"),
            rows=table.get("rows_examined_per_scan") or table.get("rows"),
            cost=table.get("cost_info", {}).get("read_cost"),
            extra=table.get("attached_condition")
        )
    except:
        return None


def _extract_mysql_rows(plan_json: dict) -> int:
    """提取MySQL估计行数"""
    try:
        table = plan_json.get("query_block", {}).get("table", {})
        return table.get("rows_examined_per_scan") or table.get("rows", 0)
    except:
        return 0


def _parse_postgres_plan(plan: dict, parent_id: int = 0) -> ExplainPlanNode:
    """递归解析PostgreSQL执行计划"""
    node = ExplainPlanNode(
        id=parent_id + 1,
        node_type=plan.get("Node Type", "Unknown"),
        table_name=plan.get("Relation Name"),
        access_type=plan.get("Scan Direction") or plan.get("Join Type"),
        key=plan.get("Index Name"),
        rows=plan.get("Plan Rows", 0),
        cost=plan.get("Total Cost", 0),
        actual_rows=plan.get("Actual Rows"),
        actual_time=plan.get("Actual Total Time"),
        extra=plan.get("Filter") or plan.get("Index Cond")
    )

    # 递归处理子节点
    plans = plan.get("Plans", [])
    for i, sub_plan in enumerate(plans):
        child = _parse_postgres_plan(sub_plan, parent_id + (i + 1) * 100)
        child.parent_id = node.id
        node.children.append(child)

    return node


def _parse_sqlserver_plan(columns: List[str], rows: List[List[Any]]) -> Optional[ExplainPlanNode]:
    """解析SQL Server执行计划"""
    if not rows:
        return None

    # 简化处理，取第一行
    row = rows[0]
    row_dict = dict(zip(columns, row))

    return ExplainPlanNode(
        id=1,
        node_type=row_dict.get("PhysicalOp", "Unknown"),
        table_name=row_dict.get("ObjectName"),
        rows=row_dict.get("EstimateRows", 0),
        extra=row_dict.get("Argument")
    )


def _analyze_warnings(result: dict, db_type: str) -> List[str]:
    """分析执行计划，生成警告"""
    warnings = []
    plan_tree = result.get("plan_tree")

    if not plan_tree:
        return warnings

    # 检查全表扫描
    def check_node(node: ExplainPlanNode):
        access_type = (node.access_type or "").upper()
        node_type = (node.node_type or "").upper()

        if access_type in ["ALL", "SEQ SCAN", "CLUSTERED INDEX SCAN"] or \
           "FULL SCAN" in node_type or \
           "SEQ SCAN" in node_type:
            warnings.append(f"表 '{node.table_name}' 发生全表扫描，建议添加索引")

        if node.rows and node.rows > 100000:
            warnings.append(f"扫描大量数据行 ({node.rows} 行)，可能影响性能")

        if node.cost and node.cost > 10000:
            warnings.append(f"估计成本较高 ({node.cost:.2f})，建议优化")

        for child in node.children:
            check_node(child)

    if isinstance(plan_tree, ExplainPlanNode):
        check_node(plan_tree)

    # 检查实际执行时间
    actual_time = result.get("actual_time_ms", 0)
    if actual_time > SLOW_QUERY_THRESHOLD:
        warnings.append(f"查询执行时间较长 ({actual_time:.2f}ms)")

    return warnings


def _generate_suggestions(result: dict, db_type: str) -> List[str]:
    """生成优化建议"""
    suggestions = []
    warnings = result.get("warnings", [])
    plan_tree = result.get("plan_tree")

    if not plan_tree:
        return suggestions

    # 基于警告生成建议
    for warning in warnings:
        if "全表扫描" in warning:
            suggestions.append("考虑在WHERE条件列上创建索引")
            suggestions.append("检查查询条件是否能有效利用索引")
        if "大量数据" in warning:
            suggestions.append("考虑添加LIMIT限制返回行数")
            suggestions.append("检查是否可以添加更精确的过滤条件")
        if "成本较高" in warning:
            suggestions.append("考虑优化JOIN顺序")
            suggestions.append("检查是否需要所有查询的列")

    # 数据库特定建议
    if db_type == "mysql":
        suggestions.append("使用 EXPLAIN FORMAT=TREE 获取更详细的执行计划")
    elif db_type == "postgresql":
        suggestions.append("使用 EXPLAIN (ANALYZE, BUFFERS) 获取详细的I/O统计")

    return list(set(suggestions))  # 去重


@router.get("/history", response_model=ExplainHistoryListResponse)
async def get_explain_history(
    limit: int = 50,
    offset: int = 0,
    db_type: Optional[str] = None,
    only_slow: bool = False,
    explain_manager: ExplainPlanManager = Depends(get_explain_manager),
):
    """获取执行计划历史"""
    records = await explain_manager.get_plans(
        limit=limit,
        offset=offset,
        db_type=db_type,
        only_slow=only_slow
    )

    total = await explain_manager.get_count(db_type=db_type, only_slow=only_slow)

    return ExplainHistoryListResponse(
        records=[ExplainHistoryRecord(**r) for r in records],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/history/{plan_id}", response_model=ExplainResponse)
async def get_explain_detail(
    plan_id: int,
    explain_manager: ExplainPlanManager = Depends(get_explain_manager),
):
    """获取执行计划详情"""
    plan = await explain_manager.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="执行计划不存在")

    return ExplainResponse(
        success=True,
        plan_id=plan_id,
        sql=plan["sql"],
        db_type=plan["db_type"],
        db_name=plan["db_name"],
        plan_tree=ExplainPlanNode(**plan["plan_json"]) if plan["plan_json"] else None,
        plan_text=plan["plan_text"],
        estimated_cost=plan["estimated_cost"],
        estimated_rows=plan["estimated_rows"],
        actual_time_ms=plan["actual_time_ms"],
        warnings=plan["warnings"],
        suggestions=plan["suggestions"],
        is_slow_query=plan["is_slow_query"]
    )


@router.delete("/history/{plan_id}")
async def delete_explain_history(
    plan_id: int,
    explain_manager: ExplainPlanManager = Depends(get_explain_manager),
):
    """删除执行计划历史"""
    success = await explain_manager.delete_plan(plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="执行计划不存在")
    return {"success": True}


@router.get("/stats", response_model=ExplainStatsResponse)
async def get_explain_stats(
    explain_manager: ExplainPlanManager = Depends(get_explain_manager),
):
    """获取执行计划统计"""
    stats = await explain_manager.get_slow_query_stats()
    return ExplainStatsResponse(**stats)

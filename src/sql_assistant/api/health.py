"""数据库健康检查 API 路由"""

from fastapi import APIRouter, HTTPException

from ..database.manager import DatabaseManager
from ..database.health import DatabaseHealthChecker

router = APIRouter()


async def get_health_checker() -> DatabaseHealthChecker:
    """获取健康检查器实例"""
    db_manager = DatabaseManager()
    try:
        connector = await db_manager.get_connector()
        return DatabaseHealthChecker(connector)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
async def health_check():
    """获取数据库健康状态概览"""
    try:
        checker = await get_health_checker()
        metrics = await checker.check_connection()

        return {
            "success": True,
            "db_type": metrics.db_type,
            "status": metrics.status,
            "connection_ok": metrics.connection_ok,
            "response_time_ms": metrics.response_time_ms,
            "error_message": metrics.error_message,
            "timestamp": metrics.timestamp,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/connection")
async def health_connection():
    """获取数据库连接详细信息"""
    try:
        checker = await get_health_checker()
        metrics = await checker.check_connection()
        performance = await checker.get_performance_metrics()

        return {
            "success": True,
            "db_type": metrics.db_type,
            "status": metrics.status,
            "connection_ok": metrics.connection_ok,
            "response_time_ms": metrics.response_time_ms,
            "max_connections": performance.get("max_connections", 0),
            "current_connections": performance.get("current_connections", 0),
            "uptime_seconds": performance.get("uptime_seconds", 0),
            "error_message": metrics.error_message,
            "timestamp": metrics.timestamp,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/tables")
async def health_tables():
    """获取数据库表健康信息"""
    try:
        checker = await get_health_checker()

        if not checker.connector._conn:
            raise HTTPException(status_code=400, detail="数据库未连接")

        tables = await checker.get_table_stats()

        total_size = sum(t.size_mb for t in tables)
        total_rows = sum(t.row_count for t in tables)

        return {
            "success": True,
            "db_type": checker.connector.db_type,
            "table_count": len(tables),
            "total_size_mb": round(total_size, 2),
            "total_rows": total_rows,
            "tables": [
                {
                    "name": t.name,
                    "engine": t.engine,
                    "row_count": t.row_count,
                    "size_mb": t.size_mb,
                    "index_length_mb": t.index_length_mb,
                    "data_length_mb": t.data_length_mb,
                    "auto_increment": t.auto_increment,
                    "avg_row_length": t.avg_row_length,
                    "check_time": t.check_time,
                }
                for t in tables
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/indexes")
async def health_indexes():
    """获取数据库索引健康信息"""
    try:
        checker = await get_health_checker()

        if not checker.connector._conn:
            raise HTTPException(status_code=400, detail="数据库未连接")

        indexes = await checker.get_index_stats()

        table_indexes = {}
        for idx in indexes:
            if idx.table_name not in table_indexes:
                table_indexes[idx.table_name] = []
            table_indexes[idx.table_name].append({
                "index_name": idx.index_name,
                "column_name": idx.column_name,
                "unique": idx.unique,
                "cardinality": idx.cardinality,
                "seq_in_index": idx.seq_in_index,
            })

        return {
            "success": True,
            "db_type": checker.connector.db_type,
            "total_indexes": len(indexes),
            "table_count": len(table_indexes),
            "indexes_by_table": table_indexes,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/performance")
async def health_performance():
    """获取数据库性能指标"""
    try:
        checker = await get_health_checker()
        metrics = await checker.check_connection()
        performance = await checker.get_performance_metrics()

        return {
            "success": True,
            "db_type": metrics.db_type,
            "status": metrics.status,
            "response_time_ms": metrics.response_time_ms,
            "slow_queries": performance.get("slow_queries", 0),
            "max_connections": performance.get("max_connections", 0),
            "current_connections": performance.get("current_connections", 0),
            "uptime_seconds": performance.get("uptime_seconds", 0),
            "query_per_second": performance.get("query_per_second", 0.0),
            "buffer_hit_ratio": performance.get("buffer_hit_ratio", 0.0),
            "timestamp": metrics.timestamp,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

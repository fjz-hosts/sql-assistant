"""数据库健康检查模块"""

from dataclasses import dataclass
from typing import Any, Optional

from .connectors.base import BaseConnector


@dataclass
class HealthMetrics:
    """健康指标数据类"""
    db_type: str = ""
    status: str = "unknown"
    response_time_ms: float = 0.0
    connection_ok: bool = False
    error_message: str = ""
    table_count: int = 0
    total_size_mb: float = 0.0
    index_count: int = 0
    slow_queries: int = 0
    max_connections: int = 0
    current_connections: int = 0
    uptime_seconds: int = 0
    buffer_hit_ratio: float = 0.0
    query_per_second: float = 0.0
    timestamp: str = ""


@dataclass
class TableHealth:
    """表健康信息"""
    name: str
    engine: str = ""
    row_count: int = 0
    size_mb: float = 0.0
    index_length_mb: float = 0.0
    data_length_mb: float = 0.0
    auto_increment: Optional[int] = None
    avg_row_length: int = 0
    check_time: Optional[str] = None


@dataclass
class IndexHealth:
    """索引健康信息"""
    table_name: str
    index_name: str
    column_name: str
    unique: bool = False
    cardinality: int = 0
    seq_in_index: int = 1


class DatabaseHealthChecker:
    """数据库健康检查器"""

    def __init__(self, connector: BaseConnector):
        self.connector = connector

    async def check_connection(self) -> HealthMetrics:
        """检查数据库连接状态"""
        import time

        metrics = HealthMetrics(db_type=self.connector.db_type)
        metrics.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            start = time.perf_counter()
            await self.connector.test_connection()
            end = time.perf_counter()

            metrics.response_time_ms = round((end - start) * 1000, 2)
            metrics.connection_ok = True
            metrics.status = "healthy"
        except Exception as e:
            metrics.status = "unhealthy"
            metrics.connection_ok = False
            metrics.error_message = str(e)

        return metrics

    async def get_table_stats(self) -> list[TableHealth]:
        """获取表统计信息"""
        db_type = self.connector.db_type

        if db_type == "mysql":
            return await self._get_mysql_table_stats()
        elif db_type == "postgresql":
            return await self._get_postgresql_table_stats()
        elif db_type == "sqlserver":
            return await self._get_sqlserver_table_stats()
        elif db_type == "redis":
            return await self._get_redis_info()
        elif db_type == "mongodb":
            return await self._get_mongodb_stats()
        else:
            return []

    async def get_index_stats(self) -> list[IndexHealth]:
        """获取索引统计信息"""
        db_type = self.connector.db_type

        if db_type == "mysql":
            return await self._get_mysql_index_stats()
        elif db_type == "postgresql":
            return await self._get_postgresql_index_stats()
        elif db_type == "sqlserver":
            return await self._get_sqlserver_index_stats()
        else:
            return []

    async def get_performance_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        db_type = self.connector.db_type

        if db_type == "mysql":
            return await self._get_mysql_performance()
        elif db_type == "postgresql":
            return await self._get_postgresql_performance()
        elif db_type == "sqlserver":
            return await self._get_sqlserver_performance()
        elif db_type == "redis":
            return await self._get_redis_performance()
        else:
            return {}

    async def _get_mysql_table_stats(self) -> list[TableHealth]:
        """获取 MySQL 表统计信息"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return []

        tables = []
        import asyncio

        def _run():
            with self.connector._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        TABLE_NAME,
                        ENGINE,
                        TABLE_ROWS,
                        ROUND(DATA_LENGTH / 1024 / 1024, 2) as data_mb,
                        ROUND(INDEX_LENGTH / 1024 / 1024, 2) as index_mb,
                        ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as total_mb,
                        AUTO_INCREMENT,
                        AVG_ROW_LENGTH,
                        CREATE_TIME,
                        UPDATE_TIME
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC
                """, (self.connector.database,))
                return cursor.fetchall()

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(None, _run)

        for row in rows:
            tables.append(TableHealth(
                name=row[0],
                engine=row[1] or "",
                row_count=int(row[2]) if row[2] else 0,
                size_mb=float(row[5]) if row[5] else 0.0,
                index_length_mb=float(row[4]) if row[4] else 0.0,
                data_length_mb=float(row[3]) if row[3] else 0.0,
                auto_increment=int(row[6]) if row[6] else None,
                avg_row_length=int(row[7]) if row[7] else 0,
                check_time=str(row[9]) if row[9] else (str(row[8]) if row[8] else None),
            ))

        return tables

    async def _get_mysql_index_stats(self) -> list[IndexHealth]:
        """获取 MySQL 索引统计信息"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return []

        indexes = []
        import asyncio

        def _run():
            with self.connector._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        TABLE_NAME,
                        INDEX_NAME,
                        COLUMN_NAME,
                        NON_UNIQUE,
                        CARDINALITY,
                        SEQ_IN_INDEX
                    FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
                """, (self.connector.database,))
                return cursor.fetchall()

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(None, _run)

        for row in rows:
            indexes.append(IndexHealth(
                table_name=row[0],
                index_name=row[1],
                column_name=row[2],
                unique=(row[3] == 0),
                cardinality=int(row[4]) if row[4] else 0,
                seq_in_index=int(row[5]) if row[5] else 1,
            ))

        return indexes

    async def _get_mysql_performance(self) -> dict[str, Any]:
        """获取 MySQL 性能指标"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return {}

        import asyncio

        def _run():
            result = {}
            with self.connector._conn.cursor() as cursor:
                cursor.execute("SHOW GLOBAL STATUS")
                status = {row[0]: row[1] for row in cursor.fetchall()}

                cursor.execute("SHOW GLOBAL VARIABLES LIKE 'max_connections'")
                max_conn = cursor.fetchone()
                result["max_connections"] = int(max_conn[1]) if max_conn else 0

                result["current_connections"] = int(status.get("Threads_connected", 0))
                result["slow_queries"] = int(status.get("Slow_queries", 0))
                result["query_per_second"] = float(status.get("Questions", 0)) / max(
                    float(status.get("Uptime", 1)), 1
                )

                cursor.execute("SHOW GLOBAL VARIABLES LIKE 'uptime'")
                uptime = cursor.fetchone()
                result["uptime_seconds"] = int(uptime[1]) if uptime else 0

                return result

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)

    async def _get_postgresql_table_stats(self) -> list[TableHealth]:
        """获取 PostgreSQL 表统计信息"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return []

        tables = []
        import asyncio

        def _run():
            with self.connector._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        c.relname as table_name,
                        COALESCE(pg_size_pretty(pg_total_relation_size(c.oid)), '0 B') as size,
                        COALESCE(pg_total_relation_size(c.oid) / 1024 / 1024, 0) as size_mb,
                        COALESCE(pg_stat_get_live_tuples(c.oid), 0) as row_count
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relkind = 'r' AND n.nspname = 'public'
                    ORDER BY pg_total_relation_size(c.oid) DESC
                    LIMIT 50
                """)
                return cursor.fetchall()

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(None, _run)

        for row in rows:
            tables.append(TableHealth(
                name=row[0],
                row_count=int(row[3]) if row[3] else 0,
                size_mb=float(row[2]) if row[2] else 0.0,
            ))

        return tables

    async def _get_postgresql_index_stats(self) -> list[IndexHealth]:
        """获取 PostgreSQL 索引统计信息"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return []

        indexes = []
        import asyncio

        def _run():
            with self.connector._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        c.relname as table_name,
                        i.relname as index_name,
                        a.attname as column_name,
                        indisunique as unique_index,
                        coalesce(pg_stat_get_live_tuples(c.oid), 0) as cardinality
                    FROM pg_index pi
                    JOIN pg_class c ON c.oid = pi.indrelid
                    JOIN pg_class i ON i.oid = pi.indexrelid
                    JOIN pg_attribute a ON a.attrelid = pi.indrelid AND a.attnum = ANY(pi.indkey)
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public'
                    ORDER BY c.relname, i.relname
                """)
                return cursor.fetchall()

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(None, _run)

        for row in rows:
            indexes.append(IndexHealth(
                table_name=row[0],
                index_name=row[1],
                column_name=row[2],
                unique=bool(row[3]) if row[3] is not None else False,
                cardinality=int(row[4]) if row[4] else 0,
            ))

        return indexes

    async def _get_postgresql_performance(self) -> dict[str, Any]:
        """获取 PostgreSQL 性能指标"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return {}

        import asyncio

        def _run():
            result = {}
            with self.connector._conn.cursor() as cursor:
                cursor.execute("SELECT pg_postmaster_start_time()")
                start_time = cursor.fetchone()
                if start_time:
                    import datetime
                    result["uptime_seconds"] = int(
                        (datetime.datetime.now() - start_time[0]).total_seconds()
                    )

                cursor.execute("SELECT count(*) FROM pg_stat_activity")
                result["current_connections"] = cursor.fetchone()[0]

                cursor.execute("SHOW max_connections")
                result["max_connections"] = int(cursor.fetchone()[0])

                cursor.execute("SELECT sum(calls) FROM pg_stat_statements WHERE query LIKE '%SELECT%'")
                result["query_per_second"] = float(cursor.fetchone()[0] or 0) / max(result.get("uptime_seconds", 1), 1)

                return result

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)

    async def _get_sqlserver_table_stats(self) -> list[TableHealth]:
        """获取 SQL Server 表统计信息"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return []

        tables = []
        import asyncio

        def _run():
            with self.connector._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        t.NAME as table_name,
                        p.rows as row_count,
                        SUM(a.total_pages) * 8 / 1024.0 as total_size_mb
                    FROM sys.tables t
                    INNER JOIN sys.indexes i ON t.object_id = i.object_id
                    INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                    INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                    WHERE t.is_ms_shipped = 0 AND p.index_id IN (0, 1)
                    GROUP BY t.NAME, p.rows
                    ORDER BY total_size_mb DESC
                """)
                return cursor.fetchall()

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(None, _run)

        for row in rows:
            tables.append(TableHealth(
                name=row[0],
                row_count=int(row[1]) if row[1] else 0,
                size_mb=float(row[2]) if row[2] else 0.0,
            ))

        return tables

    async def _get_sqlserver_index_stats(self) -> list[IndexHealth]:
        """获取 SQL Server 索引统计信息"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return []

        indexes = []
        import asyncio

        def _run():
            with self.connector._conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        t.name as table_name,
                        i.name as index_name,
                        COL_NAME(ic.object_id, ic.column_id) as column_name,
                        i.is_unique,
                        i.is_primary_key
                    FROM sys.indexes i
                    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
                    INNER JOIN sys.tables t ON i.object_id = t.object_id
                    WHERE t.is_ms_shipped = 0
                    ORDER BY t.name, i.name
                """)
                return cursor.fetchall()

        loop = asyncio.get_event_loop()
        rows = await loop.run_in_executor(None, _run)

        for row in rows:
            indexes.append(IndexHealth(
                table_name=row[0],
                index_name=row[1],
                column_name=str(row[2]) if row[2] else "",
                unique=bool(row[3]) if row[3] is not None else False,
            ))

        return indexes

    async def _get_sqlserver_performance(self) -> dict[str, Any]:
        """获取 SQL Server 性能指标"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return {}

        import asyncio

        def _run():
            result = {}
            with self.connector._conn.cursor() as cursor:
                cursor.execute("SELECT @@CONNECTIONS")
                result["max_connections"] = int(cursor.fetchone()[0])

                cursor.execute("SELECT COUNT(*) FROM sys.dm_exec_sessions WHERE status = 'running'")
                result["current_connections"] = cursor.fetchone()[0]

                cursor.execute("SELECT @@TOTAL_READ")
                result["slow_queries"] = int(cursor.fetchone()[0])

                return result

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)

    async def _get_redis_info(self) -> list[TableHealth]:
        """获取 Redis 信息"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return []

        import asyncio

        def _run():
            info = self.connector._conn.info()
            keys_count = self.connector._conn.dbsize()
            memory = info.get("used_memory_human", "0")
            return {
                "keys_count": keys_count,
                "memory_used": memory,
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _run)

        return [TableHealth(
            name="redis",
            row_count=info["keys_count"],
            size_mb=0.0,
        )]

    async def _get_redis_performance(self) -> dict[str, Any]:
        """获取 Redis 性能指标"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return {}

        import asyncio

        def _run():
            info = self.connector._conn.info()
            return {
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0"),
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)

    async def _get_mongodb_stats(self) -> list[TableHealth]:
        """获取 MongoDB 统计信息"""
        if not hasattr(self.connector, "_conn") or not self.connector._conn:
            return []

        import asyncio

        def _run():
            db = self.connector._conn[self.connector.database]
            stats = db.command("dbStats")
            return {
                "collections": stats.get("collections", 0),
                "data_size_mb": stats.get("dataSize", 0) / (1024 * 1024),
                "storage_size_mb": stats.get("storageSize", 0) / (1024 * 1024),
                "documents": stats.get("objects", 0),
            }

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _run)

        return [TableHealth(
            name="mongodb",
            row_count=info["documents"],
            size_mb=info["data_size_mb"],
        )]

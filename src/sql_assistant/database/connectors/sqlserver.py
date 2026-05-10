"""SQL Server 连接器"""

import asyncio
from typing import Any

from .base import BaseConnector, QueryResult


class SQLServerConnector(BaseConnector):
    """SQL Server 数据库连接器 (使用 pymssql)"""

    db_type = "sqlserver"

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        super().__init__(host, port, user, password, database)
        self._conn = None

    async def connect(self) -> None:
        try:
            import pymssql
        except ImportError:
            raise ImportError(
                "请安装 pymssql: uv pip install pymssql  或  pip install pymssql"
            )

        loop = asyncio.get_event_loop()
        self._conn = await loop.run_in_executor(
            None,
            lambda: pymssql.connect(
                server=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                timeout=10,
                login_timeout=10,
            ),
        )

    async def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    async def execute(self, sql: str) -> QueryResult:
        if not self._conn:
            raise RuntimeError("SQL Server 未连接")

        loop = asyncio.get_event_loop()
        result = QueryResult()

        def _run():
            cursor = self._conn.cursor()
            try:
                statements = [s.strip() for s in sql.split(";") if s.strip()]
                if not statements:
                    return result

                for stmt in statements:
                    cursor.execute(stmt)
                    sql_type = self.classify_sql(stmt)
                    result.sql_type = sql_type

                    if sql_type == "SELECT":
                        result.columns = [col[0] for col in cursor.description] if cursor.description else []
                        result.rows = cursor.fetchall() if cursor.description else []
                        result.row_count = len(result.rows)
                    else:
                        result.affected_rows = cursor.rowcount

                self._conn.commit()
                return result
            finally:
                cursor.close()

        return await loop.run_in_executor(None, _run)

    async def get_schema(self) -> dict:
        if not self._conn:
            raise RuntimeError("SQL Server 未连接")

        loop = asyncio.get_event_loop()

        def _run():
            schema_sql = """
                SELECT
                    c.TABLE_NAME,
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.CHARACTER_MAXIMUM_LENGTH,
                    CASE WHEN c.IS_NULLABLE = 'YES' THEN 1 ELSE 0 END,
                    c.COLUMN_DEFAULT,
                    CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'PRI' ELSE '' END
                FROM INFORMATION_SCHEMA.COLUMNS c
                LEFT JOIN (
                    SELECT ku.TABLE_NAME, ku.COLUMN_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                        ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                    WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
                WHERE c.TABLE_SCHEMA = 'dbo'
                ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
            """
            tables_dict: dict[str, list] = {}
            cursor = self._conn.cursor()
            try:
                cursor.execute(schema_sql)
                for row in cursor.fetchall():
                    tname = row[0]
                    col_type = row[2]
                    if row[3]:
                        col_type = f"{col_type}({row[3]})"
                    if tname not in tables_dict:
                        tables_dict[tname] = []
                    tables_dict[tname].append({
                        "name": row[1],
                        "type": col_type,
                        "nullable": bool(row[4]),
                        "key": row[6],
                        "default": str(row[5]) if row[5] is not None else None,
                        "comment": "",
                    })
            finally:
                cursor.close()

            tables = [{"name": k, "columns": v} for k, v in tables_dict.items()]
            return {"db_type": "sqlserver", "tables": tables}

        return await loop.run_in_executor(None, _run)

    async def test_connection(self) -> bool:
        try:
            await self.connect()
            return True
        except Exception:
            return False
        finally:
            await self.disconnect()

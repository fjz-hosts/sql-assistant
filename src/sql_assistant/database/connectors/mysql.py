"""MySQL 连接器"""

import asyncio
from typing import Optional

import pymysql

from .base import BaseConnector, QueryResult
from ..pool import ConnectionPool


class MySQLConnector(BaseConnector):
    """MySQL 数据库连接器"""

    db_type = "mysql"

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        pool: Optional[ConnectionPool] = None,
    ):
        super().__init__(host, port, user, password, database)
        self._conn: pymysql.Connection | None = None
        self._pool = pool

    @property
    def has_connection(self) -> bool:
        return self._conn is not None or self._pool is not None

    @staticmethod
    def create_connection_factory(
        host: str, port: int, user: str, password: str, database: str
    ):
        def _factory():
            return pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.Cursor,
                connect_timeout=10,
            )
        return _factory

    def _make_connection(self) -> pymysql.Connection:
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.Cursor,
            connect_timeout=10,
        )

    async def connect(self) -> None:
        loop = asyncio.get_event_loop()
        self._conn = await loop.run_in_executor(None, self._make_connection)

    async def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    async def execute(self, sql: str) -> QueryResult:
        loop = asyncio.get_event_loop()
        result = QueryResult()

        def _run_with_pool():
            conn = self._pool.acquire()
            try:
                self._execute_on_conn(conn, sql, result)
                return result
            except Exception:
                conn.rollback()
                raise
            finally:
                self._pool.release(conn)

        def _run_single():
            if not self._conn:
                raise RuntimeError("MySQL 未连接")
            self._execute_on_conn(self._conn, sql, result)
            return result

        _run = _run_with_pool if self._pool else _run_single
        return await loop.run_in_executor(None, _run)

    def _execute_on_conn(self, conn: pymysql.Connection, sql: str, result: QueryResult) -> None:
        with conn.cursor() as cursor:
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            if not statements:
                return

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

            conn.commit()

    async def get_schema(self) -> dict:
        loop = asyncio.get_event_loop()

        def _run_with_pool():
            conn = self._pool.acquire()
            try:
                return self._get_schema_on_conn(conn)
            finally:
                self._pool.release(conn)

        def _run_single():
            if not self._conn:
                raise RuntimeError("MySQL 未连接")
            return self._get_schema_on_conn(self._conn)

        _run = _run_with_pool if self._pool else _run_single
        return await loop.run_in_executor(None, _run)

    def _get_schema_on_conn(self, conn: pymysql.Connection) -> dict:
        tables = []
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            table_rows = cursor.fetchall()
            for (table_name,) in table_rows:
                cursor.execute(f"SHOW FULL COLUMNS FROM `{table_name}`")
                columns = []
                for col in cursor.fetchall():
                    columns.append({
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[3] == "YES",
                        "key": col[4] or "",
                        "default": str(col[5]) if col[5] is not None else None,
                        "comment": col[8] or "",
                    })
                tables.append({"name": table_name, "columns": columns})
        return {"db_type": "mysql", "tables": tables}

    async def test_connection(self) -> dict:
        from .exceptions import format_connector_result
        try:
            await self.connect()
            if self._conn:
                self._conn.ping(reconnect=False)
            return format_connector_result(True, data={"message": "MySQL 连接成功"}, db_type="mysql")
        except Exception as e:
            return format_connector_result(False, error=str(e), db_type="mysql", code="CONNECTION_FAILED")
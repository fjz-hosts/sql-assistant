"""PostgreSQL 连接器"""

import asyncio
from typing import Optional

import psycopg2
import psycopg2.extras

from .base import BaseConnector, QueryResult
from ..pool import ConnectionPool


class PostgreSQLConnector(BaseConnector):
    """PostgreSQL 数据库连接器"""

    db_type = "postgresql"

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
        self._conn: psycopg2.extensions.connection | None = None
        self._pool = pool

    @property
    def has_connection(self) -> bool:
        return self._conn is not None or self._pool is not None

    @staticmethod
    def create_connection_factory(
        host: str, port: int, user: str, password: str, database: str
    ):
        def _factory():
            return psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=database,
                connect_timeout=10,
            )
        return _factory

    def _make_connection(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            dbname=self.database,
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
                raise RuntimeError("PostgreSQL 未连接")
            self._execute_on_conn(self._conn, sql, result)
            return result

        _run = _run_with_pool if self._pool else _run_single
        return await loop.run_in_executor(None, _run)

    def _execute_on_conn(
        self, conn: psycopg2.extensions.connection, sql: str, result: QueryResult
    ) -> None:
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
                raise RuntimeError("PostgreSQL 未连接")
            return self._get_schema_on_conn(self._conn)

        _run = _run_with_pool if self._pool else _run_single
        return await loop.run_in_executor(None, _run)

    def _get_schema_on_conn(self, conn: psycopg2.extensions.connection) -> dict:
        schema_sql = """
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.character_maximum_length,
                c.is_nullable,
                c.column_default,
                tc.constraint_type
            FROM information_schema.columns c
            LEFT JOIN information_schema.key_column_usage kcu
                ON c.table_schema = kcu.table_schema
                AND c.table_name = kcu.table_name
                AND c.column_name = kcu.column_name
            LEFT JOIN information_schema.table_constraints tc
                ON kcu.constraint_name = tc.constraint_name
                AND tc.constraint_type = 'PRIMARY KEY'
            WHERE c.table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY c.table_name, c.ordinal_position
        """
        tables_dict: dict[str, list] = {}
        with conn.cursor() as cursor:
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
                    "nullable": row[4] == "YES",
                    "key": "PRI" if row[6] == "PRIMARY KEY" else "",
                    "default": str(row[5]) if row[5] is not None else None,
                    "comment": "",
                })

        tables = [{"name": k, "columns": v} for k, v in tables_dict.items()]
        return {"db_type": "postgresql", "tables": tables}

    async def test_connection(self) -> dict:
        from .exceptions import format_connector_result
        try:
            await self.connect()
            if self._conn:
                cur = self._conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
            return format_connector_result(True, data={"message": "PostgreSQL 连接成功"}, db_type="postgresql")
        except Exception as e:
            return format_connector_result(False, error=str(e), db_type="postgresql", code="CONNECTION_FAILED")
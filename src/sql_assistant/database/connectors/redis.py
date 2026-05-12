"""Redis 连接器"""

import asyncio
from typing import Any

import redis.asyncio as aioredis

from .base import BaseConnector, QueryResult


class RedisConnector(BaseConnector):
    """Redis 数据库连接器"""

    db_type = "redis"

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        # Redis database 是数字索引
        super().__init__(host, port, user, password, database)
        self._conn: aioredis.Redis | None = None

    async def connect(self) -> None:
        db_num = int(self.database) if self.database and self.database.isdigit() else 0
        self._conn = aioredis.Redis(
            host=self.host,
            port=self.port,
            username=self.user or None,
            password=self.password or None,
            db=db_num,
            decode_responses=True,
            socket_connect_timeout=10,
        )

    async def disconnect(self) -> None:
        if self._conn:
            await self._conn.aclose()
            self._conn = None

    async def get_schema(self) -> dict:
        """Redis 无传统 schema，返回 key 列表作为参考"""
        if not self._conn:
            raise RuntimeError("Redis 未连接")

        try:
            keys = await self._conn.keys("*")
            # 只取前 50 个 key
            sample = keys[:50]
            types = {}
            for k in sample:
                try:
                    t = await self._conn.type(k)
                    types[k] = t
                except Exception:
                    types[k] = "unknown"

            return {
                "db_type": "redis",
                "keys": [
                    {"name": k, "type": types.get(k, "unknown")}
                    for k in sorted(sample)
                ],
                "key_count": len(keys),
            }
        except Exception as e:
            return {"db_type": "redis", "keys": [], "error": str(e)}

    async def execute(self, sql: str) -> QueryResult:
        """执行 Redis 命令"""
        if not self._conn:
            raise RuntimeError("Redis 未连接")

        result = QueryResult(sql_type="OTHER")

        # Redis 使用原生命令格式：命令 参数1 参数2 ...
        parts = sql.strip().split()
        if not parts:
            return result

        command = parts[0].upper()
        args = parts[1:] if len(parts) > 1 else []

        try:
            # 调用 Redis 命令
            cmd_func = getattr(self._conn, command.lower(), None)
            if cmd_func is None:
                raise ValueError(f"不支持的 Redis 命令: {command}")

            value = await cmd_func(*args)

            result.sql_type = "SELECT" if command in (
                "GET", "HGET", "HGETALL", "LRANGE", "SMEMBERS", "ZRANGE",
                "KEYS", "MGET", "TYPE", "TTL", "EXISTS", "STRLEN",
            ) else "OTHER"

            # 格式化结果
            if isinstance(value, list):
                result.columns = ["result"]
                result.rows = [[v] for v in value]
                result.row_count = len(value)
            elif isinstance(value, dict):
                result.columns = ["key", "value"]
                result.rows = [[k, v] for k, v in value.items()]
                result.row_count = len(value)
            elif isinstance(value, (int, float)):
                result.affected_rows = int(value)
            else:
                result.columns = ["result"]
                result.rows = [[str(value)]]
                result.row_count = 1

        except Exception as e:
            result.columns = ["error"]
            result.rows = [[str(e)]]
            result.row_count = 1

        return result

    async def test_connection(self) -> bool:
        try:
            await self.connect()
            if self._conn:
                await self._conn.ping()
            return True
        except Exception:
            return False
        finally:
            await self.disconnect()

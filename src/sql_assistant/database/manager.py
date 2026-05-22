"""数据库连接管理器 - 统一管理所有数据库连接（含连接池）"""

from typing import Optional

from ..config import get_config_manager
from ..settings import DatabaseConfig
from .connectors.base import BaseConnector, QueryResult
from .connectors.mysql import MySQLConnector
from .connectors.sqlserver import SQLServerConnector
from .connectors.postgresql import PostgreSQLConnector
from .connectors.redis import RedisConnector
from .connectors.mongodb import MongoDBConnector
from .pool import ConnectionPool

POOL_MIN_SIZE = 2
POOL_MAX_SIZE = 10
POOL_ACQUIRE_TIMEOUT = 30.0

_VALIDATION_QUERIES: dict[str, str] = {
    "mysql": "SELECT 1",
    "postgresql": "SELECT 1",
    "sqlserver": "SELECT 1",
}


class DatabaseManager:
    """数据库连接管理器（集成连接池）"""

    def __init__(self):
        self._connectors: dict[str, BaseConnector] = {}
        self._pools: dict[str, ConnectionPool] = {}
        self._schema_cache: dict[str, dict] = {}

    def _create_connector(self, config: DatabaseConfig, use_pool: bool = True) -> BaseConnector:
        """根据配置创建对应的连接器（含连接池）"""
        connector_classes = {
            "mysql": MySQLConnector,
            "sqlserver": SQLServerConnector,
            "postgresql": PostgreSQLConnector,
            "redis": RedisConnector,
            "mongodb": MongoDBConnector,
        }
        cls = connector_classes.get(config.db_type)
        if cls is None:
            raise ValueError(f"不支持的数据库类型: {config.db_type}")

        pool = None
        if use_pool and config.db_type in _VALIDATION_QUERIES:
            if cls == MySQLConnector:
                factory = MySQLConnector.create_connection_factory(
                    config.host, config.get_port(), config.user, config.password, config.database
                )
            elif cls == PostgreSQLConnector:
                factory = PostgreSQLConnector.create_connection_factory(
                    config.host, config.get_port(), config.user, config.password, config.database
                )
            elif cls == SQLServerConnector:
                factory = SQLServerConnector.create_connection_factory(
                    config.host, config.get_port(), config.user, config.password, config.database
                )
            else:
                factory = None

            if factory:
                pool = ConnectionPool(
                    factory=factory,
                    min_size=POOL_MIN_SIZE,
                    max_size=POOL_MAX_SIZE,
                    validation_query=_VALIDATION_QUERIES[config.db_type],
                    acquire_timeout=POOL_ACQUIRE_TIMEOUT,
                )

        kwargs = {
            "host": config.host,
            "port": config.get_port(),
            "user": config.user,
            "password": config.password,
            "database": config.database,
        }

        if pool:
            kwargs["pool"] = pool

        connector = cls(**kwargs)

        if pool:
            config_name = config.name
            self._pools[config_name] = pool

        return connector

    async def get_connector(self) -> BaseConnector:
        """获取当前激活的数据库连接器（自动创建连接池）"""
        config = get_config_manager().get_active_database()
        if not config:
            raise ValueError("未配置数据库，请先在设置中添加数据库连接")

        key = config.name
        if key not in self._connectors:
            connector = self._create_connector(config)
            if key not in self._pools:
                await connector.connect()
            self._connectors[key] = connector

        return self._connectors[key]

    async def execute(self, sql: str) -> QueryResult:
        """执行 SQL 并返回结果"""
        connector = await self.get_connector()
        return await connector.execute(sql)

    async def get_schema(self, force_refresh: bool = False) -> dict:
        """获取当前激活数据库的 schema（带缓存）"""
        config = get_config_manager().get_active_database()
        if not config:
            return {"db_type": "", "tables": [], "error": "未配置数据库连接"}

        cache_key = config.name
        if not force_refresh and cache_key in self._schema_cache:
            return self._schema_cache[cache_key]

        try:
            connector = await self.get_connector()
            schema = await connector.get_schema()
            self._schema_cache[cache_key] = schema
            return schema
        except Exception as e:
            return {"db_type": config.db_type, "tables": [], "error": str(e)}

    async def refresh_schema(self) -> dict:
        """强制刷新当前数据库 schema"""
        config = get_config_manager().get_active_database()
        if config:
            cache_key = config.name
            self._schema_cache.pop(cache_key, None)
            if cache_key in self._connectors:
                await self._connectors[cache_key].disconnect()
                del self._connectors[cache_key]
            if cache_key in self._pools:
                self._pools[cache_key].close()
                del self._pools[cache_key]
        return await self.get_schema(force_refresh=True)

    async def get_schema_text(self) -> str:
        """将 schema 转为给 LLM 的文本描述"""
        schema = await self.get_schema()

        db_type = schema.get("db_type", "")

        if db_type == "redis":
            keys = schema.get("keys", [])
            if not keys:
                return "(Redis: 当前数据库无 key)"
            lines = ["## 当前 Redis Key 列表（前50个）:"]
            for k in keys:
                lines.append(f"- {k['name']} ({k['type']})")
            key_count = schema.get("key_count", 0)
            if key_count > 50:
                lines.append(f"... 共 {key_count} 个 key")
            return "\n".join(lines)

        tables = schema.get("tables", [])
        if not tables:
            error = schema.get("error", "")
            if error:
                return f"(Schema 获取失败: {error})"
            return "(数据库为空，暂无表)"

        lines = ["## 当前数据库 Schema:", ""]
        for t in tables:
            cols = t.get("columns", [])
            if not cols:
                lines.append(f"- {t['name']} (无列信息)")
                continue
            col_strs = []
            for c in cols:
                extras = []
                if c.get("key") == "PRI":
                    extras.append("PRIMARY KEY")
                if not c.get("nullable", True):
                    extras.append("NOT NULL")
                suffix = f"  -- {', '.join(extras)}" if extras else ""
                col_strs.append(f"    {c['name']} {c['type']}{suffix}")
            lines.append(f"- {t['name']}:")
            lines.extend(col_strs)
            lines.append("")

        return "\n".join(lines)

    async def test_active_connection(self) -> dict:
        """测试当前激活的连接"""
        config = get_config_manager().get_active_database()
        if not config:
            return {"success": False, "error": "未配置数据库连接"}

        connector = self._create_connector(config, use_pool=False)
        try:
            result = await connector.test_connection()
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "code": "CONNECTION_FAILED"}
        finally:
            await connector.disconnect()

    async def test_connection(self, config: DatabaseConfig) -> dict:
        """测试指定配置的连接"""
        connector = self._create_connector(config, use_pool=False)
        try:
            result = await connector.test_connection()
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "code": "CONNECTION_FAILED"}
        finally:
            await connector.disconnect()

    async def close_all(self):
        """关闭所有连接和连接池"""
        for connector in self._connectors.values():
            await connector.disconnect()
        self._connectors.clear()

        for pool in self._pools.values():
            pool.close()
        self._pools.clear()


_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
"""数据库连接器抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryResult:
    """统一查询结果"""
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    affected_rows: int = 0
    sql_type: str = ""  # SELECT, INSERT, UPDATE, DELETE, OTHER


class BaseConnector(ABC):
    """数据库连接器抽象基类"""

    db_type: str = "unknown"

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    @abstractmethod
    async def connect(self) -> None:
        """建立数据库连接"""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """断开数据库连接"""
        ...

    @abstractmethod
    async def execute(self, sql: str) -> QueryResult:
        """执行 SQL 语句，返回统一结果"""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """测试连接是否可用"""
        ...

    @abstractmethod
    async def get_schema(self) -> dict:
        """获取数据库 schema（表名 + 列信息）。
        
        返回格式:
        {
            "db_type": "mysql",
            "tables": [
                {"name": "users", "columns": [
                    {"name": "id", "type": "INT", "nullable": False, "key": "PRI"},
                    {"name": "name", "type": "VARCHAR(100)", "nullable": True, "key": ""},
                ]},
            ]
        }
        """
        ...

    @staticmethod
    def classify_sql(sql: str) -> str:
        """判断 SQL 语句类型"""
        s = sql.strip().upper()
        if s.startswith("SELECT") or s.startswith("SHOW") or s.startswith("DESCRIBE") or s.startswith("EXPLAIN"):
            return "SELECT"
        elif s.startswith("INSERT"):
            return "INSERT"
        elif s.startswith("UPDATE"):
            return "UPDATE"
        elif s.startswith("DELETE"):
            return "DELETE"
        elif s.startswith("CREATE") or s.startswith("ALTER") or s.startswith("DROP"):
            return "DDL"
        return "OTHER"

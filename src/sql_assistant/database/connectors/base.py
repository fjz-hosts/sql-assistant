"""数据库连接器抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .exceptions import format_connector_result


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
        """判断 SQL 语句类型（忽略前导注释和空行）
        
        支持多语句 SQL，检查所有子语句的类型。如果任何子语句是增删改或 DDL，
        则返回该类型，确保危险操作能触发确认对话框。
        """
        s = BaseConnector._strip_sql_comments(sql).strip()
        
        # 按分号分割 SQL 语句（处理字符串内的分号）
        statements = BaseConnector._split_sql_statements(s)
        
        for stmt in statements:
            stmt_upper = stmt.strip().upper()
            if not stmt_upper:
                continue
            
            # 按优先级判断：DDL > DELETE > UPDATE > INSERT > SELECT
            if stmt_upper.startswith("CREATE") or stmt_upper.startswith("ALTER") or stmt_upper.startswith("DROP"):
                return "DDL"
            elif stmt_upper.startswith("DELETE"):
                return "DELETE"
            elif stmt_upper.startswith("UPDATE"):
                return "UPDATE"
            elif stmt_upper.startswith("INSERT"):
                return "INSERT"
        
        # 如果没有找到增删改或 DDL，检查是否是查询语句
        for stmt in statements:
            stmt_upper = stmt.strip().upper()
            if stmt_upper.startswith("SELECT") or stmt_upper.startswith("SHOW") or stmt_upper.startswith("DESCRIBE") or stmt_upper.startswith("EXPLAIN"):
                return "SELECT"
        
        return "OTHER"
    
    @staticmethod
    def _split_sql_statements(sql: str) -> list:
        """安全地按分号分割 SQL 语句，处理字符串内的分号"""
        statements = []
        current_stmt = []
        in_single_quote = False
        in_double_quote = False
        in_comment = False
        
        for i, char in enumerate(sql):
            # 处理行注释
            if i > 0 and sql[i-1] == '-' and char == '-':
                # 跳过到行尾
                while i < len(sql) and sql[i] != '\n':
                    i += 1
                continue
            
            # 处理单引号字符串
            if char == "'" and not in_double_quote and not in_comment:
                in_single_quote = not in_single_quote
            
            # 处理双引号字符串
            if char == '"' and not in_single_quote and not in_comment:
                in_double_quote = not in_double_quote
            
            # 处理分号（仅在字符串外）
            if char == ';' and not in_single_quote and not in_double_quote:
                statements.append(''.join(current_stmt))
                current_stmt = []
                continue
            
            current_stmt.append(char)
        
        # 添加最后一个语句（如果有）
        if current_stmt:
            statements.append(''.join(current_stmt))
        
        return statements

    @staticmethod
    def _strip_sql_comments(sql: str) -> str:
        """去除 SQL 前导注释行和空行，保留实际语句部分。
        
        处理两种注释风格：
        - 行注释：-- ... 或 # ...
        - 块注释：/* ... */
        """
        lines = sql.split("\n")
        result_lines = []
        in_block_comment = False

        for line in lines:
            stripped = line.strip()

            # 处理块注释（可能跨行）
            if in_block_comment:
                end_idx = stripped.find("*/")
                if end_idx != -1:
                    in_block_comment = False
                    remaining = stripped[end_idx + 2:].strip()
                    if remaining:
                        result_lines.append(remaining)
                continue

            # 检查行首是否是块注释开始
            if stripped.startswith("/*"):
                end_idx = stripped.find("*/", 2)
                if end_idx != -1:
                    remaining = stripped[end_idx + 2:].strip()
                    if remaining:
                        result_lines.append(remaining)
                else:
                    in_block_comment = True
                continue

            # 跳过行注释和空行
            if not stripped or stripped.startswith("--") or stripped.startswith("#"):
                continue

            result_lines.append(line)

        return "\n".join(result_lines)

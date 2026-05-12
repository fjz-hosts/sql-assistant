"""数据库连接器统一异常"""

from typing import Optional


class ConnectorError(Exception):
    """数据库连接器基础异常"""
    def __init__(self, message: str, db_type: str = "", code: Optional[str] = None):
        super().__init__(message)
        self.db_type = db_type
        self.code = code

    def to_dict(self) -> dict:
        return {
            "success": False,
            "error": str(self),
            "db_type": self.db_type,
            "code": self.code,
        }


class ConnectionError(ConnectorError):
    """连接失败异常"""
    def __init__(self, message: str, db_type: str = ""):
        super().__init__(message, db_type, code="CONNECTION_FAILED")


class QueryError(ConnectorError):
    """查询执行异常"""
    def __init__(self, message: str, db_type: str = "", sql: str = ""):
        super().__init__(message, db_type, code="QUERY_FAILED")
        self.sql = sql

    def to_dict(self) -> dict:
        result = super().to_dict()
        result["sql"] = self.sql
        return result


class SchemaError(ConnectorError):
    """Schema 获取异常"""
    def __init__(self, message: str, db_type: str = ""):
        super().__init__(message, db_type, code="SCHEMA_ERROR")


class AuthenticationError(ConnectorError):
    """认证失败异常"""
    def __init__(self, message: str, db_type: str = ""):
        super().__init__(message, db_type, code="AUTH_FAILED")


class TimeoutError(ConnectorError):
    """连接超时异常"""
    def __init__(self, message: str, db_type: str = ""):
        super().__init__(message, db_type, code="TIMEOUT")


def format_connector_result(
    success: bool,
    data: any = None,
    error: Optional[str] = None,
    db_type: str = "",
    code: Optional[str] = None,
) -> dict:
    """统一格式化连接器返回结果

    Args:
        success: 是否成功
        data: 成功时返回的数据
        error: 失败时的错误信息
        db_type: 数据库类型
        code: 错误码

    Returns:
        统一格式的字典
    """
    result = {"success": success}

    if success:
        result["data"] = data
    else:
        result["error"] = error or "未知错误"
        if code:
            result["code"] = code
        if db_type:
            result["db_type"] = db_type

    return result

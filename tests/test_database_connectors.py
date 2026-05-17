"""数据库连接器测试"""
import pytest
from sql_assistant.database.connectors.base import BaseConnector, QueryResult
from sql_assistant.database.connectors.mysql import MySQLConnector
from sql_assistant.database.connectors.postgresql import PostgreSQLConnector
from sql_assistant.database.connectors.sqlserver import SQLServerConnector
from sql_assistant.database.connectors.redis import RedisConnector
from sql_assistant.database.connectors.mongodb import MongoDBConnector

class TestBaseConnector:
    """基础连接器测试"""
    
    def test_base_connector_exists(self):
        """测试基础连接器类存在"""
        assert BaseConnector is not None
    
    def test_base_connector_has_methods(self):
        """测试基础连接器有必要的方法"""
        assert hasattr(BaseConnector, 'connect')
        assert hasattr(BaseConnector, 'disconnect')
        assert hasattr(BaseConnector, 'execute')
        assert hasattr(BaseConnector, 'test_connection')
        assert hasattr(BaseConnector, 'get_schema')
        assert hasattr(BaseConnector, 'classify_sql')
    
    def test_query_result_dataclass(self):
        """测试QueryResult数据类"""
        result = QueryResult(columns=["id", "name"], rows=[[1, "test"]])
        assert result.columns == ["id", "name"]
        assert result.rows == [[1, "test"]]
    
    def test_classify_sql_select(self):
        """测试SQL分类-SELECT"""
        result = BaseConnector.classify_sql("SELECT * FROM users")
        assert result == "SELECT"
    
    def test_classify_sql_delete(self):
        """测试SQL分类-DELETE"""
        result = BaseConnector.classify_sql("DELETE FROM users WHERE id = 1")
        assert result == "DELETE"
    
    def test_classify_sql_update(self):
        """测试SQL分类-UPDATE"""
        result = BaseConnector.classify_sql("UPDATE users SET name = 'test'")
        assert result == "UPDATE"
    
    def test_classify_sql_insert(self):
        """测试SQL分类-INSERT"""
        result = BaseConnector.classify_sql("INSERT INTO users (name) VALUES ('test')")
        assert result == "INSERT"

    def test_classify_sql_create_table(self):
        """测试SQL分类-CREATE_TABLE"""
        result = BaseConnector.classify_sql("CREATE TABLE users (id INT, name VARCHAR(100))")
        assert result == "CREATE_TABLE"

    def test_classify_sql_drop_table(self):
        """测试SQL分类-DROP_TABLE"""
        result = BaseConnector.classify_sql("DROP TABLE users")
        assert result == "DROP_TABLE"

    def test_classify_sql_alter_table(self):
        """测试SQL分类-ALTER_TABLE"""
        result = BaseConnector.classify_sql("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
        assert result == "ALTER_TABLE"

    def test_classify_sql_truncate_table(self):
        """测试SQL分类-TRUNCATE_TABLE"""
        result = BaseConnector.classify_sql("TRUNCATE TABLE users")
        assert result == "TRUNCATE_TABLE"

class TestMySQLConnector:
    """MySQL连接器测试"""
    
    def test_mysql_connector_exists(self):
        """测试MySQL连接器存在"""
        assert MySQLConnector is not None
    
    def test_mysql_connector_inherits_base(self):
        """测试MySQL连接器继承自BaseConnector"""
        assert issubclass(MySQLConnector, BaseConnector)

class TestPostgreSQLConnector:
    """PostgreSQL连接器测试"""
    
    def test_postgresql_connector_exists(self):
        """测试PostgreSQL连接器存在"""
        assert PostgreSQLConnector is not None
    
    def test_postgresql_connector_inherits_base(self):
        """测试PostgreSQL连接器继承自BaseConnector"""
        assert issubclass(PostgreSQLConnector, BaseConnector)

class TestSQLServerConnector:
    """SQL Server连接器测试"""
    
    def test_sqlserver_connector_exists(self):
        """测试SQL Server连接器存在"""
        assert SQLServerConnector is not None
    
    def test_sqlserver_connector_inherits_base(self):
        """测试SQL Server连接器继承自BaseConnector"""
        assert issubclass(SQLServerConnector, BaseConnector)

class TestRedisConnector:
    """Redis连接器测试"""
    
    def test_redis_connector_exists(self):
        """测试Redis连接器存在"""
        assert RedisConnector is not None
    
    def test_redis_connector_inherits_base(self):
        """测试Redis连接器继承自BaseConnector"""
        assert issubclass(RedisConnector, BaseConnector)

class TestMongoDBConnector:
    """MongoDB连接器测试"""
    
    def test_mongodb_connector_exists(self):
        """测试MongoDB连接器存在"""
        assert MongoDBConnector is not None
    
    def test_mongodb_connector_inherits_base(self):
        """测试MongoDB连接器继承自BaseConnector"""
        assert issubclass(MongoDBConnector, BaseConnector)

class TestConnectorExceptions:
    """连接器异常测试"""
    
    def test_exceptions_exist(self):
        """测试异常类存在"""
        from sql_assistant.database.connectors.exceptions import (
            ConnectorError, ConnectionError, QueryError, 
            SchemaError, AuthenticationError, TimeoutError
        )
        assert ConnectorError is not None
        assert ConnectionError is not None
        assert QueryError is not None
        assert SchemaError is not None
        assert AuthenticationError is not None
        assert TimeoutError is not None
    
    def test_connector_error_to_dict(self):
        """测试ConnectorError的to_dict方法"""
        from sql_assistant.database.connectors.exceptions import ConnectorError
        error = ConnectorError("test error", "mysql", "TEST_ERROR")
        result = error.to_dict()
        assert result["success"] == False
        assert result["error"] == "test error"
        assert result["db_type"] == "mysql"
        assert result["code"] == "TEST_ERROR"

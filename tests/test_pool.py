"""数据库连接池测试"""
import pytest
import threading
import time
from sql_assistant.database.pool import ConnectionPool


class FakeConnection:
    """模拟数据库连接，用于测试连接池逻辑"""

    def __init__(self, conn_id: int = 0, healthy: bool = True):
        self.conn_id = conn_id
        self.healthy = healthy
        self.closed = False
        self._counter = 0

    def cursor(self):
        self._counter += 1
        return FakeCursor(self)

    def close(self):
        self.closed = True


class FakeCursor:
    def __init__(self, conn: FakeConnection):
        self._conn = conn

    def execute(self, sql: str):
        if not self._conn.healthy:
            raise Exception("连接已失效")

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestConnectionPool:
    """连接池基本测试"""

    def test_pool_creation(self):
        """测试连接池创建"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(factory=factory, min_size=2, max_size=5)
        assert pool.size == 2
        assert pool.total_created == 2
        assert pool.max_size == 5
        assert not pool.is_closed
        pool.close()

    def test_pool_acquire_release(self):
        """测试获取和归还连接"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(factory=factory, min_size=1, max_size=3)
        assert pool.size == 1

        conn = pool.acquire()
        assert conn.conn_id == 1
        assert pool.size == 0

        pool.release(conn)
        assert pool.size == 1

        pool.close()

    def test_pool_multiple_acquire(self):
        """测试并发获取连接"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(factory=factory, min_size=2, max_size=5)

        conn1 = pool.acquire()
        conn2 = pool.acquire()
        assert pool.size == 0
        assert pool.total_created >= 2

        pool.release(conn1)
        pool.release(conn2)
        assert pool.size == 2

        pool.close()

    def test_pool_grows_beyond_min(self):
        """测试池在需要时增长超过 min_size"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(factory=factory, min_size=1, max_size=3)

        c1 = pool.acquire()
        c2 = pool.acquire()
        c3 = pool.acquire()

        assert pool.total_created == 3

        pool.release(c1)
        pool.release(c2)
        pool.release(c3)

        pool.close()

    def test_pool_max_limit(self):
        """测试池达到 max_size 上限"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(factory=factory, min_size=2, max_size=2, acquire_timeout=0.5)

        c1 = pool.acquire()
        c2 = pool.acquire()

        with pytest.raises(RuntimeError, match="连接池已满"):
            pool.acquire()

        pool.release(c1)
        pool.release(c2)
        pool.close()

    def test_pool_close(self):
        """测试关闭连接池"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(factory=factory, min_size=2, max_size=5)
        conn1 = pool.acquire()
        conn2 = pool.acquire()

        pool.release(conn1)
        pool.release(conn2)

        pool.close()
        assert pool.is_closed

        with pytest.raises(RuntimeError, match="连接池已关闭"):
            pool.acquire()

    def test_pool_close_cleans_up(self):
        """测试关闭池时清理所有连接"""
        closed_connections = []

        def factory():
            conn = FakeConnection(len(closed_connections) + 1)
            closed_connections.append(conn)
            return conn

        pool = ConnectionPool(factory=factory, min_size=3, max_size=5)
        pool.close()

        assert all(conn.closed for conn in closed_connections)

    def test_pool_validation_query(self):
        """测试连接健康检查"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(
            factory=factory, min_size=1, max_size=3, validation_query="SELECT 1"
        )

        conn = pool.acquire()
        assert conn.conn_id == 1

        pool.release(conn)
        pool.close()

    def test_pool_replaces_bad_connection(self):
        """测试自动替换失效连接"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(
            factory=factory, min_size=1, max_size=3, validation_query="SELECT 1"
        )

        conn1 = pool.acquire()
        conn1_id = conn1.conn_id
        conn1.healthy = False
        pool.release(conn1)

        assert conn1.closed

        conn2 = pool.acquire()
        assert conn2.conn_id != conn1_id
        assert conn2.healthy

        pool.release(conn2)
        pool.close()

    def test_pool_validation_on_acquire(self):
        """测试获取时验证连接健康"""
        _counter = [0]

        def factory():
            _counter[0] += 1
            return FakeConnection(_counter[0], healthy=True)

        pool = ConnectionPool(
            factory=factory, min_size=1, max_size=3, validation_query="SELECT 1"
        )

        conn1 = pool.acquire()
        conn1.healthy = False
        pool.release(conn1)

        conn2 = pool.acquire()
        assert conn2.healthy
        assert conn2.conn_id != conn1.conn_id

        pool.release(conn2)
        pool.close()

    def test_pool_invalid_min_max(self):
        """测试无效的 min/max 参数"""
        def factory():
            return FakeConnection()

        with pytest.raises(ValueError, match="min_size 不能大于 max_size"):
            ConnectionPool(factory=factory, min_size=5, max_size=2)

        with pytest.raises(ValueError, match="max_size 必须 >= 1"):
            ConnectionPool(factory=factory, min_size=0, max_size=0)

    def test_pool_concurrent_access(self):
        """测试多线程并发访问"""
        _counter = [0]
        lock = threading.Lock()

        def factory():
            with lock:
                _counter[0] += 1
            return FakeConnection(_counter[0])

        pool = ConnectionPool(factory=factory, min_size=2, max_size=10)
        results = []
        errors = []

        def worker():
            try:
                conn = pool.acquire()
                time.sleep(0.02)
                results.append(conn.conn_id)
                pool.release(conn)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20
        assert len(errors) == 0
        assert pool.total_created <= 10

        pool.close()


class TestMySQLConnectorWithPool:
    """MySQL 连接器带连接池测试"""

    def test_create_connection_factory(self):
        """测试创建连接工厂"""
        from sql_assistant.database.connectors.mysql import MySQLConnector

        factory = MySQLConnector.create_connection_factory(
            host="localhost", port=3306, user="root", password="", database="test"
        )
        assert callable(factory)

    def test_connector_without_pool(self):
        """测试不带连接池的 MySQL 连接器"""
        from sql_assistant.database.connectors.mysql import MySQLConnector

        connector = MySQLConnector(
            host="localhost", port=3306, user="root", password="", database="test"
        )
        assert connector._pool is None
        assert connector._conn is None

    def test_connector_with_pool(self):
        """测试带连接池的 MySQL 连接器"""
        from sql_assistant.database.connectors.mysql import MySQLConnector
        from sql_assistant.database.pool import ConnectionPool

        def mock_factory():
            return FakeConnection()

        pool = ConnectionPool(factory=mock_factory, min_size=1, max_size=2)

        connector = MySQLConnector(
            host="localhost", port=3306, user="root", password="", database="test",
            pool=pool
        )
        assert connector._pool is not None

        pool.close()


class TestPostgreSQLConnectorWithPool:
    """PostgreSQL 连接器带连接池测试"""

    def test_create_connection_factory(self):
        """测试创建连接工厂"""
        from sql_assistant.database.connectors.postgresql import PostgreSQLConnector

        factory = PostgreSQLConnector.create_connection_factory(
            host="localhost", port=5432, user="postgres", password="", database="test"
        )
        assert callable(factory)

    def test_connector_without_pool(self):
        """测试不带连接池的 PostgreSQL 连接器"""
        from sql_assistant.database.connectors.postgresql import PostgreSQLConnector

        connector = PostgreSQLConnector(
            host="localhost", port=5432, user="postgres", password="", database="test"
        )
        assert connector._pool is None

    def test_connector_with_pool(self):
        """测试带连接池的 PostgreSQL 连接器"""
        from sql_assistant.database.connectors.postgresql import PostgreSQLConnector
        from sql_assistant.database.pool import ConnectionPool

        def mock_factory():
            return FakeConnection()

        pool = ConnectionPool(factory=mock_factory, min_size=1, max_size=2)

        connector = PostgreSQLConnector(
            host="localhost", port=5432, user="postgres", password="", database="test",
            pool=pool
        )
        assert connector._pool is not None

        pool.close()


class TestSQLServerConnectorWithPool:
    """SQL Server 连接器带连接池测试"""

    def test_create_connection_factory(self):
        """测试创建连接工厂"""
        from sql_assistant.database.connectors.sqlserver import SQLServerConnector

        factory = SQLServerConnector.create_connection_factory(
            host="localhost", port=1433, user="sa", password="", database="test"
        )
        assert callable(factory)

    def test_connector_without_pool(self):
        """测试不带连接池的 SQL Server 连接器"""
        from sql_assistant.database.connectors.sqlserver import SQLServerConnector

        connector = SQLServerConnector(
            host="localhost", port=1433, user="sa", password="", database="test"
        )
        assert connector._pool is None

    def test_connector_with_pool(self):
        """测试带连接池的 SQL Server 连接器"""
        from sql_assistant.database.connectors.sqlserver import SQLServerConnector
        from sql_assistant.database.pool import ConnectionPool

        def mock_factory():
            return FakeConnection()

        pool = ConnectionPool(factory=mock_factory, min_size=1, max_size=2)

        connector = SQLServerConnector(
            host="localhost", port=1433, user="sa", password="", database="test",
            pool=pool
        )
        assert connector._pool is not None

        pool.close()


class TestDatabaseManagerPool:
    """数据库管理器连接池集成测试"""

    def test_manager_has_pool_methods(self):
        """测试管理器有连接池相关属性"""
        from sql_assistant.database.manager import DatabaseManager

        manager = DatabaseManager()
        assert hasattr(manager, '_pools')
        assert isinstance(manager._pools, dict)

    def test_manager_close_all_clears_pools(self):
        """测试 close_all 清理连接池"""
        from sql_assistant.database.manager import DatabaseManager

        manager = DatabaseManager()
        import asyncio
        asyncio.run(manager.close_all())
        assert len(manager._pools) == 0
        assert len(manager._connectors) == 0

    def test_pool_constants(self):
        """测试连接池常量"""
        from sql_assistant.database.manager import (
            POOL_MIN_SIZE, POOL_MAX_SIZE, POOL_ACQUIRE_TIMEOUT
        )
        assert POOL_MIN_SIZE == 2
        assert POOL_MAX_SIZE == 10
        assert POOL_ACQUIRE_TIMEOUT == 30.0

    def test_validation_queries(self):
        """测试验证查询配置"""
        from sql_assistant.database.manager import _VALIDATION_QUERIES
        assert _VALIDATION_QUERIES["mysql"] == "SELECT 1"
        assert _VALIDATION_QUERIES["postgresql"] == "SELECT 1"
        assert _VALIDATION_QUERIES["sqlserver"] == "SELECT 1"
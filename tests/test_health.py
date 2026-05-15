"""数据库健康检查模块测试"""
import pytest
import asyncio
from sql_assistant.database.health import (
    DatabaseHealthChecker,
    HealthMetrics,
    TableHealth,
    IndexHealth,
)


class TestHealthMetrics:
    """健康指标数据类测试"""

    def test_health_metrics_init(self):
        """测试健康指标初始化"""
        metrics = HealthMetrics()
        assert metrics.db_type == ""
        assert metrics.status == "unknown"
        assert metrics.response_time_ms == 0.0
        assert metrics.connection_ok is False

    def test_health_metrics_with_values(self):
        """测试带值的健康指标"""
        metrics = HealthMetrics(
            db_type="mysql",
            status="healthy",
            response_time_ms=15.5,
            connection_ok=True,
            table_count=10,
            total_size_mb=100.5,
        )
        assert metrics.db_type == "mysql"
        assert metrics.status == "healthy"
        assert metrics.response_time_ms == 15.5
        assert metrics.connection_ok is True
        assert metrics.table_count == 10
        assert metrics.total_size_mb == 100.5


class TestTableHealth:
    """表健康信息测试"""

    def test_table_health_init(self):
        """测试表健康信息初始化"""
        table = TableHealth(name="users")
        assert table.name == "users"
        assert table.engine == ""
        assert table.row_count == 0
        assert table.size_mb == 0.0

    def test_table_health_with_values(self):
        """测试带值的表健康信息"""
        table = TableHealth(
            name="orders",
            engine="InnoDB",
            row_count=50000,
            size_mb=250.5,
            index_length_mb=50.2,
            data_length_mb=200.3,
            auto_increment=10001,
            avg_row_length=256,
        )
        assert table.name == "orders"
        assert table.engine == "InnoDB"
        assert table.row_count == 50000
        assert table.size_mb == 250.5
        assert table.index_length_mb == 50.2
        assert table.data_length_mb == 200.3
        assert table.auto_increment == 10001
        assert table.avg_row_length == 256


class TestIndexHealth:
    """索引健康信息测试"""

    def test_index_health_init(self):
        """测试索引健康信息初始化"""
        index = IndexHealth(
            table_name="users",
            index_name="idx_user_id",
            column_name="id",
        )
        assert index.table_name == "users"
        assert index.index_name == "idx_user_id"
        assert index.column_name == "id"
        assert index.unique is False
        assert index.cardinality == 0
        assert index.seq_in_index == 1

    def test_index_health_unique(self):
        """测试唯一索引"""
        index = IndexHealth(
            table_name="users",
            index_name="uk_user_email",
            column_name="email",
            unique=True,
            cardinality=10000,
            seq_in_index=1,
        )
        assert index.unique is True
        assert index.cardinality == 10000


class TestDatabaseHealthChecker:
    """数据库健康检查器测试"""

    def test_health_checker_init(self):
        """测试健康检查器初始化"""
        class MockConnector:
            db_type = "mysql"

        checker = DatabaseHealthChecker(MockConnector())
        assert checker is not None
        assert checker.connector.db_type == "mysql"

    def test_health_checker_has_get_table_stats(self):
        """测试健康检查器有获取表统计方法"""
        class MockConnector:
            db_type = "mysql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "get_table_stats")
        assert asyncio.iscoroutinefunction(checker.get_table_stats)

    def test_health_checker_has_get_index_stats(self):
        """测试健康检查器有获取索引统计方法"""
        class MockConnector:
            db_type = "mysql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "get_index_stats")
        assert asyncio.iscoroutinefunction(checker.get_index_stats)

    def test_health_checker_has_get_performance_metrics(self):
        """测试健康检查器有获取性能指标方法"""
        class MockConnector:
            db_type = "mysql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "get_performance_metrics")
        assert asyncio.iscoroutinefunction(checker.get_performance_metrics)

    def test_health_checker_has_check_connection(self):
        """测试健康检查器有检查连接方法"""
        class MockConnector:
            db_type = "mysql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "check_connection")
        assert asyncio.iscoroutinefunction(checker.check_connection)


class TestHealthCheckerMySQLMethods:
    """MySQL健康检查方法测试"""

    def test_health_checker_has_mysql_table_stats(self):
        """测试健康检查器有MySQL表统计方法"""
        class MockConnector:
            db_type = "mysql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_mysql_table_stats")
        assert asyncio.iscoroutinefunction(checker._get_mysql_table_stats)

    def test_health_checker_has_mysql_index_stats(self):
        """测试健康检查器有MySQL索引统计方法"""
        class MockConnector:
            db_type = "mysql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_mysql_index_stats")
        assert asyncio.iscoroutinefunction(checker._get_mysql_index_stats)

    def test_health_checker_has_mysql_performance(self):
        """测试健康检查器有MySQL性能方法"""
        class MockConnector:
            db_type = "mysql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_mysql_performance")
        assert asyncio.iscoroutinefunction(checker._get_mysql_performance)


class TestHealthCheckerPostgreSQLMethods:
    """PostgreSQL健康检查方法测试"""

    def test_health_checker_has_postgresql_table_stats(self):
        """测试健康检查器有PostgreSQL表统计方法"""
        class MockConnector:
            db_type = "postgresql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_postgresql_table_stats")
        assert asyncio.iscoroutinefunction(checker._get_postgresql_table_stats)

    def test_health_checker_has_postgresql_index_stats(self):
        """测试健康检查器有PostgreSQL索引统计方法"""
        class MockConnector:
            db_type = "postgresql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_postgresql_index_stats")
        assert asyncio.iscoroutinefunction(checker._get_postgresql_index_stats)

    def test_health_checker_has_postgresql_performance(self):
        """测试健康检查器有PostgreSQL性能方法"""
        class MockConnector:
            db_type = "postgresql"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_postgresql_performance")
        assert asyncio.iscoroutinefunction(checker._get_postgresql_performance)


class TestHealthCheckerSQLServerMethods:
    """SQL Server健康检查方法测试"""

    def test_health_checker_has_sqlserver_table_stats(self):
        """测试健康检查器有SQLServer表统计方法"""
        class MockConnector:
            db_type = "sqlserver"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_sqlserver_table_stats")
        assert asyncio.iscoroutinefunction(checker._get_sqlserver_table_stats)

    def test_health_checker_has_sqlserver_index_stats(self):
        """测试健康检查器有SQLServer索引统计方法"""
        class MockConnector:
            db_type = "sqlserver"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_sqlserver_index_stats")
        assert asyncio.iscoroutinefunction(checker._get_sqlserver_index_stats)

    def test_health_checker_has_sqlserver_performance(self):
        """测试健康检查器有SQLServer性能方法"""
        class MockConnector:
            db_type = "sqlserver"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_sqlserver_performance")
        assert asyncio.iscoroutinefunction(checker._get_sqlserver_performance)


class TestHealthCheckerRedisMethods:
    """Redis健康检查方法测试"""

    def test_health_checker_has_redis_info(self):
        """测试健康检查器有Redis信息方法"""
        class MockConnector:
            db_type = "redis"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_redis_info")
        assert asyncio.iscoroutinefunction(checker._get_redis_info)

    def test_health_checker_has_redis_performance(self):
        """测试健康检查器有Redis性能方法"""
        class MockConnector:
            db_type = "redis"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_redis_performance")
        assert asyncio.iscoroutinefunction(checker._get_redis_performance)


class TestHealthCheckerMongoDBMethods:
    """MongoDB健康检查方法测试"""

    def test_health_checker_has_mongodb_stats(self):
        """测试健康检查器有MongoDB统计方法"""
        class MockConnector:
            db_type = "mongodb"

        checker = DatabaseHealthChecker(MockConnector())
        assert hasattr(checker, "_get_mongodb_stats")
        assert asyncio.iscoroutinefunction(checker._get_mongodb_stats)

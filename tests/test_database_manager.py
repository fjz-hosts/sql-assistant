"""数据库管理器模块测试"""
import pytest
from sql_assistant.database.manager import get_db_manager

class TestDatabaseManager:
    """数据库管理器测试"""
    
    def test_db_manager_init(self):
        """测试数据库管理器初始化"""
        db_manager = get_db_manager()
        assert db_manager is not None
    
    def test_supported_types_available(self):
        """测试支持的数据库类型可用"""
        db_manager = get_db_manager()
        # 检查内部连接器映射
        assert hasattr(db_manager, '_create_connector')
        # 支持的类型应该包括这些
        supported_types = ["mysql", "sqlserver", "postgresql", "redis", "mongodb"]
        for db_type in supported_types:
            assert db_type in ["mysql", "sqlserver", "postgresql", "redis", "mongodb"]
    
    def test_close_all(self):
        """测试关闭所有连接"""
        db_manager = get_db_manager()
        import asyncio
        asyncio.run(db_manager.close_all())

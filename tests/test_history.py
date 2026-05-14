"""历史记录模块测试"""
import pytest
import asyncio
from sql_assistant.database.history import get_history_manager

class TestHistoryManager:
    """历史记录管理器测试"""
    
    def test_history_manager_init(self):
        """测试历史记录管理器初始化"""
        history_manager = get_history_manager()
        assert history_manager is not None
    
    def test_add_record(self):
        """测试添加历史记录"""
        history_manager = get_history_manager()
        record_id = asyncio.run(history_manager.add_record(
            question="test question",
            sql="SELECT * FROM test",
            result={"test": "data"},
            db_type="mysql",
            llm_provider="deepseek",
            success=True
        ))
        assert record_id is not None
        assert isinstance(record_id, int)
    
    def test_get_records(self):
        """测试获取历史记录列表"""
        history_manager = get_history_manager()
        records = asyncio.run(history_manager.get_records(limit=10))
        assert isinstance(records, list)
    
    def test_get_record(self):
        """测试根据ID获取历史记录"""
        history_manager = get_history_manager()
        record_id = asyncio.run(history_manager.add_record(
            question="test",
            sql="SELECT 1",
            result={},
            db_type="mysql",
            llm_provider="test",
            success=True
        ))
        record = asyncio.run(history_manager.get_record(record_id))
        assert record is not None
        assert record["id"] == record_id
    
    def test_delete_record(self):
        """测试删除历史记录"""
        history_manager = get_history_manager()
        record_id = asyncio.run(history_manager.add_record(
            question="to delete",
            sql="DELETE FROM test",
            result={},
            db_type="mysql",
            llm_provider="test",
            success=True
        ))
        success = asyncio.run(history_manager.delete_record(record_id))
        assert success is True
        record = asyncio.run(history_manager.get_record(record_id))
        assert record is None
    
    def test_create_conversation(self):
        """测试创建对话"""
        history_manager = get_history_manager()
        conv_id = asyncio.run(history_manager.create_conversation("Test Conversation"))
        assert isinstance(conv_id, int)
    
    def test_get_conversations(self):
        """测试获取对话列表"""
        history_manager = get_history_manager()
        convs = asyncio.run(history_manager.get_conversations())
        assert isinstance(convs, list)
    
    def test_close_manager(self):
        """测试关闭历史记录管理器"""
        from sql_assistant.database.history import close_history_manager
        asyncio.run(close_history_manager())

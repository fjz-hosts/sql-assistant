"""对话上下文功能测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sql_assistant.api.query import _build_messages_with_context, MAX_CONTEXT_MESSAGES
from sql_assistant.database.history import HistoryManager


class TestConversationContext:
    """对话上下文测试"""

    @pytest.mark.asyncio
    async def test_build_messages_no_context(self):
        """测试构建没有上下文的消息"""
        messages = await _build_messages_with_context(
            db_type="mysql",
            schema_text="TABLE: users (id, name)",
            question="查询用户",
            conversation_id=None,
        )
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "查询用户" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_build_messages_with_context(self):
        """测试构建带有上下文的消息"""
        mock_history = MagicMock()
        mock_history.get_conversation_messages = AsyncMock(return_value=[
            {
                "question": "查询所有用户",
                "sql": "SELECT * FROM users",
                "result_json": '{"columns": ["id", "name"], "rows": [[1, "Alice"], [2, "Bob"]], "row_count": 2}',
            }
        ])
        
        with patch("sql_assistant.api.query.get_history", return_value=mock_history):
            messages = await _build_messages_with_context(
                db_type="mysql",
                schema_text="TABLE: users (id, name)",
                question="统计数量",
                conversation_id=1,
            )
        
        assert len(messages) == 4  # system + 历史用户 + 历史助手 + 当前用户
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"
        assert "统计数量" in messages[3]["content"]

    @pytest.mark.asyncio
    async def test_context_includes_result_summary(self):
        """测试上下文包含结果摘要"""
        mock_history = MagicMock()
        mock_history.get_conversation_messages = AsyncMock(return_value=[
            {
                "question": "查询用户",
                "sql": "SELECT * FROM users LIMIT 2",
                "result_json": '{"columns": ["id", "name"], "rows": [[1, "Alice"], [2, "Bob"]], "row_count": 2}',
            }
        ])
        
        with patch("sql_assistant.api.query.get_history", return_value=mock_history):
            messages = await _build_messages_with_context(
                db_type="mysql",
                schema_text="TABLE: users (id, name)",
                question="继续查询",
                conversation_id=1,
            )
        
        assistant_msg = messages[2]["content"]
        assert "执行结果" in assistant_msg
        assert "2 行数据" in assistant_msg
        assert "列: id, name" in assistant_msg

    @pytest.mark.asyncio
    async def test_context_truncation(self):
        """测试上下文消息数量限制"""
        mock_history = MagicMock()
        # 创建超过 MAX_CONTEXT_MESSAGES 的历史消息
        history_messages = []
        for i in range(MAX_CONTEXT_MESSAGES + 5):
            history_messages.append({
                "question": f"问题{i}",
                "sql": f"SELECT * FROM t{i}",
                "result_json": '{"columns": ["id"], "rows": [[1]], "row_count": 1}',
            })
        mock_history.get_conversation_messages = AsyncMock(return_value=history_messages)
        
        with patch("sql_assistant.api.query.get_history", return_value=mock_history):
            messages = await _build_messages_with_context(
                db_type="mysql",
                schema_text="TABLE: users (id, name)",
                question="当前问题",
                conversation_id=1,
            )
        
        # 系统消息 + (MAX_CONTEXT_MESSAGES * 2) 历史消息 + 当前用户消息
        expected_count = 1 + (MAX_CONTEXT_MESSAGES * 2) + 1
        assert len(messages) == expected_count

    @pytest.mark.asyncio
    async def test_context_without_result_json(self):
        """测试没有 result_json 的历史消息"""
        mock_history = MagicMock()
        mock_history.get_conversation_messages = AsyncMock(return_value=[
            {
                "question": "查询用户",
                "sql": "SELECT * FROM users",
                "result_json": None,
            }
        ])
        
        with patch("sql_assistant.api.query.get_history", return_value=mock_history):
            messages = await _build_messages_with_context(
                db_type="mysql",
                schema_text="TABLE: users (id, name)",
                question="继续",
                conversation_id=1,
            )
        
        assistant_msg = messages[2]["content"]
        assert "SQL:" in assistant_msg
        assert "SELECT * FROM users" in assistant_msg

    @pytest.mark.asyncio
    async def test_empty_context_messages(self):
        """测试空的上下文消息列表"""
        mock_history = MagicMock()
        mock_history.get_conversation_messages = AsyncMock(return_value=[])
        
        with patch("sql_assistant.api.query.get_history", return_value=mock_history):
            messages = await _build_messages_with_context(
                db_type="mysql",
                schema_text="TABLE: users (id, name)",
                question="查询",
                conversation_id=1,
            )
        
        # 应该只有系统消息和当前用户消息
        assert len(messages) == 2
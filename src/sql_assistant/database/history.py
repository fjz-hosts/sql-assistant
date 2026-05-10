"""查询历史管理 - 使用 SQLite 存储"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

from ..config import DEFAULT_CONFIG_DIR

HISTORY_DB_PATH = DEFAULT_CONFIG_DIR / "history.db"


class HistoryManager:
    """查询历史管理器 - 支持对话管理"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or HISTORY_DB_PATH
        self._db: Optional[aiosqlite.Connection] = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(str(self.db_path))
            self._db.row_factory = aiosqlite.Row
            await self._init_tables()
        return self._db

    async def _init_tables(self):
        db = self._db
        # 对话表 - 存储对话会话
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
            ON conversations(updated_at DESC)
        """)
        
        # 查询历史表 - 添加 conversation_id 字段关联对话
        await db.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                question TEXT NOT NULL,
                sql TEXT NOT NULL,
                result_json TEXT,
                db_type TEXT DEFAULT '',
                llm_provider TEXT DEFAULT '',
                success INTEGER DEFAULT 1,
                error_message TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_conversation_id
            ON query_history(conversation_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_created_at
            ON query_history(created_at DESC)
        """)
        await db.commit()

    # ============ 对话管理方法 ============

    async def create_conversation(self, title: str = "") -> int:
        """创建新对话，返回对话 ID"""
        db = await self._get_db()
        if not title:
            title = "未命名对话"
        
        cursor = await db.execute(
            """INSERT INTO conversations (title, created_at, updated_at)
               VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (title,),
        )
        await db.commit()
        return cursor.lastrowid

    async def get_conversations(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """获取对话列表"""
        db = await self._get_db()
        cursor = await db.execute(
            """SELECT c.id, c.title, c.created_at, c.updated_at,
                      COUNT(q.id) as message_count
               FROM conversations c
               LEFT JOIN query_history q ON c.id = q.conversation_id
               GROUP BY c.id
               ORDER BY c.updated_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_conversation(self, conversation_id: int) -> Optional[dict]:
        """获取单个对话详情"""
        db = await self._get_db()
        cursor = await db.execute(
            """SELECT c.id, c.title, c.created_at, c.updated_at,
                      COUNT(q.id) as message_count
               FROM conversations c
               LEFT JOIN query_history q ON c.id = q.conversation_id
               WHERE c.id = ?
               GROUP BY c.id""",
            (conversation_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def update_conversation(self, conversation_id: int, title: str) -> bool:
        """更新对话标题"""
        db = await self._get_db()
        cursor = await db.execute(
            """UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (title, conversation_id),
        )
        await db.commit()
        return cursor.rowcount > 0

    async def delete_conversation(self, conversation_id: int) -> bool:
        """删除对话（会级联删除相关的查询记录）"""
        db = await self._get_db()
        cursor = await db.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        await db.commit()
        return cursor.rowcount > 0

    async def get_conversation_messages(self, conversation_id: int) -> list[dict]:
        """获取对话中的所有消息"""
        db = await self._get_db()
        cursor = await db.execute(
            """SELECT q.id, q.question, q.sql, q.result_json, q.db_type,
                      q.llm_provider, q.success, q.error_message, q.created_at
               FROM query_history q
               WHERE q.conversation_id = ?
               ORDER BY q.created_at ASC""",
            (conversation_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ============ 查询历史方法 ============

    async def add_record(
        self,
        question: str,
        sql: str,
        result: Optional[dict] = None,
        db_type: str = "",
        llm_provider: str = "",
        success: bool = True,
        error_message: str = "",
        conversation_id: Optional[int] = None,
    ) -> int:
        """添加一条查询记录，返回记录 ID"""
        db = await self._get_db()
        result_json = json.dumps(result, ensure_ascii=False, default=str) if result else None

        cursor = await db.execute(
            """INSERT INTO query_history
               (conversation_id, question, sql, result_json, db_type, llm_provider, success, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (conversation_id, question, sql, result_json, db_type, llm_provider, int(success), error_message),
        )
        await db.commit()
        
        # 如果关联了对话，更新对话的 updated_at
        if conversation_id:
            await db.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,),
            )
            await db.commit()
        
        return cursor.lastrowid

    async def get_records(
        self,
        limit: int = 50,
        offset: int = 0,
        conversation_id: Optional[int] = None,
    ) -> list[dict]:
        """获取查询历史记录"""
        db = await self._get_db()
        if conversation_id:
            cursor = await db.execute(
                """SELECT id, conversation_id, question, sql, result_json, db_type, llm_provider,
                          success, error_message, created_at
                   FROM query_history
                   WHERE conversation_id = ?
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (conversation_id, limit, offset),
            )
        else:
            cursor = await db.execute(
                """SELECT id, conversation_id, question, sql, result_json, db_type, llm_provider,
                          success, error_message, created_at
                   FROM query_history
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_record(self, record_id: int) -> Optional[dict]:
        """获取单条记录"""
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT * FROM query_history WHERE id = ?",
            (record_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def delete_record(self, record_id: int) -> bool:
        """删除单条记录"""
        db = await self._get_db()
        cursor = await db.execute(
            "DELETE FROM query_history WHERE id = ?",
            (record_id,),
        )
        await db.commit()
        return cursor.rowcount > 0

    async def clear_history(self) -> int:
        """清空所有历史记录（包括所有对话）"""
        db = await self._get_db()
        cursor = await db.execute("DELETE FROM query_history")
        await db.commit()
        await db.execute("DELETE FROM conversations")
        await db.commit()
        return cursor.rowcount

    async def get_count(self, conversation_id: Optional[int] = None) -> int:
        """获取记录总数"""
        db = await self._get_db()
        if conversation_id:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM query_history WHERE conversation_id = ?",
                (conversation_id,),
            )
        else:
            cursor = await db.execute("SELECT COUNT(*) FROM query_history")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_conversation_count(self) -> int:
        """获取对话总数"""
        db = await self._get_db()
        cursor = await db.execute("SELECT COUNT(*) FROM conversations")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None


# 全局单例
_history_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager


async def close_history_manager():
    global _history_manager
    if _history_manager:
        await _history_manager.close()
        _history_manager = None
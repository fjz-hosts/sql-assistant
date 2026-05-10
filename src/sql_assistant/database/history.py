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
    """查询历史管理器"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or HISTORY_DB_PATH
        self._db: Optional[aiosqlite.Connection] = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(str(self.db_path))
            self._db.row_factory = aiosqlite.Row
            await self._init_table()
        return self._db

    async def _init_table(self):
        db = self._db
        await db.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                sql TEXT NOT NULL,
                result_json TEXT,
                db_type TEXT DEFAULT '',
                llm_provider TEXT DEFAULT '',
                success INTEGER DEFAULT 1,
                error_message TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_created_at
            ON query_history(created_at DESC)
        """)
        await db.commit()

    async def add_record(
        self,
        question: str,
        sql: str,
        result: Optional[dict] = None,
        db_type: str = "",
        llm_provider: str = "",
        success: bool = True,
        error_message: str = "",
    ) -> int:
        """添加一条查询记录，返回记录 ID"""
        db = await self._get_db()
        result_json = json.dumps(result, ensure_ascii=False, default=str) if result else None

        cursor = await db.execute(
            """INSERT INTO query_history
               (question, sql, result_json, db_type, llm_provider, success, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (question, sql, result_json, db_type, llm_provider, int(success), error_message),
        )
        await db.commit()
        return cursor.lastrowid

    async def get_records(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """获取查询历史记录"""
        db = await self._get_db()
        cursor = await db.execute(
            """SELECT id, question, sql, result_json, db_type, llm_provider,
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
        """清空所有历史记录"""
        db = await self._get_db()
        cursor = await db.execute("DELETE FROM query_history")
        await db.commit()
        return cursor.rowcount

    async def get_count(self) -> int:
        """获取记录总数"""
        db = await self._get_db()
        cursor = await db.execute("SELECT COUNT(*) FROM query_history")
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

"""SQL模板管理 - 使用 SQLite 存储"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import aiosqlite

from ..config import DEFAULT_CONFIG_DIR

TEMPLATE_DB_PATH = DEFAULT_CONFIG_DIR / "templates.db"


class TemplateManager:
    """SQL模板管理器"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or TEMPLATE_DB_PATH
        self._db: Optional[aiosqlite.Connection] = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(str(self.db_path))
            self._db.row_factory = aiosqlite.Row
            await self._init_tables()
        return self._db

    async def _init_tables(self):
        """初始化数据库表"""
        db = self._db
        await db.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                sql TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_templates_name
            ON templates(name)
        """)
        await db.commit()

    async def create_template(
        self,
        name: str,
        description: str = "",
        sql: str = "",
        tags: List[str] = None
    ) -> int:
        """创建新模板"""
        db = await self._get_db()
        tags_json = json.dumps(tags or [])
        
        cursor = await db.execute(
            """INSERT INTO templates (name, description, sql, tags, created_at, updated_at)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (name, description, sql, tags_json),
        )
        await db.commit()
        return cursor.lastrowid

    async def get_template(self, template_id: int) -> Optional[dict]:
        """获取单个模板"""
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT * FROM templates WHERE id = ?",
            (template_id,),
        )
        row = await cursor.fetchone()
        if row:
            result = dict(row)
            result["tags"] = json.loads(result["tags"])
            return result
        return None

    async def get_templates(
        self,
        limit: int = 50,
        offset: int = 0,
        tag: Optional[str] = None
    ) -> List[dict]:
        """获取模板列表"""
        db = await self._get_db()
        
        if tag:
            # SQLite不支持JSON数组包含查询，需要特殊处理
            cursor = await db.execute(
                """SELECT * FROM templates
                   WHERE tags LIKE ?
                   ORDER BY updated_at DESC
                   LIMIT ? OFFSET ?""",
                (f"%{tag}%", limit, offset),
            )
        else:
            cursor = await db.execute(
                """SELECT * FROM templates
                   ORDER BY updated_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            )
        
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["tags"] = json.loads(item["tags"])
            result.append(item)
        return result

    async def update_template(
        self,
        template_id: int,
        name: str,
        description: str = "",
        sql: str = "",
        tags: List[str] = None
    ) -> bool:
        """更新模板"""
        db = await self._get_db()
        tags_json = json.dumps(tags or [])
        
        cursor = await db.execute(
            """UPDATE templates
               SET name = ?, description = ?, sql = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (name, description, sql, tags_json, template_id),
        )
        await db.commit()
        return cursor.rowcount > 0

    async def delete_template(self, template_id: int) -> bool:
        """删除模板"""
        db = await self._get_db()
        cursor = await db.execute(
            "DELETE FROM templates WHERE id = ?",
            (template_id,),
        )
        await db.commit()
        return cursor.rowcount > 0

    async def get_count(self, tag: Optional[str] = None) -> int:
        """获取模板数量"""
        db = await self._get_db()
        
        if tag:
            cursor = await db.execute(
                """SELECT COUNT(*) FROM templates
                   WHERE tags LIKE ?""",
                (f"%{tag}%",),
            )
        else:
            cursor = await db.execute("SELECT COUNT(*) FROM templates")
        
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        db = await self._get_db()
        cursor = await db.execute("SELECT tags FROM templates")
        rows = await cursor.fetchall()
        
        tags_set = set()
        for row in rows:
            try:
                tags = json.loads(row["tags"])
                tags_set.update(tags)
            except:
                pass
        
        return sorted(list(tags_set))


# 全局实例
_template_manager = None


def get_template_manager() -> TemplateManager:
    """获取模板管理器实例"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
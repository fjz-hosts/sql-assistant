"""SQL执行计划管理 - 使用 SQLite 存储"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import aiosqlite

from ..config import DEFAULT_CONFIG_DIR

EXPLAIN_DB_PATH = DEFAULT_CONFIG_DIR / "explain_history.db"


class ExplainPlanManager:
    """SQL执行计划管理器"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or EXPLAIN_DB_PATH
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
            CREATE TABLE IF NOT EXISTS explain_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sql TEXT NOT NULL,
                db_type TEXT NOT NULL,
                db_name TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                plan_text TEXT,
                estimated_cost REAL,
                estimated_rows INTEGER,
                actual_time_ms REAL,
                warnings TEXT DEFAULT '[]',
                suggestions TEXT DEFAULT '[]',
                is_slow_query BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_explain_created_at
            ON explain_plans(created_at DESC)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_explain_db_type
            ON explain_plans(db_type)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_explain_slow
            ON explain_plans(is_slow_query)
        """)
        await db.commit()

    async def save_plan(
        self,
        sql: str,
        db_type: str,
        db_name: str,
        plan_json: dict,
        plan_text: str = "",
        estimated_cost: float = 0.0,
        estimated_rows: int = 0,
        actual_time_ms: float = 0.0,
        warnings: List[str] = None,
        suggestions: List[str] = None,
        is_slow_query: bool = False
    ) -> int:
        """保存执行计划"""
        db = await self._get_db()

        local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = await db.execute(
            """INSERT INTO explain_plans
               (sql, db_type, db_name, plan_json, plan_text, estimated_cost,
                estimated_rows, actual_time_ms, warnings, suggestions, is_slow_query, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                sql,
                db_type,
                db_name,
                json.dumps(plan_json, ensure_ascii=False),
                plan_text,
                estimated_cost,
                estimated_rows,
                actual_time_ms,
                json.dumps(warnings or [], ensure_ascii=False),
                json.dumps(suggestions or [], ensure_ascii=False),
                is_slow_query,
                local_time
            ),
        )
        await db.commit()
        return cursor.lastrowid

    async def get_plan(self, plan_id: int) -> Optional[dict]:
        """获取单个执行计划"""
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT * FROM explain_plans WHERE id = ?",
            (plan_id,),
        )
        row = await cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None

    async def get_plans(
        self,
        limit: int = 50,
        offset: int = 0,
        db_type: Optional[str] = None,
        only_slow: bool = False
    ) -> List[dict]:
        """获取执行计划列表"""
        db = await self._get_db()

        conditions = []
        params = []

        if db_type:
            conditions.append("db_type = ?")
            params.append(db_type)
        if only_slow:
            conditions.append("is_slow_query = 1")

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        cursor = await db.execute(
            f"""SELECT * FROM explain_plans
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )

        rows = await cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]

    async def delete_plan(self, plan_id: int) -> bool:
        """删除执行计划"""
        db = await self._get_db()
        cursor = await db.execute(
            "DELETE FROM explain_plans WHERE id = ?",
            (plan_id,),
        )
        await db.commit()
        return cursor.rowcount > 0

    async def get_count(
        self,
        db_type: Optional[str] = None,
        only_slow: bool = False
    ) -> int:
        """获取执行计划数量"""
        db = await self._get_db()

        conditions = []
        params = []

        if db_type:
            conditions.append("db_type = ?")
            params.append(db_type)
        if only_slow:
            conditions.append("is_slow_query = 1")

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        cursor = await db.execute(
            f"SELECT COUNT(*) FROM explain_plans {where_clause}",
            params
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_slow_query_stats(self) -> dict:
        """获取慢查询统计"""
        db = await self._get_db()

        cursor = await db.execute(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_slow_query = 1 THEN 1 ELSE 0 END) as slow_count,
                AVG(estimated_cost) as avg_cost,
                MAX(estimated_cost) as max_cost
            FROM explain_plans"""
        )
        row = await cursor.fetchone()

        return {
            "total_plans": row[0] or 0,
            "slow_query_count": row[1] or 0,
            "average_cost": round(row[2] or 0, 2),
            "max_cost": round(row[3] or 0, 2)
        }

    def _row_to_dict(self, row: aiosqlite.Row) -> dict:
        """将行转换为字典"""
        result = dict(row)
        result["plan_json"] = json.loads(result["plan_json"])
        result["warnings"] = json.loads(result["warnings"])
        result["suggestions"] = json.loads(result["suggestions"])
        return result

    async def close(self):
        """关闭数据库连接"""
        if self._db:
            await self._db.close()
            self._db = None

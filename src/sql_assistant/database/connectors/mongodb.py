"""MongoDB 连接器"""

import json
import asyncio
from typing import Any

from pymongo import MongoClient

from .base import BaseConnector, QueryResult


class MongoDBConnector(BaseConnector):
    """MongoDB 数据库连接器"""

    db_type = "mongodb"

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        super().__init__(host, port, user, password, database)
        self._client: MongoClient | None = None
        self._db = None

    async def connect(self) -> None:
        loop = asyncio.get_event_loop()
        connection_string = f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/" if self.user else f"mongodb://{self.host}:{self.port}/"
        self._client = await loop.run_in_executor(
            None,
            lambda: MongoClient(connection_string, serverSelectionTimeoutMS=10000),
        )
        self._db = self._client[self.database]

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    async def get_schema(self) -> dict:
        """MongoDB 无固定 schema，采样分析每个 collection 的字段"""
        if not self._client or self._db is None:
            raise RuntimeError("MongoDB 未连接")

        loop = asyncio.get_event_loop()

        def _run():
            collections = self._db.list_collection_names()
            tables = []
            for coll_name in collections:
                # 采样最多 5 条文档推断字段
                docs = list(self._db[coll_name].find().limit(5))
                columns_set: dict[str, set] = {}
                for doc in docs:
                    for key in doc.keys():
                        if key not in columns_set:
                            columns_set[key] = set()
                        val = doc[key]
                        columns_set[key].add(type(val).__name__ if val is not None else "null")

                columns = []
                for col_name, types in columns_set.items():
                    columns.append({
                        "name": col_name,
                        "type": ", ".join(sorted(types)),
                        "nullable": True,
                        "key": "_id" if col_name == "_id" else "",
                        "default": None,
                        "comment": "",
                    })
                tables.append({"name": coll_name, "columns": columns})

            return {"db_type": "mongodb", "tables": tables}

        return await loop.run_in_executor(None, _run)

    async def execute(self, sql: str) -> QueryResult:
        """执行 MongoDB 查询（JSON 格式）"""
        if not self._client or self._db is None:
            raise RuntimeError("MongoDB 未连接")

        loop = asyncio.get_event_loop()
        result = QueryResult()

        def _run():
            try:
                # 解析 JSON 查询
                query = json.loads(sql)
                collection_name = query.get("collection", "")
                operation = query.get("operation", "find").lower()
                collection = self._db[collection_name]

                if operation == "find":
                    filter_obj = query.get("filter", {})
                    projection = query.get("projection", None)
                    sort_list = query.get("sort", None)
                    limit_val = query.get("limit", 100)

                    cursor = collection.find(filter_obj, projection)
                    if sort_list:
                        cursor = cursor.sort(sort_list)
                    if limit_val:
                        cursor = cursor.limit(limit_val)

                    docs = list(cursor)
                    # 提取所有字段名
                    columns_set = set()
                    for doc in docs:
                        columns_set.update(doc.keys())
                    result.columns = sorted(columns_set)
                    result.rows = []
                    for doc in docs:
                        result.rows.append([doc.get(col, None) for col in result.columns])
                    result.row_count = len(docs)
                    result.sql_type = "SELECT"

                elif operation == "insert":
                    documents = query.get("documents", [])
                    if isinstance(documents, dict):
                        documents = [documents]
                    result_obj = collection.insert_many(documents)
                    result.affected_rows = len(result_obj.inserted_ids)
                    result.sql_type = "INSERT"

                elif operation == "update":
                    filter_obj = query.get("filter", {})
                    update_obj = query.get("update", {})
                    many = query.get("many", False)
                    if many:
                        update_result = collection.update_many(filter_obj, update_obj)
                    else:
                        update_result = collection.update_one(filter_obj, update_obj)
                    result.affected_rows = update_result.modified_count
                    result.sql_type = "UPDATE"

                elif operation == "delete":
                    filter_obj = query.get("filter", {})
                    many = query.get("many", False)
                    if many:
                        delete_result = collection.delete_many(filter_obj)
                    else:
                        delete_result = collection.delete_one(filter_obj)
                    result.affected_rows = delete_result.deleted_count
                    result.sql_type = "DELETE"

                elif operation == "aggregate":
                    pipeline = query.get("pipeline", [])
                    docs = list(collection.aggregate(pipeline))
                    columns_set = set()
                    for doc in docs:
                        columns_set.update(doc.keys())
                    result.columns = sorted(columns_set)
                    result.rows = [[doc.get(col, None) for col in result.columns] for doc in docs]
                    result.row_count = len(docs)
                    result.sql_type = "SELECT"

                elif operation == "count":
                    filter_obj = query.get("filter", {})
                    count = collection.count_documents(filter_obj)
                    result.columns = ["count"]
                    result.rows = [[count]]
                    result.row_count = 1
                    result.sql_type = "SELECT"

                else:
                    result.columns = ["error"]
                    result.rows = [[f"不支持的操作: {operation}"]]
                    result.row_count = 1

            except json.JSONDecodeError as e:
                result.columns = ["error"]
                result.rows = [[f"JSON 解析错误: {e}"]]
                result.row_count = 1
            except Exception as e:
                result.columns = ["error"]
                result.rows = [[str(e)]]
                result.row_count = 1

            return result

        return await loop.run_in_executor(None, _run)

    async def test_connection(self) -> dict:
        from .exceptions import format_connector_result
        try:
            await self.connect()
            if self._client:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self._client.admin.command("ping"),
                )
            return format_connector_result(True, data={"message": "MongoDB 连接成功"}, db_type="mongodb")
        except Exception as e:
            return format_connector_result(False, error=str(e), db_type="mongodb", code="CONNECTION_FAILED")

"""数据库备份模块 - 支持全量备份和增量备份"""

import asyncio
import json
import os
import shutil
from datetime import datetime, date, time
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from ..config import get_config_manager
from .manager import get_db_manager
from .connectors.base import BaseConnector, QueryResult


def _json_serializable(obj):
    """将对象转换为可 JSON 序列化的类型"""
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    elif hasattr(obj, '__dict__'):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@dataclass
class BackupConfig:
    """备份配置"""
    backup_type: str = "full"  # full: 全量备份, incremental: 增量备份
    tables: List[str] = None  # 指定表名列表，None 表示所有表
    backup_path: str = "./backups"  # 备份存储路径
    include_schema: bool = True  # 是否包含表结构
    include_data: bool = True  # 是否包含数据


@dataclass
class BackupResult:
    """备份结果"""
    success: bool
    message: str
    backup_id: str
    backup_path: str
    tables_backed_up: List[str]
    total_records: int
    backup_size: int  # bytes
    backup_time: str


@dataclass
class BackupInfo:
    """备份信息"""
    backup_id: str
    backup_type: str
    db_type: str
    db_name: str
    tables: List[str]
    record_count: int
    backup_time: str
    file_size: int


@dataclass
class RestoreResult:
    """恢复结果"""
    success: bool
    message: str
    backup_id: str
    tables_restored: List[str]
    total_records: int


class BackupManager:
    """数据库备份管理器"""

    def __init__(self):
        self._backup_path = "./backups"
        self._incremental_marker = ".last_backup_timestamp"

    async def backup(self, config: BackupConfig) -> BackupResult:
        """执行数据库备份"""
        db_manager = get_db_manager()
        connector = await db_manager.get_connector()
        db_config = get_config_manager().get_active_database()

        if not db_config:
            return BackupResult(
                success=False,
                message="未配置数据库连接",
                backup_id="",
                backup_path="",
                tables_backed_up=[],
                total_records=0,
                backup_size=0,
                backup_time=""
            )

        backup_id = self._generate_backup_id(config.backup_type)
        backup_dir = Path(config.backup_path) / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 获取要备份的表列表
            if config.tables:
                tables = config.tables
            else:
                schema = await connector.get_schema()
                tables = [t["name"] for t in schema.get("tables", [])]

            if not tables:
                return BackupResult(
                    success=False,
                    message="数据库中没有表可备份",
                    backup_id=backup_id,
                    backup_path=str(backup_dir),
                    tables_backed_up=[],
                    total_records=0,
                    backup_size=0,
                    backup_time=datetime.now().isoformat()
                )

            total_records = 0
            backed_up_tables = []

            # 获取增量备份的时间戳（仅增量备份时使用）
            last_backup_time = None
            if config.backup_type == "incremental":
                last_backup_time = self._get_last_backup_time()

            for table in tables:
                # 备份表结构
                if config.include_schema:
                    schema_file = backup_dir / f"{table}_schema.json"
                    schema_data = await self._get_table_schema(connector, table)
                    with open(schema_file, 'w', encoding='utf-8') as f:
                        json.dump(schema_data, f, ensure_ascii=False, indent=2)

                # 备份表数据
                if config.include_data:
                    data_file = backup_dir / f"{table}_data.json"
                    count = await self._backup_table_data(
                        connector, table, data_file, config.backup_type, last_backup_time
                    )
                    total_records += count

                backed_up_tables.append(table)

            # 保存备份元信息
            metadata = {
                "backup_id": backup_id,
                "backup_type": config.backup_type,
                "db_type": connector.db_type,
                "db_name": db_config.database,
                "tables": backed_up_tables,
                "record_count": total_records,
                "backup_time": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            with open(backup_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 更新最后备份时间戳
            self._update_last_backup_time()

            # 计算备份大小
            backup_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())

            return BackupResult(
                success=True,
                message=f"备份成功，共备份 {len(backed_up_tables)} 个表，{total_records} 条记录",
                backup_id=backup_id,
                backup_path=str(backup_dir),
                tables_backed_up=backed_up_tables,
                total_records=total_records,
                backup_size=backup_size,
                backup_time=datetime.now().isoformat()
            )

        except Exception as e:
            # 清理失败的备份
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            return BackupResult(
                success=False,
                message=f"备份失败: {str(e)}",
                backup_id=backup_id,
                backup_path=str(backup_dir),
                tables_backed_up=[],
                total_records=0,
                backup_size=0,
                backup_time=datetime.now().isoformat()
            )

    async def _get_table_schema(self, connector: BaseConnector, table_name: str) -> Dict:
        """获取表结构信息"""
        schema = await connector.get_schema()
        for table in schema.get("tables", []):
            if table["name"] == table_name:
                return table
        return {"name": table_name, "columns": []}

    async def _backup_table_data(self, connector: BaseConnector, table_name: str, 
                                output_file: Path, backup_type: str, 
                                last_backup_time: Optional[str]) -> int:
        """备份表数据"""
        if backup_type == "incremental" and last_backup_time:
            # 增量备份：只备份上次备份后修改的数据
            # 这里使用通用的增量备份策略，实际应用中可能需要根据数据库类型调整
            # 对于没有时间戳字段的表，退化为全量备份
            result = await self._get_incremental_data(connector, table_name, last_backup_time)
        else:
            # 全量备份：备份所有数据
            result = await connector.execute(f"SELECT * FROM {table_name}")

        # 将结果中的不可序列化对象转换为可序列化的字符串
        def convert_row(row):
            converted = []
            for item in row:
                try:
                    json.dumps(item)
                    converted.append(item)
                except (TypeError, ValueError):
                    converted.append(_json_serializable(item))
            return converted

        # 将结果写入 JSON 文件
        data = {
            "columns": result.columns,
            "rows": [convert_row(row) for row in result.rows],
            "row_count": result.row_count
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return result.row_count

    async def _get_incremental_data(self, connector: BaseConnector, table_name: str, 
                                   last_backup_time: str) -> QueryResult:
        """获取增量数据（上次备份后新增/修改的数据）"""
        # 尝试查找可能的时间戳字段
        timestamp_fields = ["updated_at", "update_time", "modify_time", "create_time", "created_at"]
        
        schema = await connector.get_schema()
        table_info = None
        for table in schema.get("tables", []):
            if table["name"] == table_name:
                table_info = table
                break

        if table_info:
            # 查找时间戳字段
            for field in timestamp_fields:
                for col in table_info.get("columns", []):
                    if col["name"].lower() == field:
                        # 找到时间戳字段，执行增量查询
                        query = f"SELECT * FROM {table_name} WHERE {field} > '{last_backup_time}'"
                        return await connector.execute(query)

        # 没有找到时间戳字段，执行全量查询
        return await connector.execute(f"SELECT * FROM {table_name}")

    def _generate_backup_id(self, backup_type: str) -> str:
        """生成唯一的备份 ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{backup_type}_{timestamp}"

    def _get_last_backup_time(self) -> Optional[str]:
        """获取上次备份时间"""
        marker_file = Path(self._backup_path) / self._incremental_marker
        if marker_file.exists():
            with open(marker_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None

    def _update_last_backup_time(self):
        """更新最后备份时间戳"""
        marker_file = Path(self._backup_path) / self._incremental_marker
        marker_file.parent.mkdir(parents=True, exist_ok=True)
        with open(marker_file, 'w', encoding='utf-8') as f:
            f.write(datetime.now().isoformat())

    def list_backups(self) -> List[BackupInfo]:
        """列出所有备份"""
        backups = []
        backup_dir = Path(self._backup_path)
        
        if not backup_dir.exists():
            return backups

        for item in backup_dir.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # 计算备份大小
                        file_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                        
                        backups.append(BackupInfo(
                            backup_id=metadata.get("backup_id", item.name),
                            backup_type=metadata.get("backup_type", "full"),
                            db_type=metadata.get("db_type", ""),
                            db_name=metadata.get("db_name", ""),
                            tables=metadata.get("tables", []),
                            record_count=metadata.get("record_count", 0),
                            backup_time=metadata.get("backup_time", ""),
                            file_size=file_size
                        ))
                    except Exception:
                        pass

        # 按时间排序（最新的在前）
        backups.sort(key=lambda x: x.backup_time, reverse=True)
        return backups

    def get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """获取指定备份的详细信息"""
        backup_dir = Path(self._backup_path) / backup_id
        metadata_file = backup_dir / "metadata.json"
        
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            file_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
            
            return BackupInfo(
                backup_id=metadata.get("backup_id", backup_id),
                backup_type=metadata.get("backup_type", "full"),
                db_type=metadata.get("db_type", ""),
                db_name=metadata.get("db_name", ""),
                tables=metadata.get("tables", []),
                record_count=metadata.get("record_count", 0),
                backup_time=metadata.get("backup_time", ""),
                file_size=file_size
            )
        except Exception:
            return None

    def delete_backup(self, backup_id: str) -> bool:
        """删除指定备份"""
        backup_dir = Path(self._backup_path) / backup_id
        if backup_dir.exists() and backup_dir.is_dir():
            shutil.rmtree(backup_dir)
            return True
        return False

    async def restore(self, backup_id: str, restore_schema: bool = False, 
                    restore_data: bool = True, tables: Optional[List[str]] = None) -> RestoreResult:
        """从备份恢复数据库
        
        Args:
            backup_id: 备份ID
            restore_schema: 是否重建表结构（谨慎使用，会删除现有表）
            restore_data: 是否恢复数据
            tables: 指定要恢复的表，None 表示恢复所有表
        """
        backup_dir = Path(self._backup_path) / backup_id
        metadata_file = backup_dir / "metadata.json"
        
        if not metadata_file.exists():
            return RestoreResult(
                success=False,
                message="备份文件不存在",
                backup_id=backup_id,
                tables_restored=[],
                total_records=0
            )
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            db_type = metadata.get("db_type", "")
            backup_tables = metadata.get("tables", [])
            
            # 确定要恢复的表
            if tables:
                tables_to_restore = [t for t in tables if t in backup_tables]
            else:
                tables_to_restore = backup_tables
            
            db_manager = get_db_manager()
            connector = await db_manager.get_connector()
            
            total_records = 0
            restored_tables = []
            
            for table_name in tables_to_restore:
                # 恢复表结构
                if restore_schema:
                    schema_file = backup_dir / f"{table_name}_schema.json"
                    if schema_file.exists():
                        await self._restore_table_schema(connector, table_name, schema_file)
                
                # 恢复表数据
                if restore_data:
                    data_file = backup_dir / f"{table_name}_data.json"
                    if data_file.exists():
                        count = await self._restore_table_data(connector, table_name, data_file, db_type)
                        total_records += count
                        restored_tables.append(table_name)
            
            return RestoreResult(
                success=True,
                message=f"恢复成功，共恢复 {len(restored_tables)} 个表，{total_records} 条记录",
                backup_id=backup_id,
                tables_restored=restored_tables,
                total_records=total_records
            )
            
        except Exception as e:
            return RestoreResult(
                success=False,
                message=f"恢复失败: {str(e)}",
                backup_id=backup_id,
                tables_restored=[],
                total_records=0
            )

    async def _restore_table_schema(self, connector: BaseConnector, table_name: str, schema_file: Path):
        """恢复表结构"""
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        columns = schema_data.get("columns", [])
        if not columns:
            return
        
        # 构建 CREATE TABLE 语句
        col_defs = []
        for col in columns:
            col_name = col.get("name", "")
            col_type = col.get("type", "VARCHAR(255)")
            nullable = col.get("nullable", True)
            key = col.get("key", "")
            
            definition = f"{col_name} {col_type}"
            if not nullable:
                definition += " NOT NULL"
            if key == "PRI":
                definition += " PRIMARY KEY"
            
            col_defs.append(definition)
        
        # 先删除表（如果存在）
        try:
            await connector.execute(f"DROP TABLE IF EXISTS {table_name}")
        except Exception:
            pass
        
        # 创建表
        create_sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
        await connector.execute(create_sql)

    async def _restore_table_data(self, connector: BaseConnector, table_name: str, 
                                  data_file: Path, db_type: str) -> int:
        """恢复表数据"""
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        columns = data.get("columns", [])
        rows = data.get("rows", [])
        
        if not columns or not rows:
            return 0
        
        # 根据数据库类型调整数据插入方式
        total_inserted = 0
        
        for row in rows:
            # 将数据转换回合适的类型
            values = self._convert_data_types(row, columns)
            
            # 构建 INSERT 语句
            placeholders = ", ".join(["?" for _ in columns])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            try:
                await connector.execute(insert_sql, values)
                total_inserted += 1
            except Exception as e:
                # 跳过插入失败的行
                continue
        
        return total_inserted

    def _convert_data_types(self, row: list, columns: list) -> list:
        """将 JSON 中的数据转换回合适的 Python 类型"""
        converted = []
        for i, item in enumerate(row):
            if item is None:
                converted.append(None)
            elif isinstance(item, str):
                # 尝试转换 ISO 格式的时间字符串
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"]:
                    try:
                        converted.append(datetime.strptime(item, fmt))
                        break
                    except ValueError:
                        continue
                else:
                    converted.append(item)
            else:
                converted.append(item)
        return converted


# 全局单例
_backup_manager = None


def get_backup_manager() -> BackupManager:
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager
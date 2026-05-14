"""数据库备份模块测试"""
import pytest
import asyncio
from sql_assistant.database.backup import get_backup_manager, BackupConfig, BackupInfo, BackupResult

class TestBackupManager:
    """备份管理器测试"""
    
    def test_backup_manager_init(self):
        """测试备份管理器初始化"""
        backup_manager = get_backup_manager()
        assert backup_manager is not None
    
    def test_backup_path_exists(self):
        """测试备份路径属性存在"""
        backup_manager = get_backup_manager()
        assert hasattr(backup_manager, '_backup_path')
        assert backup_manager._backup_path == "./backups"
    
    def test_backup_config_dataclass(self):
        """测试BackupConfig数据类"""
        config = BackupConfig(
            backup_type="full",
            tables=["users", "orders"],
            backup_path="./backups",
            include_schema=True,
            include_data=True
        )
        assert config.backup_type == "full"
        assert config.tables == ["users", "orders"]
        assert config.backup_path == "./backups"
    
    def test_backup_info_dataclass(self):
        """测试BackupInfo数据类"""
        info = BackupInfo(
            backup_id="test_backup",
            backup_type="full",
            db_type="mysql",
            db_name="test_db",
            tables=["users"],
            record_count=100,
            backup_time="2024-01-01T00:00:00",
            file_size=1024
        )
        assert info.backup_id == "test_backup"
        assert info.record_count == 100
    
    def test_list_backups(self):
        """测试列出备份"""
        backup_manager = get_backup_manager()
        backups = backup_manager.list_backups()
        assert isinstance(backups, list)
    
    def test_get_backup_info_nonexistent(self):
        """测试获取不存在的备份信息"""
        backup_manager = get_backup_manager()
        info = backup_manager.get_backup_info("nonexistent_backup")
        assert info is None
    
    def test_delete_backup_nonexistent(self):
        """测试删除不存在的备份"""
        backup_manager = get_backup_manager()
        result = backup_manager.delete_backup("nonexistent_backup")
        assert result is False
    
    def test_generate_backup_id_exists(self):
        """测试生成备份ID方法存在"""
        backup_manager = get_backup_manager()
        assert hasattr(backup_manager, '_generate_backup_id')
    
    def test_backup_result_dataclass(self):
        """测试BackupResult数据类"""
        result = BackupResult(
            success=True,
            message="备份成功",
            backup_id="test_backup",
            backup_path="./backups/test_backup",
            tables_backed_up=["users"],
            total_records=100,
            backup_size=1024,
            backup_time="2024-01-01T00:00:00"
        )
        assert result.success is True
        assert result.total_records == 100

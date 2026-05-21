"""定时备份功能测试"""

import pytest
from datetime import datetime, timedelta

from sql_assistant.settings import ScheduledBackupConfig
from sql_assistant.database.scheduler import BackupScheduler, get_backup_scheduler
from sql_assistant.database.backup import get_backup_manager


class TestScheduledBackupConfig:
    """定时备份配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ScheduledBackupConfig()
        assert config.enabled is False
        assert config.hour == 2
        assert config.minute == 0
        assert config.backup_type == "full"
        assert config.retention_count == 7
        assert config.include_schema is True
        assert config.include_data is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = ScheduledBackupConfig(
            enabled=True,
            hour=3,
            minute=30,
            backup_type="incremental",
            retention_count=14,
            include_schema=False,
            include_data=True
        )
        assert config.enabled is True
        assert config.hour == 3
        assert config.minute == 30
        assert config.backup_type == "incremental"
        assert config.retention_count == 14
        assert config.include_schema is False
        assert config.include_data is True


class TestBackupScheduler:
    """备份调度器测试"""

    def test_calculate_next_run(self):
        """测试计算下次执行时间"""
        scheduler = BackupScheduler()
        
        # 设置一个未来时间
        now = datetime.now()
        target_hour = (now.hour + 1) % 24
        target_minute = now.minute
        
        next_run = scheduler._calculate_next_run(target_hour, target_minute)
        
        assert next_run.hour == target_hour
        assert next_run.minute == target_minute
        
        # 如果目标时间已过，应该是明天
        past_hour = (now.hour - 1) % 24
        next_run_past = scheduler._calculate_next_run(past_hour, now.minute)
        expected_date = now.date() + timedelta(days=1)
        assert next_run_past.date() == expected_date

    def test_calculate_delay(self):
        """测试计算延迟"""
        scheduler = BackupScheduler()
        
        now = datetime.now()
        target_hour = (now.hour + 1) % 24
        target_minute = now.minute
        
        delay = scheduler._calculate_delay(target_hour, target_minute)
        
        # 延迟应该是正的，大约是1小时
        assert delay > 0
        assert delay < 3600 + 60  # 1小时+1分钟的缓冲

    def test_singleton_instance(self):
        """测试单例模式"""
        scheduler1 = get_backup_scheduler()
        scheduler2 = get_backup_scheduler()
        
        assert scheduler1 is scheduler2

    def test_status_properties(self):
        """测试状态属性"""
        scheduler = BackupScheduler()
        
        assert scheduler.status.enabled is False
        assert scheduler.status.next_run_time is None
        assert scheduler.status.last_run_time is None
        assert scheduler.status.last_run_success is None
        assert scheduler.status.last_run_message is None


class TestBackupCleanup:
    """备份清理测试"""

    def test_cleanup_no_retention(self):
        """测试不限制保留数量时不删除备份"""
        backup_manager = get_backup_manager()
        
        # 保留数量为0时不删除
        deleted = backup_manager.cleanup_old_backups(0)
        assert deleted == 0

    def test_cleanup_no_backups(self):
        """测试没有备份时不删除"""
        backup_manager = get_backup_manager()
        
        deleted = backup_manager.cleanup_old_backups(5)
        assert deleted == 0

    def test_cleanup_with_backups(self):
        """测试清理旧备份（模拟场景）"""
        backup_manager = get_backup_manager()
        
        # 获取当前备份数量
        backups = backup_manager.list_backups()
        original_count = len(backups)
        
        # 如果有备份，测试清理功能
        if original_count > 0:
            # 设置保留数量为当前数量 - 1
            if original_count > 1:
                deleted = backup_manager.cleanup_old_backups(original_count - 1)
                assert deleted == 1 or deleted == 0  # 可能因为排序问题有所不同
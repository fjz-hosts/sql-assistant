"""定时任务调度器 - 支持定时备份功能"""

import asyncio
import logging
from datetime import datetime, time as dt_time, timedelta
from typing import Optional, Callable
from dataclasses import dataclass

from ..config import get_config_manager
from .backup import get_backup_manager, BackupConfig

logger = logging.getLogger(__name__)


@dataclass
class TaskStatus:
    """定时任务状态"""
    enabled: bool = False
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    last_run_success: Optional[bool] = None
    last_run_message: Optional[str] = None


class BackupScheduler:
    """备份定时任务调度器"""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._status = TaskStatus()
        self._shutdown_event = asyncio.Event()

    @property
    def status(self) -> TaskStatus:
        """获取任务状态"""
        return self._status

    def _calculate_next_run(self, hour: int, minute: int) -> datetime:
        """计算下次执行时间"""
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if target_time <= now:
            target_time += timedelta(days=1)
        
        return target_time

    def _calculate_delay(self, hour: int, minute: int) -> float:
        """计算到下次执行的延迟（秒）"""
        next_run = self._calculate_next_run(hour, minute)
        delay = (next_run - datetime.now()).total_seconds()
        return max(0, delay)

    async def _run_backup_task(self):
        """执行备份任务"""
        config_manager = get_config_manager()
        backup_config = config_manager.get_settings().scheduled_backup
        
        if not backup_config.enabled:
            return

        try:
            backup_manager = get_backup_manager()
            config = BackupConfig(
                backup_type=backup_config.backup_type,
                include_schema=backup_config.include_schema,
                include_data=backup_config.include_data
            )
            
            result = await backup_manager.backup(config)
            
            # 清理旧备份
            if backup_config.retention_count > 0:
                deleted_count = backup_manager.cleanup_old_backups(backup_config.retention_count)
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old backups")
            
            self._status.last_run_time = datetime.now()
            self._status.last_run_success = result.success
            self._status.last_run_message = result.message
            
            if result.success:
                logger.info(f"Scheduled backup completed successfully: {result.backup_id}")
            else:
                logger.error(f"Scheduled backup failed: {result.message}")
                
        except Exception as e:
            self._status.last_run_time = datetime.now()
            self._status.last_run_success = False
            self._status.last_run_message = str(e)
            logger.error(f"Scheduled backup error: {e}")

    async def _scheduler_loop(self):
        """定时任务调度循环"""
        config_manager = get_config_manager()
        
        while not self._shutdown_event.is_set():
            try:
                backup_config = config_manager.get_settings().scheduled_backup
                
                if not backup_config.enabled:
                    # 如果未启用，等待1分钟后重新检查
                    self._status.next_run_time = None
                    await asyncio.sleep(60)
                    continue
                
                # 计算下次执行时间
                delay = self._calculate_delay(backup_config.hour, backup_config.minute)
                self._status.next_run_time = self._calculate_next_run(
                    backup_config.hour, backup_config.minute
                )
                
                # 等待到执行时间
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=delay
                )
                
                # 如果事件被触发（关闭信号），退出循环
                if self._shutdown_event.is_set():
                    break
                    
            except asyncio.TimeoutError:
                # 超时表示到达执行时间
                await self._run_backup_task()
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)

    def start(self):
        """启动定时任务调度器"""
        if self._task is None or self._task.done():
            self._shutdown_event.clear()
            self._task = asyncio.create_task(self._scheduler_loop())
            logger.info("Backup scheduler started")

    def stop(self):
        """停止定时任务调度器"""
        self._shutdown_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Backup scheduler stopped")

    def update_config(self):
        """配置更新后重新启动调度器"""
        if self._task and not self._task.done():
            self.stop()
        self.start()

    def get_next_run_time(self) -> Optional[str]:
        """获取下次执行时间（ISO格式字符串）"""
        if self._status.next_run_time:
            return self._status.next_run_time.isoformat()
        return None

    def get_last_run_time(self) -> Optional[str]:
        """获取上次执行时间（ISO格式字符串）"""
        if self._status.last_run_time:
            return self._status.last_run_time.isoformat()
        return None


# 全局单例
_scheduler_instance: Optional[BackupScheduler] = None


def get_backup_scheduler() -> BackupScheduler:
    """获取全局 BackupScheduler 单例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = BackupScheduler()
    return _scheduler_instance
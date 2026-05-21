"""定时备份任务 API 路由"""

from fastapi import APIRouter, HTTPException

from .models import ScheduledBackupRequest, ScheduledBackupResponse, ScheduledTaskStatus
from ..config import get_config_manager
from ..database.scheduler import get_backup_scheduler

router = APIRouter()


@router.get("/scheduler/backup/config", response_model=ScheduledBackupResponse)
async def get_scheduled_backup_config():
    """获取定时备份配置"""
    config_manager = get_config_manager()
    settings = config_manager.get_settings()
    backup_config = settings.scheduled_backup
    
    scheduler = get_backup_scheduler()
    next_run_time = scheduler.get_next_run_time()
    
    return ScheduledBackupResponse(
        enabled=backup_config.enabled,
        hour=backup_config.hour,
        minute=backup_config.minute,
        backup_type=backup_config.backup_type,
        retention_count=backup_config.retention_count,
        include_schema=backup_config.include_schema,
        include_data=backup_config.include_data,
        next_run_time=next_run_time
    )


@router.post("/scheduler/backup/config", response_model=ScheduledBackupResponse)
async def update_scheduled_backup_config(request: ScheduledBackupRequest):
    """更新定时备份配置"""
    config_manager = get_config_manager()
    settings = config_manager.get_settings()
    
    # 更新配置
    settings.scheduled_backup.enabled = request.enabled
    settings.scheduled_backup.hour = request.hour
    settings.scheduled_backup.minute = request.minute
    settings.scheduled_backup.backup_type = request.backup_type
    settings.scheduled_backup.retention_count = request.retention_count
    settings.scheduled_backup.include_schema = request.include_schema
    settings.scheduled_backup.include_data = request.include_data
    
    config_manager.save()
    
    # 更新调度器
    scheduler = get_backup_scheduler()
    if request.enabled:
        scheduler.update_config()
    else:
        scheduler.stop()
    
    next_run_time = scheduler.get_next_run_time() if request.enabled else None
    
    return ScheduledBackupResponse(
        enabled=request.enabled,
        hour=request.hour,
        minute=request.minute,
        backup_type=request.backup_type,
        retention_count=request.retention_count,
        include_schema=request.include_schema,
        include_data=request.include_data,
        next_run_time=next_run_time
    )


@router.get("/scheduler/backup/status", response_model=ScheduledTaskStatus)
async def get_scheduled_backup_status():
    """获取定时备份任务状态"""
    scheduler = get_backup_scheduler()
    status = scheduler.status
    
    return ScheduledTaskStatus(
        enabled=status.enabled,
        next_run_time=scheduler.get_next_run_time(),
        last_run_time=scheduler.get_last_run_time(),
        last_run_success=status.last_run_success,
        last_run_message=status.last_run_message
    )


@router.post("/scheduler/backup/run-now")
async def run_backup_now():
    """立即执行一次备份（测试用）"""
    from ..database.backup import get_backup_manager, BackupConfig
    
    config_manager = get_config_manager()
    backup_config = config_manager.get_settings().scheduled_backup
    
    backup_manager = get_backup_manager()
    config = BackupConfig(
        backup_type=backup_config.backup_type,
        include_schema=backup_config.include_schema,
        include_data=backup_config.include_data
    )
    
    result = await backup_manager.backup(config)
    
    # 清理旧备份
    if backup_config.retention_count > 0:
        backup_manager.cleanup_old_backups(backup_config.retention_count)
    
    return {
        "success": result.success,
        "message": result.message,
        "backup_id": result.backup_id,
        "backup_time": result.backup_time
    }


@router.post("/scheduler/backup/test")
async def test_scheduled_backup():
    """测试定时备份配置"""
    config_manager = get_config_manager()
    backup_config = config_manager.get_settings().scheduled_backup
    
    if backup_config.hour < 0 or backup_config.hour > 23:
        raise HTTPException(status_code=400, detail="小时必须在 0-23 之间")
    
    if backup_config.minute < 0 or backup_config.minute > 59:
        raise HTTPException(status_code=400, detail="分钟必须在 0-59 之间")
    
    scheduler = get_backup_scheduler()
    next_run = scheduler.get_next_run_time()
    
    return {
        "success": True,
        "message": "配置验证通过",
        "next_run_time": next_run
    }
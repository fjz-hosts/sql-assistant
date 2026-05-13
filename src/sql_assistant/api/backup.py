"""备份相关 API 路由"""

from fastapi import APIRouter, HTTPException

from .dependencies import get_config, get_db
from .models import (
    BackupRequest, BackupResponse, BackupInfoResponse, BackupListResponse,
    RestoreRequest, RestoreResponse,
)

router = APIRouter()


@router.post("/backup", response_model=BackupResponse)
async def create_backup(request: BackupRequest):
    from ..database.backup import get_backup_manager, BackupConfig

    backup_manager = get_backup_manager()

    config = BackupConfig(
        backup_type=request.backup_type,
        tables=request.tables,
        include_schema=request.include_schema,
        include_data=request.include_data
    )

    result = await backup_manager.backup(config)

    return BackupResponse(
        success=result.success,
        message=result.message,
        backup_id=result.backup_id,
        backup_path=result.backup_path,
        tables_backed_up=result.tables_backed_up,
        total_records=result.total_records,
        backup_size=result.backup_size,
        backup_time=result.backup_time
    )


@router.get("/backup/list", response_model=BackupListResponse)
async def list_backups():
    from ..database.backup import get_backup_manager

    backup_manager = get_backup_manager()
    backups = backup_manager.list_backups()

    return BackupListResponse(
        backups=[BackupInfoResponse(
            backup_id=b.backup_id,
            backup_type=b.backup_type,
            db_type=b.db_type,
            db_name=b.db_name,
            tables=b.tables,
            record_count=b.record_count,
            backup_time=b.backup_time,
            file_size=b.file_size
        ) for b in backups],
        total=len(backups)
    )


@router.get("/backup/{backup_id}", response_model=BackupInfoResponse)
async def get_backup_info(backup_id: str):
    from ..database.backup import get_backup_manager

    backup_manager = get_backup_manager()
    backup_info = backup_manager.get_backup_info(backup_id)

    if not backup_info:
        raise HTTPException(status_code=404, detail="备份不存在")

    return BackupInfoResponse(
        backup_id=backup_info.backup_id,
        backup_type=backup_info.backup_type,
        db_type=backup_info.db_type,
        db_name=backup_info.db_name,
        tables=backup_info.tables,
        record_count=backup_info.record_count,
        backup_time=backup_info.backup_time,
        file_size=backup_info.file_size
    )


@router.delete("/backup/{backup_id}")
async def delete_backup(backup_id: str):
    from ..database.backup import get_backup_manager

    backup_manager = get_backup_manager()

    if not backup_manager.delete_backup(backup_id):
        raise HTTPException(status_code=404, detail="备份不存在")

    return {"ok": True, "message": "备份删除成功"}


@router.post("/backup/restore", response_model=RestoreResponse)
async def restore_backup(request: RestoreRequest):
    from ..database.backup import get_backup_manager

    backup_manager = get_backup_manager()

    result = await backup_manager.restore(
        backup_id=request.backup_id,
        restore_schema=request.restore_schema,
        restore_data=request.restore_data,
        tables=request.tables
    )

    return RestoreResponse(
        success=result.success,
        message=result.message,
        backup_id=result.backup_id,
        tables_restored=result.tables_restored,
        total_records=result.total_records
    )
"""开机自启服务管理 API"""

from fastapi import APIRouter

from ..service.installer import get_status, install, uninstall, start, stop

router = APIRouter(prefix="/service", tags=["service"])


@router.get("/status")
async def service_status():
    return get_status()


@router.post("/install")
async def service_install():
    return install()


@router.post("/uninstall")
async def service_uninstall():
    return uninstall()


@router.post("/start")
async def service_start():
    return start()


@router.post("/stop")
async def service_stop():
    return stop()
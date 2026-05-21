"""服务安装器 - 支持 Windows (Task Scheduler) 和 Linux (systemd)"""

import os
import sys
import signal
import socket
import platform
import subprocess
from pathlib import Path

SERVICE_NAME = "sql-assistant"
SERVICE_PORT = 5010


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _get_pid_file() -> Path:
    return _get_project_root() / ".data" / "service.pid"


def _get_python_path() -> str:
    return sys.executable


def _get_entry_module() -> str:
    return "sql_assistant.main"


def _get_data_dir() -> Path:
    data_dir = _get_project_root() / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _check_port(port: int = SERVICE_PORT) -> bool:
    """检测本地端口是否已被占用（即服务正在运行）"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except (OSError, socket.timeout):
        return False


def get_status() -> dict:
    """获取服务安装和运行状态"""
    system = platform.system()
    try:
        if system == "Windows":
            installed = _check_windows()
        else:
            installed = _check_linux()
        running = _check_port()
        return {
            "installed": installed,
            "running": running,
            "platform": system,
            "service_name": SERVICE_NAME,
        }
    except Exception as e:
        return {
            "installed": False,
            "running": False,
            "platform": system,
            "service_name": SERVICE_NAME,
            "error": str(e),
        }


def install() -> dict:
    """安装并立即启动开机自启服务"""
    system = platform.system()
    try:
        if system == "Windows":
            result = _install_windows()
        else:
            result = _install_linux()
        return {"success": True, "platform": system, "message": result}
    except Exception as e:
        return {"success": False, "platform": system, "error": str(e)}


def uninstall() -> dict:
    """停止并卸载开机自启服务"""
    system = platform.system()
    try:
        if system == "Windows":
            result = _uninstall_windows()
        else:
            result = _uninstall_linux()
        return {"success": True, "platform": system, "message": result}
    except Exception as e:
        return {"success": False, "platform": system, "error": str(e)}


def start() -> dict:
    """手动启动服务（不安装开机自启）"""
    system = platform.system()
    try:
        if system == "Windows":
            result = _start_windows()
        else:
            result = _start_linux()
        return {"success": True, "platform": system, "message": result}
    except Exception as e:
        return {"success": False, "platform": system, "error": str(e)}


def stop() -> dict:
    """手动停止正在运行的服务"""
    system = platform.system()
    try:
        if system == "Windows":
            result = _stop_windows()
        else:
            result = _stop_linux()
        return {"success": True, "platform": system, "message": result}
    except Exception as e:
        return {"success": False, "platform": system, "error": str(e)}


# ==================== Windows ====================

def _check_windows() -> bool:
    result = subprocess.run(
        ["nssm", "status", SERVICE_NAME],
        capture_output=True, text=True, encoding='utf-8', errors='ignore',
    )
    return result.returncode == 0


def _install_windows() -> str:
    messages = []

    if not _check_windows():
        pythonw_path = _get_pythonw_path()
        project_root = str(_get_project_root())
        log_dir = _get_data_dir()

        result = subprocess.run(
            [
                "nssm", "install", SERVICE_NAME,
                pythonw_path,
                "-m", "sql_assistant.main",
            ],
            capture_output=True, text=True, encoding='utf-8', errors='ignore',
            cwd=project_root,
        )

        if result.returncode != 0:
            raise RuntimeError(f"NSSM 安装服务失败")

        subprocess.run(["nssm", "set", SERVICE_NAME, "AppDirectory", project_root], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        subprocess.run(["nssm", "set", SERVICE_NAME, "DisplayName", "SQL Assistant"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        subprocess.run(["nssm", "set", SERVICE_NAME, "Description", "SQL Assistant Service"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        subprocess.run(["nssm", "set", SERVICE_NAME, "Start", "SERVICE_AUTO_START"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        subprocess.run(["nssm", "set", SERVICE_NAME, "AppStdout", str(log_dir / "app.log")], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        subprocess.run(["nssm", "set", SERVICE_NAME, "AppStderr", str(log_dir / "app_error.log")], capture_output=True, text=True, encoding='utf-8', errors='ignore')

        messages.append("已通过 NSSM 创建 Windows 服务")
        subprocess.run(["nssm", "start", SERVICE_NAME], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        messages.append("服务已启动")
    else:
        messages.append("Windows 服务已存在")
        if not _check_port():
            subprocess.run(["nssm", "start", SERVICE_NAME], capture_output=True, text=True, encoding='utf-8', errors='ignore')
            messages.append("服务已启动")
        else:
            messages.append("服务已在运行中")

    _stop_current_if_frontend()

    return "；".join(messages)


def _uninstall_windows() -> str:
    messages = []

    if _check_windows():
        # 先停止服务
        subprocess.run(["nssm", "stop", SERVICE_NAME], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        import time
        time.sleep(1)
        
        # 删除服务
        result = subprocess.run(
            ["nssm", "remove", SERVICE_NAME, "confirm"],
            capture_output=True, text=True, encoding='utf-8', errors='ignore',
        )

        if result.returncode != 0:
            raise RuntimeError(f"NSSM 删除服务失败")

        messages.append("已通过 NSSM 删除 Windows 服务")
    else:
        messages.append("Windows 服务不存在")

    # 如果端口还在占用，强制杀掉进程
    if _check_port():
        pid = _find_pid_by_port(SERVICE_PORT)
        if pid is not None:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.5)
                if _check_port():
                    os.kill(pid, signal.SIGKILL)
                messages.append("已强制终止残留进程")
            except OSError:
                pass

    return "；".join(messages)


def _start_windows() -> str:
    if _check_port():
        return "服务已在运行中"

    if not _check_windows():
        raise RuntimeError("请先安装服务再启动")

    subprocess.run(["nssm", "start", SERVICE_NAME], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    messages = ["服务已通过 NSSM 启动"]

    _stop_current_if_frontend()

    return "；".join(messages)


def _stop_windows() -> str:
    if not _check_port():
        return "服务未在运行"

    if _check_windows():
        subprocess.run(["nssm", "stop", SERVICE_NAME], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        return "服务已通过 NSSM 停止"
    else:
        pid = _find_pid_by_port(SERVICE_PORT)
        if pid is not None:
            try:
                os.kill(pid, signal.SIGTERM)
                import time
                time.sleep(0.5)
                if _check_port():
                    os.kill(pid, signal.SIGTERM)
                return "服务已停止"
            except OSError:
                pass

    return "服务已停止"


def _find_pid_by_port(port: int) -> int | None:
    """通过端口号查找进程 PID"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                if parts:
                    pid_str = parts[-1]
                    if pid_str.isdigit():
                        return int(pid_str)
    except Exception:
        pass
    return None


def _start_detached() -> None:
    pythonw_path = _get_pythonw_path()
    project_root = str(_get_project_root())

    CREATE_NO_WINDOW = 0x08000000

    env = os.environ.copy()
    env["PYTHONPATH"] = project_root

    proc = subprocess.Popen(
        [pythonw_path, "-m", "sql_assistant.main"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        | subprocess.DETACHED_PROCESS
        | CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=project_root,
        close_fds=True,
        env=env,
    )

    _save_pid(proc.pid)


def _get_pythonw_path() -> str:
    """获取 pythonw.exe 路径（无窗口版 Python），找不到则回退到 python.exe"""
    python_dir = os.path.dirname(_get_python_path())
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return _get_python_path()


def _is_frontend_process() -> bool:
    """判断当前进程是否是前台 python.exe（而非后台 pythonw.exe）"""
    return sys.executable.lower().endswith("python.exe")


def _stop_current_if_frontend() -> None:
    """如果当前是前台进程，后台启动成功后自动停止前台，让后台接管"""
    if not _is_frontend_process():
        return
    
    # 等待服务启动（最多等待5秒）
    import time
    for _ in range(50):
        if _check_port():
            os._exit(0)
        time.sleep(0.1)


# ==================== Linux ====================

def _check_linux() -> bool:
    systemd_dir = _get_systemd_user_dir()
    service_file = systemd_dir / f"{SERVICE_NAME}.service"
    return service_file.exists()


def _install_linux() -> str:
    messages = []

    if not _check_linux():
        systemd_dir = _get_systemd_user_dir()
        systemd_dir.mkdir(parents=True, exist_ok=True)

        python_path = _get_python_path()

        service_content = f"""[Unit]
Description=SQL Assistant Service
After=network.target

[Service]
Type=simple
ExecStart={python_path} -m sql_assistant.main
WorkingDirectory={_get_project_root()}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""

        service_file = systemd_dir / f"{SERVICE_NAME}.service"
        service_file.write_text(service_content)

        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True,
        )
        subprocess.run(
            ["systemctl", "--user", "enable", SERVICE_NAME],
            capture_output=True,
        )
        messages.append("已创建并启用 systemd 用户服务")
    else:
        messages.append("systemd 服务已存在")

    if _check_port():
        messages.append("服务已在运行中")
    else:
        subprocess.run(
            ["systemctl", "--user", "start", SERVICE_NAME],
            capture_output=True,
        )
        messages.append("服务已启动，可以关闭此终端")

    return "；".join(messages)


def _uninstall_linux() -> str:
    messages = []

    _stop_linux()

    if _check_linux():
        subprocess.run(
            ["systemctl", "--user", "disable", SERVICE_NAME],
            capture_output=True,
        )

        service_file = _get_systemd_user_dir() / f"{SERVICE_NAME}.service"
        if service_file.exists():
            service_file.unlink()

        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            capture_output=True,
        )
        messages.append("已删除 systemd 用户服务")
    else:
        messages.append("systemd 服务不存在")

    return "；".join(messages)


def _start_linux() -> str:
    if _check_port():
        return "服务已在运行中"

    if not _check_linux():
        raise RuntimeError("请先安装服务再启动")

    subprocess.run(
        ["systemctl", "--user", "start", SERVICE_NAME],
        capture_output=True,
    )
    return "服务已启动"


def _stop_linux() -> str:
    if not _check_linux() and not _check_port():
        return "服务未在运行"

    subprocess.run(
        ["systemctl", "--user", "stop", SERVICE_NAME],
        capture_output=True,
    )
    return "服务已停止"


# ==================== PID 文件管理 (Windows) ====================

def _read_pid() -> int | None:
    try:
        pid_file = _get_pid_file()
        if pid_file.exists():
            return int(pid_file.read_text().strip())
    except (ValueError, OSError):
        pass
    return None


def _save_pid(pid: int) -> None:
    _get_data_dir()
    _get_pid_file().write_text(str(pid))


def _clear_pid() -> None:
    pid_file = _get_pid_file()
    if pid_file.exists():
        pid_file.unlink()


# ==================== 通用 ====================

def _get_systemd_user_dir() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(xdg_config) / "systemd" / "user"
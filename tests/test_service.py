"""开机自启服务安装 API 模块测试"""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sql_assistant.main import app

client = TestClient(app)


class TestServiceAPI:
    """服务安装 API 测试"""

    def test_get_service_status(self):
        response = client.get("/api/service/status")
        assert response.status_code == 200
        data = response.json()
        assert "installed" in data
        assert "running" in data
        assert "platform" in data
        assert "service_name" in data

    def test_get_service_status_fields(self):
        response = client.get("/api/service/status")
        data = response.json()
        assert isinstance(data["installed"], bool)
        assert isinstance(data["running"], bool)
        assert isinstance(data["platform"], str)
        assert data["service_name"] == "sql-assistant"


class TestServiceInstaller:
    """服务安装器模块测试"""

    def test_get_status_returns_dict(self):
        from sql_assistant.service.installer import get_status

        result = get_status()
        assert isinstance(result, dict)
        assert "installed" in result
        assert "running" in result
        assert "platform" in result
        assert "service_name" in result
        assert result["service_name"] == "sql-assistant"

    @patch("sql_assistant.service.installer._check_windows", return_value=False)
    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    def test_status_not_installed_windows(self, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import get_status

        result = get_status()
        assert result["installed"] is False
        assert result["running"] is False
        assert result["platform"] == "Windows"

    @patch("sql_assistant.service.installer._check_linux", return_value=False)
    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Linux")
    def test_status_not_installed_linux(self, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import get_status

        result = get_status()
        assert result["installed"] is False
        assert result["running"] is False
        assert result["platform"] == "Linux"

    @patch("sql_assistant.service.installer._check_windows", return_value=True)
    @patch("sql_assistant.service.installer._check_port", return_value=True)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    def test_status_installed_and_running(self, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import get_status

        result = get_status()
        assert result["installed"] is True
        assert result["running"] is True

    @patch("sql_assistant.service.installer._check_windows", return_value=True)
    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    def test_status_installed_not_running(self, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import get_status

        result = get_status()
        assert result["installed"] is True
        assert result["running"] is False

    @patch("sql_assistant.service.installer._check_windows", return_value=True)
    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    def test_install_already_installed(self, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import install

        result = install()
        assert result["success"] is True
        assert "已存在" in result["message"]

    @patch("sql_assistant.service.installer._check_linux", return_value=True)
    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Linux")
    @patch("sql_assistant.service.installer._install_linux", return_value="systemd 服务已存在；服务已启动")
    def test_install_already_installed_linux(self, mock_install, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import install

        result = install()
        assert result["success"] is True

    @patch("sql_assistant.service.installer._check_windows", return_value=False)
    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    @patch("sql_assistant.service.installer._install_windows", return_value="已创建计划任务；服务已在后台启动")
    def test_install_success(self, mock_install, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import install

        result = install()
        assert result["success"] is True
        assert "已创建" in result["message"]

    @patch("sql_assistant.service.installer._check_windows", return_value=True)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    @patch("sql_assistant.service.installer._uninstall_windows", return_value="已删除")
    def test_uninstall_success(self, mock_uninstall, mock_system, mock_check):
        from sql_assistant.service.installer import uninstall

        result = uninstall()
        assert result["success"] is True
        assert "已删除" in result["message"]

    @patch("sql_assistant.service.installer._check_windows", return_value=False)
    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    @patch("sql_assistant.service.installer._uninstall_windows", return_value="计划任务不存在")
    def test_uninstall_not_installed(self, mock_uninstall, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import uninstall

        result = uninstall()
        assert result["success"] is True

    @patch("sql_assistant.service.installer._check_linux", return_value=False)
    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Linux")
    @patch("sql_assistant.service.installer._uninstall_linux", return_value="systemd 服务不存在")
    def test_uninstall_not_installed_linux(self, mock_uninstall, mock_system, mock_port, mock_check):
        from sql_assistant.service.installer import uninstall

        result = uninstall()
        assert result["success"] is True

    def test_service_constants(self):
        from sql_assistant.service.installer import SERVICE_NAME, SERVICE_PORT

        assert SERVICE_NAME == "sql-assistant"
        assert isinstance(SERVICE_NAME, str)
        assert SERVICE_PORT == 5010

    def test_get_project_root(self):
        from sql_assistant.service.installer import _get_project_root

        root = _get_project_root()
        assert root.exists()
        assert (root / "pyproject.toml").exists()

    def test_get_python_path(self):
        from sql_assistant.service.installer import _get_python_path

        path = _get_python_path()
        assert path
        assert isinstance(path, str)
        assert "python" in path.lower()

    def test_get_entry_module(self):
        from sql_assistant.service.installer import _get_entry_module

        module = _get_entry_module()
        assert module == "sql_assistant.main"

    def test_find_pid_by_port(self):
        from sql_assistant.service.installer import _find_pid_by_port

        result = _find_pid_by_port(99999)
        assert result is None

    @patch("platform.system", return_value="Windows")
    def test_get_status_calls_windows(self, mock_system):
        from sql_assistant.service.installer import get_status

        result = get_status()
        assert result["platform"] == "Windows"
        assert "running" in result

    @patch("platform.system", return_value="Linux")
    def test_get_status_calls_linux(self, mock_system):
        from sql_assistant.service.installer import get_status

        result = get_status()
        assert result["platform"] == "Linux"
        assert "running" in result

    def test_systemd_user_dir_linux(self):
        from sql_assistant.service.installer import _get_systemd_user_dir

        result = _get_systemd_user_dir()
        assert isinstance(result, type(__import__("pathlib").Path()))
        parts = result.parts
        assert "systemd" in parts
        assert "user" in parts

    @patch("sql_assistant.service.installer._check_windows", side_effect=Exception("模拟错误"))
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    def test_get_status_handles_error(self, mock_system, mock_check):
        from sql_assistant.service.installer import get_status

        result = get_status()
        assert result["installed"] is False
        assert result["running"] is False
        assert "error" in result

    @patch("sql_assistant.service.installer._check_windows", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    @patch("sql_assistant.service.installer._install_windows", side_effect=Exception("模拟错误"))
    def test_install_handles_error(self, mock_install, mock_system, mock_check):
        from sql_assistant.service.installer import install

        result = install()
        assert result["success"] is False
        assert "error" in result

    @patch("sql_assistant.service.installer._check_windows", return_value=True)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    @patch("sql_assistant.service.installer._uninstall_windows", side_effect=Exception("模拟错误"))
    def test_uninstall_handles_error(self, mock_uninstall, mock_system, mock_check):
        from sql_assistant.service.installer import uninstall

        result = uninstall()
        assert result["success"] is False
        assert "error" in result

    def test_start_returns_dict(self):
        from sql_assistant.service.installer import start

        result = start()
        assert isinstance(result, dict)
        assert "success" in result
        assert "platform" in result
        assert "message" in result

    def test_stop_returns_dict(self):
        from sql_assistant.service.installer import stop

        result = stop()
        assert isinstance(result, dict)
        assert "success" in result
        assert "platform" in result
        assert "message" in result

    @patch("sql_assistant.service.installer._check_port", return_value=True)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    def test_start_already_running(self, mock_system, mock_port):
        from sql_assistant.service.installer import start

        result = start()
        assert result["success"] is True
        assert "已在运行" in result["message"]

    @patch("sql_assistant.service.installer._check_port", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    def test_stop_not_running(self, mock_system, mock_port):
        from sql_assistant.service.installer import stop

        result = stop()
        assert result["success"] is True
        assert "未在运行" in result["message"]

    @patch("sql_assistant.service.installer._check_windows", return_value=False)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    @patch("sql_assistant.service.installer._start_windows", side_effect=Exception("模拟错误"))
    def test_start_handles_error(self, mock_start, mock_system, mock_check):
        from sql_assistant.service.installer import start

        result = start()
        assert result["success"] is False
        assert "error" in result

    @patch("sql_assistant.service.installer._check_port", return_value=True)
    @patch("sql_assistant.service.installer.platform.system", return_value="Windows")
    @patch("sql_assistant.service.installer._stop_windows", side_effect=Exception("模拟错误"))
    def test_stop_handles_error(self, mock_stop, mock_system, mock_port):
        from sql_assistant.service.installer import stop

        result = stop()
        assert result["success"] is False
        assert "error" in result

    def test_check_port(self):
        from sql_assistant.service.installer import _check_port, SERVICE_PORT

        result = _check_port()
        assert isinstance(result, bool)
        assert SERVICE_PORT == 5010


class TestServiceAPIEndpoints:
    """服务 API 端点测试"""

    @patch("sql_assistant.api.service.get_status", return_value={
        "installed": False, "running": False, "platform": "Windows", "service_name": "sql-assistant"
    })
    def test_api_status_endpoint(self, mock_status):
        response = client.get("/api/service/status")
        assert response.status_code == 200
        data = response.json()
        assert data["installed"] is False
        assert data["running"] is False

    @patch("sql_assistant.service.installer.install", return_value={
        "success": True, "platform": "Windows", "message": "已创建"
    })
    def test_api_install_endpoint(self, mock_install):
        response = client.post("/api/service/install")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("sql_assistant.service.installer.uninstall", return_value={
        "success": True, "platform": "Windows", "message": "已删除"
    })
    def test_api_uninstall_endpoint(self, mock_uninstall):
        response = client.post("/api/service/uninstall")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("sql_assistant.service.installer.start", return_value={
        "success": True, "platform": "Windows", "message": "服务已启动"
    })
    def test_api_start_endpoint(self, mock_start):
        response = client.post("/api/service/start")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("sql_assistant.service.installer.stop", return_value={
        "success": True, "platform": "Windows", "message": "服务已停止"
    })
    def test_api_stop_endpoint(self, mock_stop):
        response = client.post("/api/service/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
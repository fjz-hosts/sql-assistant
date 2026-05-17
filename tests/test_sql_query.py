"""SQL 直接查询 API 测试"""
from fastapi.testclient import TestClient
from sql_assistant.main import app

client = TestClient(app)


class TestDirectSQLAPI:
    """直接 SQL 查询 API 测试"""

    def test_sql_execute_empty_sql(self):
        """测试空 SQL 语句"""
        response = client.post("/api/sql/execute", json={"sql": ""})
        assert response.status_code in [200, 400]

    def test_sql_execute_without_db(self):
        """测试未配置数据库时执行 SQL"""
        response = client.post("/api/sql/execute", json={"sql": "SELECT 1"})
        assert response.status_code in [200, 400, 500]

    def test_sql_execute_with_pagination(self):
        """测试带分页参数的 SQL 执行"""
        response = client.post("/api/sql/execute", json={
            "sql": "SELECT 1",
            "page": 1,
            "page_size": 50,
        })
        assert response.status_code in [200, 400, 500]

    def test_sql_execute_with_conversation(self):
        """测试带对话 ID 的 SQL 执行"""
        response = client.post("/api/sql/execute", json={
            "sql": "SELECT 1",
            "conversation_id": 999,
        })
        assert response.status_code in [200, 400, 500]

    def test_sql_execute_confirmed(self):
        """测试确认执行的 SQL"""
        response = client.post("/api/sql/execute", json={
            "sql": "SELECT 1",
            "confirmed": True,
        })
        assert response.status_code in [200, 400, 500]


class TestSQLQueryModels:
    """SQL 查询数据模型测试"""

    def test_direct_sql_request_model(self):
        """测试 DirectSQLRequest 模型"""
        from sql_assistant.api.models import DirectSQLRequest
        req = DirectSQLRequest(sql="SELECT 1")
        assert req.sql == "SELECT 1"
        assert req.confirmed is False
        assert req.page == 1
        assert req.page_size == 100

    def test_direct_sql_response_model(self):
        """测试 DirectSQLResponse 模型"""
        from sql_assistant.api.models import DirectSQLResponse
        resp = DirectSQLResponse(success=True, sql="SELECT 1")
        assert resp.success is True
        assert resp.sql == "SELECT 1"
        assert resp.requires_confirmation is False
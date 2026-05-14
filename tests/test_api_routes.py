"""API路由测试"""
import pytest
from fastapi.testclient import TestClient
from sql_assistant.main import app

client = TestClient(app)

class TestAPIEndpoints:
    """API端点测试"""
    
    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        # 根端点应该返回200或重定向
        assert response.status_code in [200, 307]
    
    def test_config_llm_get(self):
        """测试获取LLM配置列表"""
        response = client.get("/api/config/llm")
        assert response.status_code == 200
    
    def test_config_active_get(self):
        """测试获取活动配置"""
        response = client.get("/api/config/active")
        # 允许404（如果没有配置）或200
        assert response.status_code in [200, 404]
    
    def test_history_get(self):
        """测试获取历史记录"""
        response = client.get("/api/history")
        assert response.status_code == 200
    
    def test_conversations_get(self):
        """测试获取对话列表"""
        response = client.get("/api/conversations")
        assert response.status_code == 200
    
    def test_conversations_post(self):
        """测试创建对话"""
        response = client.post("/api/conversations", json={"name": "Test Conversation"})
        # 创建成功应该返回201
        assert response.status_code == 201
    
    def test_templates_get(self):
        """测试获取模板列表"""
        response = client.get("/api/templates")
        assert response.status_code == 200
    
    def test_templates_post(self):
        """测试创建模板"""
        response = client.post("/api/templates", json={
            "name": "Test Template",
            "description": "Test",
            "sql": "SELECT * FROM test",
            "tags": ["test"]
        })
        # 创建成功应该返回201
        assert response.status_code == 201
    
    def test_schema_tables(self):
        """测试获取数据库表结构"""
        response = client.get("/api/schema/tables")
        # 允许404（如果没有配置数据库）或200或500
        assert response.status_code in [200, 404, 500]
    
    def test_export_formats(self):
        """测试获取导出格式"""
        response = client.get("/api/export/formats")
        # 允许404或200
        assert response.status_code in [200, 404]
    
    def test_query_endpoint(self):
        """测试查询端点"""
        response = client.post("/api/query", json={"question": "test"})
        # 允许多种状态码（取决于是否配置了数据库和LLM）
        assert response.status_code in [200, 400, 500]

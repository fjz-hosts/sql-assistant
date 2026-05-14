"""模板管理模块测试"""
import pytest
import asyncio
from sql_assistant.database.templates import get_template_manager

class TestTemplateManager:
    """模板管理器测试"""
    
    def test_template_manager_init(self):
        """测试模板管理器初始化"""
        template_manager = get_template_manager()
        assert template_manager is not None
    
    def test_create_template(self):
        """测试创建模板"""
        template_manager = get_template_manager()
        template_id = asyncio.run(template_manager.create_template(
            name="Test Template",
            description="Test description",
            sql="SELECT * FROM users WHERE id = {{id}}",
            tags=["test", "users"]
        ))
        assert template_id is not None
        assert isinstance(template_id, int)
    
    def test_get_templates(self):
        """测试获取模板列表"""
        template_manager = get_template_manager()
        templates = asyncio.run(template_manager.get_templates())
        assert isinstance(templates, list)
    
    def test_get_template(self):
        """测试根据ID获取模板"""
        template_manager = get_template_manager()
        template_id = asyncio.run(template_manager.create_template(
            name="Get by ID Template",
            description="Test",
            sql="SELECT * FROM test",
            tags=["test"]
        ))
        template = asyncio.run(template_manager.get_template(template_id))
        assert template is not None
        assert template["id"] == template_id
        assert template["name"] == "Get by ID Template"
    
    def test_update_template(self):
        """测试更新模板"""
        template_manager = get_template_manager()
        template_id = asyncio.run(template_manager.create_template(
            name="Original Name",
            description="Original",
            sql="SELECT 1",
            tags=["original"]
        ))
        success = asyncio.run(template_manager.update_template(
            template_id,
            name="Updated Name",
            description="Updated",
            sql="SELECT 2",
            tags=["updated"]
        ))
        assert success is True
        template = asyncio.run(template_manager.get_template(template_id))
        assert template["name"] == "Updated Name"
        assert template["sql"] == "SELECT 2"
    
    def test_delete_template(self):
        """测试删除模板"""
        template_manager = get_template_manager()
        template_id = asyncio.run(template_manager.create_template(
            name="To Delete",
            description="Will be deleted",
            sql="SELECT 1",
            tags=["delete"]
        ))
        success = asyncio.run(template_manager.delete_template(template_id))
        assert success is True
        template = asyncio.run(template_manager.get_template(template_id))
        assert template is None
    
    def test_get_all_tags(self):
        """测试获取所有标签"""
        template_manager = get_template_manager()
        asyncio.run(template_manager.create_template(
            name="Tag Template",
            description="Test",
            sql="SELECT * FROM tags",
            tags=["tag1", "tag2"]
        ))
        tags = asyncio.run(template_manager.get_all_tags())
        assert isinstance(tags, list)
    
    def test_get_templates_with_tag(self):
        """测试按标签过滤模板"""
        template_manager = get_template_manager()
        asyncio.run(template_manager.create_template(
            name="Filter Template",
            description="Test",
            sql="SELECT * FROM filter",
            tags=["filter_tag"]
        ))
        templates = asyncio.run(template_manager.get_templates(tag="filter_tag"))
        assert isinstance(templates, list)
    
    def test_get_count(self):
        """测试获取模板数量"""
        template_manager = get_template_manager()
        count = asyncio.run(template_manager.get_count())
        assert isinstance(count, int)
        assert count >= 0

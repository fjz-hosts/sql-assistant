"""配置管理模块测试"""
import pytest
from sql_assistant.config import get_config_manager
from sql_assistant.settings import AppSettings, LLMProviderConfig, DatabaseConfig

class TestConfigManager:
    """配置管理器测试"""
    
    def test_config_manager_init(self):
        """测试配置管理器初始化"""
        config_manager = get_config_manager()
        assert config_manager is not None
    
    def test_get_settings(self):
        """测试获取设置"""
        config_manager = get_config_manager()
        settings = config_manager.get_settings()
        assert isinstance(settings, AppSettings)
    
    def test_get_llm_providers(self):
        """测试获取LLM提供商列表"""
        config_manager = get_config_manager()
        providers = config_manager.get_llm_providers()
        assert isinstance(providers, list)
    
    def test_get_databases(self):
        """测试获取数据库连接列表"""
        config_manager = get_config_manager()
        connections = config_manager.get_databases()
        assert isinstance(connections, list)
    
    def test_get_active_llm(self):
        """测试获取当前活动LLM"""
        config_manager = get_config_manager()
        active_llm = config_manager.get_active_llm()
        assert active_llm is None or isinstance(active_llm, LLMProviderConfig)
    
    def test_get_active_database(self):
        """测试获取当前活动数据库"""
        config_manager = get_config_manager()
        active_db = config_manager.get_active_database()
        assert active_db is None or isinstance(active_db, DatabaseConfig)
    
    def test_set_active_llm(self):
        """测试设置活动LLM配置名称 - 必须先添加配置"""
        config_manager = get_config_manager()
        # 先添加测试配置
        provider = LLMProviderConfig(
            name="test_llm_for_set",
            provider="deepseek",
            api_key="test_key",
            base_url="",
            model="test_model",
            enabled=True
        )
        config_manager.add_llm_provider(provider)
        
        # 保存原始值
        settings = config_manager.get_settings()
        original = settings.active_llm
        
        # 设置活动LLM
        success = config_manager.set_active_llm("test_llm_for_set")
        assert success is True
        settings = config_manager.get_settings()
        assert settings.active_llm == "test_llm_for_set"
        
        # 清理：恢复原始值并删除测试配置
        config_manager.set_active_llm(original if original else "")
        config_manager.remove_llm_provider("test_llm_for_set")
    
    def test_set_active_database(self):
        """测试设置活动数据库配置名称 - 必须先添加配置"""
        config_manager = get_config_manager()
        # 先添加测试配置
        db_config = DatabaseConfig(
            name="test_db_for_set",
            db_type="mysql",
            host="localhost",
            port=3306,
            user="test",
            password="test",
            database="test_db"
        )
        config_manager.add_database(db_config)
        
        # 保存原始值
        settings = config_manager.get_settings()
        original = settings.active_database
        
        # 设置活动数据库
        success = config_manager.set_active_database("test_db_for_set")
        assert success is True
        settings = config_manager.get_settings()
        assert settings.active_database == "test_db_for_set"
        
        # 清理：恢复原始值并删除测试配置
        config_manager.set_active_database(original if original else "")
        config_manager.remove_database("test_db_for_set")
    
    def test_add_and_remove_llm_provider(self):
        """测试添加和删除LLM提供商"""
        config_manager = get_config_manager()
        provider = LLMProviderConfig(
            name="test_provider",
            provider="deepseek",
            api_key="test_key",
            base_url="",
            model="test_model",
            enabled=True
        )
        config_manager.add_llm_provider(provider)
        assert config_manager.get_llm_provider("test_provider") is not None
        config_manager.remove_llm_provider("test_provider")
        assert config_manager.get_llm_provider("test_provider") is None
    
    def test_add_and_remove_database(self):
        """测试添加和删除数据库配置"""
        config_manager = get_config_manager()
        db_config = DatabaseConfig(
            name="test_db_config",
            db_type="mysql",
            host="localhost",
            port=3306,
            user="test",
            password="test",
            database="test_db"
        )
        config_manager.add_database(db_config)
        assert config_manager.get_database("test_db_config") is not None
        config_manager.remove_database("test_db_config")
        assert config_manager.get_database("test_db_config") is None
    
    def test_set_active_llm_nonexistent(self):
        """测试设置不存在的LLM配置返回False"""
        config_manager = get_config_manager()
        success = config_manager.set_active_llm("nonexistent_llm")
        assert success is False
    
    def test_set_active_database_nonexistent(self):
        """测试设置不存在的数据库配置返回False"""
        config_manager = get_config_manager()
        success = config_manager.set_active_database("nonexistent_db")
        assert success is False

"""配置管理 - YAML 文件读写"""

import os
import yaml
from pathlib import Path
from typing import Optional

from .settings import AppSettings, LLMProviderConfig, DatabaseConfig

DEFAULT_CONFIG_DIR = Path.home() / ".sql-assistant"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


class ConfigManager:
    """统一配置管理器"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        self._settings: AppSettings = AppSettings()
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """确保配置目录存在"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- 加载/保存 ----

    def load(self) -> AppSettings:
        """从 YAML 文件加载配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            self._settings = AppSettings(**data)
        except Exception:
            self._settings = AppSettings()
        return self._settings

    def save(self) -> None:
        """保存配置到 YAML 文件"""
        self._ensure_config_exists()
        data = self._settings.model_dump(
            exclude={"llm_providers": {"__all__": {"DEFAULT_BASE_URLS", "DEFAULT_MODELS"}},
                     "databases": {"__all__": {"DEFAULT_PORTS"}}}
        )
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def get_settings(self) -> AppSettings:
        return self._settings

    # ---- LLM Provider CRUD ----

    def get_llm_providers(self) -> list[LLMProviderConfig]:
        return self._settings.llm_providers

    def get_llm_provider(self, name: str) -> Optional[LLMProviderConfig]:
        for p in self._settings.llm_providers:
            if p.name == name:
                return p
        return None

    def add_llm_provider(self, config: LLMProviderConfig) -> None:
        existing = self.get_llm_provider(config.name)
        if existing:
            idx = self._settings.llm_providers.index(existing)
            self._settings.llm_providers[idx] = config
        else:
            self._settings.llm_providers.append(config)
        self.save()

    def remove_llm_provider(self, name: str) -> bool:
        provider = self.get_llm_provider(name)
        if provider:
            self._settings.llm_providers.remove(provider)
            if self._settings.active_llm == name:
                self._settings.active_llm = ""
            self.save()
            return True
        return False

    def get_active_llm(self) -> Optional[LLMProviderConfig]:
        return self.get_llm_provider(self._settings.active_llm)

    def set_active_llm(self, name: str) -> bool:
        if self.get_llm_provider(name):
            self._settings.active_llm = name
            self.save()
            return True
        return False

    # ---- Database CRUD ----

    def get_databases(self) -> list[DatabaseConfig]:
        return self._settings.databases

    def get_database(self, name: str) -> Optional[DatabaseConfig]:
        for db in self._settings.databases:
            if db.name == name:
                return db
        return None

    def add_database(self, config: DatabaseConfig) -> None:
        existing = self.get_database(config.name)
        if existing:
            idx = self._settings.databases.index(existing)
            self._settings.databases[idx] = config
        else:
            self._settings.databases.append(config)
        self.save()

    def remove_database(self, name: str) -> bool:
        db = self.get_database(name)
        if db:
            self._settings.databases.remove(db)
            if self._settings.active_database == name:
                self._settings.active_database = ""
            self.save()
            return True
        return False

    def get_active_database(self) -> Optional[DatabaseConfig]:
        return self.get_database(self._settings.active_database)

    def set_active_database(self, name: str) -> bool:
        if self.get_database(name):
            self._settings.active_database = name
            self.save()
            return True
        return False


# 全局单例
_config_instance: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局 ConfigManager 单例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
        _config_instance.load()
    return _config_instance

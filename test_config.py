"""Config recursion test"""
import tempfile, os
from sql_assistant.config import ConfigManager
from sql_assistant.settings import LLMProviderConfig

tmp = os.path.join(tempfile.gettempdir(), "test_cfg3.yaml")
if os.path.exists(tmp):
    os.remove(tmp)

cm = ConfigManager(tmp)
print("ConfigManager created - no recursion!")

cm.add_llm_provider(LLMProviderConfig(name="Test3", provider="deepseek", api_key="sk-test3"))
configs = cm.get_llm_providers()
print(f"LLM configs: {len(configs)}, name={configs[0].name}")

# Test serialize
cm.save()
with open(tmp, "r") as f:
    content = f.read()
print(f"Config file written: {len(content)} bytes")
assert "DEFAULT_BASE_URLS" not in content, "ClassVar not excluded!"
assert "DEFAULT_MODELS" not in content, "ClassVar not excluded!"
print("All assertions passed!")

os.remove(tmp)
print("SUCCESS")

"""键盘快捷键 API 模块测试"""
from fastapi.testclient import TestClient
from sql_assistant.main import app

client = TestClient(app)


class TestShortcutsAPI:
    """快捷键 API 测试"""

    def test_get_shortcuts(self):
        response = client.get("/api/shortcuts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "sendQuery" in data
        assert "newConversation" in data
        assert "focusInput" in data
        assert "closePanel" in data

    def test_get_shortcuts_structure(self):
        response = client.get("/api/shortcuts")
        data = response.json()
        for action_id, shortcut in data.items():
            assert "keys" in shortcut
            assert isinstance(shortcut["keys"], list)
            assert len(shortcut["keys"]) > 0
            assert "description" in shortcut
            assert "category" in shortcut
            assert "action" in shortcut

    def test_get_default_shortcuts(self):
        response = client.get("/api/shortcuts/defaults")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_update_shortcut_valid(self):
        response = client.put("/api/shortcuts/sendQuery", json={"keys": ["Ctrl", "Shift", "Enter"]})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_shortcut_invalid_action(self):
        response = client.put("/api/shortcuts/nonexistent", json={"keys": ["Ctrl", "X"]})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_update_shortcut_invalid_modifier(self):
        response = client.put("/api/shortcuts/sendQuery", json={"keys": ["Win", "Enter"]})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_update_shortcut_conflict(self):
        response = client.put(
            "/api/shortcuts/sendQuery",
            json={"keys": ["Ctrl", "N"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "冲突" in data.get("error", "")

    def test_update_shortcut_invalid_key(self):
        response = client.put("/api/shortcuts/sendQuery", json={"keys": ["Ctrl", "InvalidKeyLong"]})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestShortcutDefaults:
    """快捷键默认值测试"""

    def test_all_defaults_have_required_fields(self):
        from sql_assistant.api.shortcuts import DEFAULT_SHORTCUTS

        required_fields = {"keys", "description", "category", "action"}
        for action_id, shortcut in DEFAULT_SHORTCUTS.items():
            assert required_fields.issubset(
                shortcut.keys()
            ), f"{action_id} missing fields: {required_fields - set(shortcut.keys())}"

    def test_no_duplicate_default_shortcuts(self):
        from sql_assistant.api.shortcuts import DEFAULT_SHORTCUTS

        key_combos = set()
        for shortcut in DEFAULT_SHORTCUTS.values():
            combo = "+".join(shortcut["keys"])
            assert combo not in key_combos, f"Duplicate key combo: {combo}"
            key_combos.add(combo)

    def test_all_default_keys_valid(self):
        from sql_assistant.api.shortcuts import DEFAULT_SHORTCUTS

        valid_single_keys = {
            "Enter", "Escape", "Space", "Tab", "Delete",
            "Up", "Down", "Left", "Right",
        }
        for shortcut in DEFAULT_SHORTCUTS.values():
            keys = shortcut["keys"]
            main_key = keys[-1]
            if main_key not in valid_single_keys:
                assert len(main_key) <= 3, f"Invalid main key: {main_key}"

    def test_shortcuts_count(self):
        from sql_assistant.api.shortcuts import DEFAULT_SHORTCUTS

        assert len(DEFAULT_SHORTCUTS) == 18
"""键盘快捷键管理 API"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/shortcuts", tags=["shortcuts"])

DEFAULT_SHORTCUTS = {
    "sendQuery": {
        "keys": ["Ctrl", "Enter"],
        "description": "发送查询",
        "category": "查询",
        "action": "sendQuery",
    },
    "newConversation": {
        "keys": ["Ctrl", "N"],
        "description": "新建对话",
        "category": "对话",
        "action": "newConversation",
    },
    "focusInput": {
        "keys": ["Ctrl", "K"],
        "description": "聚焦输入框",
        "category": "导航",
        "action": "focusInput",
    },
    "toggleTemplates": {
        "keys": ["Ctrl", "/"],
        "description": "切换SQL模板面板",
        "category": "面板",
        "action": "toggleTemplates",
    },
    "toggleExplain": {
        "keys": ["Ctrl", "Shift", "E"],
        "description": "切换执行计划面板",
        "category": "面板",
        "action": "toggleExplain",
    },
    "toggleHealth": {
        "keys": ["Ctrl", "Shift", "H"],
        "description": "切换健康检查面板",
        "category": "面板",
        "action": "toggleHealth",
    },
    "toggleInsights": {
        "keys": ["Ctrl", "Shift", "I"],
        "description": "切换数据洞察面板",
        "category": "面板",
        "action": "toggleInsights",
    },
    "openSettings": {
        "keys": ["Ctrl", ","],
        "description": "打开设置",
        "category": "导航",
        "action": "openSettings",
    },
    "toggleTheme": {
        "keys": ["Ctrl", "Shift", "D"],
        "description": "切换主题",
        "category": "外观",
        "action": "toggleTheme",
    },
    "closePanel": {
        "keys": ["Escape"],
        "description": "关闭面板/弹窗",
        "category": "导航",
        "action": "closePanel",
    },
    "refreshSchema": {
        "keys": ["Ctrl", "Shift", "R"],
        "description": "刷新数据库 Schema",
        "category": "查询",
        "action": "refreshSchema",
    },
    "switchQueryMode": {
        "keys": ["Ctrl", "Shift", "M"],
        "description": "切换查询模式 (NL/SQL)",
        "category": "查询",
        "action": "switchQueryMode",
    },
    "clearChat": {
        "keys": ["Ctrl", "L"],
        "description": "清空聊天区域",
        "category": "对话",
        "action": "clearChat",
    },
    "toggleSidebar": {
        "keys": ["Ctrl", "B"],
        "description": "切换侧边栏显示",
        "category": "外观",
        "action": "toggleSidebar",
    },
    "copyLastSQL": {
        "keys": ["Ctrl", "Shift", "C"],
        "description": "复制最后一条 SQL",
        "category": "查询",
        "action": "copyLastSQL",
    },
    "deleteConversation": {
        "keys": ["Ctrl", "Shift", "Delete"],
        "description": "删除当前对话",
        "category": "对话",
        "action": "deleteConversation",
    },
    "saveAsTemplate": {
        "keys": ["Ctrl", "S"],
        "description": "保存当前SQL为模板",
        "category": "查询",
        "action": "saveAsTemplate",
    },
    "toggleShortcutsPanel": {
        "keys": ["?"],
        "description": "打开快捷键面板",
        "category": "导航",
        "action": "toggleShortcutsPanel",
    },
    "installAsService": {
        "keys": ["Ctrl", "Shift", "S"],
        "description": "安装/卸载开机自启服务",
        "category": "导航",
        "action": "installAsService",
    },
}


class ShortcutUpdate(BaseModel):
    keys: list[str]


@router.get("")
async def get_shortcuts():
    return DEFAULT_SHORTCUTS


@router.get("/defaults")
async def get_default_shortcuts():
    return DEFAULT_SHORTCUTS


@router.put("/{action_id}")
async def update_shortcut(action_id: str, data: ShortcutUpdate):
    if action_id not in DEFAULT_SHORTCUTS:
        return {"error": "未知的快捷键操作", "success": False}

    valid_modifiers = {"Ctrl", "Shift", "Alt"}
    for key in data.keys[:-1]:
        if key not in valid_modifiers:
            return {"error": f"无效的修饰键: {key}", "success": False}

    main_key = data.keys[-1]
    if len(main_key) > 3 and main_key not in (
        "Enter", "Escape", "Space", "Tab", "Delete",
        "Up", "Down", "Left", "Right",
    ):
        return {"error": f"无效的快捷键: {main_key}", "success": False}

    for existing_id, shortcut in DEFAULT_SHORTCUTS.items():
        if existing_id != action_id and shortcut["keys"] == data.keys:
            return {
                "error": f"快捷键冲突: 已被「{shortcut['description']}」使用",
                "success": False,
            }

    return {"success": True, "keys": data.keys}
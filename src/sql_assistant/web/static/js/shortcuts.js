/**
 * Keyboard Shortcuts Manager Module
 * Manages global keyboard shortcuts with customizable key bindings
 */

const ShortcutManager = {
    STORAGE_KEY: 'sql_assistant_shortcuts',
    enabled: true,
    shortcuts: {},

    DEFAULT_SHORTCUTS: {
        sendQuery: {
            keys: ['Ctrl', 'Enter'],
            description: '发送查询',
            category: '查询',
            action: 'sendQuery',
        },
        newConversation: {
            keys: ['Ctrl', 'N'],
            description: '新建对话',
            category: '对话',
            action: 'newConversation',
        },
        focusInput: {
            keys: ['Ctrl', 'K'],
            description: '聚焦输入框',
            category: '导航',
            action: 'focusInput',
        },
        toggleTemplates: {
            keys: ['Ctrl', '/'],
            description: '切换SQL模板面板',
            category: '面板',
            action: 'toggleTemplates',
        },
        toggleExplain: {
            keys: ['Ctrl', 'Shift', 'E'],
            description: '切换执行计划面板',
            category: '面板',
            action: 'toggleExplain',
        },
        toggleHealth: {
            keys: ['Ctrl', 'Shift', 'H'],
            description: '切换健康检查面板',
            category: '面板',
            action: 'toggleHealth',
        },
        toggleInsights: {
            keys: ['Ctrl', 'Shift', 'I'],
            description: '切换数据洞察面板',
            category: '面板',
            action: 'toggleInsights',
        },
        openSettings: {
            keys: ['Ctrl', ','],
            description: '打开设置',
            category: '导航',
            action: 'openSettings',
        },
        toggleTheme: {
            keys: ['Ctrl', 'Shift', 'D'],
            description: '切换主题',
            category: '外观',
            action: 'toggleTheme',
        },
        closePanel: {
            keys: ['Escape'],
            description: '关闭面板/弹窗',
            category: '导航',
            action: 'closePanel',
        },
        refreshSchema: {
            keys: ['Ctrl', 'Shift', 'R'],
            description: '刷新数据库 Schema',
            category: '查询',
            action: 'refreshSchema',
        },
        switchQueryMode: {
            keys: ['Ctrl', 'Shift', 'M'],
            description: '切换查询模式 (NL/SQL)',
            category: '查询',
            action: 'switchQueryMode',
        },
        clearChat: {
            keys: ['Ctrl', 'L'],
            description: '清空聊天区域',
            category: '对话',
            action: 'clearChat',
        },
        toggleSidebar: {
            keys: ['Ctrl', 'B'],
            description: '切换侧边栏显示',
            category: '外观',
            action: 'toggleSidebar',
        },
        copyLastSQL: {
            keys: ['Ctrl', 'Shift', 'C'],
            description: '复制最后一条 SQL',
            category: '查询',
            action: 'copyLastSQL',
        },
        deleteConversation: {
            keys: ['Ctrl', 'Shift', 'Delete'],
            description: '删除当前对话',
            category: '对话',
            action: 'deleteConversation',
        },
        saveAsTemplate: {
            keys: ['Ctrl', 'S'],
            description: '保存当前SQL为模板',
            category: '查询',
            action: 'saveAsTemplate',
        },
        toggleShortcutsPanel: {
            keys: ['?'],
            description: '打开快捷键面板',
            category: '导航',
            action: 'toggleShortcutsPanel',
        },
        installAsService: {
            keys: ['Ctrl', 'Shift', 'S'],
            description: '安装/卸载开机自启服务',
            category: '导航',
            action: 'installAsService',
        },
    },

    init() {
        this.loadShortcuts();
        this.bindEvents();
    },

    loadShortcuts() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (saved) {
                const parsed = JSON.parse(saved);
                this.shortcuts = { ...this.DEFAULT_SHORTCUTS, ...parsed };
            } else {
                this.shortcuts = JSON.parse(JSON.stringify(this.DEFAULT_SHORTCUTS));
            }
        } catch {
            this.shortcuts = JSON.parse(JSON.stringify(this.DEFAULT_SHORTCUTS));
        }
    },

    saveShortcuts() {
        const customShortcuts = {};
        for (const [id, shortcut] of Object.entries(this.shortcuts)) {
            if (this.DEFAULT_SHORTCUTS[id]) {
                const defaultKeys = this.DEFAULT_SHORTCUTS[id].keys.join('+');
                const currentKeys = shortcut.keys.join('+');
                if (defaultKeys !== currentKeys) {
                    customShortcuts[id] = shortcut;
                }
            }
        }
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(customShortcuts));
    },

    resetShortcuts() {
        this.shortcuts = JSON.parse(JSON.stringify(this.DEFAULT_SHORTCUTS));
        localStorage.removeItem(this.STORAGE_KEY);
        this.saveShortcuts();
    },

    bindEvents() {
        document.addEventListener('keydown', (e) => {
            if (!this.enabled) return;
            if (this.isInputFocused() && !this.isModifierKey(e.key)) {
                return;
            }
            this.handleKeyEvent(e);
        });
    },

    isInputFocused() {
        const tag = document.activeElement?.tagName?.toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') {
            return true;
        }
        return document.activeElement?.isContentEditable;
    },

    isModifierKey(key) {
        return ['Control', 'Shift', 'Alt', 'Meta', 'Escape'].includes(key);
    },

    getPressedModifiers(e) {
        const modifiers = [];
        if (e.ctrlKey || e.metaKey) modifiers.push('Ctrl');
        if (e.shiftKey) modifiers.push('Shift');
        if (e.altKey) modifiers.push('Alt');
        return modifiers;
    },

    normalizeKey(key) {
        const keyMap = {
            ',': ',',
            '.': '.',
            '/': '/',
            '?': '?',
            '\\': '\\',
            '-': '-',
            '=': '=',
            'ArrowUp': 'Up',
            'ArrowDown': 'Down',
            'ArrowLeft': 'Left',
            'ArrowRight': 'Right',
            'Escape': 'Escape',
            'Enter': 'Enter',
            'Tab': 'Tab',
            'Delete': 'Delete',
            ' ': 'Space',
        };
        if (keyMap[key]) return keyMap[key];
        if (key.length === 1) return key.toUpperCase();
        return key;
    },

    buildKeyCombo(e) {
        const modifiers = this.getPressedModifiers(e);
        const key = this.normalizeKey(e.key);
        if (this.isModifierKey(e.key) && key !== 'Escape') {
            return null;
        }
        const combo = [...modifiers, key];
        return combo.join('+');
    },

    handleKeyEvent(e) {
        const pressed = this.buildKeyCombo(e);
        if (!pressed) return;

        for (const [actionId, shortcut] of Object.entries(this.shortcuts)) {
            if (shortcut.keys.join('+') === pressed) {
                e.preventDefault();
                e.stopPropagation();
                this.executeAction(actionId);
                return;
            }
        }
    },

    executeAction(actionId) {
        switch (actionId) {
            case 'sendQuery': {
                const queryInput = document.getElementById('query-input');
                const btnSend = document.getElementById('btn-send');
                if (queryInput && !btnSend?.disabled) {
                    if (typeof sendQuery === 'function') {
                        sendQuery(queryInput.value);
                    }
                }
                break;
            }
            case 'newConversation': {
                if (typeof createNewConversation === 'function') {
                    createNewConversation();
                }
                break;
            }
            case 'focusInput': {
                const queryInput = document.getElementById('query-input');
                if (queryInput) {
                    queryInput.focus();
                    queryInput.select();
                }
                break;
            }
            case 'toggleTemplates': {
                if (typeof templateManager !== 'undefined' && templateManager.togglePanel) {
                    templateManager.togglePanel();
                }
                break;
            }
            case 'toggleExplain': {
                if (typeof explainManager !== 'undefined' && explainManager.togglePanel) {
                    explainManager.togglePanel();
                }
                break;
            }
            case 'toggleHealth': {
                if (typeof healthManager !== 'undefined' && healthManager.togglePanel) {
                    healthManager.togglePanel();
                }
                break;
            }
            case 'toggleInsights': {
                if (typeof insightsManager !== 'undefined' && insightsManager.togglePanel) {
                    insightsManager.togglePanel();
                }
                break;
            }
            case 'openSettings': {
                if (typeof openSettings === 'function') {
                    openSettings();
                }
                break;
            }
            case 'toggleTheme': {
                if (typeof ThemeManager !== 'undefined') {
                    ThemeManager.toggle();
                }
                break;
            }
            case 'closePanel': {
                this.closeActivePanel();
                break;
            }
            case 'refreshSchema': {
                if (typeof refreshSchema === 'function') {
                    refreshSchema();
                }
                break;
            }
            case 'switchQueryMode': {
                if (typeof switchQueryMode === 'function') {
                    const currentMode = window.state?.queryMode || 'nl';
                    switchQueryMode(currentMode === 'nl' ? 'sql' : 'nl');
                }
                break;
            }
            case 'clearChat': {
                if (typeof clearChatMessages === 'function') {
                    clearChatMessages();
                }
                break;
            }
            case 'toggleSidebar': {
                const sidebar = document.getElementById('sidebar');
                if (sidebar) {
                    sidebar.classList.toggle('collapsed');
                }
                break;
            }
            case 'copyLastSQL': {
                const sqlBlocks = document.querySelectorAll('.sql-block code');
                if (sqlBlocks.length > 0) {
                    const lastSQL = sqlBlocks[sqlBlocks.length - 1].textContent;
                    navigator.clipboard.writeText(lastSQL).then(() => {
                        if (typeof showToast === 'function') {
                            showToast('已复制 SQL 到剪贴板', 'success');
                        }
                    }).catch(() => {});
                } else {
                    if (typeof showToast === 'function') {
                        showToast('没有可复制的 SQL', 'warning');
                    }
                }
                break;
            }
            case 'deleteConversation': {
                if (typeof deleteConversation === 'function' && window.state?.currentConversationId) {
                    if (confirm('确定删除当前对话吗？')) {
                        deleteConversation(window.state.currentConversationId);
                    }
                }
                break;
            }
            case 'saveAsTemplate': {
                if (typeof templateManager !== 'undefined' && templateManager.createFromCurrentSQL) {
                    templateManager.createFromCurrentSQL();
                }
                break;
            }
            case 'toggleShortcutsPanel': {
                this.togglePanel();
                break;
            }
            case 'installAsService': {
                if (typeof ServiceManager !== 'undefined' && ServiceManager.toggle) {
                    ServiceManager.toggle();
                }
                break;
            }
        }
    },

    closeActivePanel() {
        const shortcutsPanel = document.getElementById('shortcuts-panel');
        if (shortcutsPanel?.classList.contains('active')) {
            this.closePanel();
            return;
        }

        const settingsModal = document.getElementById('settings-modal');
        if (settingsModal?.classList.contains('active')) {
            if (typeof closeSettings === 'function') {
                closeSettings();
                return;
            }
        }

        if (typeof hideSQLConfirmDialog === 'function') {
            const sqlConfirm = document.getElementById('sql-confirm-modal');
            if (sqlConfirm?.style.display !== 'none' && sqlConfirm?.classList.contains('active')) {
                hideSQLConfirmDialog();
                return;
            }
        }

        const panels = [
            { el: 'template-panel', close: () => templateManager?.closePanel?.() },
            { el: 'explain-panel', close: () => explainManager?.closePanel?.() },
            { el: 'health-panel', close: () => healthManager?.closePanel?.() },
            { el: 'insights-panel', close: () => insightsManager?.closePanel?.() },
        ];

        for (const panel of panels) {
            const panelEl = document.getElementById(panel.el);
            if (panelEl?.classList.contains('active')) {
                if (panel.close) panel.close();
                return;
            }
        }
    },

    updateShortcut(actionId, newKeys) {
        if (!this.shortcuts[actionId]) return false;

        for (const [id, shortcut] of Object.entries(this.shortcuts)) {
            if (id !== actionId && shortcut.keys.join('+') === newKeys.join('+')) {
                return false;
            }
        }

        this.shortcuts[actionId].keys = newKeys;
        this.saveShortcuts();
        return true;
    },

    getShortcutsByCategory() {
        const categories = {};
        for (const [id, shortcut] of Object.entries(this.shortcuts)) {
            const cat = shortcut.category || '其他';
            if (!categories[cat]) {
                categories[cat] = [];
            }
            categories[cat].push({ id, ...shortcut });
        }
        return categories;
    },

    getDisplayKey(key) {
        const displayMap = {
            'Ctrl': '⌘',
            'Shift': '⇧',
            'Alt': '⌥',
            'Enter': '↵',
            'Escape': 'Esc',
            'Space': '␣',
            'Up': '↑',
            'Down': '↓',
            'Left': '←',
            'Right': '→',
            'Tab': '⇥',
            'Delete': 'Del',
        };
        return displayMap[key] || key;
    },

    getShortcutDisplay(keys) {
        return keys.map(k => this.getDisplayKey(k)).join('');
    },

    getRawShortcutDisplay(keys) {
        return keys.join('+');
    },

    getConflicts(newKeys, excludeActionId) {
        const conflicts = [];
        for (const [id, shortcut] of Object.entries(this.shortcuts)) {
            if (id !== excludeActionId && shortcut.keys.join('+') === newKeys.join('+')) {
                conflicts.push({ id, ...shortcut });
            }
        }
        return conflicts;
    },

    setEnabled(enabled) {
        this.enabled = enabled;
    },

    isEnabled() {
        return this.enabled;
    },

    bindPanelEvents() {
        const shortcutsBtn = document.getElementById('btn-shortcuts');
        const closeBtn = document.getElementById('btn-close-shortcuts');
        const overlay = document.getElementById('shortcuts-overlay');
        const panel = document.getElementById('shortcuts-panel');
        const resetBtn = document.getElementById('btn-reset-shortcuts');
        const enabledCheckbox = document.getElementById('shortcuts-enabled');

        if (shortcutsBtn) {
            shortcutsBtn.addEventListener('click', () => this.openPanel());
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }

        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) this.closePanel();
            });
        }

        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetShortcuts();
                this.renderPanel();
                if (typeof showToast === 'function') {
                    showToast('快捷键已恢复默认', 'success');
                }
            });
        }

        if (enabledCheckbox) {
            enabledCheckbox.checked = this.enabled;
            enabledCheckbox.addEventListener('change', (e) => {
                this.setEnabled(e.target.checked);
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel?.classList.contains('active')) {
                e.stopPropagation();
                this.closePanel();
            }
        });
    },

    openPanel() {
        const overlay = document.getElementById('shortcuts-overlay');
        const panel = document.getElementById('shortcuts-panel');
        if (overlay) overlay.classList.add('active');
        if (panel) panel.classList.add('active');
        this.renderPanel();
    },

    closePanel() {
        const overlay = document.getElementById('shortcuts-overlay');
        const panel = document.getElementById('shortcuts-panel');
        if (overlay) overlay.classList.remove('active');
        if (panel) panel.classList.remove('active');
        this.cancelRecording();
    },

    togglePanel() {
        const panel = document.getElementById('shortcuts-panel');
        if (panel?.classList.contains('active')) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    },

    renderPanel() {
        const body = document.getElementById('shortcuts-panel-body');
        if (!body) return;

        const categories = this.getShortcutsByCategory();
        const categoryOrder = ['查询', '导航', '面板', '对话', '外观'];

        let html = '';
        for (const cat of categoryOrder) {
            if (!categories[cat] || categories[cat].length === 0) continue;
            html += this.renderCategory(cat, categories[cat]);
            delete categories[cat];
        }

        for (const [cat, shortcuts] of Object.entries(categories)) {
            if (shortcuts.length === 0) continue;
            html += this.renderCategory(cat, shortcuts);
        }

        body.innerHTML = html;
    },

    renderCategory(categoryName, shortcuts) {
        let html = `<div class="shortcuts-category">`;
        html += `<div class="shortcuts-category-title">${this.escapeHtml(categoryName)}</div>`;

        for (const shortcut of shortcuts) {
            html += `
                <div class="shortcut-item" data-action="${this.escapeHtml(shortcut.id)}">
                    <div class="shortcut-info">
                        <span class="shortcut-name">${this.escapeHtml(shortcut.description)}</span>
                        <span class="shortcut-desc">${this.escapeHtml(shortcut.id)}</span>
                    </div>
                    <div class="shortcut-keys" id="keys-${this.escapeHtml(shortcut.id)}">
                        ${this.renderKeys(shortcut.keys)}
                    </div>
                    <div class="shortcut-actions">
                        <button class="shortcut-action-btn" onclick="ShortcutManager.startRecording('${this.escapeHtml(shortcut.id)}')" title="修改快捷键">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                        </button>
                        <button class="shortcut-action-btn reset-btn" onclick="ShortcutManager.resetSingleShortcut('${this.escapeHtml(shortcut.id)}')" title="恢复默认">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/></svg>
                        </button>
                    </div>
                </div>`;
        }

        html += '</div>';
        return html;
    },

    renderKeys(keys) {
        return keys.map(k => `<span class="shortcut-key">${this.escapeHtml(this.getDisplayKey(k))}</span>`).join('<span class="shortcut-plus">+</span>');
    },

    startRecording(actionId) {
        this.cancelRecording();

        const shortcut = this.shortcuts[actionId];
        if (!shortcut) return;

        this._recordingAction = actionId;
        this._recordingKeys = [];
        this._recordingHandler = this._handleRecording.bind(this);

        const item = document.querySelector(`.shortcut-item[data-action="${actionId}"]`);
        if (item) item.classList.add('editing');

        const keysContainer = document.getElementById(`keys-${actionId}`);
        if (keysContainer) {
            keysContainer.innerHTML = '<span class="shortcut-key recording">...</span>';
        }

        const hint = document.getElementById('recording-hint');
        if (hint) hint.classList.add('active');

        document.addEventListener('keydown', this._recordingHandler, true);
    },

    _handleRecording(e) {
        e.preventDefault();
        e.stopPropagation();

        if (e.key === 'Escape') {
            this.cancelRecording();
            return;
        }

        const modifiers = [];
        if (e.ctrlKey || e.metaKey) modifiers.push('Ctrl');
        if (e.shiftKey) modifiers.push('Shift');
        if (e.altKey) modifiers.push('Alt');

        if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) return;

        const normalizedKey = this.normalizeKey(e.key);
        const newKeys = [...modifiers, normalizedKey];

        if (newKeys.length === 0) return;

        const conflicts = this.getConflicts(newKeys, this._recordingAction);
        if (conflicts.length > 0) {
            if (typeof showToast === 'function') {
                showToast(`快捷键冲突: 已被「${conflicts[0].description}」使用`, 'warning');
            }
            this.cancelRecording();
            return;
        }

        const success = this.updateShortcut(this._recordingAction, newKeys);
        if (success) {
            this.cancelRecording();
            this.renderPanel();
            if (typeof showToast === 'function') {
                showToast('快捷键已更新', 'success');
            }
        }
    },

    cancelRecording() {
        if (this._recordingHandler) {
            document.removeEventListener('keydown', this._recordingHandler, true);
            this._recordingHandler = null;
        }

        this._recordingAction = null;
        this._recordingKeys = [];

        const hint = document.getElementById('recording-hint');
        if (hint) hint.classList.remove('active');

        document.querySelectorAll('.shortcut-item.editing').forEach(el => {
            el.classList.remove('editing');
        });
    },

    resetSingleShortcut(actionId) {
        const defaults = this.DEFAULT_SHORTCUTS[actionId];
        if (!defaults) return;

        this.shortcuts[actionId] = { ...defaults };
        this.saveShortcuts();
        this.renderPanel();

        if (typeof showToast === 'function') {
            showToast(`「${defaults.description}」快捷键已恢复默认`, 'success');
        }
    },

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
};

window.ShortcutManager = ShortcutManager;
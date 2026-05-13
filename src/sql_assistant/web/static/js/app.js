/**
 * SQL 智能助手 - 主入口文件
 * 负责初始化和事件绑定
 */

// ============================================================
// Event Listeners
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    // 初始化主题管理器
    ThemeManager.init();
    ColorThemeManager.init();

    // 加载流式响应设置
    state.streamingEnabled = false;

    // 加载设置和对话列表
    loadSettings().then(() => {
        if (state.activeDB) refreshSchema();
    });
    loadConversations();

    // Query form
    dom.queryForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendQuery(dom.queryInput.value);
    });

    dom.queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuery(dom.queryInput.value);
        }
    });

    // Auto-resize textarea
    dom.queryInput.addEventListener('input', () => {
        dom.queryInput.style.height = 'auto';
        dom.queryInput.style.height = Math.min(dom.queryInput.scrollHeight, 120) + 'px';
    });

    // Example tags
    document.querySelectorAll('.example-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            const question = tag.dataset.question;
            dom.queryInput.value = question;
            sendQuery(question);
        });
    });

    // Settings
    $('btn-settings').addEventListener('click', openSettings);
    $('btn-close-modal').addEventListener('click', closeSettings);
    dom.settingsModal.addEventListener('click', (e) => {
        if (e.target === dom.settingsModal) closeSettings();
    });

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // LLM form
    $('btn-add-llm').addEventListener('click', () => {
        state.editingLLM = null;
        $('llm-form-title').textContent = '添加 LLM 提供商';
        $('llm-api-key').placeholder = 'sk-...';
        $('llm-name').value = '';
        $('llm-provider').value = 'deepseek';
        $('llm-api-key').value = '';
        $('llm-base-url').value = '';
        updateModelSelect('deepseek');
        updateLLMFormByProvider('deepseek');
        dom.llmForm.style.display = 'block';
        dom.llmForm.scrollIntoView({ behavior: 'smooth' });
    });
    
    // Provider change - update model list and form fields
    $('llm-provider').addEventListener('change', async (e) => {
        const provider = e.target.value;
        if (!state.llmModels[provider] || state.llmModels[provider].length === 0) {
            await loadLLMModels(provider);
        }
        updateModelSelect(provider);
        updateLLMFormByProvider(provider);
    });

    // LLM form events
    $('btn-save-llm').addEventListener('click', saveLLM);
    $('btn-test-llm').addEventListener('click', testNewLLM);

    // DB form
    $('btn-add-db').addEventListener('click', () => {
        state.editingDB = null;
        $('db-form-title').textContent = '添加数据库连接';
        $('db-password').placeholder = '数据库密码';
        dom.dbForm.style.display = 'block';
        dom.dbForm.scrollIntoView({ behavior: 'smooth' });
    });
    $('btn-save-db').addEventListener('click', saveDB);
    $('btn-cancel-db').addEventListener('click', cancelDBForm);
    $('btn-test-db').addEventListener('click', testNewDB);

    // New conversation
    $('btn-new-chat').addEventListener('click', createNewConversation);

    // Refresh schema button
    const refreshBtn = $('btn-refresh-schema');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshSchema);
    }

    // Backup
    const backupBtn = $('btn-create-backup');
    if (backupBtn) {
        backupBtn.addEventListener('click', createBackup);
    }

    const confirmRestoreBtn = $('btn-confirm-restore');
    if (confirmRestoreBtn) {
        confirmRestoreBtn.addEventListener('click', confirmRestore);
    }

    // Load backup list when backup tab is shown
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.tab === 'backup') {
                loadBackupList();
            }
        });
    });

    // SQL 确认对话框
    $('btn-close-sql-confirm').addEventListener('click', hideSQLConfirmDialog);
    $('btn-cancel-sql').addEventListener('click', hideSQLConfirmDialog);
    $('btn-confirm-sql').addEventListener('click', confirmAndExecuteSQL);
    
    $('sql-confirm-modal').addEventListener('click', (e) => {
        if (e.target === $('sql-confirm-modal')) hideSQLConfirmDialog();
    });
    
    $('btn-copy-confirm-sql').addEventListener('click', () => {
        const code = document.getElementById('sql-confirm-code').textContent;
        navigator.clipboard.writeText(code).then(() => {
            showToast('已复制到剪贴板', 'success');
        });
    });

    // Keyboard shortcut: Escape to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && dom.settingsModal.classList.contains('active')) {
            closeSettings();
        }
        if (e.key === 'Escape' && $('restore-modal').classList.contains('active')) {
            closeRestoreModal();
        }
        if (e.key === 'Escape' && $('sql-confirm-modal').classList.contains('active')) {
            hideSQLConfirmDialog();
        }
    });
});
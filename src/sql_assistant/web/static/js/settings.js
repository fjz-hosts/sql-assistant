/**
 * Settings Management Module
 */

// ============================================================
// Settings Modal
// ============================================================
function openSettings() { 
    dom.settingsModal.classList.add('active'); 
    loadSettings(); 
}

function closeSettings() { 
    dom.settingsModal.classList.remove('active'); 
}

async function loadSettings() {
    try {
        const [settings, models] = await Promise.all([
            API.get('/api/config/settings'),
            API.get('/api/config/llm/models')
        ]);
        
        state.llmConfigs = settings.llm_providers;
        state.dbConfigs = settings.databases;
        state.activeLLM = settings.active_llm;
        state.activeDB = settings.active_database;
        state.llmModels = models.models || {};

        renderLLMConfigs();
        renderDBConfigs();
        updateConnectionStatus();
    } catch (err) {
        showToast('加载设置失败', 'error');
    }
}

async function loadLLMModels(provider) {
    try {
        const result = await API.get(`/api/config/llm/models?provider=${encodeURIComponent(provider)}`);
        state.llmModels[provider] = result.models || [];
        return result.models || [];
    } catch (err) {
        console.error('加载模型列表失败:', err);
        return [];
    }
}

function updateModelSelect(provider) {
    const select = $('llm-model');
    select.innerHTML = '<option value="">选择模型...</option>';
    
    const models = state.llmModels[provider] || [];
    if (models.length === 0) {
        return;
    }
    
    for (const model of models) {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        select.appendChild(option);
    }
    
    const defaultModel = getDefaultModel(provider);
    if (defaultModel) {
        select.value = defaultModel;
    }
}

function getDefaultModel(provider) {
    const defaults = {
        deepseek: 'deepseek-v4-pro',
        doubao: 'doubao-seed-2-0-pro-260215',
        kimi: 'kimi-k2.6',
        qwen: 'qwen3.6-max-preview',
        openai: 'gpt-5.5',
        gemini: 'gemini-3.1-pro-preview',
        claude: 'claude-opus-4-7',
        glm: 'glm-5.1',
        minimax: 'MiniMax-M2.7',
        siliconflow: 'deepseek-ai/DeepSeek-V3.2',
        openrouter: 'deepseek/deepseek-v4-pro',
        grok: 'grok-4.20-reasoning',
        tencent: 'hy3-preview',
        mimo: 'mimo-v2.5-pro',
        ollama: 'llama3.3',
    };
    return defaults[provider] || '';
}

function updateLLMFormByProvider(provider) {
    const apiKeyField = document.querySelector('#llm-api-key').closest('.form-group');
    const baseUrlField = document.querySelector('#llm-base-url').closest('.form-group');
    
    const noApiKeyProviders = ['ollama'];
    const defaultBaseUrlProviders = ['openai', 'deepseek', 'kimi', 'qwen', 'doubao', 'glm', 'grok', 'tencent', 'mimo', 'ollama'];
    
    if (noApiKeyProviders.includes(provider)) {
        apiKeyField.style.display = 'none';
        $('llm-api-key').value = '';
    } else {
        apiKeyField.style.display = 'block';
    }
    
    if (defaultBaseUrlProviders.includes(provider)) {
        baseUrlField.style.display = 'none';
        $('llm-base-url').value = '';
    } else {
        baseUrlField.style.display = 'block';
    }
}

function requiresApiKey(provider) {
    return !['ollama'].includes(provider);
}

// ============================================================
// LLM Configs
// ============================================================
function renderLLMConfigs() {
    if (state.llmConfigs.length === 0) {
        dom.llmConfigList.innerHTML = '<p style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 16px;">暂无 LLM 配置</p>';
        return;
    }

    const providerIcons = {
        deepseek: '🐋', doubao: '🫘', kimi: '🌙', qwen: '☁️',
        openai: '🤖', gemini: '💎', claude: '🧠',
    };

    dom.llmConfigList.innerHTML = state.llmConfigs.map(c => `
        <div class="config-card ${c.name === state.activeLLM ? 'active' : ''}">
            <div class="provider-icon">${providerIcons[c.provider] || '🤖'}</div>
            <div class="info">
                <div class="name">${escapeHtml(c.name)}</div>
            </div>
            <div class="actions">
                <button class="btn-sm active-btn" onclick="activateLLM('${escapeHtml(c.name)}')">${c.name === state.activeLLM ? '✓ 当前' : '激活'}</button>
                <button class="btn-sm" onclick="editLLM('${escapeHtml(c.name)}')">编辑</button>
                <button class="btn-sm btn-test" onclick="testLLM('${escapeHtml(c.name)}')">测试</button>
                <button class="btn-sm danger" onclick="deleteLLM('${escapeHtml(c.name)}')">删除</button>
            </div>
        </div>
    `).join('');
}

async function activateLLM(name) {
    try {
        await API.put(`/api/config/llm/active/${encodeURIComponent(name)}`);
        state.activeLLM = name;
        renderLLMConfigs();
        updateConnectionStatus();
        showToast(`已激活 LLM: ${name}`, 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function editLLM(name) {
    const config = state.llmConfigs.find(c => c.name === name);
    if (!config) return;

    state.editingLLM = name;
    $('llm-form-title').textContent = '编辑 LLM 提供商';
    $('llm-name').value = config.name;
    $('llm-provider').value = config.provider;
    $('llm-api-key').value = '';
    $('llm-api-key').placeholder = '留空保留原 Key';
    $('llm-base-url').value = '';
    
    updateModelSelect(config.provider);
    $('llm-model').value = config.model || '';
    updateLLMFormByProvider(config.provider);
    
    dom.llmForm.style.display = 'block';
    dom.llmForm.scrollIntoView({ behavior: 'smooth' });
}

async function deleteLLM(name) {
    if (!confirm(`确定删除 LLM 配置 "${name}"？`)) return;
    try {
        await API.del(`/api/config/llm/${encodeURIComponent(name)}`);
        if (state.activeLLM === name) state.activeLLM = '';
        await loadSettings();
        showToast('已删除', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function testLLM(name) {
    try {
        showToast('正在测试 LLM 连接...', 'info');
        const result = await API.post('/api/config/llm/test', { name });
        showToast(result.message, result.success ? 'success' : 'error');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function testNewLLM() {
    const provider = $('llm-provider').value;
    const data = {
        name: $('llm-name').value.trim() || 'temp_test',
        provider: provider,
        api_key: $('llm-api-key').value.trim(),
        base_url: $('llm-base-url').value.trim(),
        model: $('llm-model').value,
    };

    if (requiresApiKey(provider) && !data.api_key) return showToast('请输入 API Key', 'error');
    if (!data.model) return showToast('请选择模型', 'error');

    try {
        showToast('正在测试 LLM 连接...', 'info');
        const result = await API.post('/api/config/llm/test', { config: data });
        showToast(result.message, result.success ? 'success' : 'error');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function saveLLM() {
    const name = $('llm-name').value.trim();
    const provider = $('llm-provider').value;
    const apiKey = $('llm-api-key').value.trim();
    const baseUrl = $('llm-base-url').value.trim();
    const model = $('llm-model').value;

    if (!name) return showToast('请输入配置名称', 'error');
    if (!state.editingLLM && requiresApiKey(provider) && !apiKey) return showToast('请输入 API Key', 'error');
    if (!model) return showToast('请选择模型', 'error');

    try {
        await API.post('/api/config/llm', { name, provider, api_key: apiKey, base_url: baseUrl, model });
        state.editingLLM = null;
        cancelLLMForm();
        await loadSettings();
        showToast('保存成功', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function cancelLLMForm() {
    state.editingLLM = null;
    dom.llmForm.style.display = 'none';
    $('llm-name').value = '';
    $('llm-api-key').value = '';
    $('llm-base-url').value = '';
    $('llm-model').innerHTML = '<option value="">选择模型...</option>';
    
    const apiKeyField = document.querySelector('#llm-api-key').closest('.form-group');
    const baseUrlField = document.querySelector('#llm-base-url').closest('.form-group');
    apiKeyField.style.display = 'block';
    baseUrlField.style.display = 'block';
}

// ============================================================
// DB Configs
// ============================================================
function renderDBConfigs() {
    if (state.dbConfigs.length === 0) {
        dom.dbConfigList.innerHTML = '<p style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 16px;">暂无数据库配置</p>';
        return;
    }

    const dbIcons = {
        mysql: '🐬', postgresql: '🐘', sqlserver: '🪟', redis: '🔴', mongodb: '🍃',
    };

    dom.dbConfigList.innerHTML = state.dbConfigs.map(c => `
        <div class="config-card ${c.name === state.activeDB ? 'active' : ''}">
            <div class="provider-icon">${dbIcons[c.db_type] || '🗄️'}</div>
            <div class="info">
                <div class="name">${escapeHtml(c.name)}</div>
            </div>
            <div class="actions">
                <button class="btn-sm active-btn" onclick="activateDB('${escapeHtml(c.name)}')">${c.name === state.activeDB ? '✓ 当前' : '激活'}</button>
                <button class="btn-sm" onclick="editDB('${escapeHtml(c.name)}')">编辑</button>
                <button class="btn-sm" onclick="testDB('${escapeHtml(c.name)}')">测试</button>
                <button class="btn-sm danger" onclick="deleteDB('${escapeHtml(c.name)}')">删除</button>
            </div>
        </div>
    `).join('');
}

async function activateDB(name) {
    try {
        await API.put(`/api/config/database/active/${encodeURIComponent(name)}`);
        state.activeDB = name;
        renderDBConfigs();
        updateConnectionStatus();
        showToast(`已激活数据库: ${name}`, 'success');
        refreshSchema();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function editDB(name) {
    const config = state.dbConfigs.find(c => c.name === name);
    if (!config) return;

    state.editingDB = name;
    $('db-form-title').textContent = '编辑数据库连接';
    $('db-name').value = config.name;
    $('db-type').value = config.db_type;
    $('db-host').value = config.host;
    $('db-port').value = config.port || '';
    $('db-user').value = config.user;
    $('db-password').value = '';
    $('db-password').placeholder = '留空保留原密码';
    $('db-database').value = config.database;
    dom.dbForm.style.display = 'block';
    dom.dbForm.scrollIntoView({ behavior: 'smooth' });
}

async function testDB(name) {
    try {
        showToast('正在测试连接...', 'info');
        const result = await API.post('/api/config/database/test', { name });
        showToast(result.message, result.success ? 'success' : 'error');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function deleteDB(name) {
    if (!confirm(`确定删除数据库配置 "${name}"？`)) return;
    try {
        await API.del(`/api/config/database/${encodeURIComponent(name)}`);
        if (state.activeDB === name) state.activeDB = '';
        await loadSettings();
        showToast('已删除', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function saveDB() {
    const data = {
        name: $('db-name').value.trim(),
        db_type: $('db-type').value,
        host: $('db-host').value.trim() || 'localhost',
        port: parseInt($('db-port').value) || 0,
        user: $('db-user').value.trim(),
        password: $('db-password').value.trim(),
        database: $('db-database').value.trim(),
    };

    if (!data.name) return showToast('请输入连接名称', 'error');
    if (!data.database) return showToast('请输入数据库名', 'error');

    try {
        await API.post('/api/config/database', data);
        state.editingDB = null;
        cancelDBForm();
        await loadSettings();
        showToast('保存成功', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function testNewDB() {
    const data = {
        name: $('db-name').value.trim() || 'temp_test',
        db_type: $('db-type').value,
        host: $('db-host').value.trim() || 'localhost',
        port: parseInt($('db-port').value) || 0,
        user: $('db-user').value.trim(),
        password: $('db-password').value.trim(),
        database: $('db-database').value.trim(),
    };

    if (!data.database) return showToast('请输入数据库名', 'error');

    try {
        showToast('正在测试连接...', 'info');
        const result = await API.post('/api/config/database/test', { config: data });
        showToast(result.message, result.success ? 'success' : 'error');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function cancelDBForm() {
    state.editingDB = null;
    dom.dbForm.style.display = 'none';
    ['db-name', 'db-host', 'db-port', 'db-user', 'db-password', 'db-database'].forEach(id => $(id).value = '');
}

// ============================================================
// Settings Tabs
// ============================================================
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    $(`tab-${tabName}`)?.classList.add('active');
}

// Expose functions
window.openSettings = openSettings;
window.closeSettings = closeSettings;
window.loadSettings = loadSettings;
window.updateModelSelect = updateModelSelect;
window.updateLLMFormByProvider = updateLLMFormByProvider;
window.activateLLM = activateLLM;
window.editLLM = editLLM;
window.testLLM = testLLM;
window.deleteLLM = deleteLLM;
window.testNewLLM = testNewLLM;
window.saveLLM = saveLLM;
window.cancelLLMForm = cancelLLMForm;
window.activateDB = activateDB;
window.editDB = editDB;
window.testDB = testDB;
window.deleteDB = deleteDB;
window.saveDB = saveDB;
window.testNewDB = testNewDB;
window.cancelDBForm = cancelDBForm;
window.switchTab = switchTab;
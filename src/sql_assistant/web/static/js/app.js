/**
 * SQL 智能助手 - 前端应用
 */

// ============================================================
// API Helper
// ============================================================
const API = {
    async post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(err.detail || '请求失败');
        }
        return res.json();
    },
    async get(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error('请求失败');
        return res.json();
    },
    async del(url) {
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error('请求失败');
        return res.json();
    },
    async put(url, data) {
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data || {}),
        });
        if (!res.ok) throw new Error('请求失败');
        return res.json();
    },
};

// ============================================================
// Toast
// ============================================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 200ms';
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}

function createToastContainer() {
    const el = document.createElement('div');
    el.id = 'toast-container';
    el.className = 'toast-container';
    document.body.appendChild(el);
    return el;
}

// ============================================================
// State
// ============================================================
const state = {
    llmConfigs: [],
    dbConfigs: [],
    activeLLM: '',
    activeDB: '',
    editingLLM: null,
    editingDB: null,
    schemaLoaded: false,
    schemaError: '',
    tableCount: 0,
    currentConversationId: null,
    conversations: [],
    llmModels: {}, // 存储各提供商的模型列表
};

// ============================================================
// DOM Elements
// ============================================================
const $ = (id) => document.getElementById(id);

const dom = {
    chatMessages: $('chat-messages'),
    queryInput: $('query-input'),
    queryForm: $('query-form'),
    btnSend: $('btn-send'),
    historyList: $('history-list'),
    connectionStatus: $('connection-status'),
    settingsModal: $('settings-modal'),

    llmConfigList: $('llm-config-list'),
    llmForm: $('llm-form'),
    dbConfigList: $('db-config-list'),
    dbForm: $('db-form'),
};

// ============================================================
// Connection Status
// ============================================================
function updateConnectionStatus() {
    const hasLLM = state.activeLLM;
    const hasDB = state.activeDB;
    const dot = dom.connectionStatus.querySelector('.status-dot');
    const text = dom.connectionStatus.querySelector('.status-text');

    const refreshBtn = $('btn-refresh-schema');

    if (hasLLM && hasDB) {
        if (state.schemaError) {
            dot.className = 'status-dot error';
            text.textContent = `DB: ${state.activeDB} | Schema 加载失败`;
        } else if (state.schemaLoaded) {
            dot.className = 'status-dot online';
            text.textContent = `LLM: ${state.activeLLM} | DB: ${state.activeDB} (${state.tableCount} 表)`;
        } else {
            dot.className = 'status-dot online';
            text.textContent = `LLM: ${state.activeLLM} | DB: ${state.activeDB}`;
        }
        dom.btnSend.disabled = false;
        if (refreshBtn) refreshBtn.style.display = 'flex';
    } else if (hasLLM || hasDB) {
        dot.className = 'status-dot error';
        text.textContent = hasLLM ? '请配置数据库连接' : '请配置 LLM';
        dom.btnSend.disabled = true;
        if (refreshBtn) refreshBtn.style.display = 'none';
    } else {
        dot.className = 'status-dot offline';
        text.textContent = '未配置连接';
        dom.btnSend.disabled = true;
        if (refreshBtn) refreshBtn.style.display = 'none';
    }
}

async function refreshSchema() {
    try {
        state.schemaLoaded = false;
        state.schemaError = '';
        const schema = await API.post('/api/schema/refresh');
        if (schema.error) {
            state.schemaError = schema.error;
            showToast('Schema 加载失败: ' + schema.error, 'error');
        } else {
            const tables = schema.tables || schema.keys || [];
            state.tableCount = tables.length;
            state.schemaLoaded = true;
            showToast(`Schema 已刷新: ${tables.length} 个对象`, 'success');
        }
    } catch (err) {
        state.schemaError = err.message;
        showToast('Schema 刷新失败: ' + err.message, 'error');
    }
    updateConnectionStatus();
}

// ============================================================
// Chat
// ============================================================
function addMessage(type, content) {
    // Remove welcome message if present
    const welcome = dom.chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const msg = document.createElement('div');
    msg.className = `message ${type}`;
    msg.innerHTML = `<div class="message-content">${content}</div>`;
    dom.chatMessages.appendChild(msg);
    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
    return msg;
}

function addSQLBlock(sql) {
    const block = document.createElement('div');
    block.className = 'sql-block';
    block.innerHTML = `
        <div class="sql-block-header">
            <span>📋 SQL</span>
            <button class="btn-copy" onclick="copySQL(this)">复制</button>
        </div>
        <pre><code>${escapeHtml(sql)}</code></pre>
    `;
    return block;
}

function addResultTable(result) {
    const wrapper = document.createElement('div');
    if (!result || result.error) {
        wrapper.innerHTML = `<div class="error-message">${escapeHtml(result?.error || '执行失败')}</div>`;
        return wrapper;
    }

    const { columns, rows, row_count, affected_rows, sql_type } = result;

    // For non-SELECT
    if (sql_type !== 'SELECT' && affected_rows !== undefined && affected_rows > 0) {
        wrapper.innerHTML = `
            <div class="result-meta" style="color: var(--success); font-size: 14px;">
                ✅ 执行成功，影响 ${affected_rows} 行
            </div>
        `;
        return wrapper;
    }

    if (!columns || !rows) {
        wrapper.innerHTML = `<div class="result-meta">执行完成</div>`;
        return wrapper;
    }

    let html = '<div class="result-table-wrapper"><table class="result-table">';
    html += '<thead><tr>';
    for (const col of columns) {
        html += `<th>${escapeHtml(String(col))}</th>`;
    }
    html += '</tr></thead><tbody>';
    for (const row of rows.slice(0, 100)) {
        html += '<tr>';
        for (const cell of row) {
            html += `<td>${escapeHtml(String(cell ?? 'NULL'))}</td>`;
        }
        html += '</tr>';
    }
    html += '</tbody></table></div>';

    let meta = `显示 ${Math.min(row_count, 100)} 条`;
    if (row_count > 100) meta += `，共 ${row_count} 条`;
    meta += ` (${sql_type})`;
    html += `<div class="result-meta">${meta}</div>`;

    wrapper.innerHTML = html;
    return wrapper;
}

async function sendQuery(question) {
    if (!question.trim()) return;

    addMessage('user', escapeHtml(question));
    dom.queryInput.value = '';
    dom.queryInput.style.height = 'auto';

    const msgDiv = addMessage('assistant', '<div class="loading-dots"><span></span><span></span><span></span></div>');
    const contentDiv = msgDiv.querySelector('.message-content');

    try {
        // 如果没有选中任何对话，先创建一个新对话，以问题作为标题
        if (!state.currentConversationId) {
            const convData = await API.post('/api/conversations', { title: question.slice(0, 50) });
            state.currentConversationId = convData.id;
            await loadConversations();
        }

        const data = await API.post('/api/query', { 
            question, 
            conversation_id: state.currentConversationId 
        });

        contentDiv.innerHTML = '';

        if (data.sql) {
            contentDiv.appendChild(addSQLBlock(data.sql));
        }

        if (data.result) {
            contentDiv.appendChild(addResultTable(data.result));
        }

        if (data.error && !data.result) {
            contentDiv.innerHTML += `<div class="error-message">${escapeHtml(data.error)}</div>`;
        }
    } catch (err) {
        contentDiv.innerHTML = `<div class="error-message">${escapeHtml(err.message)}</div>`;
    }

    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
    loadConversations();
}

// ============================================================
// Conversation Management
// ============================================================
async function loadConversations() {
    try {
        const data = await API.get('/api/conversations');
        state.conversations = data.conversations || [];
        renderConversations();
        
        // 如果有对话但没有选中任何对话，默认选中第一个
        if (state.conversations.length > 0 && !state.currentConversationId) {
            state.currentConversationId = state.conversations[0].id;
            renderConversations();
        }
    } catch (err) {
        dom.historyList.innerHTML = '<div class="history-empty">加载失败</div>';
    }
}

function renderConversations() {
    if (!state.conversations || state.conversations.length === 0) {
        dom.historyList.innerHTML = '<div class="history-empty">暂无对话</div>';
        return;
    }

    dom.historyList.innerHTML = state.conversations.map(c => `
        <div class="history-item ${state.currentConversationId === c.id ? 'active' : ''}" onclick="selectConversation(${c.id})">
            <div class="history-item-main">
                <div class="history-item-title">${escapeHtml(c.title || '未命名对话')}</div>
                <div class="history-item-actions">
                    <button class="btn-icon-chat" onclick="event.stopPropagation(); startRenameConversation(${c.id})" title="重命名">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="btn-delete-chat" onclick="event.stopPropagation(); deleteConversation(${c.id})" title="删除对话">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </div>
            <div class="meta">
                <span>${c.message_count || 0} 条消息</span>
                <span>${c.updated_at?.split('T')[0] || ''}</span>
            </div>
        </div>
    `).join('');
}

function startRenameConversation(conversationId) {
    const item = document.querySelector(`.history-item[onclick*="selectConversation(${conversationId})"]`);
    if (!item) return;
    
    const titleDiv = item.querySelector('.history-item-title');
    const currentTitle = titleDiv.textContent;
    
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'rename-input';
    input.value = currentTitle;
    input.maxLength = 50;
    
    titleDiv.innerHTML = '';
    titleDiv.appendChild(input);
    input.focus();
    input.select();
    
    const finishRename = async () => {
        const newTitle = input.value.trim() || currentTitle;
        try {
            await API.put(`/api/conversations/${conversationId}`, { title: newTitle });
            await loadConversations();
            showToast('重命名成功', 'success');
        } catch (err) {
            showToast(err.message, 'error');
        }
    };
    
    input.addEventListener('blur', finishRename);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
        } else if (e.key === 'Escape') {
            input.value = currentTitle;
            input.blur();
        }
    });
}

async function createNewConversation() {
    try {
        const data = await API.post('/api/conversations', { title: '新对话' });
        state.currentConversationId = data.id;
        clearChatMessages();
        loadConversations();
        renderConversations();
        showToast('已创建新对话', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function selectConversation(conversationId) {
    try {
        state.currentConversationId = conversationId;
        const data = await API.get(`/api/conversations/${conversationId}`);
        
        clearChatMessages();
        
        if (data.messages && data.messages.length > 0) {
            for (const msg of data.messages) {
                addMessage('user', escapeHtml(msg.question));
                
                const msgDiv = addMessage('assistant', '');
                const contentDiv = msgDiv.querySelector('.message-content');
                
                if (msg.sql) {
                    contentDiv.appendChild(addSQLBlock(msg.sql));
                }
                
                if (msg.result_json) {
                    try {
                        const result = JSON.parse(msg.result_json);
                        contentDiv.appendChild(addResultTable(result));
                    } catch (e) {
                        // ignore
                    }
                }
                
                if (!msg.success && msg.error_message) {
                    contentDiv.innerHTML += `<div class="error-message">${escapeHtml(msg.error_message)}</div>`;
                }
            }
        }
        
        renderConversations();
    } catch (err) {
        showToast('加载对话失败', 'error');
    }
}

async function deleteConversation(conversationId) {
    if (!confirm('确定删除这个对话吗？')) return;
    try {
        await API.del(`/api/conversations/${conversationId}`);
        if (state.currentConversationId === conversationId) {
            state.currentConversationId = null;
            clearChatMessages();
        }
        loadConversations();
        showToast('对话已删除', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function clearChatMessages() {
    dom.chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">💬</div>
            <h2>SQL 智能助手</h2>
            <p>用自然语言描述你的查询需求，AI 会帮你生成 SQL 并执行</p>
            <p class="welcome-hint">请先在设置中配置 LLM API Key 和数据库连接</p>
            <div class="welcome-examples">
                <span class="example-tag" data-question="查询所有用户信息">查询所有用户信息</span>
                <span class="example-tag" data-question="统计每个部门的员工数量">统计每个部门的员工数量</span>
                <span class="example-tag" data-question="添加一条商品记录，名称 iPhone 15，价格 6999">添加商品记录</span>
                <span class="example-tag" data-question="查询最近7天的订单">查询最近7天订单</span>
            </div>
        </div>
    `;
}

// ============================================================
// Settings Modal
// ============================================================
function openSettings() { dom.settingsModal.classList.add('active'); loadSettings(); }
function closeSettings() { dom.settingsModal.classList.remove('active'); }

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

// LLM Configs
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
    
    // 恢复所有字段显示
    const apiKeyField = document.querySelector('#llm-api-key').closest('.form-group');
    const baseUrlField = document.querySelector('#llm-base-url').closest('.form-group');
    apiKeyField.style.display = 'block';
    baseUrlField.style.display = 'block';
}

// DB Configs
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

// ============================================================
// Utilities
// ============================================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = String(text ?? '');
    return div.innerHTML;
}

function copySQL(btn) {
    const code = btn.closest('.sql-block')?.querySelector('code')?.textContent;
    if (code) {
        navigator.clipboard.writeText(code).then(() => {
            btn.textContent = '已复制!';
            setTimeout(() => btn.textContent = '复制', 2000);
        }).catch(() => {
            showToast('复制失败', 'error');
        });
    }
}

// ============================================================
// Event Listeners
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    ColorThemeManager.init();
    
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

    $('btn-save-llm').addEventListener('click', saveLLM);
    $('btn-cancel-llm').addEventListener('click', cancelLLMForm);
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

    // Clear history (legacy, kept for compatibility)
    if ($('btn-clear-history')) {
        $('btn-clear-history').addEventListener('click', async () => {
            if (confirm('确定清空所有对话？')) {
                try {
                    for (const conv of state.conversations) {
                        await API.del(`/api/conversations/${conv.id}`);
                    }
                    state.currentConversationId = null;
                    clearChatMessages();
                    loadConversations();
                    showToast('所有对话已清空', 'success');
                } catch (err) {
                    showToast(err.message, 'error');
                }
            }
        });
    }

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

    // Keyboard shortcut: Escape to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && dom.settingsModal.classList.contains('active')) {
            closeSettings();
        }
        if (e.key === 'Escape' && $('restore-modal').classList.contains('active')) {
            closeRestoreModal();
        }
    });
});

// ============================================================
// Backup Functions
// ============================================================
function toggleTableSelection() {
    const scope = $('backup-scope').value;
    const group = $('table-selection-group');
    if (scope === 'selected') {
        group.style.display = 'block';
        loadTablesForBackup();
    } else {
        group.style.display = 'none';
    }
}

async function loadTablesForBackup() {
    try {
        const schema = await API.get('/api/schema');
        const tables = schema.tables || [];
        const select = $('backup-tables');
        select.innerHTML = tables.map(t => `
            <option value="${escapeHtml(t.name)}">${escapeHtml(t.name)}</option>
        `).join('');
    } catch (err) {
        showToast('加载表列表失败: ' + err.message, 'error');
    }
}

async function createBackup() {
    const backupType = $('backup-type').value;
    const scope = $('backup-scope').value;
    const includeSchema = $('backup-include-schema').checked;
    const includeData = $('backup-include-data').checked;

    let tables = null;
    if (scope === 'selected') {
        const select = $('backup-tables');
        tables = Array.from(select.selectedOptions).map(opt => opt.value);
        if (tables.length === 0) {
            return showToast('请至少选择一个表', 'error');
        }
    }

    const btn = $('btn-create-backup');
    const originalText = btn.textContent;
    btn.textContent = '备份中...';
    btn.disabled = true;

    try {
        showToast('正在创建备份...', 'info');
        const result = await API.post('/api/backup', {
            backup_type: backupType,
            tables,
            include_schema: includeSchema,
            include_data: includeData
        });

        if (result.success) {
            showToast(result.message, 'success');
            await loadBackupList();
        } else {
            showToast(result.message, 'error');
        }
    } catch (err) {
        showToast('备份失败: ' + err.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

async function loadBackupList() {
    try {
        const result = await API.get('/api/backup/list');
        const backups = result.backups || [];
        const list = $('backup-list');

        if (backups.length === 0) {
            list.innerHTML = '<div class="empty-state">暂无备份记录</div>';
            return;
        }

        list.innerHTML = backups.map(b => `
            <div class="backup-item">
                <div class="backup-item-header">
                    <span class="backup-item-id">${escapeHtml(b.backup_id)}</span>
                    <span class="backup-item-type ${b.backup_type}">${b.backup_type === 'full' ? '全量备份' : '增量备份'}</span>
                </div>
                <div class="backup-item-info">数据库: ${escapeHtml(b.db_name || '未知')}</div>
                <div class="backup-item-meta">
                    <span>表数: ${b.tables.length}</span>
                    <span>记录数: ${b.record_count}</span>
                    <span>大小: ${formatFileSize(b.file_size)}</span>
                    <span>${b.backup_time ? new Date(b.backup_time).toLocaleString('zh-CN') : ''}</span>
                </div>
                <div class="backup-item-actions">
                    <button onclick="viewBackupDetail('${escapeHtml(b.backup_id)}')">详情</button>
                    <button onclick="openRestoreModal('${escapeHtml(b.backup_id)}')">恢复</button>
                    <button class="danger" onclick="deleteBackup('${escapeHtml(b.backup_id)}')">删除</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        showToast('加载备份列表失败: ' + err.message, 'error');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function viewBackupDetail(backupId) {
    try {
        const result = await API.get(`/api/backup/${encodeURIComponent(backupId)}`);
        const info = [
            `备份ID: ${result.backup_id}`,
            `类型: ${result.backup_type === 'full' ? '全量备份' : '增量备份'}`,
            `数据库: ${result.db_name}`,
            `数据库类型: ${result.db_type}`,
            `表数量: ${result.tables.length}`,
            `记录数: ${result.record_count}`,
            `大小: ${formatFileSize(result.file_size)}`,
            `时间: ${result.backup_time ? new Date(result.backup_time).toLocaleString('zh-CN') : ''}`
        ];
        alert(info.join('\n'));
    } catch (err) {
        showToast('获取备份详情失败: ' + err.message, 'error');
    }
}

async function deleteBackup(backupId) {
    if (!confirm(`确定删除备份 "${backupId}" 吗？`)) return;

    try {
        await API.del(`/api/backup/${encodeURIComponent(backupId)}`);
        showToast('备份已删除', 'success');
        await loadBackupList();
    } catch (err) {
        showToast('删除备份失败: ' + err.message, 'error');
    }
}

let currentRestoreBackupId = null;

function openRestoreModal(backupId) {
    currentRestoreBackupId = backupId;
    $('restore-backup-info').innerHTML = `
        <div style="font-weight: 600; margin-bottom: 8px;">备份ID: ${escapeHtml(backupId)}</div>
        <div style="font-size: 12px; color: var(--text-secondary);">
            恢复操作会将备份数据写入当前激活的数据库。
        </div>
    `;
    $('restore-schema').checked = false;
    $('restore-data').checked = true;
    $('restore-warning').style.display = 'block';
    $('restore-modal').classList.add('active');
}

function closeRestoreModal() {
    $('restore-modal').classList.remove('active');
    currentRestoreBackupId = null;
}

async function confirmRestore() {
    if (!currentRestoreBackupId) return;

    const restoreSchema = $('restore-schema').checked;
    const restoreData = $('restore-data').checked;

    if (!restoreData && !restoreSchema) {
        return showToast('请至少选择一个恢复选项', 'error');
    }

    const btn = $('btn-confirm-restore');
    const originalText = btn.textContent;
    btn.textContent = '恢复中...';
    btn.disabled = true;

    try {
        showToast('正在恢复备份...', 'info');
        const result = await API.post('/api/backup/restore', {
            backup_id: currentRestoreBackupId,
            restore_schema: restoreSchema,
            restore_data: restoreData
        });

        if (result.success) {
            showToast(result.message, 'success');
            closeRestoreModal();
        } else {
            showToast(result.message, 'error');
        }
    } catch (err) {
        showToast('恢复失败: ' + err.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// ============================================================
// Expose functions for inline onclick handlers
// ============================================================
window.activateLLM = activateLLM;
window.editLLM = editLLM;
window.testLLM = testLLM;
window.deleteLLM = deleteLLM;
window.activateDB = activateDB;
window.editDB = editDB;
window.testDB = testDB;
window.deleteDB = deleteDB;
window.refreshSchema = refreshSchema;
window.copySQL = copySQL;
window.selectConversation = selectConversation;
window.deleteConversation = deleteConversation;
window.startRenameConversation = startRenameConversation;
window.toggleTableSelection = toggleTableSelection;

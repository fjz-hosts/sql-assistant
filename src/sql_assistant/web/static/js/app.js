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
        const data = await API.post('/api/query', { question });

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
    loadHistory();
}

// ============================================================
// History
// ============================================================
async function loadHistory() {
    try {
        const data = await API.get('/api/history?limit=50');
        renderHistory(data.records);
    } catch (err) {
        dom.historyList.innerHTML = '<div class="history-empty">加载失败</div>';
    }
}

function renderHistory(records) {
    if (!records || records.length === 0) {
        dom.historyList.innerHTML = '<div class="history-empty">暂无查询记录</div>';
        return;
    }

    dom.historyList.innerHTML = records.map(r => `
        <div class="history-item" onclick="viewHistory(${r.id})">
            <div class="question">${escapeHtml(r.question)}</div>
            <div class="meta">
                <span class="badge">${escapeHtml(r.db_type)}</span>
                <span>${r.created_at?.split('T')[0] || ''}</span>
            </div>
        </div>
    `).join('');
}

async function viewHistory(id) {
    try {
        const record = await API.get(`/api/history/${id}`);

        // Remove welcome
        const welcome = dom.chatMessages.querySelector('.welcome-message');
        if (welcome) welcome.remove();

        // Clear current messages
        dom.chatMessages.innerHTML = '';

        addMessage('user', escapeHtml(record.question));

        const msgDiv = addMessage('assistant', '');
        const contentDiv = msgDiv.querySelector('.message-content');

        if (record.sql) {
            contentDiv.appendChild(addSQLBlock(record.sql));
        }

        if (record.result_json) {
            try {
                const result = JSON.parse(record.result_json);
                contentDiv.appendChild(addResultTable(result));
            } catch (e) {
                // ignore
            }
        }

        if (!record.success) {
            contentDiv.innerHTML += `<div class="error-message">${escapeHtml(record.error_message)}</div>`;
        }
    } catch (err) {
        showToast('加载记录失败', 'error');
    }
}

// ============================================================
// Settings Modal
// ============================================================
function openSettings() { dom.settingsModal.classList.add('active'); loadSettings(); }
function closeSettings() { dom.settingsModal.classList.remove('active'); }

async function loadSettings() {
    try {
        const settings = await API.get('/api/config/settings');
        state.llmConfigs = settings.llm_providers;
        state.dbConfigs = settings.databases;
        state.activeLLM = settings.active_llm;
        state.activeDB = settings.active_database;

        renderLLMConfigs();
        renderDBConfigs();
        updateConnectionStatus();
    } catch (err) {
        showToast('加载设置失败', 'error');
    }
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
                <div class="detail">${escapeHtml(c.provider)} · ${escapeHtml(c.model)} · Key: ${escapeHtml(c.api_key_masked)}</div>
            </div>
            <div class="actions">
                <button class="btn-sm active-btn" onclick="activateLLM('${escapeHtml(c.name)}')">${c.name === state.activeLLM ? '✓ 当前' : '激活'}</button>
                <button class="btn-sm" onclick="editLLM('${escapeHtml(c.name)}')">编辑</button>
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
    $('llm-model').value = config.model;
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

async function saveLLM() {
    const name = $('llm-name').value.trim();
    const provider = $('llm-provider').value;
    const apiKey = $('llm-api-key').value.trim();
    const baseUrl = $('llm-base-url').value.trim();
    const model = $('llm-model').value.trim();

    if (!name) return showToast('请输入配置名称', 'error');
    if (!state.editingLLM && !apiKey) return showToast('请输入 API Key', 'error');

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
    $('llm-model').value = '';
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
                <div class="detail">${escapeHtml(c.db_type)} · ${escapeHtml(c.host)}:${c.port}/${escapeHtml(c.database)}</div>
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
    loadSettings().then(() => {
        if (state.activeDB) refreshSchema();
    });
    loadHistory();

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
        dom.llmForm.style.display = 'block';
        dom.llmForm.scrollIntoView({ behavior: 'smooth' });
    });
    $('btn-save-llm').addEventListener('click', saveLLM);
    $('btn-cancel-llm').addEventListener('click', cancelLLMForm);

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

    // Clear history
    $('btn-clear-history').addEventListener('click', async () => {
        if (confirm('确定清空所有查询历史？')) {
            try {
                await API.del('/api/history');
                await loadHistory();
                showToast('历史已清空', 'success');
            } catch (err) {
                showToast(err.message, 'error');
            }
        }
    });

    // Refresh schema button
    const refreshBtn = $('btn-refresh-schema');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshSchema);
    }

    // Keyboard shortcut: Escape to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && dom.settingsModal.classList.contains('active')) {
            closeSettings();
        }
    });
});

// Expose functions for inline onclick handlers
window.activateLLM = activateLLM;
window.editLLM = editLLM;
window.deleteLLM = deleteLLM;
window.activateDB = activateDB;
window.editDB = editDB;
window.testDB = testDB;
window.deleteDB = deleteDB;
window.refreshSchema = refreshSchema;
window.viewHistory = viewHistory;
window.copySQL = copySQL;

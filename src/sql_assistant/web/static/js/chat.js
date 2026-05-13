/**
 * Chat Module
 */

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

function addMessage(type, content) {
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
        <pre><code class="language-sql">${escapeHtml(sql)}</code></pre>
    `;
    const codeEl = block.querySelector('code');
    if (typeof hljs !== 'undefined') {
        hljs.highlightElement(codeEl);
    }
    return block;
}

function addResultTable(result, pagination) {
    const wrapper = document.createElement('div');
    if (!result || result.error) {
        wrapper.innerHTML = `<div class="error-message">${escapeHtml(result?.error || '执行失败')}</div>`;
        return wrapper;
    }

    const { columns, rows, row_count, affected_rows, sql_type } = result;

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
    for (const row of rows) {
        html += '<tr>';
        for (const cell of row) {
            html += `<td>${escapeHtml(String(cell ?? 'NULL'))}</td>`;
        }
        html += '</tr>';
    }
    html += '</tbody></table></div>';

    let meta = '';
    if (pagination && pagination.total_rows > 0) {
        const start = (pagination.page - 1) * pagination.page_size + 1;
        const end = Math.min(pagination.page * pagination.page_size, pagination.total_rows);
        meta = `显示 ${start}-${end} 条，共 ${pagination.total_rows} 条`;
    } else {
        meta = `显示 ${row_count} 条`;
    }
    meta += ` (${sql_type})`;
    html += `<div class="result-meta">${meta}</div>`;

    if (pagination && pagination.total_pages > 1) {
        html += `<div class="result-pagination">`;
        html += `<button class="btn-page" onclick="changePage(-1)" ${pagination.page <= 1 ? 'disabled' : ''}>上一页</button>`;
        html += `<span class="page-info">第 ${pagination.page} / ${pagination.total_pages} 页</span>`;
        html += `<button class="btn-page" onclick="changePage(1)" ${pagination.page >= pagination.total_pages ? 'disabled' : ''}>下一页</button>`;
        html += `</div>`;
    }

    wrapper.innerHTML = html;
    wrapper.dataset.pagination = JSON.stringify(pagination || {});
    return wrapper;
}

function changePage(delta) {
    const resultDiv = document.querySelector('.result-pagination')?.closest('.result-wrapper');
    if (!resultDiv) return;

    let pagination = {};
    try {
        pagination = JSON.parse(resultDiv.dataset.pagination || '{}');
    } catch (e) {}

    if (!pagination.page) return;

    const newPage = pagination.page + delta;
    if (newPage < 1 || newPage > pagination.total_pages) return;

    state.pendingPageChange = { page: newPage, page_size: pagination.page_size };
    sendQuery(state.pendingQuestion);
}

async function sendQuery(question) {
    if (!question.trim()) return;

    addMessage('user', escapeHtml(question));
    dom.queryInput.value = '';
    dom.queryInput.style.height = 'auto';

    const msgDiv = addMessage('assistant', '<div class="loading-dots"><span></span><span></span><span></span></div>');
    const contentDiv = msgDiv.querySelector('.message-content');

    try {
        if (!state.currentConversationId) {
            const convData = await API.post('/api/conversations', { title: question.slice(0, 50) });
            state.currentConversationId = convData.id;
            await loadConversations();
        }

        const queryParams = {
            question,
            conversation_id: state.currentConversationId
        };

        if (state.pendingPageChange) {
            queryParams.page = state.pendingPageChange.page;
            queryParams.page_size = state.pendingPageChange.page_size;
            state.pendingPageChange = null;
        }
        state.pendingQuestion = question;

        contentDiv.innerHTML = '<div class="streaming-indicator">正在生成 SQL...</div>';

        const previewData = await API.post('/api/query/preview', queryParams);

        if (!previewData.success) {
            contentDiv.innerHTML = `<div class="error-message">${escapeHtml(previewData.error)}</div>`;
            return;
        }

        contentDiv.innerHTML = '';

        contentDiv.appendChild(addSQLBlock(previewData.sql));

        if (previewData.requires_confirmation) {
            window.pendingSQLData = {
                question: question,
                sql: previewData.sql,
                sqlHash: previewData.sql_hash,
                conversationId: state.currentConversationId,
                contentDiv: contentDiv,
                msgDiv: msgDiv
            };
            showSQLConfirmDialog(previewData);
        } else {
            await executeConfirmedQuery(queryParams, contentDiv, msgDiv);
        }
    } catch (err) {
        contentDiv.innerHTML = `<div class="error-message">${escapeHtml(err.message)}</div>`;
    }

    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
    loadConversations();
}

window.updateConnectionStatus = updateConnectionStatus;
window.refreshSchema = refreshSchema;
window.addMessage = addMessage;
window.addSQLBlock = addSQLBlock;
window.addResultTable = addResultTable;
window.changePage = changePage;
window.sendQuery = sendQuery;
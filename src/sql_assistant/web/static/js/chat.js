/**
 * Chat Module
 */

function updateConnectionStatus() {
    const hasLLM = state.activeLLM;
    const hasDB = state.activeDB;
    const dot = dom.connectionStatus.querySelector('.status-dot');
    const text = dom.connectionStatus.querySelector('.status-text');

    const refreshBtn = $('btn-refresh-schema');
    const isSQLMode = state.queryMode === 'sql';

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
    } else if (isSQLMode && hasDB) {
        if (state.schemaError) {
            dot.className = 'status-dot error';
            text.textContent = `DB: ${state.activeDB} | Schema 加载失败`;
        } else if (state.schemaLoaded) {
            dot.className = 'status-dot online';
            text.textContent = `DB: ${state.activeDB} (${state.tableCount} 表) - SQL 模式`;
        } else {
            dot.className = 'status-dot online';
            text.textContent = `DB: ${state.activeDB} - SQL 模式`;
        }
        dom.btnSend.disabled = false;
        if (refreshBtn) refreshBtn.style.display = 'flex';
    } else if (hasLLM || hasDB) {
        dot.className = 'status-dot error';
        text.textContent = hasLLM ? '请配置数据库连接' : '请配置 LLM';
        dom.btnSend.disabled = !isSQLMode || !hasDB;
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
            <div class="sql-block-actions">
                <button class="btn-copy" onclick="copySQL(this)">复制</button>
                <button class="btn-analyze" onclick="analyzeSQLFromChat(this)">分析</button>
            </div>
        </div>
        <pre><code class="language-sql">${escapeHtml(sql)}</code></pre>
    `;
    const codeEl = block.querySelector('code');
    if (typeof hljs !== 'undefined') {
        hljs.highlightElement(codeEl);
    }
    return block;
}

function addResultTable(result, pagination, extraData) {
    const wrapper = document.createElement('div');
    wrapper.className = 'result-wrapper';
    
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

    wrapper.dataset.allRows = JSON.stringify(rows);
    wrapper.dataset.columns = JSON.stringify(columns);
    wrapper.dataset.resultData = JSON.stringify({ columns, rows });

    if (extraData) {
        wrapper.dataset.historyId = extraData.historyId || '';
        wrapper.dataset.sql = extraData.sql || '';
        wrapper.dataset.question = extraData.question || '';
        wrapper.dataset.conversationId = extraData.conversationId || '';
    }

    const pageSize = (pagination && pagination.page_size) || 100;
    const currentPage = (pagination && pagination.page) || 1;
    const totalRows = (pagination && pagination.total_rows) || rows.length;
    const totalPages = (pagination && pagination.total_pages) || Math.ceil(totalRows / pageSize);

    const startIdx = (currentPage - 1) * pageSize;
    const endIdx = Math.min(startIdx + pageSize, totalRows);
    const pageRows = rows.slice(startIdx, endIdx);

    let html = '<div class="result-header"><span class="result-title">📊 查询结果</span><button class="btn-export" onclick="showExportMenu(this)">导出</button></div>';
    html += '<div class="result-table-wrapper"><table class="result-table">';
    html += '<thead><tr>';
    for (const col of columns) {
        html += `<th>${escapeHtml(String(col))}</th>`;
    }
    html += '</tr></thead><tbody class="result-tbody">';
    for (const row of pageRows) {
        html += '<tr>';
        for (const cell of row) {
            html += `<td>${escapeHtml(String(cell ?? 'NULL'))}</td>`;
        }
        html += '</tr>';
    }
    html += '</tbody></table></div>';

    html += `<div class="result-meta">显示 ${startIdx + 1}-${endIdx} 条，共 ${totalRows} 条 (${sql_type})</div>`;

    if (totalPages > 1) {
        html += `<div class="result-pagination">`;
        html += `<button class="btn-page" onclick="changePage(-1, this)" ${currentPage <= 1 ? 'disabled' : ''}>上一页</button>`;
        html += `<span class="page-info">第 ${currentPage} / ${totalPages} 页</span>`;
        html += `<button class="btn-page" onclick="changePage(1, this)" ${currentPage >= totalPages ? 'disabled' : ''}>下一页</button>`;
        html += `</div>`;
    }

    wrapper.innerHTML = html;

    wrapper.dataset.pagination = JSON.stringify({
        page: currentPage,
        page_size: pageSize,
        total_rows: totalRows,
        total_pages: totalPages,
        sql_type: sql_type
    });

    return wrapper;
}

function showExportMenu(btn) {
    const resultWrapper = btn.closest('.result-wrapper');
    if (!resultWrapper) return;
    
    const historyId = resultWrapper.dataset.historyId;
    
    try {
        const data = JSON.parse(resultWrapper.dataset.resultData);
        if (data.columns && data.rows) {
            ExportManager.showExportMenu(btn, data.columns, data.rows, historyId);
        }
    } catch (e) {
        console.error('导出数据解析失败:', e);
        showToast('导出数据解析失败', 'error');
    }
}

function changePage(delta, btn) {
    const wrapper = btn.closest('.result-wrapper');
    if (!wrapper) return;

    let pagination = {};
    try {
        pagination = JSON.parse(wrapper.dataset.pagination || '{}');
    } catch (e) {
        return;
    }

    if (!pagination.page || !pagination.total_pages) return;

    const newPage = pagination.page + delta;
    if (newPage < 1 || newPage > pagination.total_pages) return;

    let allRows = [];
    try {
        allRows = JSON.parse(wrapper.dataset.allRows || '[]');
    } catch (e) {
        return;
    }

    const pageSize = pagination.page_size;
    const totalRows = pagination.total_rows;
    const totalPages = pagination.total_pages;
    const sqlType = pagination.sql_type || '';

    const startIdx = (newPage - 1) * pageSize;
    const endIdx = Math.min(startIdx + pageSize, totalRows);
    const pageRows = allRows.slice(startIdx, endIdx);

    const tbody = wrapper.querySelector('.result-tbody');
    if (tbody) {
        let rowsHtml = '';
        for (const row of pageRows) {
            rowsHtml += '<tr>';
            for (const cell of row) {
                rowsHtml += `<td>${escapeHtml(String(cell ?? 'NULL'))}</td>`;
            }
            rowsHtml += '</tr>';
        }
        tbody.innerHTML = rowsHtml;
    }

    const metaEl = wrapper.querySelector('.result-meta');
    if (metaEl) {
        metaEl.textContent = `显示 ${startIdx + 1}-${endIdx} 条，共 ${totalRows} 条`;
        if (sqlType) {
            metaEl.textContent += ` (${sqlType})`;
        }
    }

    const paginationEl = wrapper.querySelector('.result-pagination');
    if (paginationEl) {
        paginationEl.innerHTML = `
            <button class="btn-page" onclick="changePage(-1, this)" ${newPage <= 1 ? 'disabled' : ''}>上一页</button>
            <span class="page-info">第 ${newPage} / ${totalPages} 页</span>
            <button class="btn-page" onclick="changePage(1, this)" ${newPage >= totalPages ? 'disabled' : ''}>下一页</button>
        `;
    }

    pagination.page = newPage;
    wrapper.dataset.pagination = JSON.stringify(pagination);
}

async function sendQuery(question) {
    if (!question.trim()) return;

    if (state.queryMode === 'sql') {
        return sendDirectSQL(question);
    }

    return sendNaturalLanguageQuery(question);
}

async function sendNaturalLanguageQuery(question) {
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
            await executeConfirmedQuery(queryParams, contentDiv, msgDiv, question, previewData.sql, state.currentConversationId);
        }
    } catch (err) {
        contentDiv.innerHTML = `<div class="error-message">${escapeHtml(err.message)}</div>`;
    }

    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
    loadConversations();
}

async function sendDirectSQL(sql) {
    addMessage('user', escapeHtml(sql));
    dom.queryInput.value = '';
    dom.queryInput.style.height = 'auto';

    const msgDiv = addMessage('assistant', '<div class="loading-dots"><span></span><span></span><span></span></div>');
    const contentDiv = msgDiv.querySelector('.message-content');

    try {
        if (!state.currentConversationId) {
            const convData = await API.post('/api/conversations', { title: `[SQL] ${sql.slice(0, 50)}` });
            state.currentConversationId = convData.id;
            await loadConversations();
        }

        const queryParams = {
            sql,
            conversation_id: state.currentConversationId
        };

        state.pendingQuestion = sql;

        contentDiv.innerHTML = '<div class="streaming-indicator">正在执行 SQL...</div>';

        const data = await API.post('/api/sql/execute', queryParams);

        if (!data.success) {
            if (data.requires_confirmation) {
                contentDiv.innerHTML = '';
                contentDiv.appendChild(addSQLBlock(data.sql));

                if (data.warning) {
                    const warnDiv = document.createElement('div');
                    warnDiv.className = 'sql-warning-box';
                    warnDiv.textContent = `⚠️ ${data.warning}`;
                    warnDiv.style.display = 'block';
                    contentDiv.insertBefore(warnDiv, contentDiv.firstChild);
                }

                window.pendingSQLData = {
                    question: `[SQL] ${sql.slice(0, 100)}`,
                    sql: data.sql,
                    sqlHash: null,
                    conversationId: state.currentConversationId,
                    contentDiv: contentDiv,
                    msgDiv: msgDiv,
                    isDirectSQL: true
                };
                showSQLConfirmDialog({
                    requires_confirmation: true,
                    confirmation_reason: data.confirmation_reason,
                    warning: data.warning,
                    risk_level: data.risk_level,
                    sql: data.sql
                });
                return;
            }

            contentDiv.innerHTML = `<div class="error-message">${escapeHtml(data.error)}</div>`;
            return;
        }

        contentDiv.innerHTML = '';

        const operationLabel = document.createElement('div');
        operationLabel.className = 'message-label';
        operationLabel.textContent = 'SQL 直接查询';
        contentDiv.appendChild(operationLabel);

        contentDiv.appendChild(addSQLBlock(data.sql));

        if (data.result) {
            contentDiv.appendChild(addResultTable(data.result, data.pagination, {
                historyId: data.history_id,
                sql: data.sql,
                question: sql,
                conversationId: state.currentConversationId
            }));
        }
    } catch (err) {
        contentDiv.innerHTML = `<div class="error-message">${escapeHtml(err.message)}</div>`;
    }

    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
    loadConversations();
}

function switchQueryMode(mode) {
    state.queryMode = mode;
    const textarea = dom.queryInput;
    const placeholderEl = $('query-placeholder');

    if (mode === 'sql') {
        textarea.placeholder = '输入 SQL 语句，例如：SELECT * FROM users WHERE id = 1';
        if (placeholderEl) placeholderEl.textContent = '输入 SQL 语句';
    } else {
        textarea.placeholder = '输入自然语言查询，例如：查询所有用户的姓名和邮箱';
        if (placeholderEl) placeholderEl.textContent = '按 Enter 发送，Shift+Enter 换行';
    }

    const nlBtn = $('btn-mode-nl');
    const sqlBtn = $('btn-mode-sql');
    if (nlBtn) nlBtn.classList.toggle('active', mode === 'nl');
    if (sqlBtn) sqlBtn.classList.toggle('active', mode === 'sql');

    updateConnectionStatus();
}

window.updateConnectionStatus = updateConnectionStatus;
window.refreshSchema = refreshSchema;
window.addMessage = addMessage;
window.addSQLBlock = addSQLBlock;
window.addResultTable = addResultTable;
window.changePage = changePage;
window.sendQuery = sendQuery;
window.showExportMenu = showExportMenu;
window.switchQueryMode = switchQueryMode;
window.sendDirectSQL = sendDirectSQL;
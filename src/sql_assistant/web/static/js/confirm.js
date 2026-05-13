/**
 * SQL Confirmation Dialog Module
 */

window.pendingSQLData = null;

function showSQLConfirmDialog(previewData) {
    const modal = document.getElementById('sql-confirm-modal');
    const titleEl = document.getElementById('sql-confirm-title');
    const warningEl = document.getElementById('sql-confirm-warning');
    const reasonEl = document.getElementById('sql-confirm-reason');
    const codeEl = document.getElementById('sql-confirm-code');

    titleEl.textContent = '⚠️ 确认执行 SQL';

    if (previewData.warning) {
        warningEl.textContent = previewData.warning;
        warningEl.style.display = 'block';
        warningEl.className = 'sql-warning-box ' + previewData.risk_level;
    } else {
        warningEl.style.display = 'none';
    }

    reasonEl.textContent = previewData.confirmation_reason || '此操作可能修改数据，请确认后再执行';

    codeEl.textContent = previewData.sql;
    if (typeof hljs !== 'undefined') {
        hljs.highlightElement(codeEl);
    }

    modal.classList.add('active');
}

function hideSQLConfirmDialog() {
    const modal = document.getElementById('sql-confirm-modal');
    modal.classList.remove('active');
    window.pendingSQLData = null;
}

async function confirmAndExecuteSQL() {
    if (!window.pendingSQLData) return;

    const { question, sql, sqlHash, conversationId, contentDiv, msgDiv } = window.pendingSQLData;

    hideSQLConfirmDialog();

    const existingLoading = contentDiv.querySelector('.loading-dots');
    if (existingLoading) existingLoading.remove();

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-dots';
    loadingDiv.innerHTML = '<span></span><span></span><span></span>';
    loadingDiv.style.marginTop = '12px';
    contentDiv.appendChild(loadingDiv);

    const queryParams = {
        question,
        conversation_id: conversationId,
        confirmed: true,
        sql_hash: sqlHash,
        sql: sql  // 直接传递 SQL 语句，避免 LLM 重新生成导致 hash 不匹配
    };

    await executeConfirmedQuery(queryParams, contentDiv, msgDiv);
}

async function executeConfirmedQuery(queryParams, contentDiv, msgDiv) {
    try {
        const data = await API.post('/api/query', queryParams);

        // 移除 loading 动画
        const loadingDots = contentDiv.querySelector('.loading-dots');
        if (loadingDots) loadingDots.remove();

        if (data.result) {
            contentDiv.appendChild(addResultTable(data.result, data.pagination));
        }

        if (data.error && !data.result) {
            contentDiv.innerHTML += `<div class="error-message">${escapeHtml(data.error)}</div>`;
        }
    } catch (err) {
        const loadingDots = contentDiv.querySelector('.loading-dots');
        if (loadingDots) loadingDots.remove();
        contentDiv.innerHTML += `<div class="error-message">${escapeHtml(err.message)}</div>`;
    }

    dom.chatMessages.scrollTop = dom.chatMessages.scrollTop;
    loadConversations();
}

window.showSQLConfirmDialog = showSQLConfirmDialog;
window.hideSQLConfirmDialog = hideSQLConfirmDialog;
window.confirmAndExecuteSQL = confirmAndExecuteSQL;
window.executeConfirmedQuery = executeConfirmedQuery;
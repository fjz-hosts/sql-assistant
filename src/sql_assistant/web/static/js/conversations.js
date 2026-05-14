/**
 * Conversation Management Module
 */

// ============================================================
// Conversation Management
// ============================================================
async function loadConversations() {
    try {
        const data = await API.get('/api/conversations');
        state.conversations = data.conversations || [];
        renderConversations();
        
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
                <span>${c.updated_at?.split(' ')[0] || ''}</span>
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

// Expose functions
window.loadConversations = loadConversations;
window.renderConversations = renderConversations;
window.startRenameConversation = startRenameConversation;
window.createNewConversation = createNewConversation;
window.selectConversation = selectConversation;
window.deleteConversation = deleteConversation;
window.clearChatMessages = clearChatMessages;
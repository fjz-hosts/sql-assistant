/**
 * SQL Explain Plan Module - SQL执行计划分析模块
 */

class ExplainManager {
    constructor() {
        this.history = [];
        this.currentPlan = null;
        this.stats = null;
    }

    /**
     * 初始化
     */
    init() {
        this.bindEvents();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 新建分析按钮
        const analyzeBtn = document.getElementById('btn-explain-analyze');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.showInputForm());
        }

        // 关闭面板
        const closeBtn = document.getElementById('btn-close-explain');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }

        // 历史记录按钮
        const historyBtn = document.getElementById('btn-explain-history');
        if (historyBtn) {
            historyBtn.addEventListener('click', () => this.showHistory());
        }

        // 统计按钮
        const statsBtn = document.getElementById('btn-explain-stats');
        if (statsBtn) {
            statsBtn.addEventListener('click', () => this.showStats());
        }

        // 关闭详情
        const closeDetailBtn = document.getElementById('btn-close-explain-detail');
        if (closeDetailBtn) {
            closeDetailBtn.addEventListener('click', () => this.closeDetailPanel());
        }

        // 点击遮罩关闭
        const overlay = document.getElementById('explain-overlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.closePanel();
                }
            });
        }
    }

    /**
     * 显示执行计划面板
     */
    showPanel() {
        const panel = document.getElementById('explain-panel');
        const overlay = document.getElementById('explain-overlay');
        if (panel && overlay) {
            panel.classList.add('active');
            overlay.classList.add('active');
            this.loadHistory();
            this.loadStats();
        }
    }

    /**
     * 关闭面板
     */
    closePanel() {
        const panel = document.getElementById('explain-panel');
        const overlay = document.getElementById('explain-overlay');
        if (panel && overlay) {
            panel.classList.remove('active');
            overlay.classList.remove('active');
        }
    }

    /**
     * 显示输入表单
     */
    showInputForm() {
        const content = document.getElementById('explain-content');
        if (content) {
            content.innerHTML = `
                <div class="explain-input-section">
                    <textarea id="explain-sql-input" placeholder="在此输入SQL语句进行分析...&#10;&#10;例如: SELECT * FROM users WHERE status = 1"></textarea>
                    <button class="btn-explain-submit" onclick="explainManager.analyzeInputSQL()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
                        分析SQL
                    </button>
                </div>
                <div class="empty-state" style="margin-top: 20px;">
                    <p>💡 提示：您也可以在聊天消息的SQL代码块右侧点击"分析"按钮</p>
                    <p style="font-size: 12px; margin-top: 8px;">支持 MySQL、PostgreSQL、SQL Server 的 SELECT 语句</p>
                </div>
            `;
        }
    }

    /**
     * 分析当前SQL（从主输入框）
     */
    async analyzeCurrentSQL() {
        const sqlInput = document.getElementById('query-input');
        if (!sqlInput) return;

        const sql = sqlInput.value.trim();
        if (!sql) {
            showToast('请在主输入框中输入SQL语句', 'warning');
            return;
        }

        // 检查是否是SELECT语句
        if (!sql.match(/^\s*SELECT/i)) {
            showToast('执行计划分析仅支持SELECT语句', 'warning');
            return;
        }

        await this.analyzeSQL(sql);
    }

    /**
     * 分析输入框中的SQL（面板内输入）
     */
    async analyzeInputSQL() {
        const sqlInput = document.getElementById('explain-sql-input');
        if (!sqlInput) return;

        const sql = sqlInput.value.trim();
        if (!sql) {
            showToast('请输入SQL语句', 'warning');
            return;
        }

        // 检查是否是SELECT语句
        if (!sql.match(/^\s*SELECT/i)) {
            showToast('执行计划分析仅支持SELECT语句', 'warning');
            return;
        }

        await this.analyzeSQL(sql);
    }

    /**
     * 分析SQL
     */
    async analyzeSQL(sql) {
        const loadingEl = document.getElementById('explain-loading');
        const contentEl = document.getElementById('explain-content');

        if (loadingEl) loadingEl.style.display = 'flex';
        if (contentEl) contentEl.style.display = 'none';

        try {
            const response = await API.post('/api/explain/analyze', {
                sql: sql,
                analyze: true
            });

            if (response.success) {
                this.currentPlan = response;
                this.renderPlan(response);
                await this.loadHistory();
                showToast('执行计划分析完成', 'success');
            } else {
                showToast(response.error || '分析失败', 'error');
            }
        } catch (error) {
            showToast('分析失败: ' + error.message, 'error');
        } finally {
            if (loadingEl) loadingEl.style.display = 'none';
            if (contentEl) contentEl.style.display = 'block';
        }
    }

    /**
     * 渲染执行计划
     */
    renderPlan(plan) {
        const container = document.getElementById('explain-content');
        if (!container) return;

        const isSlow = plan.is_slow_query;
        const costLevel = this._getCostLevel(plan.estimated_cost);
        const timeLevel = this._getTimeLevel(plan.actual_time_ms);

        container.innerHTML = `
            <div class="explain-header">
                <div class="explain-title">
                    <span class="db-badge ${plan.db_type}">${plan.db_type}</span>
                    <span class="db-name">${escapeHtml(plan.db_name)}</span>
                    ${isSlow ? '<span class="slow-badge">慢查询</span>' : ''}
                </div>
                <div class="explain-actions">
                    <button class="btn-text" onclick="explainManager.viewRawPlan()">查看原始计划</button>
                </div>
            </div>

            <div class="explain-sql">
                <pre><code class="language-sql">${escapeHtml(plan.sql)}</code></pre>
            </div>

            <div class="explain-metrics">
                <div class="metric-card ${costLevel}">
                    <div class="metric-value">${plan.estimated_cost.toFixed(2)}</div>
                    <div class="metric-label">估计成本</div>
                </div>
                <div class="metric-card ${plan.estimated_rows > 10000 ? 'warning' : ''}">
                    <div class="metric-value">${plan.estimated_rows.toLocaleString()}</div>
                    <div class="metric-label">估计行数</div>
                </div>
                <div class="metric-card ${timeLevel}">
                    <div class="metric-value">${plan.actual_time_ms.toFixed(2)}ms</div>
                    <div class="metric-label">实际时间</div>
                </div>
            </div>

            ${plan.warnings.length > 0 ? `
            <div class="explain-warnings">
                <h4>⚠️ 警告</h4>
                <ul>
                    ${plan.warnings.map(w => `<li>${escapeHtml(w)}</li>`).join('')}
                </ul>
            </div>
            ` : ''}

            ${plan.suggestions.length > 0 ? `
            <div class="explain-suggestions">
                <h4>💡 优化建议</h4>
                <ul>
                    ${plan.suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                </ul>
            </div>
            ` : ''}

            ${plan.plan_tree ? `
            <div class="explain-tree">
                <h4>📊 执行计划树</h4>
                <div class="plan-tree-container">
                    ${this._renderPlanTree(plan.plan_tree)}
                </div>
            </div>
            ` : ''}
        `;

        // 高亮SQL
        if (window.hljs) {
            container.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
        }
    }

    /**
     * 渲染计划树
     */
    _renderPlanTree(node, level = 0) {
        if (!node) return '';

        const indent = level * 24;
        const hasChildren = node.children && node.children.length > 0;
        const nodeClass = this._getNodeClass(node);

        let html = `
            <div class="plan-node ${nodeClass}" style="margin-left: ${indent}px">
                <div class="plan-node-header">
                    <span class="node-type">${escapeHtml(node.node_type)}</span>
                    ${node.table_name ? `<span class="node-table">${escapeHtml(node.table_name)}</span>` : ''}
                </div>
                <div class="plan-node-details">
                    ${node.access_type ? `<span class="node-detail">访问: ${escapeHtml(node.access_type)}</span>` : ''}
                    ${node.key ? `<span class="node-detail">索引: ${escapeHtml(node.key)}</span>` : ''}
                    ${node.rows ? `<span class="node-detail">行数: ${node.rows.toLocaleString()}</span>` : ''}
                    ${node.cost ? `<span class="node-detail">成本: ${node.cost.toFixed(2)}</span>` : ''}
                    ${node.actual_time ? `<span class="node-detail">时间: ${node.actual_time.toFixed(2)}ms</span>` : ''}
                </div>
                ${node.extra ? `<div class="node-extra">${escapeHtml(node.extra)}</div>` : ''}
            </div>
        `;

        if (hasChildren) {
            html += `<div class="plan-children">`;
            for (const child of node.children) {
                html += this._renderPlanTree(child, level + 1);
            }
            html += `</div>`;
        }

        return html;
    }

    /**
     * 获取节点样式类
     */
    _getNodeClass(node) {
        const accessType = (node.access_type || '').toUpperCase();
        const nodeType = (node.node_type || '').toUpperCase();

        if (accessType.includes('FULL') || accessType.includes('ALL') || accessType.includes('SEQ')) {
            return 'node-warning';
        }
        if (nodeType.includes('INDEX')) {
            return 'node-info';
        }
        if (nodeType.includes('JOIN')) {
            return 'node-join';
        }
        return '';
    }

    /**
     * 获取成本级别
     */
    _getCostLevel(cost) {
        if (cost > 10000) return 'danger';
        if (cost > 1000) return 'warning';
        return 'success';
    }

    /**
     * 获取时间级别
     */
    _getTimeLevel(time) {
        if (time > 1000) return 'danger';
        if (time > 100) return 'warning';
        return 'success';
    }

    /**
     * 查看原始计划
     */
    viewRawPlan() {
        if (!this.currentPlan || !this.currentPlan.plan_text) {
            showToast('无原始计划数据', 'warning');
            return;
        }

        const modal = document.createElement('div');
        modal.className = 'modal-overlay active';
        modal.innerHTML = `
            <div class="modal-container" style="max-width: 800px; max-height: 80vh;">
                <div class="modal-header">
                    <h3>原始执行计划</h3>
                    <button class="btn-icon" onclick="this.closest('.modal-overlay').remove()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="modal-body">
                    <pre style="overflow: auto; max-height: 60vh; background: var(--bg-secondary); padding: 16px; border-radius: 8px;"><code>${escapeHtml(this.currentPlan.plan_text)}</code></pre>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    /**
     * 加载历史记录
     */
    async loadHistory() {
        try {
            const response = await API.get('/api/explain/history?limit=20');
            this.history = response.records || [];
            this.renderHistory();
        } catch (error) {
            console.error('加载执行计划历史失败:', error);
        }
    }

    /**
     * 渲染历史记录
     */
    renderHistory() {
        const container = document.getElementById('explain-history-list');
        if (!container) return;

        if (this.history.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无执行计划历史</div>';
            return;
        }

        container.innerHTML = this.history.map(plan => `
            <div class="explain-history-item ${plan.is_slow_query ? 'slow' : ''}">
                <div class="history-content" onclick="explainManager.viewPlanDetail(${plan.id})">
                    <div class="history-sql">${escapeHtml(plan.sql.substring(0, 60))}${plan.sql.length > 60 ? '...' : ''}</div>
                    <div class="history-meta">
                        <span class="db-badge ${plan.db_type}">${plan.db_type}</span>
                        <span class="history-cost">成本: ${plan.estimated_cost.toFixed(2)}</span>
                        <span class="history-time">${plan.created_at}</span>
                        ${plan.is_slow_query ? '<span class="slow-badge">慢</span>' : ''}
                    </div>
                </div>
                <button class="history-delete-btn" onclick="event.stopPropagation(); explainManager.deletePlan(${plan.id})" title="删除">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        `).join('');
    }

    /**
     * 删除执行计划
     */
    async deletePlan(planId) {
        try {
            const response = await API.del(`/api/explain/history/${planId}`);
            if (response.success) {
                showToast('删除成功', 'success');
                await this.loadHistory();
            } else {
                showToast(response.error || '删除失败', 'error');
            }
        } catch (error) {
            showToast('删除失败: ' + error.message, 'error');
        }
    }

    /**
     * 显示历史记录
     */
    showHistory() {
        const content = document.getElementById('explain-content');
        if (content) {
            content.innerHTML = `
                <div class="explain-section">
                    <h4>📜 执行计划历史</h4>
                    <div id="explain-history-list"></div>
                </div>
            `;
            this.renderHistory();
        }
    }

    /**
     * 查看计划详情
     */
    async viewPlanDetail(planId) {
        try {
            const response = await API.get(`/api/explain/history/${planId}`);
            if (response.success) {
                this.currentPlan = response;
                this.renderPlan(response);
            }
        } catch (error) {
            showToast('加载详情失败', 'error');
        }
    }

    /**
     * 加载统计
     */
    async loadStats() {
        try {
            const response = await API.get('/api/explain/stats');
            this.stats = response;
            this.renderStats();
        } catch (error) {
            console.error('加载统计失败:', error);
        }
    }

    /**
     * 渲染统计
     */
    renderStats() {
        const container = document.getElementById('explain-stats');
        if (!container || !this.stats) return;

        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${this.stats.total_plans}</div>
                    <div class="stat-label">总分析次数</div>
                </div>
                <div class="stat-item ${this.stats.slow_query_count > 0 ? 'warning' : ''}">
                    <div class="stat-value">${this.stats.slow_query_count}</div>
                    <div class="stat-label">慢查询</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${this.stats.average_cost.toFixed(2)}</div>
                    <div class="stat-label">平均成本</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${this.stats.max_cost.toFixed(2)}</div>
                    <div class="stat-label">最高成本</div>
                </div>
            </div>
        `;
    }

    /**
     * 显示统计
     */
    showStats() {
        const content = document.getElementById('explain-content');
        if (content) {
            content.innerHTML = `
                <div class="explain-section">
                    <h4>📊 执行计划统计</h4>
                    <div id="explain-stats"></div>
                </div>
            `;
            this.renderStats();
        }
    }

    /**
     * 关闭详情面板
     */
    closeDetailPanel() {
        const panel = document.getElementById('explain-detail-panel');
        if (panel) {
            panel.classList.remove('active');
        }
    }
}

// 创建全局实例
const explainManager = new ExplainManager();

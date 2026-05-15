/**
 * Database Health Check Module
 */

class HealthManager {
    constructor() {
        this.currentTab = 'overview';
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const healthBtn = document.getElementById('btn-health');
        if (healthBtn) {
            healthBtn.addEventListener('click', () => this.showPanel());
        }

        const closeBtn = document.getElementById('btn-close-health');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }

        const overlay = document.getElementById('health-overlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.closePanel();
                }
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closePanel();
            }
        });
    }

    showPanel() {
        const panel = document.getElementById('health-panel');
        const overlay = document.getElementById('health-overlay');
        if (panel && overlay) {
            panel.classList.add('active');
            overlay.classList.add('active');
            this.loadOverview();
        }
    }

    closePanel() {
        const panel = document.getElementById('health-panel');
        const overlay = document.getElementById('health-overlay');
        if (panel && overlay) {
            panel.classList.remove('active');
            overlay.classList.remove('active');
        }
    }

    switchTab(tab) {
        this.currentTab = tab;
        const tabs = document.querySelectorAll('.health-tab');
        tabs.forEach(t => t.classList.remove('active'));

        const tabEl = document.querySelector(`[data-tab="${tab}"]`);
        if (tabEl) tabEl.classList.add('active');

        if (tab === 'overview') {
            this.loadOverview();
        } else if (tab === 'connection') {
            this.loadConnection();
        } else if (tab === 'tables') {
            this.loadTables();
        } else if (tab === 'indexes') {
            this.loadIndexes();
        } else if (tab === 'performance') {
            this.loadPerformance();
        }
    }

    async loadOverview() {
        const content = document.getElementById('health-content');
        if (!content) return;

        content.innerHTML = '<div class="health-loading"><div class="spinner"></div><p>正在检查数据库健康状态...</p></div>';

        try {
            const data = await API.get('/api/health');
            if (data.success) {
                content.innerHTML = `
                    <div class="health-overview">
                        <div class="health-status-card ${data.status}">
                            <div class="status-icon">
                                ${data.status === 'healthy'
                                    ? '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
                                    : '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
                                }
                            </div>
                            <div class="status-text">
                                <h3>${data.status === 'healthy' ? '数据库连接正常' : '数据库连接异常'}</h3>
                                <p class="db-type">${data.db_type?.toUpperCase() || 'Unknown'}</p>
                            </div>
                        </div>

                        <div class="health-metrics-grid">
                            <div class="metric-card">
                                <div class="metric-label">响应时间</div>
                                <div class="metric-value">${data.response_time_ms} ms</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">连接状态</div>
                                <div class="metric-value status-badge ${data.connection_ok ? 'success' : 'danger'}">
                                    ${data.connection_ok ? '已连接' : '未连接'}
                                </div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">检查时间</div>
                                <div class="metric-value time">${data.timestamp || '-'}</div>
                            </div>
                        </div>

                        ${data.error_message ? `
                            <div class="health-error">
                                <strong>错误信息:</strong> ${escapeHtml(data.error_message)}
                            </div>
                        ` : ''}

                        <div class="health-actions">
                            <button class="btn-primary" onclick="healthManager.switchTab('connection')">
                                详细连接信息
                            </button>
                            <button class="btn-primary" onclick="healthManager.switchTab('tables')">
                                表信息
                            </button>
                            <button class="btn-primary" onclick="healthManager.switchTab('performance')">
                                性能指标
                            </button>
                        </div>
                    </div>
                `;
            } else {
                content.innerHTML = '<div class="empty-state">获取健康状态失败</div>';
            }
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    async loadConnection() {
        const content = document.getElementById('health-content');
        if (!content) return;

        content.innerHTML = '<div class="health-loading"><div class="spinner"></div><p>正在加载连接信息...</p></div>';

        try {
            const data = await API.get('/api/health/connection');
            if (data.success) {
                const uptime = this.formatUptime(data.uptime_seconds);
                content.innerHTML = `
                    <div class="health-connection-info">
                        <div class="info-section">
                            <h4>基本信息</h4>
                            <div class="info-grid">
                                <div class="info-item">
                                    <span class="info-label">数据库类型</span>
                                    <span class="info-value">${data.db_type?.toUpperCase() || '-'}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">连接状态</span>
                                    <span class="info-value status-badge ${data.connection_ok ? 'success' : 'danger'}">
                                        ${data.connection_ok ? '已连接' : '未连接'}
                                    </span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">响应时间</span>
                                    <span class="info-value">${data.response_time_ms} ms</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">运行时间</span>
                                    <span class="info-value">${uptime}</span>
                                </div>
                            </div>
                        </div>

                        <div class="info-section">
                            <h4>连接统计</h4>
                            <div class="info-grid">
                                <div class="info-item">
                                    <span class="info-label">当前连接数</span>
                                    <span class="info-value">${data.current_connections || 0}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">最大连接数</span>
                                    <span class="info-value">${data.max_connections || 0}</span>
                                </div>
                                <div class="info-item">
                                    <span class="info-label">连接使用率</span>
                                    <span class="info-value">${data.max_connections > 0
                                        ? ((data.current_connections / data.max_connections) * 100).toFixed(1) + '%'
                                        : '-'}</span>
                                </div>
                            </div>
                        </div>

                        ${data.error_message ? `
                            <div class="health-error">
                                <strong>错误信息:</strong> ${escapeHtml(data.error_message)}
                            </div>
                        ` : ''}

                        <div class="health-refresh">
                            <button class="btn-text" onclick="healthManager.loadConnection()">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
                                刷新
                            </button>
                        </div>
                    </div>
                `;
            } else {
                content.innerHTML = '<div class="empty-state">获取连接信息失败</div>';
            }
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    async loadTables() {
        const content = document.getElementById('health-content');
        if (!content) return;

        content.innerHTML = '<div class="health-loading"><div class="spinner"></div><p>正在加载表信息...</p></div>';

        try {
            const data = await API.get('/api/health/tables');
            if (data.success) {
                const tablesHtml = data.tables && data.tables.length > 0
                    ? data.tables.map(t => `
                        <tr>
                            <td class="table-name">${escapeHtml(t.name)}</td>
                            <td>${t.engine || '-'}</td>
                            <td class="numeric">${this.formatNumber(t.row_count)}</td>
                            <td class="numeric">${t.size_mb?.toFixed(2) || '0.00'} MB</td>
                            <td class="numeric">${t.index_length_mb?.toFixed(2) || '0.00'} MB</td>
                            <td class="numeric">${t.data_length_mb?.toFixed(2) || '0.00'} MB</td>
                        </tr>
                    `).join('')
                    : '<tr><td colspan="6" class="empty">暂无表数据</td></tr>';

                content.innerHTML = `
                    <div class="health-tables-info">
                        <div class="tables-summary">
                            <div class="summary-item">
                                <span class="summary-label">数据库类型</span>
                                <span class="summary-value">${data.db_type?.toUpperCase() || '-'}</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">表数量</span>
                                <span class="summary-value">${data.table_count || 0}</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">总行数</span>
                                <span class="summary-value">${this.formatNumber(data.total_rows || 0)}</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">总大小</span>
                                <span class="summary-value">${data.total_size_mb?.toFixed(2) || '0.00'} MB</span>
                            </div>
                        </div>

                        <div class="tables-table-wrapper">
                            <table class="tables-table">
                                <thead>
                                    <tr>
                                        <th>表名</th>
                                        <th>引擎</th>
                                        <th>行数</th>
                                        <th>总大小</th>
                                        <th>索引大小</th>
                                        <th>数据大小</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${tablesHtml}
                                </tbody>
                            </table>
                        </div>

                        <div class="health-refresh">
                            <button class="btn-text" onclick="healthManager.loadTables()">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
                                刷新
                            </button>
                        </div>
                    </div>
                `;
            } else {
                content.innerHTML = '<div class="empty-state">获取表信息失败</div>';
            }
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    async loadIndexes() {
        const content = document.getElementById('health-content');
        if (!content) return;

        content.innerHTML = '<div class="health-loading"><div class="spinner"></div><p>正在加载索引信息...</p></div>';

        try {
            const data = await API.get('/api/health/indexes');
            if (data.success) {
                let indexesHtml = '';
                const tableNames = Object.keys(data.indexes_by_table || {});

                if (tableNames.length > 0) {
                    indexesHtml = tableNames.map(tableName => {
                        const indexes = data.indexes_by_table[tableName];
                        return `
                            <div class="index-group">
                                <div class="index-group-header">
                                    <span class="index-table-name">${escapeHtml(tableName)}</span>
                                    <span class="index-count">${indexes.length} 个索引</span>
                                </div>
                                <div class="index-list">
                                    ${indexes.map(idx => `
                                        <div class="index-item">
                                            <div class="index-name">
                                                ${escapeHtml(idx.index_name)}
                                                ${idx.unique ? '<span class="index-badge unique">唯一</span>' : ''}
                                            </div>
                                            <div class="index-column">${escapeHtml(idx.column_name)}</div>
                                            <div class="index-cardinality">基数: ${this.formatNumber(idx.cardinality)}</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    indexesHtml = '<div class="empty-state">暂无索引数据</div>';
                }

                content.innerHTML = `
                    <div class="health-indexes-info">
                        <div class="indexes-summary">
                            <div class="summary-item">
                                <span class="summary-label">数据库类型</span>
                                <span class="summary-value">${data.db_type?.toUpperCase() || '-'}</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">表数量</span>
                                <span class="summary-value">${data.table_count || 0}</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">索引总数</span>
                                <span class="summary-value">${data.total_indexes || 0}</span>
                            </div>
                        </div>

                        <div class="indexes-list">
                            ${indexesHtml}
                        </div>

                        <div class="health-refresh">
                            <button class="btn-text" onclick="healthManager.loadIndexes()">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
                                刷新
                            </button>
                        </div>
                    </div>
                `;
            } else {
                content.innerHTML = '<div class="empty-state">获取索引信息失败</div>';
            }
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    async loadPerformance() {
        const content = document.getElementById('health-content');
        if (!content) return;

        content.innerHTML = '<div class="health-loading"><div class="spinner"></div><p>正在加载性能指标...</p></div>';

        try {
            const data = await API.get('/api/health/performance');
            if (data.success) {
                const uptime = this.formatUptime(data.uptime_seconds);
                content.innerHTML = `
                    <div class="health-performance-info">
                        <div class="performance-overview">
                            <div class="performance-status ${data.status}">
                                <div class="perf-icon">
                                    ${data.status === 'healthy'
                                        ? '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
                                        : '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
                                    }
                                </div>
                                <div class="perf-text">
                                    <span class="perf-status">${data.status === 'healthy' ? '正常' : '异常'}</span>
                                    <span class="perf-db">${data.db_type?.toUpperCase() || ''}</span>
                                </div>
                            </div>

                            <div class="perf-metric highlight">
                                <div class="perf-metric-value">${data.response_time_ms} ms</div>
                                <div class="perf-metric-label">平均响应时间</div>
                            </div>
                        </div>

                        <div class="performance-grid">
                            <div class="perf-card">
                                <div class="perf-card-header">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                                    运行时间
                                </div>
                                <div class="perf-card-value">${uptime}</div>
                            </div>

                            <div class="perf-card">
                                <div class="perf-card-header">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                                    当前连接
                                </div>
                                <div class="perf-card-value">${data.current_connections || 0} <span class="perf-unit">/ ${data.max_connections || 0}</span></div>
                            </div>

                            <div class="perf-card">
                                <div class="perf-card-header">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                                    慢查询
                                </div>
                                <div class="perf-card-value ${(data.slow_queries || 0) > 0 ? 'warning' : ''}">${data.slow_queries || 0}</div>
                            </div>

                            <div class="perf-card">
                                <div class="perf-card-header">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                                    QPS
                                </div>
                                <div class="perf-card-value">${(data.query_per_second || 0).toFixed(2)}</div>
                            </div>
                        </div>

                        <div class="health-refresh">
                            <button class="btn-text" onclick="healthManager.loadPerformance()">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
                                刷新
                            </button>
                        </div>
                    </div>
                `;
            } else {
                content.innerHTML = '<div class="empty-state">获取性能指标失败</div>';
            }
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    formatUptime(seconds) {
        if (!seconds) return '-';
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);

        const parts = [];
        if (days > 0) parts.push(`${days} 天`);
        if (hours > 0) parts.push(`${hours} 小时`);
        if (minutes > 0) parts.push(`${minutes} 分钟`);

        return parts.length > 0 ? parts.join(' ') : '< 1 分钟';
    }
}

const healthManager = new HealthManager();
window.healthManager = healthManager;

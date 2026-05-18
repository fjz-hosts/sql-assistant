/**
 * Data Insights Module
 */

class InsightsManager {
    constructor() {
        this.currentTab = 'overview';
        this.currentTable = '';
        this.tables = [];
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const insightsBtn = document.getElementById('btn-insights');
        if (insightsBtn) {
            insightsBtn.addEventListener('click', () => this.showPanel());
        }

        const closeBtn = document.getElementById('btn-close-insights');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }

        const overlay = document.getElementById('insights-overlay');
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
        const panel = document.getElementById('insights-panel');
        const overlay = document.getElementById('insights-overlay');
        if (panel && overlay) {
            panel.classList.add('active');
            overlay.classList.add('active');
            this.loadTables();
        }
    }

    closePanel() {
        const panel = document.getElementById('insights-panel');
        const overlay = document.getElementById('insights-overlay');
        if (panel && overlay) {
            panel.classList.remove('active');
            overlay.classList.remove('active');
        }
    }

    switchTab(tab) {
        this.currentTab = tab;
        const tabs = document.querySelectorAll('.insights-tab');
        tabs.forEach(t => t.classList.remove('active'));

        const tabEl = document.querySelector(`[data-tab="${tab}"]`);
        if (tabEl) tabEl.classList.add('active');

        if (this.currentTable) {
            if (tab === 'overview') {
                this.loadOverview();
            } else if (tab === 'summary') {
                this.loadSummary();
            } else if (tab === 'outliers') {
                this.loadOutliers();
            } else if (tab === 'trends') {
                this.loadTrends();
            } else if (tab === 'report') {
                this.loadReport();
            }
        } else {
            this.showEmptyState();
        }
    }

    async loadTables() {
        const selector = document.getElementById('insights-table-select');
        if (!selector) return;

        try {
            const data = await API.get('/api/insights/tables');
            if (data.tables && data.tables.length > 0) {
                this.tables = data.tables;
                selector.innerHTML = data.tables.map(t => 
                    `<option value="${escapeHtml(t.name)}">${escapeHtml(t.name)}</option>`
                ).join('');
                
                this.currentTable = data.tables[0].name;
                this.loadOverview();
            } else {
                selector.innerHTML = '<option value="">暂无数据表</option>';
                this.showEmptyState();
            }
        } catch (err) {
            selector.innerHTML = '<option value="">加载失败</option>';
            this.showEmptyState();
        }
    }

    onTableChange() {
        const selector = document.getElementById('insights-table-select');
        if (selector) {
            this.currentTable = selector.value;
            if (this.currentTable) {
                this.switchTab(this.currentTab);
            } else {
                this.showEmptyState();
            }
        }
    }

    showEmptyState() {
        const content = document.getElementById('insights-content');
        if (content) {
            content.innerHTML = `
                <div class="empty-state">
                    <p>请先选择数据表</p>
                    <p style="font-size: 12px; margin-top: 8px;">需要先配置数据库连接</p>
                </div>
            `;
        }
    }

    async loadOverview() {
        const content = document.getElementById('insights-content');
        if (!content || !this.currentTable) return;

        content.innerHTML = '<div class="insights-loading"><div class="spinner"></div><p>正在生成数据洞察...</p></div>';

        try {
            const report = await API.get(`/api/insights/report/${encodeURIComponent(this.currentTable)}`);
            
            content.innerHTML = `
                <div class="insights-report-overview">
                    <div class="insights-report-title">
                        📊 数据洞察报告
                        <span class="insights-report-table-name">${escapeHtml(this.currentTable)}</span>
                    </div>
                    <div class="insights-report-timestamp">生成时间: ${report.generated_at || '-'}</div>

                    <!-- 数据摘要 -->
                    <div class="insights-report-section">
                        <div class="insights-report-section-header">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                            数据摘要
                        </div>
                        <div class="insights-summary-stats">
                            <div class="insights-stat-item">
                                <div class="insights-stat-label">总行数</div>
                                <div class="insights-stat-value">${this.formatNumber(report.summary.row_count || 0)}</div>
                            </div>
                            <div class="insights-stat-item">
                                <div class="insights-stat-label">列数</div>
                                <div class="insights-stat-value">${report.summary.column_count || 0}</div>
                            </div>
                        </div>
                    </div>

                    <!-- 异常检测 -->
                    ${report.outliers && report.outliers.length > 0 ? `
                        <div class="insights-report-section">
                            <div class="insights-report-section-header">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="22" x2="12" y2="15.5"/></svg>
                                异常检测
                            </div>
                            <div class="insights-outliers-list">
                                ${report.outliers.map(o => `
                                    <div class="insights-outlier-card">
                                        <div class="insights-outlier-header">
                                            <span class="insights-outlier-column">${escapeHtml(o.column_name)}</span>
                                            <span class="insights-outlier-count">${o.outlier_count} 个异常值</span>
                                        </div>
                                        <div class="insights-outlier-values">
                                            ${o.outliers.slice(0, 5).map(v => v.value).join(', ') || '-'}
                                            ${o.outliers.length > 5 ? '...' : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 趋势分析 -->
                    ${report.trends && report.trends.length > 0 ? `
                        <div class="insights-report-section">
                            <div class="insights-report-section-header">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10"/><path d="M8 20V4"/><path d="M3 20h18"/></svg>
                                趋势分析
                            </div>
                            <div class="insights-trends-list">
                                ${report.trends.map(t => `
                                    <div class="insights-trend-card">
                                        <div class="insights-trend-header">
                                            <span class="insights-trend-column">${escapeHtml(t.column_name)}</span>
                                            <span class="insights-trend-badge ${t.trend_type}">${this.getTrendLabel(t.trend_type)}</span>
                                        </div>
                                        <div class="insights-trend-score">趋势强度: ${(t.trend_score * 100).toFixed(0)}%</div>
                                        <div class="insights-trend-chart">
                                            ${this.renderTrendChart(t.data_points)}
                                        </div>
                                        ${t.prediction !== null && t.prediction !== undefined ? `
                                            <div class="insights-trend-prediction">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v6m0 0l3-3m-3 3l-3-3"/></svg>
                                                预测下一个值: ${t.prediction}
                                            </div>
                                        ` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- 建议 -->
                    ${report.recommendations && report.recommendations.length > 0 ? `
                        <div class="insights-report-section">
                            <div class="insights-report-section-header">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                                分析建议
                            </div>
                            <div class="insights-recommendations-list">
                                ${report.recommendations.map(r => `
                                    <div class="insights-recommendation-item ${this.getRecommendationClass(r)}">
                                        ${escapeHtml(r)}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    async loadSummary() {
        const content = document.getElementById('insights-content');
        if (!content || !this.currentTable) return;

        content.innerHTML = '<div class="insights-loading"><div class="spinner"></div><p>正在加载数据摘要...</p></div>';

        try {
            const summary = await API.get(`/api/insights/summary/${encodeURIComponent(this.currentTable)}`);
            
            const nullRateHtml = Object.entries(summary.null_rates || {}).map(([col, rate]) => `
                <div class="insights-column-item">
                    <div>
                        <span class="insights-column-name">${escapeHtml(col)}</span>
                        <div class="insights-null-rate">
                            <div class="insights-null-rate-bar">
                                <div class="insights-null-rate-fill" style="width: ${(rate * 100)}%"></div>
                            </div>
                            <span class="insights-null-rate-value">${(rate * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                    <span class="insights-column-type">${escapeHtml(summary.column_types?.[col] || '-')}</span>
                </div>
            `).join('');

            const statsHtml = Object.entries(summary.summary_stats || {}).map(([col, stats]) => `
                <div class="insights-summary-card">
                    <div class="insights-summary-header">
                        <h3>${escapeHtml(col)}</h3>
                    </div>
                    <div class="insights-summary-body">
                        <div class="insights-summary-stats">
                            <div class="insights-stat-item">
                                <div class="insights-stat-label">最小值</div>
                                <div class="insights-stat-value">${stats.min?.toFixed(2) || '-'}</div>
                            </div>
                            <div class="insights-stat-item">
                                <div class="insights-stat-label">最大值</div>
                                <div class="insights-stat-value">${stats.max?.toFixed(2) || '-'}</div>
                            </div>
                            <div class="insights-stat-item">
                                <div class="insights-stat-label">平均值</div>
                                <div class="insights-stat-value">${stats.avg?.toFixed(2) || '-'}</div>
                            </div>
                            <div class="insights-stat-item">
                                <div class="insights-stat-label">唯一值</div>
                                <div class="insights-stat-value">${stats.unique || '-'}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');

            const sampleHtml = summary.sample_rows && summary.sample_rows.length > 0 ? `
                <div class="insights-summary-card">
                    <div class="insights-summary-header">
                        <h3>样本数据</h3>
                    </div>
                    <div class="insights-summary-body">
                        <div class="insights-sample-data">
                            <table class="insights-sample-table">
                                <thead>
                                    <tr>${summary.columns?.slice(0, 6).map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>
                                </thead>
                                <tbody>
                                    ${summary.sample_rows.slice(0, 5).map(row => `
                                        <tr>${summary.columns?.slice(0, 6).map(c => `<td>${escapeHtml(String(row[c]) || '-')}</td>`).join('')}</tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            ` : '';

            content.innerHTML = `
                <div>
                    <div class="insights-summary-card">
                        <div class="insights-summary-header">
                            <h3>基本信息</h3>
                        </div>
                        <div class="insights-summary-body">
                            <div class="insights-summary-stats">
                                <div class="insights-stat-item">
                                    <div class="insights-stat-label">总行数</div>
                                    <div class="insights-stat-value">${this.formatNumber(summary.row_count || 0)}</div>
                                </div>
                                <div class="insights-stat-item">
                                    <div class="insights-stat-label">列数</div>
                                    <div class="insights-stat-value">${summary.column_count || 0}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="insights-summary-card">
                        <div class="insights-summary-header">
                            <h3>列信息与空值率</h3>
                        </div>
                        <div class="insights-summary-body">
                            <div class="insights-columns-list">
                                ${nullRateHtml || '<div class="empty-state">暂无列信息</div>'}
                            </div>
                        </div>
                    </div>

                    ${statsHtml}
                    ${sampleHtml}
                </div>
            `;
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    async loadOutliers() {
        const content = document.getElementById('insights-content');
        if (!content || !this.currentTable) return;

        content.innerHTML = '<div class="insights-loading"><div class="spinner"></div><p>正在检测异常值...</p></div>';

        try {
            const summary = await API.get(`/api/insights/summary/${encodeURIComponent(this.currentTable)}`);
            const numericCols = Object.entries(summary.column_types || {}).filter(
                ([, type]) => type && ['int', 'float', 'decimal', 'double', 'number'].some(t => type.toLowerCase().includes(t))
            ).map(([name]) => name);

            if (numericCols.length === 0) {
                content.innerHTML = '<div class="empty-state">该表没有数值列可分析</div>';
                return;
            }

            const outliers = await Promise.all(
                numericCols.map(col => API.get(`/api/insights/outliers/${encodeURIComponent(this.currentTable)}/${encodeURIComponent(col)}`))
            );

            const outliersHtml = outliers.map((outlier, idx) => {
                if (outlier.outlier_count === 0) return '';
                return `
                    <div class="insights-outlier-card">
                        <div class="insights-outlier-header">
                            <span class="insights-outlier-column">${escapeHtml(numericCols[idx])}</span>
                            <span class="insights-outlier-count">${outlier.outlier_count} 个异常值</span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">
                            检测方法: ${outlier.detection_method === 'zscore' ? 'Z-score' : 'IQR'}
                            ${outlier.threshold ? ` | 阈值: ${outlier.threshold}` : ''}
                        </div>
                        <div class="insights-outlier-values">
                            ${outlier.outliers.slice(0, 10).map(v => v.value).join(', ') || '-'}
                            ${outlier.outliers.length > 10 ? `... (共 ${outlier.outlier_count} 个)` : ''}
                        </div>
                    </div>
                `;
            }).join('');

            content.innerHTML = `
                <div>
                    <div style="margin-bottom: 16px; font-size: 13px; color: var(--text-secondary);">
                        已分析 ${numericCols.length} 个数值列
                    </div>
                    <div class="insights-outliers-list">
                        ${outliersHtml || '<div class="empty-state">未检测到异常值</div>'}
                    </div>
                </div>
            `;
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    async loadTrends() {
        const content = document.getElementById('insights-content');
        if (!content || !this.currentTable) return;

        content.innerHTML = '<div class="insights-loading"><div class="spinner"></div><p>正在分析趋势...</p></div>';

        try {
            const summary = await API.get(`/api/insights/summary/${encodeURIComponent(this.currentTable)}`);
            const numericCols = Object.entries(summary.column_types || {}).filter(
                ([, type]) => type && ['int', 'float', 'decimal', 'double', 'number'].some(t => type.toLowerCase().includes(t))
            ).map(([name]) => name);

            if (numericCols.length === 0) {
                content.innerHTML = '<div class="empty-state">该表没有数值列可分析</div>';
                return;
            }

            const dateCols = Object.entries(summary.column_types || {}).filter(
                ([, type]) => type && ['date', 'time', 'timestamp'].some(t => type.toLowerCase().includes(t))
            ).map(([name]) => name);

            const trends = await Promise.all(
                numericCols.slice(0, 4).map(col => 
                    API.get(`/api/insights/trend/${encodeURIComponent(this.currentTable)}/${encodeURIComponent(col)}${dateCols[0] ? `?date_column=${encodeURIComponent(dateCols[0])}` : ''}`)
                )
            );

            const trendsHtml = trends.map((trend, idx) => `
                <div class="insights-trend-card">
                    <div class="insights-trend-header">
                        <span class="insights-trend-column">${escapeHtml(numericCols[idx])}</span>
                        <span class="insights-trend-badge ${trend.trend_type}">${this.getTrendLabel(trend.trend_type)}</span>
                    </div>
                    <div class="insights-trend-score">趋势强度: ${(trend.trend_score * 100).toFixed(0)}%</div>
                    <div class="insights-trend-chart">
                        ${this.renderTrendChart(trend.data_points)}
                    </div>
                    ${trend.prediction !== null && trend.prediction !== undefined ? `
                        <div class="insights-trend-prediction">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v6m0 0l3-3m-3 3l-3-3"/></svg>
                            预测下一个值: ${trend.prediction}
                        </div>
                    ` : ''}
                </div>
            `).join('');

            content.innerHTML = `
                <div>
                    <div style="margin-bottom: 16px; font-size: 13px; color: var(--text-secondary);">
                        ${dateCols.length > 0 ? `使用日期列: ${dateCols[0]}` : '基于行顺序分析'}
                    </div>
                    <div class="insights-trends-list">
                        ${trendsHtml}
                    </div>
                </div>
            `;
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    async loadReport() {
        const content = document.getElementById('insights-content');
        if (!content || !this.currentTable) return;

        content.innerHTML = '<div class="insights-loading"><div class="spinner"></div><p>正在生成完整报告...</p></div>';

        try {
            const report = await API.get(`/api/insights/report/${encodeURIComponent(this.currentTable)}`);

            const recommendationsHtml = report.recommendations.map(r => `
                <div class="insights-recommendation-item ${this.getRecommendationClass(r)}">
                    ${escapeHtml(r)}
                </div>
            `).join('');

            content.innerHTML = `
                <div class="insights-report-overview">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div>
                            <div class="insights-report-title">
                                📊 完整洞察报告
                            </div>
                            <div class="insights-report-table-name">${escapeHtml(this.currentTable)}</div>
                        </div>
                        <div class="insights-report-timestamp">${report.generated_at || '-'}</div>
                    </div>

                    <div class="insights-summary-card">
                        <div class="insights-summary-header">
                            <h3>📋 数据摘要</h3>
                        </div>
                        <div class="insights-summary-body">
                            <div class="insights-summary-stats">
                                <div class="insights-stat-item">
                                    <div class="insights-stat-label">总行数</div>
                                    <div class="insights-stat-value">${this.formatNumber(report.summary.row_count || 0)}</div>
                                </div>
                                <div class="insights-stat-item">
                                    <div class="insights-stat-label">列数</div>
                                    <div class="insights-stat-value">${report.summary.column_count || 0}</div>
                                </div>
                                <div class="insights-stat-item">
                                    <div class="insights-stat-label">数值列</div>
                                    <div class="insights-stat-value">${Object.keys(report.summary.summary_stats || {}).length}</div>
                                </div>
                                <div class="insights-stat-item">
                                    <div class="insights-stat-label">检测异常</div>
                                    <div class="insights-stat-value">${report.outliers?.reduce((sum, o) => sum + o.outlier_count, 0) || 0}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="insights-summary-card">
                        <div class="insights-summary-header">
                            <h3>💡 分析建议</h3>
                        </div>
                        <div class="insights-summary-body">
                            <div class="insights-recommendations-list">
                                ${recommendationsHtml || '<div class="empty-state">暂无建议</div>'}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (err) {
            content.innerHTML = `<div class="empty-state error">加载失败: ${escapeHtml(err.message)}</div>`;
        }
    }

    renderTrendChart(dataPoints) {
        if (!dataPoints || dataPoints.length === 0) {
            return '<div style="text-align: center; line-height: 80px; color: var(--text-muted);">无数据</div>';
        }

        const values = dataPoints.map(p => p.value);
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;
        const width = 100 / (dataPoints.length - 1 || 1);

        return dataPoints.map((point, idx) => {
            const x = idx * width;
            const y = 100 - ((point.value - min) / range) * 90 - 5;
            return `<div class="insights-trend-point" style="left: ${x}%; bottom: ${y}%;"></div>`;
        }).join('');
    }

    getTrendLabel(type) {
        const labels = {
            'increasing': '上升',
            'decreasing': '下降',
            'stable': '稳定',
            'seasonal': '周期性'
        };
        return labels[type] || type;
    }

    getRecommendationClass(text) {
        if (text.includes('⚠️')) return 'warning';
        if (text.includes('📈') || text.includes('📉') || text.includes('🔮')) return 'info';
        if (text.includes('✅') || text.includes('良好')) return 'success';
        return 'info';
    }

    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
}

const insightsManager = new InsightsManager();
window.insightsManager = insightsManager;
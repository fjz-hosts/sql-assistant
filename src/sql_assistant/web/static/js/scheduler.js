/**
 * Scheduled Backup Module
 */

const SchedulerManager = {
    init: function() {
        this.bindEvents();
        this.loadScheduledConfig();
        this.loadScheduledStatus();
    },

    bindEvents: function() {
        // 启用/禁用定时备份
        $('scheduled-enabled').addEventListener('change', () => {
            this.toggleScheduledEnabled();
        });

        // 保存定时备份配置
        $('btn-save-scheduled').addEventListener('click', () => {
            this.saveScheduledConfig();
        });

        // 立即执行一次备份
        $('btn-run-scheduled-now').addEventListener('click', () => {
            this.runBackupNow();
        });
    },

    toggleScheduledEnabled: function() {
        const enabled = $('scheduled-enabled').checked;
        const form = $('scheduled-backup-form');
        const inputs = form.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            if (input !== $('scheduled-enabled')) {
                input.disabled = !enabled;
            }
        });

        if (enabled) {
            form.classList.add('enabled');
        } else {
            form.classList.remove('enabled');
        }
    },

    async loadScheduledConfig() {
        try {
            const result = await API.get('/api/scheduler/backup/config');
            const config = result;
            
            $('scheduled-enabled').checked = config.enabled;
            $('scheduled-hour').value = config.hour;
            $('scheduled-minute').value = config.minute;
            $('scheduled-backup-type').value = config.backup_type;
            $('scheduled-retention').value = config.retention_count;
            $('scheduled-include-schema').checked = config.include_schema;
            $('scheduled-include-data').checked = config.include_data;
            
            // 更新下次执行时间显示
            if (config.next_run_time) {
                $('scheduled-next-run').textContent = this.formatDateTime(config.next_run_time);
            }
            
            this.toggleScheduledEnabled();
        } catch (err) {
            console.error('加载定时备份配置失败:', err);
        }
    },

    async loadScheduledStatus() {
        try {
            const result = await API.get('/api/scheduler/backup/status');
            
            if (result.last_run_time) {
                $('scheduled-last-run').textContent = this.formatDateTime(result.last_run_time);
            }
            
            if (result.last_run_success !== null) {
                const resultEl = $('scheduled-last-result');
                if (result.last_run_success) {
                    resultEl.textContent = '成功';
                    resultEl.classList.add('success');
                    resultEl.classList.remove('error');
                } else {
                    resultEl.textContent = '失败';
                    resultEl.classList.add('error');
                    resultEl.classList.remove('success');
                }
            }
            
            if (result.next_run_time) {
                $('scheduled-next-run').textContent = this.formatDateTime(result.next_run_time);
            }
        } catch (err) {
            console.error('加载定时备份状态失败:', err);
        }
    },

    async saveScheduledConfig() {
        const enabled = $('scheduled-enabled').checked;
        const hour = parseInt($('scheduled-hour').value) || 2;
        const minute = parseInt($('scheduled-minute').value) || 0;
        const backupType = $('scheduled-backup-type').value;
        const retention = parseInt($('scheduled-retention').value) || 7;
        const includeSchema = $('scheduled-include-schema').checked;
        const includeData = $('scheduled-include-data').checked;

        // 验证时间
        if (hour < 0 || hour > 23) {
            return showToast('小时必须在 0-23 之间', 'error');
        }
        if (minute < 0 || minute > 59) {
            return showToast('分钟必须在 0-59 之间', 'error');
        }

        const btn = $('btn-save-scheduled');
        const originalText = btn.textContent;
        btn.textContent = '保存中...';
        btn.disabled = true;

        try {
            const result = await API.post('/api/scheduler/backup/config', {
                enabled,
                hour,
                minute,
                backup_type: backupType,
                retention_count: retention,
                include_schema: includeSchema,
                include_data: includeData
            });

            if (result.next_run_time) {
                $('scheduled-next-run').textContent = this.formatDateTime(result.next_run_time);
            } else {
                $('scheduled-next-run').textContent = '--';
            }

            showToast(enabled ? '定时备份已启用' : '定时备份已禁用', 'success');
            
        } catch (err) {
            showToast('保存定时备份配置失败: ' + err.message, 'error');
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    },

    async runBackupNow() {
        const btn = $('btn-run-scheduled-now');
        const originalText = btn.textContent;
        btn.textContent = '执行中...';
        btn.disabled = true;

        try {
            showToast('正在执行备份...', 'info');
            const result = await API.post('/api/scheduler/backup/run-now');

            if (result.success) {
                showToast('备份执行成功: ' + result.backup_id, 'success');
                await loadBackupList();
                await this.loadScheduledStatus();
            } else {
                showToast('备份执行失败: ' + result.message, 'error');
            }
        } catch (err) {
            showToast('执行备份失败: ' + err.message, 'error');
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    },

    formatDateTime: function(dateTimeStr) {
        try {
            const date = new Date(dateTimeStr);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return dateTimeStr;
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    SchedulerManager.init();
});

// 暴露全局函数
window.SchedulerManager = SchedulerManager;
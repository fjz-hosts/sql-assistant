/**
 * Backup Module
 */

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

// Expose functions
window.toggleTableSelection = toggleTableSelection;
window.createBackup = createBackup;
window.loadBackupList = loadBackupList;
window.viewBackupDetail = viewBackupDetail;
window.deleteBackup = deleteBackup;
window.openRestoreModal = openRestoreModal;
window.closeRestoreModal = closeRestoreModal;
window.confirmRestore = confirmRestore;
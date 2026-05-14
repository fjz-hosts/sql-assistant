/**
 * UI Utility Functions
 */

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

function analyzeSQLFromChat(btn) {
    const sql = btn.closest('.sql-block')?.querySelector('code')?.textContent;
    if (sql) {
        explainManager.showPanel();
        explainManager.analyzeSQL(sql.trim());
    }
}

// Expose functions
window.showToast = showToast;
window.escapeHtml = escapeHtml;
window.copySQL = copySQL;
window.analyzeSQLFromChat = analyzeSQLFromChat;
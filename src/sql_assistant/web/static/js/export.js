/**
 * Export Module - 导出查询结果
 * 支持 CSV、JSON、Excel 格式导出
 */

class ExportManager {
    /**
     * 导出为 CSV 格式
     * @param {Array} columns - 列名数组
     * @param {Array} rows - 数据行数组
     * @param {string} filename - 文件名（不含扩展名）
     */
    static exportToCSV(columns, rows, filename = 'query_result') {
        // 处理特殊字符，添加 BOM 支持中文
        const BOM = '\uFEFF';
        
        // 构建 CSV 内容
        let csv = BOM;
        
        // 添加表头
        csv += columns.map(col => this._escapeCSV(String(col))).join(',') + '\n';
        
        // 添加数据行
        for (const row of rows) {
            csv += row.map(cell => this._escapeCSV(String(cell ?? ''))).join(',') + '\n';
        }
        
        // 下载文件
        this._downloadFile(csv, `${filename}.csv`, 'text/csv;charset=utf-8');
    }

    /**
     * 导出为 JSON 格式
     * @param {Array} columns - 列名数组
     * @param {Array} rows - 数据行数组
     * @param {string} filename - 文件名（不含扩展名）
     */
    static exportToJSON(columns, rows, filename = 'query_result') {
        // 转换为对象数组格式
        const data = rows.map(row => {
            const obj = {};
            columns.forEach((col, index) => {
                obj[col] = row[index] ?? null;
            });
            return obj;
        });
        
        // 添加元数据
        const result = {
            export_time: new Date().toISOString(),
            columns: columns,
            row_count: rows.length,
            data: data
        };
        
        const jsonContent = JSON.stringify(result, null, 2);
        this._downloadFile(jsonContent, `${filename}.json`, 'application/json');
    }

    /**
     * 导出为 Excel 格式（使用 HTML table 方式）
     * @param {Array} columns - 列名数组
     * @param {Array} rows - 数据行数组
     * @param {string} filename - 文件名（不含扩展名）
     */
    static exportToExcel(columns, rows, filename = 'query_result') {
        // 创建 HTML table
        let html = `
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
<head>
    <meta charset="UTF-8">
    <style>
        table { border-collapse: collapse; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background: #f0f0f0; font-weight: bold; }
    </style>
</head>
<body>
    <table>
        <thead>
            <tr>${columns.map(col => `<th>${this._escapeHtml(String(col))}</th>`).join('')}</tr>
        </thead>
        <tbody>
            ${rows.map(row => `<tr>${row.map(cell => `<td>${this._escapeHtml(String(cell ?? ''))}</td>`).join('')}</tr>`).join('')}
        </tbody>
    </table>
</body>
</html>`;
        
        // 添加 Excel 特定的 MIME 类型
        const blob = new Blob([html], { 
            type: 'application/vnd.ms-excel;charset=utf-8' 
        });
        
        this._downloadBlob(blob, `${filename}.xls`);
    }

    /**
     * 显示导出格式选择菜单
     * @param {HTMLElement} anchorEl - 锚点元素（按钮位置）
     * @param {Array} columns - 列名数组
     * @param {Array} rows - 数据行数组
     */
    static showExportMenu(anchorEl, columns, rows) {
        // 移除已存在的菜单
        const existingMenu = document.querySelector('.export-menu');
        if (existingMenu) {
            existingMenu.remove();
        }
        
        // 创建菜单
        const menu = document.createElement('div');
        menu.className = 'export-menu';
        menu.innerHTML = `
            <div class="export-menu-header">选择导出格式</div>
            <button class="export-menu-item" data-format="csv">
                <span>📄</span> CSV
            </button>
            <button class="export-menu-item" data-format="json">
                <span>📋</span> JSON
            </button>
            <button class="export-menu-item" data-format="excel">
                <span>📊</span> Excel
            </button>
        `;
        
        // 获取锚点元素位置
        const rect = anchorEl.getBoundingClientRect();
        menu.style.position = 'fixed';
        menu.style.top = `${rect.top - menu.offsetHeight - 8}px`;
        menu.style.right = `${window.innerWidth - rect.right + 8}px`;
        
        // 添加点击事件
        menu.querySelectorAll('.export-menu-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const format = e.currentTarget.dataset.format;
                const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                const filename = `query_result_${timestamp}`;
                
                switch (format) {
                    case 'csv':
                        this.exportToCSV(columns, rows, filename);
                        break;
                    case 'json':
                        this.exportToJSON(columns, rows, filename);
                        break;
                    case 'excel':
                        this.exportToExcel(columns, rows, filename);
                        break;
                }
                
                menu.remove();
            });
        });
        
        // 点击外部关闭菜单
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target) && e.target !== anchorEl) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
        
        document.body.appendChild(menu);
        
        // 自动聚焦到菜单
        menu.focus();
    }

    /**
     * 转义 CSV 特殊字符
     * @param {string} value - 要转义的值
     * @returns {string} 转义后的值
     */
    static _escapeCSV(value) {
        // 如果包含逗号、引号或换行符，需要用引号包裹并转义内部引号
        if (value.includes(',') || value.includes('"') || value.includes('\n')) {
            return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
    }

    /**
     * 转义 HTML 特殊字符
     * @param {string} value - 要转义的值
     * @returns {string} 转义后的值
     */
    static _escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value;
        return div.innerHTML;
    }

    /**
     * 下载文件（文本内容）
     * @param {string} content - 文件内容
     * @param {string} filename - 文件名
     * @param {string} mimeType - MIME类型
     */
    static _downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        this._downloadBlob(blob, filename);
    }

    /**
     * 下载 Blob 文件
     * @param {Blob} blob - Blob 对象
     * @param {string} filename - 文件名
     */
    static _downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// 暴露到全局
window.ExportManager = ExportManager;
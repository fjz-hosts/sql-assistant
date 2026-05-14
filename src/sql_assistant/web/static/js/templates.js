/**
 * SQL Templates Module - SQL模板/收藏管理
 */

class TemplateManager {
    constructor() {
        this.templates = [];
        this.currentTemplateId = null;
    }

    /**
     * 加载所有模板
     */
    async loadTemplates() {
        try {
            const response = await API.get('/api/templates');
            this.templates = response.templates || [];
            this.renderTemplateList();
        } catch (error) {
            console.error('加载模板失败:', error);
            showToast('加载模板失败', 'error');
        }
    }

    /**
     * 渲染模板列表
     */
    renderTemplateList() {
        const listEl = document.getElementById('template-list');
        if (!listEl) return;

        if (this.templates.length === 0) {
            listEl.innerHTML = '<div class="empty-state">暂无模板，点击下方按钮添加</div>';
            return;
        }

        listEl.innerHTML = this.templates.map(tpl => `
            <div class="template-item" data-id="${tpl.id}" onclick="templateManager.selectTemplate(${tpl.id})">
                <div class="template-info">
                    <div class="template-name">${escapeHtml(tpl.name)}</div>
                    <div class="template-desc">${escapeHtml(tpl.description || '无描述')}</div>
                </div>
                <div class="template-actions">
                    <button class="btn-edit" onclick="event.stopPropagation(); templateManager.editTemplate(${tpl.id})" title="编辑">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                    </button>
                    <button class="btn-delete" onclick="event.stopPropagation(); templateManager.deleteTemplate(${tpl.id})" title="删除">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * 选择模板
     */
    selectTemplate(id) {
        const template = this.templates.find(t => t.id === id);
        if (!template) return;

        // 将模板内容插入到输入框
        const inputEl = document.getElementById('query-input');
        if (inputEl) {
            inputEl.value = template.sql;
            inputEl.style.height = 'auto';
            inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
        }

        // 关闭模板面板
        this.closePanel();

        showToast(`已插入模板: ${template.name}`, 'success');
    }

    /**
     * 显示添加模板表单
     */
    showAddForm() {
        this.currentTemplateId = null;
        this.showForm('添加模板');
    }

    /**
     * 编辑模板
     */
    async editTemplate(id) {
        const template = this.templates.find(t => t.id === id);
        if (!template) return;

        this.currentTemplateId = id;
        this.showForm('编辑模板', template);
    }

    /**
     * 显示表单
     */
    showForm(title, template = null) {
        const formEl = document.getElementById('template-form');
        const titleEl = document.getElementById('template-form-title');
        
        titleEl.textContent = title;
        
        document.getElementById('template-name').value = template?.name || '';
        document.getElementById('template-desc').value = template?.description || '';
        document.getElementById('template-sql').value = template?.sql || '';
        document.getElementById('template-tags').value = template?.tags?.join(', ') || '';
        
        formEl.style.display = 'block';
        
        // 滚动到表单
        formEl.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * 保存模板
     */
    async saveTemplate() {
        const name = document.getElementById('template-name').value.trim();
        const description = document.getElementById('template-desc').value.trim();
        const sql = document.getElementById('template-sql').value.trim();
        const tagsInput = document.getElementById('template-tags').value.trim();
        const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(Boolean) : [];

        if (!name || !sql) {
            showToast('请填写模板名称和SQL内容', 'error');
            return;
        }

        try {
            const data = { name, description, sql, tags };
            
            if (this.currentTemplateId) {
                await API.put(`/api/templates/${this.currentTemplateId}`, data);
                showToast('模板更新成功', 'success');
            } else {
                await API.post('/api/templates', data);
                showToast('模板添加成功', 'success');
            }

            this.closeForm();
            await this.loadTemplates();
        } catch (error) {
            showToast('保存模板失败: ' + error.message, 'error');
        }
    }

    /**
     * 删除模板
     */
    async deleteTemplate(id) {
        if (!confirm('确定要删除这个模板吗？')) return;

        try {
            await API.del(`/api/templates/${id}`);
            showToast('模板删除成功', 'success');
            await this.loadTemplates();
        } catch (error) {
            showToast('删除模板失败: ' + error.message, 'error');
        }
    }

    /**
     * 关闭表单
     */
    closeForm() {
        document.getElementById('template-form').style.display = 'none';
        this.currentTemplateId = null;
    }

    /**
     * 显示模板面板
     */
    showPanel() {
        const panel = document.getElementById('template-panel');
        if (panel) {
            panel.classList.add('show');
        }
        this.loadTemplates();
    }

    /**
     * 关闭模板面板
     */
    closePanel() {
        const panel = document.getElementById('template-panel');
        if (panel) {
            panel.classList.remove('show');
        }
    }

    /**
     * 从当前SQL创建模板
     */
    createFromCurrentSQL() {
        const sql = document.getElementById('query-input')?.value?.trim();
        if (!sql) {
            showToast('请先输入SQL语句', 'error');
            return;
        }

        this.currentTemplateId = null;
        document.getElementById('template-form-title').textContent = '从当前SQL创建模板';
        document.getElementById('template-name').value = '';
        document.getElementById('template-desc').value = '';
        document.getElementById('template-sql').value = sql;
        document.getElementById('template-tags').value = '';
        document.getElementById('template-form').style.display = 'block';
        
        this.showPanel();
        setTimeout(() => {
            document.getElementById('template-name').focus();
        }, 100);
    }
}

// 全局实例
const templateManager = new TemplateManager();

// 暴露到全局
window.templateManager = templateManager;
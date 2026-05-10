/**
 * 主题管理器 - 处理亮色/暗色模式切换
 */

const ThemeManager = {
    STORAGE_KEY: 'sql_assistant_theme',
    currentTheme: 'dark',

    init() {
        this.loadTheme();
        this.bindEvents();
    },

    loadTheme() {
        const saved = localStorage.getItem(this.STORAGE_KEY);
        if (saved) {
            this.currentTheme = saved;
        }
        this.applyTheme();
    },

    bindEvents() {
        const toggleBtn = document.getElementById('btn-toggle-theme');
        const checkbox = document.getElementById('theme-toggle-checkbox');
        
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }
        
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                this.currentTheme = e.target.checked ? 'light' : 'dark';
                this.saveTheme();
                this.applyTheme();
            });
            checkbox.checked = this.currentTheme === 'light';
        }
    },

    toggle() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.saveTheme();
        this.applyTheme();

        const checkbox = document.getElementById('theme-toggle-checkbox');
        if (checkbox) {
            checkbox.checked = this.currentTheme === 'light';
        }
    },

    saveTheme() {
        localStorage.setItem(this.STORAGE_KEY, this.currentTheme);
    },

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
    },

    getCurrentTheme() {
        return this.currentTheme;
    }
};

window.ThemeManager = ThemeManager;

/**
 * 颜色主题管理器 - 处理主题色切换
 */

const ColorThemeManager = {
    STORAGE_KEY: 'sql_assistant_color_theme',
    currentColor: 'blue',

    COLOR_PRESETS: {
        blue: {
            name: '蓝色',
            accent: '#58a6ff',
            'accent-hover': '#79c0ff',
            'accent-rgb': '88, 166, 255',
        },
        purple: {
            name: '紫色',
            accent: '#a371f7',
            'accent-hover': '#b87ff7',
            'accent-rgb': '163, 113, 247',
        },
        pink: {
            name: '粉色',
            accent: '#f778ba',
            'accent-hover': '#ff9bce',
            'accent-rgb': '247, 120, 186',
        },
        red: {
            name: '红色',
            accent: '#f85149',
            'accent-hover': '#ff7b72',
            'accent-rgb': '248, 81, 73',
        },
        orange: {
            name: '橙色',
            accent: '#d29922',
            'accent-hover': '#e3b341',
            'accent-rgb': '210, 153, 34',
        },
        yellow: {
            name: '黄色',
            accent: '#d4a72c',
            'accent-hover': '#e6c454',
            'accent-rgb': '212, 167, 44',
        },
        green: {
            name: '绿色',
            accent: '#3fb950',
            'accent-hover': '#56d364',
            'accent-rgb': '63, 185, 80',
        },
        cyan: {
            name: '青色',
            accent: '#39c5cf',
            'accent-hover': '#56d4dd',
            'accent-rgb': '57, 197, 207',
        },
    },

    init() {
        this.loadColor();
        this.bindEvents();
    },

    loadColor() {
        const saved = localStorage.getItem(this.STORAGE_KEY);
        if (saved && this.COLOR_PRESETS[saved]) {
            this.currentColor = saved;
        }
        this.applyColor();
    },

    bindEvents() {
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const color = e.target.dataset.color;
                if (color) {
                    this.setColor(color);
                }
            });
        });
    },

    setColor(colorName) {
        if (!this.COLOR_PRESETS[colorName]) {
            console.warn(`Color ${colorName} not found`);
            return;
        }
        this.currentColor = colorName;
        this.saveColor();
        this.applyColor();
        this.updateColorButtons();
    },

    saveColor() {
        localStorage.setItem(this.STORAGE_KEY, this.currentColor);
    },

    applyColor() {
        const preset = this.COLOR_PRESETS[this.currentColor];
        if (!preset) return;

        const root = document.documentElement;
        root.style.setProperty('--accent', preset.accent);
        root.style.setProperty('--accent-hover', preset['accent-hover']);
        root.style.setProperty('--accent-rgb', preset['accent-rgb']);

        this.updateColorButtons();
    },

    updateColorButtons() {
        document.querySelectorAll('.color-btn').forEach(btn => {
            if (btn.dataset.color === this.currentColor) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    },

    getCurrentColor() {
        return this.currentColor;
    },

    getColorName(colorName) {
        return this.COLOR_PRESETS[colorName]?.name || colorName;
    }
};

window.ColorThemeManager = ColorThemeManager;

/**
 * Navigation Bar Module
 * Handles the top navigation bar with theme toggle, color picker, and action buttons
 */

const NavbarManager = {
    init() {
        this.bindEvents();
        this.updateThemeToggleIcon();
    },

    bindEvents() {
        // Color picker dropdown toggle
        const colorPickerBtn = document.getElementById('btn-color-picker');
        const colorPickerDropdown = document.getElementById('color-picker-dropdown');
        
        if (colorPickerBtn) {
            colorPickerBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                colorPickerDropdown.classList.toggle('active');
            });
        }

        // Close color picker when clicking outside
        document.addEventListener('click', (e) => {
            if (!colorPickerDropdown?.contains(e.target) && !colorPickerBtn?.contains(e.target)) {
                colorPickerDropdown?.classList.remove('active');
            }
        });

        // Theme toggle button - handled by ThemeManager, just update icon after toggle
        document.addEventListener('themeChanged', () => {
            this.updateThemeToggleIcon();
        });

        // Color buttons
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const color = e.target.dataset.color;
                if (color) {
                    ColorThemeManager.setColor(color);
                    colorPickerDropdown?.classList.remove('active');
                }
            });
        });

        // Settings button
        const settingsBtn = document.getElementById('btn-settings');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', openSettings);
        }

        // Templates button
        const templatesBtn = document.getElementById('btn-templates');
        if (templatesBtn) {
            templatesBtn.addEventListener('click', () => templateManager.togglePanel());
        }

        // Explain button
        const explainBtn = document.getElementById('btn-explain');
        if (explainBtn) {
            explainBtn.addEventListener('click', () => explainManager.togglePanel());
        }
    },

    updateThemeToggleIcon() {
        const themeBtn = document.getElementById('btn-toggle-theme');
        if (!themeBtn) return;

        const isDark = ThemeManager.getCurrentTheme() === 'dark';
        const iconHtml = isDark ? 
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>' :
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        
        themeBtn.innerHTML = iconHtml;
        themeBtn.title = isDark ? '切换到浅色模式' : '切换到深色模式';
    },

    updateColorPreview() {
        const colorPickerBtn = document.getElementById('btn-color-picker');
        if (!colorPickerBtn) return;

        const currentColor = ColorThemeManager.getCurrentColor();
        const preset = ColorThemeManager.COLOR_PRESETS[currentColor];
        if (preset) {
            colorPickerBtn.style.backgroundColor = preset.accent;
            colorPickerBtn.style.borderColor = preset.accent;
            colorPickerBtn.style.color = '#fff';
        }
    }
};

window.NavbarManager = NavbarManager;

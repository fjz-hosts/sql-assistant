/**
 * Service Manager Module
 * Manages installing/uninstalling SQL Assistant as a system service
 * Supports Install/Uninstall (auto-start on boot) + Start/Stop (immediate control)
 */

const ServiceManager = {
    installed: false,
    running: false,
    platform: '',

    async init() {
        await this.checkStatus();
        this.bindEvents();
    },

    async checkStatus() {
        try {
            const result = await API.get('/api/service/status');
            this.installed = result.installed;
            this.running = result.running;
            this.platform = result.platform;
            this.updateUI();
        } catch {
            this.installed = false;
            this.running = false;
            this.updateUI();
        }
    },

    updateUI() {
        const statusDot = document.getElementById('service-status-dot');
        const statusText = document.getElementById('service-status-text');
        const installBtn = document.getElementById('btn-install-service');
        const startBtn = document.getElementById('btn-start-service');
        const stopBtn = document.getElementById('btn-stop-service');
        const uninstallBtn = document.getElementById('btn-uninstall-service');
        const platformInfo = document.getElementById('service-platform-info');
        const navbarDot = document.getElementById('service-navbar-dot');

        if (statusDot && statusText) {
            statusDot.className = 'service-status-dot';
            if (this.running) {
                statusDot.classList.add('running');
                statusText.textContent = '运行中' + (this.installed ? ' · 已安装开机自启' : '');
            } else if (this.installed) {
                statusDot.classList.add('installed');
                statusText.textContent = '已安装 · 未运行';
            } else {
                statusDot.classList.add('not-installed');
                statusText.textContent = '未安装';
            }
        }

        if (installBtn) {
            installBtn.disabled = this.installed;
            installBtn.style.display = this.installed ? 'none' : '';
        }
        if (startBtn) {
            startBtn.disabled = this.running;
            startBtn.style.display = this.installed ? '' : 'none';
        }
        if (stopBtn) {
            stopBtn.disabled = !this.running;
            stopBtn.style.display = this.installed ? '' : 'none';
        }
        if (uninstallBtn) {
            uninstallBtn.disabled = !this.installed;
            uninstallBtn.style.display = this.installed ? '' : 'none';
        }
        if (platformInfo) {
            const method = this.platform === 'Windows' ? 'Task Scheduler' : 'systemd';
            platformInfo.textContent = `当前系统: ${this.platform || '未知'} · 方式: ${method}`;
        }
        if (navbarDot) {
            navbarDot.className = 'service-dot';
            if (this.running) {
                navbarDot.classList.add('running');
            } else if (this.installed) {
                navbarDot.classList.add('installed');
            }
        }
    },

    bindEvents() {
        const installBtn = document.getElementById('btn-install-service');
        const startBtn = document.getElementById('btn-start-service');
        const stopBtn = document.getElementById('btn-stop-service');
        const uninstallBtn = document.getElementById('btn-uninstall-service');

        if (installBtn) {
            installBtn.addEventListener('click', () => this.install());
        }
        if (startBtn) {
            startBtn.addEventListener('click', () => this.start());
        }
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stop());
        }
        if (uninstallBtn) {
            uninstallBtn.addEventListener('click', () => this.uninstall());
        }
    },

    async install() {
        if (!confirm(
            '即将安装 SQL Assistant 为开机自启服务，并立即在后台启动。\n\n' +
            (this.platform === 'Windows'
                ? '安装后即使关闭此终端，服务也会在后台继续运行。'
                : '安装后服务将由 systemd 管理，开机自动启动。') +
            '\n\n确定要继续吗？'
        )) {
            return;
        }

        try {
            this.setButtonsDisabled(true);
            const result = await API.post('/api/service/install');
            if (result.success) {
                showToast(result.message || '安装成功', 'success');
                await this.checkStatus();
            } else {
                showToast(result.error || '安装失败', 'error');
            }
        } catch (err) {
            showToast(err.message || '安装失败', 'error');
        } finally {
            this.setButtonsDisabled(false);
        }
    },

    async start() {
        try {
            this.setButtonsDisabled(true);
            const result = await API.post('/api/service/start');
            if (result.success) {
                showToast(result.message || '启动成功', 'success');
                await this.checkStatus();
            } else {
                showToast(result.error || '启动失败', 'error');
            }
        } catch (err) {
            showToast(err.message || '启动失败', 'error');
        } finally {
            this.setButtonsDisabled(false);
        }
    },

    async stop() {
        try {
            this.setButtonsDisabled(true);
            const result = await API.post('/api/service/stop');
            if (result.success) {
                showToast(result.message || '停止成功', 'success');
                await this.checkStatus();
            } else {
                showToast(result.error || '停止失败', 'error');
            }
        } catch (err) {
            showToast(err.message || '停止失败', 'error');
        } finally {
            this.setButtonsDisabled(false);
        }
    },

    async uninstall() {
        if (!confirm(
            '即将停止并卸载 SQL Assistant 的开机自启服务。\n\n' +
            '卸载后不会影响已安装的项目文件。\n\n' +
            '确定要继续吗？'
        )) {
            return;
        }

        try {
            this.setButtonsDisabled(true);
            const result = await API.post('/api/service/uninstall');
            if (result.success) {
                showToast(result.message || '卸载成功', 'success');
                await this.checkStatus();
            } else {
                showToast(result.error || '卸载失败', 'error');
            }
        } catch (err) {
            showToast('卸载成功，服务已停止', 'success');
            await this.checkStatus();
        } finally {
            this.setButtonsDisabled(false);
        }
    },

    setButtonsDisabled(disabled) {
        ['btn-install-service', 'btn-start-service', 'btn-stop-service', 'btn-uninstall-service'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.disabled = disabled;
        });
    },

    toggle() {
        if (this.running) {
            this.stop();
        } else if (this.installed) {
            this.start();
        } else {
            this.install();
        }
    }
};

window.ServiceManager = ServiceManager;
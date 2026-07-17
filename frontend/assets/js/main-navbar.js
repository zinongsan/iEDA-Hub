/**
 * 主页风格用户菜单组件
 */

// 创建用户菜单HTML（主页风格）
function createMainUserMenu(user) {
    const firstChar = (user.real_name || user.username || user.email || 'U').charAt(0).toUpperCase();
    const tierText = user.is_admin ? '管理员' : (user.tier === 'premium' ? '高级' : '普通');
    const tierClass = user.is_admin ? 'admin' : '';

    return `
        <div class="__user-menu">
            <div class="__user-trigger" tabindex="0">
                <span class="__user-avatar">${firstChar}</span>
                <span class="__user-name">${user.real_name || user.username}</span>
                <span class="__user-tier ${tierClass}">${tierText}</span>
                <span class="__user-caret">▼</span>
            </div>
            <div class="__user-dropdown">
                <div class="__user-info">
                    <div class="__user-info-name">${user.real_name || user.username}</div>
                    <div class="__user-info-email">${user.email}</div>
                    <span class="__user-info-tag ${tierClass}">${tierText}</span>
                </div>
                <div class="__user-menu-list">
                    <a class="__user-menu-item" href="/profile" id="__menu-profile">
                        <span class="__icon">👤</span><span>个人中心</span>
                    </a>
                    <a class="__user-menu-item" href="/logs" id="__menu-logs">
                        <span class="__icon">📊</span><span>操作日志</span>
                    </a>
                    ${user.is_admin ? `
                    <a class="__user-menu-item" href="/admin" id="__menu-admin">
                        <span class="__icon">⚙️</span><span>管理后台</span>
                    </a>
                    ` : ''}
                    <div class="__user-menu-divider"></div>
                    <a class="__user-menu-item danger" id="__menu-logout">
                        <span class="__icon">🚪</span><span>退出登录</span>
                    </a>
                </div>
            </div>
        </div>
    `;
}

// 初始化用户菜单事件
function initMainUserMenu() {
    const logoutBtn = document.getElementById('__menu-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (window.doLogout) {
                window.doLogout();
            } else if (confirm('确定要退出登录吗？')) {
                // 默认退出逻辑
                fetch('/api/v1/auth/logout', { method: 'POST' })
                    .then(() => {
                        localStorage.removeItem('token');
                        location.href = '/login';
                    });
            }
        });
    }
}

// 导出到全局
window.createMainUserMenu = createMainUserMenu;
window.initMainUserMenu = initMainUserMenu;

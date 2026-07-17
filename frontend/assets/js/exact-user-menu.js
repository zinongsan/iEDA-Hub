// 主页用户菜单 - 完全复制
function createExactUserMenu(user) {
    const firstChar = (user.real_name || user.username || 'U').charAt(0);
    const tierText = user.is_admin ? '管理员' : (user.tier === 'premium' ? '高级' : '普通');
    const tierClass = user.is_admin ? 'admin' : (user.tier === 'premium' ? 'premium' : 'normal');

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

function initExactUserMenu() {
    const logoutBtn = document.getElementById('__menu-logout');
    if (logoutBtn) {
        logoutBtn.onclick = function(e) {
            e.preventDefault();
            if (window.doLogout) {
                window.doLogout();
            }
        };
    }

    // 如果有个人中心按钮，跳转
    const profileBtn = document.getElementById('__menu-profile');
    if (profileBtn) {
        profileBtn.onclick = function(e) {
            e.preventDefault();
            location.href = '/profile';
        };
    }

    // 操作日志按钮
    const logsBtn = document.getElementById('__menu-logs');
    if (logsBtn) {
        logsBtn.onclick = function(e) {
            e.preventDefault();
            location.href = '/logs';
        };
    }
}

window.createExactUserMenu = createExactUserMenu;
window.initExactUserMenu = initExactUserMenu;

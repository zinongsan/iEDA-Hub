/**
 * 统一导航栏组件
 * 适用于主页和个人中心
 */

// 创建用户菜单HTML
function createUserMenu(user) {
    const firstChar = (user.real_name || user.username || user.email || 'U').charAt(0).toUpperCase();
    const avatarStyle = user.avatar_url
        ? `background-image: url('${user.avatar_url}'); background-size: cover; background-position: center;`
        : `background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);`;

    return `
        <div class="user-menu-container">
            <div class="user-avatar-btn" id="userAvatarBtn">
                <div class="user-avatar-small" style="${avatarStyle}">
                    ${user.avatar_url ? '' : firstChar}
                </div>
                <span class="user-name">${user.real_name || user.username}</span>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                    <path d="M6 8L2 4h8z"/>
                </svg>
            </div>
            <div class="user-dropdown" id="userDropdown">
                <div class="dropdown-header">
                    <div class="dropdown-avatar" style="${avatarStyle}">
                        ${user.avatar_url ? '' : firstChar}
                    </div>
                    <div class="dropdown-user-info">
                        <div class="dropdown-user-name">${user.real_name || user.username}</div>
                        <div class="dropdown-user-email">${user.email}</div>
                    </div>
                </div>
                <div class="dropdown-divider"></div>
                <a href="/profile" class="dropdown-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                    <span>个人中心</span>
                </a>
                <a href="/logs" class="dropdown-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    <span>操作日志</span>
                </a>
                <div class="dropdown-divider"></div>
                <button class="dropdown-item" onclick="window.doLogout ? window.doLogout() : (window.handleLogout && window.handleLogout())">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                        <polyline points="16 17 21 12 16 7"></polyline>
                        <line x1="21" y1="12" x2="9" y2="12"></line>
                    </svg>
                    <span>退出登录</span>
                </button>
            </div>
        </div>
    `;
}

// 初始化用户菜单
function initUserMenu() {
    const avatarBtn = document.getElementById('userAvatarBtn');
    const dropdown = document.getElementById('userDropdown');

    if (!avatarBtn || !dropdown) return;

    // 点击头像显示/隐藏菜单
    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });

    // 点击其他地方关闭菜单
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.user-menu-container')) {
            dropdown.classList.remove('show');
        }
    });
}

// 导出到全局
window.createUserMenu = createUserMenu;
window.initUserMenu = initUserMenu;

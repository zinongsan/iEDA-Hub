// 主页用户菜单 - 完全复制
(function() {
    // 注入样式
    const style = document.createElement('style');
    style.textContent = `
        .__user-menu {
            position: fixed;
            top: 8px;
            right: 16px;
            z-index: 99999;
            font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
            font-size: 13px;
        }
        .__user-trigger {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 20px;
            color: #fff;
            cursor: pointer;
            transition: background .2s;
            user-select: none;
        }
        .__user-trigger:hover { background: rgba(255,255,255,0.22); }
        .__user-avatar {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4a7bc8, #1e3c72);
            color: #fff;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .__user-name { font-weight: 500; }
        .__user-tier {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 10px;
            line-height: 1.2;
        }
        .__user-tier.normal {
            background: #e0e7ee;
            color: #475569;
        }
        .__user-tier.premium {
            background: linear-gradient(135deg, #ffd700, #ffa726);
            color: #5a4500;
        }
        .__user-tier.admin {
            background: #d9534f;
            color: #fff;
        }
        .__user-caret {
            font-size: 10px;
            opacity: .75;
            transition: transform .2s;
        }
        .__user-menu:hover .__user-caret { transform: rotate(180deg); }

        .__user-dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            min-width: 220px;
            background: #fff;
            border-radius: 10px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.04);
            opacity: 0;
            visibility: hidden;
            transform: translateY(-6px);
            transition: all .2s ease;
            overflow: hidden;
        }
        .__user-menu::after {
            content: '';
            position: absolute;
            top: 100%;
            right: 0;
            width: 240px;
            height: 12px;
            pointer-events: auto;
        }
        .__user-menu:hover .__user-dropdown,
        .__user-dropdown:hover {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }

        .__user-info {
            padding: 14px 16px;
            border-bottom: 1px solid #f0f2f5;
            background: linear-gradient(135deg, #f8fafc, #fff);
        }
        .__user-info-name {
            font-size: 14px;
            font-weight: 600;
            color: #1e3c72;
            margin-bottom: 2px;
        }
        .__user-info-email {
            font-size: 12px;
            color: #6c7a89;
            word-break: break-all;
        }
        .__user-info-tag {
            display: inline-block;
            margin-top: 6px;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 10px;
        }

        .__user-menu-list { padding: 6px 0; }
        .__user-menu-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 16px;
            font-size: 13px;
            color: #2c3e50;
            cursor: pointer;
            text-decoration: none;
            transition: background .15s;
        }
        .__user-menu-item:hover { background: #f0f6ff; color: #1e3c72; }
        .__user-menu-item .__icon {
            width: 16px;
            display: inline-block;
            text-align: center;
            opacity: .8;
        }
        .__user-menu-divider {
            height: 1px;
            background: #f0f2f5;
            margin: 4px 0;
        }
        .__user-menu-item.danger { color: #d9534f; }
        .__user-menu-item.danger:hover { background: #fef2f2; color: #b91c1c; }
    `;
    document.head.appendChild(style);

    function escapeHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function tierStyle(cls) {
        if (cls === 'admin') return 'background:#d9534f;color:#fff;';
        if (cls === 'premium') return 'background:linear-gradient(135deg,#ffd700,#ffa726);color:#5a4500;';
        return 'background:#e0e7ee;color:#475569;';
    }

    window.renderProfileUserMenu = function(user) {
        const tier = user.tier || 'normal';
        const isAdmin = !!user.is_admin;
        const tierClass = isAdmin ? 'admin' : tier;
        const tierLabel = isAdmin ? '管理员' : (tier === 'premium' ? '高级用户' : '普通用户');
        const firstChar = (user.real_name || user.username || user.email || 'U').charAt(0);

        const wrap = document.createElement('div');
        wrap.className = '__user-menu';
        wrap.innerHTML = `
            <div class="__user-trigger" tabindex="0">
                <span class="__user-avatar">${escapeHtml(firstChar)}</span>
                <span class="__user-name">${escapeHtml(user.real_name || user.username || '用户')}</span>
                <span class="__user-tier ${tierClass}">${tierLabel}</span>
                <span class="__user-caret">▼</span>
            </div>
            <div class="__user-dropdown">
                <div class="__user-info">
                    <div class="__user-info-name">${escapeHtml(user.real_name || user.username || '')}</div>
                    <div class="__user-info-email">${escapeHtml(user.email || '')}</div>
                    <span class="__user-info-tag ${tierClass}"
                          style="${tierStyle(tierClass)}">${tierLabel}</span>
                </div>
                <div class="__user-menu-list">
                    <a class="__user-menu-item" href="/profile" id="__menu-profile">
                        <span class="__icon">👤</span><span>个人中心</span>
                    </a>
                    <a class="__user-menu-item" href="/logs" id="__menu-logs">
                        <span class="__icon">📊</span><span>操作日志</span>
                    </a>
                    ${isAdmin ? `
                    <a class="__user-menu-item" href="/admin" id="__menu-admin">
                        <span class="__icon">⚙️</span><span>管理后台</span>
                    </a>` : ''}
                    <div class="__user-menu-divider"></div>
                    <a class="__user-menu-item danger" id="__menu-logout">
                        <span class="__icon">🚪</span><span>退出登录</span>
                    </a>
                </div>
            </div>
        `;

        // 移除旧的菜单
        const oldMenu = document.querySelector('.__user-menu');
        if (oldMenu) oldMenu.remove();

        document.body.appendChild(wrap);

        // 退出登录
        document.getElementById('__menu-logout').onclick = (e) => {
            e.preventDefault();
            if (window.doLogout) {
                window.doLogout();
            }
        };
    };
})();

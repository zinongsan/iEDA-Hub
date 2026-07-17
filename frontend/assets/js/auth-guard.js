/**
 * 鉴权守卫（注入到 iedahub.html 等受保护页面）
 *
 * 功能：
 *  1. 调用 /api/v1/users/me（带 HttpOnly cookie）校验登录态
 *  2. 校验失败 → 自动跳转登录页
 *  3. 校验成功 → 隐藏页面原有「登录」按钮，注入「用户名 + 等级徽章」 + 悬停下拉菜单
 *
 * 暴露：window.currentUser, window.logout()
 */
(function () {
    'use strict';

    // 注入下拉菜单样式
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

        /* 下拉面板 */
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
        /* hover 桥接区 - 避免鼠标离开按钮立即关闭 */
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

    // 二次校验登录态（令牌走 HttpOnly cookie，credentials:'include' 携带）
    fetch('/api/v1/users/me', { credentials: 'include' })
        .then(r => {
            if (!r.ok) throw new Error('unauth');
            return r.json();
        })
        .then(user => {
            window.currentUser = user;
            renderUserMenu(user);
            hideOldLoginButton();
        })
        .catch(() => {
            location.replace('/login?next=' + encodeURIComponent(location.pathname));
        });

    // 隐藏原页面（iedahub 等）的「登录」按钮
    function hideOldLoginButton() {
        // 通过类名 .nl 隐藏
        document.querySelectorAll('.nl, button.nl').forEach(el => { el.style.display = 'none'; });
        // 通过文本兜底
        document.querySelectorAll('button, a').forEach(el => {
            const txt = (el.textContent || '').trim();
            if (txt === '登录' || txt === '登陆' || txt.toLowerCase() === 'login' || txt.toLowerCase() === 'sign in') {
                el.style.display = 'none';
            }
        });
    }

    function renderUserMenu(user) {
        const tier = user.tier || 'normal';
        const isAdmin = !!user.is_admin;
        const tierClass = isAdmin ? 'admin' : tier;
        const tierLabel = isAdmin ? '管理员' : (tier === 'premium' ? '高级用户' : '普通用户');
        const firstChar = (user.username || user.email || 'U').charAt(0);

        const wrap = document.createElement('div');
        wrap.className = '__user-menu';
        wrap.innerHTML = `
            <div class="__user-trigger" tabindex="0">
                <span class="__user-avatar">${escapeHtml(firstChar)}</span>
                <span class="__user-name">${escapeHtml(user.username || '用户')}</span>
                <span class="__user-tier ${tierClass}">${tierLabel}</span>
                <span class="__user-caret">▼</span>
            </div>
            <div class="__user-dropdown">
                <div class="__user-info">
                    <div class="__user-info-name">${escapeHtml(user.username || '')}</div>
                    <div class="__user-info-email">${escapeHtml(user.email || '')}</div>
                    <span class="__user-info-tag ${tierClass}"
                          style="${tierStyle(tierClass)}">${tierLabel}</span>
                </div>
                <div class="__user-menu-list">
                    ${(isAdmin || user.role === 'teacher') ? `
                    <a class="__user-menu-item" id="__menu-teacher">
                        <span class="__icon">📚</span><span>教师中心</span>
                    </a>` : `
                    <a class="__user-menu-item" id="__menu-profile">
                        <span class="__icon">👤</span><span>个人中心</span>
                    </a>`}
                    <a class="__user-menu-item" id="__menu-password">
                        <span class="__icon">🔑</span><span>修改密码</span>
                    </a>
                    ${isAdmin ? `
                    <a class="__user-menu-item" id="__menu-admin">
                        <span class="__icon">⚙️</span><span>管理后台</span>
                    </a>` : ''}
                    ${tier === 'normal' && !isAdmin && user.role !== 'teacher' ? `
                    <a class="__user-menu-item" id="__menu-upgrade">
                        <span class="__icon">⭐</span><span>升级高级版</span>
                    </a>` : ''}
                    <div class="__user-menu-divider"></div>
                    <a class="__user-menu-item danger" id="__menu-logout">
                        <span class="__icon">🚪</span><span>退出登录</span>
                    </a>
                </div>
            </div>
        `;
        document.body.appendChild(wrap);

        // 菜单点击事件
        const profileBtn = document.getElementById('__menu-profile');
        if (profileBtn) profileBtn.onclick = (e) => {
            e.preventDefault();
            location.href = '/profile';
        };
        const teacherBtn = document.getElementById('__menu-teacher');
        if (teacherBtn) teacherBtn.onclick = () => { location.href = '/app/teacher-dashboard.html'; };

        document.getElementById('__menu-password').onclick = (e) => {
            e.preventDefault();
            location.href = '/profile#password';
        };
        const adminBtn = document.getElementById('__menu-admin');
        if (adminBtn) adminBtn.onclick = () => { location.href = '/admin'; };

        const upBtn = document.getElementById('__menu-upgrade');
        if (upBtn) upBtn.onclick = () => { location.href = '/app/iedahub?page=pricing'; };

        document.getElementById('__menu-logout').onclick = (e) => {
            e.preventDefault();
            window.logout();
        };
    }

    // 全局退出登录（access/refresh 走 HttpOnly cookie，后端拉黑并清 cookie）
    window.logout = function () {
        fetch('/api/v1/auth/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: '{}',
        }).finally(() => {
            document.cookie = 'logged_in=; path=/; max-age=0; samesite=lax';
            location.replace('/login');
        });
    };

    // 个人中心弹窗
    function showProfileModal(user) {
        const html = `
            <div><strong>用户名：</strong>${escapeHtml(user.username || '')}</div>
            <div><strong>邮箱：</strong>${escapeHtml(user.email || '')}</div>
            <div><strong>等级：</strong>${user.is_admin ? '管理员' : (user.tier === 'premium' ? '高级用户' : '普通用户')}</div>
            <div><strong>所属组：</strong>${user.group ? escapeHtml(user.group.name) : '未分配'}</div>
            <div><strong>注册时间：</strong>${user.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '-'}</div>
            <div><strong>上次登录：</strong>${user.last_login_at ? new Date(user.last_login_at).toLocaleString('zh-CN') : '-'}</div>
        `;
        openModal('个人中心', html);
    }

    // 修改密码弹窗
    function showPasswordModal() {
        const html = `
            <form id="__pwd-form" style="display:flex;flex-direction:column;gap:12px;">
                <label style="font-size:13px;color:#5a6c7d;">当前密码
                    <input type="password" name="old_password" required minlength="8"
                        style="width:100%;padding:9px 12px;border:1px solid #d1d9e0;border-radius:6px;margin-top:4px;">
                </label>
                <label style="font-size:13px;color:#5a6c7d;">新密码（至少 8 位）
                    <input type="password" name="new_password" required minlength="8"
                        style="width:100%;padding:9px 12px;border:1px solid #d1d9e0;border-radius:6px;margin-top:4px;">
                </label>
                <div id="__pwd-msg" style="font-size:12px;color:#d9534f;display:none;"></div>
                <button type="submit" style="padding:10px;background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;border:none;border-radius:6px;font-size:14px;cursor:pointer;">提 交</button>
            </form>
        `;
        const modal = openModal('修改密码', html);
        const form = modal.querySelector('#__pwd-form');
        const msg = modal.querySelector('#__pwd-msg');
        form.onsubmit = async (e) => {
            e.preventDefault();
            msg.style.display = 'none';
            const fd = new FormData(form);
            try {
                const res = await fetch('/api/v1/users/me/password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        old_password: fd.get('old_password'),
                        new_password: fd.get('new_password'),
                    })
                });
                if (res.ok) {
                    msg.style.color = '#10b981';
                    msg.textContent = '修改成功，请重新登录';
                    msg.style.display = 'block';
                    setTimeout(() => window.logout(), 1200);
                } else {
                    const j = await res.json().catch(() => ({}));
                    msg.style.color = '#d9534f';
                    msg.textContent = j.detail || '修改失败';
                    msg.style.display = 'block';
                }
            } catch (err) {
                msg.style.color = '#d9534f';
                msg.textContent = '网络错误';
                msg.style.display = 'block';
            }
        };
    }

    // 通用 modal
    function openModal(title, contentHtml) {
        const mask = document.createElement('div');
        mask.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:100000;display:flex;align-items:center;justify-content:center;font-family:-apple-system,"PingFang SC",sans-serif;';
        mask.innerHTML = `
            <div style="background:#fff;border-radius:12px;width:90%;max-width:420px;box-shadow:0 20px 60px rgba(0,0,0,0.3);overflow:hidden;animation:__modalIn .25s ease;">
                <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid #f0f2f5;">
                    <div style="font-size:15px;font-weight:600;color:#1e3c72;">${escapeHtml(title)}</div>
                    <button type="button" style="background:none;border:none;font-size:20px;cursor:pointer;color:#94a3b8;line-height:1;">×</button>
                </div>
                <div style="padding:18px 20px;font-size:13px;color:#2c3e50;line-height:2;">${contentHtml}</div>
            </div>
        `;
        // 关闭事件
        const close = () => mask.remove();
        mask.querySelector('button').onclick = close;
        mask.addEventListener('click', (e) => { if (e.target === mask) close(); });
        // 动画
        if (!document.getElementById('__modal-anim')) {
            const s = document.createElement('style');
            s.id = '__modal-anim';
            s.textContent = '@keyframes __modalIn{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}';
            document.head.appendChild(s);
        }
        document.body.appendChild(mask);
        return mask;
    }

    function tierStyle(cls) {
        if (cls === 'admin') return 'background:#d9534f;color:#fff;';
        if (cls === 'premium') return 'background:linear-gradient(135deg,#ffd700,#ffa726);color:#5a4500;';
        return 'background:#e0e7ee;color:#475569;';
    }

    function escapeHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
})();

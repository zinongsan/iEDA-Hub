/**
 * API 客户端
 *
 * 鉴权令牌存放在后端下发的 HttpOnly cookie（access_token / refresh_token）中，
 * 前端不可读、XSS 也读不到。请求统一 credentials:'include' 携带 cookie。
 * logged_in 为非 HttpOnly 的标记 cookie，仅供前端 UI 判断“是否已登录”。
 *
 * 401 时自动用 refresh cookie 换新 access cookie，失败再跳登录。
 */
const LOGGED_IN_KEY = 'logged_in';

function getCookie(name) {
    const m = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'));
    return m ? m[2] : '';
}

export const tokenStore = {
    // 仅判断登录态（HttpOnly 令牌前端不可读，用 logged_in 标记 cookie）
    get: () => !!getCookie(LOGGED_IN_KEY),
    // 兼容旧调用：令牌已由后端 Set-Cookie 下发，前端无需也不应存储
    set: () => {},
    getRefresh: () => null,
    clear: () => {
        // 清前端可见的标记；HttpOnly 的 access/refresh 由后端 delete_cookie 清除
        document.cookie = `${LOGGED_IN_KEY}=; path=/; max-age=0; samesite=lax`;
    },
};

// 防止并发 401 触发多次刷新
let _refreshing = null;

async function doRefresh() {
    if (_refreshing) return _refreshing;
    _refreshing = (async () => {
        try {
            const res = await fetch('/api/v1/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: '{}',  // refresh 走 HttpOnly cookie，无需放 body
            });
            if (!res.ok) throw new Error('refresh failed');
            // 新令牌由后端 Set-Cookie 下发，无需读响应体
            return true;
        } catch (e) {
            tokenStore.clear();
            if (!location.pathname.endsWith('/login')) {
                location.href = '/login?next=' + encodeURIComponent(location.pathname);
            }
            throw e;
        } finally {
            _refreshing = null;
        }
    })();
    return _refreshing;
}

export async function api(path, options = {}) {
    const buildHeaders = () => {
        const headers = options.headers || {};
        headers['Content-Type'] = 'application/json';
        return headers;
    };

    let res = await fetch(path, { ...options, headers: buildHeaders(), credentials: 'include' });

    // 401 且不是登录/刷新接口本身 → 尝试刷新一次后重试
    if (res.status === 401 && !path.endsWith('/auth/login') && !path.endsWith('/auth/refresh')) {
        try {
            await doRefresh();
        } catch (_) {
            throw new Error('未登录');
        }
        res = await fetch(path, { ...options, headers: buildHeaders(), credentials: 'include' });
    }

    if (res.status === 401) {
        tokenStore.clear();
        if (!path.endsWith('/auth/login') && !location.pathname.endsWith('/login')) {
            location.href = '/login?next=' + encodeURIComponent(location.pathname);
        }
        throw new Error('未登录');
    }
    if (!res.ok) {
        let msg = '请求失败';
        try { msg = (await res.json()).detail || msg; } catch (_) {}
        throw new Error(msg);
    }
    if (res.status === 204) return null;
    return res.json();
}

/**
 * 登出：拉黑 access 与 refresh token，清登录态并跳登录页。
 * 用裸 fetch（不走 api()），避免 401 触发自动刷新把 refresh 轮换掉导致旧 refresh 未拉黑。
 */
export async function logout() {
    try {
        await fetch('/api/v1/auth/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: '{}',
        });
    } catch (_) {}
    tokenStore.clear();
    if (!location.pathname.endsWith('/login')) {
        location.href = '/login';
    }
}

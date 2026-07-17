/**
 * 前端公共工具函数 - 认证相关
 * 包含：密码强度检查、验证码管理、表单验证等
 */

// ============================================
// 密码强度检查
// ============================================

/**
 * 检查密码强度
 * @param {string} password - 密码
 * @returns {Object} - { strength: 0-100, level: 'weak'|'medium'|'strong', checks: {...} }
 */
function checkPasswordStrength(password) {
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password)
  };

  let strength = 0;
  strength += checks.length ? 20 : 0;
  strength += checks.uppercase ? 20 : 0;
  strength += checks.lowercase ? 20 : 0;
  strength += checks.number ? 20 : 0;
  strength += checks.special ? 20 : 0;

  let level = 'weak';
  if (strength >= 80) level = 'strong';
  else if (strength >= 60) level = 'medium';

  return { strength, level, checks };
}

/**
 * 更新密码强度UI
 * @param {string} password - 密码
 * @param {HTMLElement} strengthBar - 强度条元素
 * @param {HTMLElement} strengthText - 强度文本元素
 * @param {HTMLElement} hintsContainer - 提示列表容器（可选）
 */
function updatePasswordStrength(password, strengthBar, strengthText, hintsContainer) {
  const result = checkPasswordStrength(password);

  // 更新强度条
  strengthBar.className = `strength-bar ${result.level}`;
  strengthBar.style.width = `${result.strength}%`;

  // 更新文本
  const levelText = {
    weak: '弱',
    medium: '中',
    strong: '强'
  };
  strengthText.textContent = levelText[result.level];
  strengthText.className = `strength-text ${result.level}`;

  // 更新提示列表
  if (hintsContainer) {
    const hints = hintsContainer.querySelectorAll('.hint');
    hints[0].className = result.checks.length ? 'hint valid' : 'hint';
    hints[0].textContent = result.checks.length ? '✓ 至少8位' : '○ 至少8位';

    if (hints[1]) {
      hints[1].className = result.checks.uppercase ? 'hint valid' : 'hint';
      hints[1].textContent = result.checks.uppercase ? '✓ 包含大写字母' : '○ 包含大写字母';
    }

    if (hints[2]) {
      hints[2].className = result.checks.lowercase ? 'hint valid' : 'hint';
      hints[2].textContent = result.checks.lowercase ? '✓ 包含小写字母' : '○ 包含小写字母';
    }

    if (hints[3]) {
      hints[3].className = result.checks.number ? 'hint valid' : 'hint';
      hints[3].textContent = result.checks.number ? '✓ 包含数字' : '○ 包含数字';
    }
  }

  return result;
}

// ============================================
// 验证码管理
// ============================================

/**
 * 加载验证码
 * @param {HTMLImageElement} imgElement - 图片元素
 * @returns {Promise<string>} - 返回captcha_id
 */
async function loadCaptcha(imgElement) {
  try {
    const response = await fetch('/api/v1/auth/captcha', {
      method: 'GET',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error('加载验证码失败');
    }

    const captchaId = response.headers.get('X-Captcha-Id');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    imgElement.src = url;
    imgElement.dataset.captchaId = captchaId;

    return captchaId;
  } catch (error) {
    console.error('加载验证码失败:', error);
    imgElement.alt = '加载失败';
    throw error;
  }
}

/**
 * 刷新验证码
 * @param {HTMLImageElement} imgElement - 图片元素
 */
async function refreshCaptcha(imgElement) {
  imgElement.style.opacity = '0.5';
  try {
    return await loadCaptcha(imgElement);
  } finally {
    imgElement.style.opacity = '1';
  }
}

// ============================================
// 密码显示/隐藏
// ============================================

/**
 * 切换密码显示/隐藏
 * @param {HTMLInputElement} passwordInput - 密码输入框
 * @param {HTMLButtonElement} toggleButton - 切换按钮
 */
function togglePasswordVisibility(passwordInput, toggleButton) {
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleButton.innerHTML = '👁️';
    toggleButton.setAttribute('aria-label', '隐藏密码');
  } else {
    passwordInput.type = 'password';
    toggleButton.innerHTML = '👁️‍🗨️';
    toggleButton.setAttribute('aria-label', '显示密码');
  }
}

// ============================================
// 表单验证
// ============================================

/**
 * 验证邮箱格式
 * @param {string} email
 * @returns {boolean}
 */
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * 验证用户名格式（3-50字符，字母数字下划线）
 * @param {string} username
 * @returns {boolean}
 */
function validateUsername(username) {
  return username.length >= 3 && username.length <= 50 && /^[a-zA-Z0-9_]+$/.test(username);
}

/**
 * 显示字段错误
 * @param {HTMLInputElement} input - 输入框
 * @param {string} message - 错误消息
 */
function showFieldError(input, message) {
  input.classList.add('error');
  let errorEl = input.parentElement.querySelector('.field-error');
  if (!errorEl) {
    errorEl = document.createElement('div');
    errorEl.className = 'field-error';
    input.parentElement.appendChild(errorEl);
  }
  errorEl.textContent = message;
  errorEl.style.display = 'block';
}

/**
 * 清除字段错误
 * @param {HTMLInputElement} input - 输入框
 */
function clearFieldError(input) {
  input.classList.remove('error');
  const errorEl = input.parentElement.querySelector('.field-error');
  if (errorEl) {
    errorEl.style.display = 'none';
  }
}

// ============================================
// API辅助函数（修复JSON解析错误）
// ============================================

/**
 * API请求封装
 * @param {string} url
 * @param {Object} options
 * @returns {Promise<any>}
 */
async function api(url, options = {}) {
  try {
    const res = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    // 检查Content-Type，只有JSON才解析
    const contentType = res.headers.get('content-type');
    let data;

    if (contentType && contentType.includes('application/json')) {
      data = await res.json();
    } else {
      // 非JSON响应（可能是HTML错误页面）
      const text = await res.text();
      console.error('服务器返回非JSON响应:', text.substring(0, 200));
      data = { detail: `服务器错误 (HTTP ${res.status})` };
    }

    if (!res.ok) {
      throw new Error(data.detail || `HTTP ${res.status}`);
    }

    return data;
  } catch (error) {
    // 处理网络错误
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('网络连接失败，请检查网络');
    }
    throw error;
  }
}

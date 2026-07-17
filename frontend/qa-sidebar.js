// ========================================
// 对话历史管理 JavaScript 功能
// ========================================

// 全局状态
window.qaSidebarState = {
  conversations: [],
  currentConversationId: null
};

// 初始化
window.addEventListener('DOMContentLoaded', function() {
  qaLoadConversations();
});

/**
 * 加载对话列表
 */
window.qaLoadConversations = async function() {
  try {
    const response = await fetch('/api/v1/rag/conversations?page=1&page_size=50', {
      credentials: 'include'  // ⭐ 携带cookie
    });
    if (!response.ok) {
      console.error('加载对话列表失败:', response.status);
      return;
    }

    const data = await response.json();
    window.qaSidebarState.conversations = data.conversations || [];

    // 更新统计面板
    if(window.qaUpdateStatsPanel) {
      window.qaUpdateStatsPanel();
    }

    // 重新渲染对话面板（如果打开的话）
    if(window.S && window.S.qaOpen && window.render) {
      window.render();
    }
  } catch (error) {
    console.error('加载对话列表失败:', error);
  }
};

/**
 * 按时间分组对话
 */
window.qaGroupByTime = function(conversations) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 24*60*60*1000);
  const thisWeek = new Date(today.getTime() - 7*24*60*60*1000);

  const groups = {
    '🕐 今天': [],
    '🕐 昨天': [],
    '🕐 本周': [],
    '🕐 更早': []
  };

  for (const conv of conversations) {
    const date = new Date(conv.updated_at);
    if (date >= today) {
      groups['🕐 今天'].push(conv);
    } else if (date >= yesterday) {
      groups['🕐 昨天'].push(conv);
    } else if (date >= thisWeek) {
      groups['🕐 本周'].push(conv);
    } else {
      groups['🕐 更早'].push(conv);
    }
  }

  // 移除空分组
  for (const key in groups) {
    if (groups[key].length === 0) delete groups[key];
  }

  return groups;
};

/**
 * 加载单个对话
 */
window.qaLoadConversation = async function(conversationId) {
  try {
    const response = await fetch(`/api/v1/rag/conversations/${conversationId}`, {
      credentials: 'include'  // ⭐ 携带cookie
    });
    if (!response.ok) throw new Error('加载失败');

    const data = await response.json();

    // 更新当前对话ID和session_id
    window.qaSidebarState.currentConversationId = conversationId;
    sessionStorage.setItem('qa_session_id', data.session_id);

    // 清空当前消息
    if(window.S) {
      window.S.qaMsg = [];
    }

    // 渲染消息列表
    for (const msg of data.messages) {
      if (msg.message_role === 'user') {
        window.S.qaMsg.push({
          r: 'me',
          t: msg.message_content,
          messageId: msg.id  // ⭐ 保存用户消息的ID
        });
      } else {
        window.S.qaMsg.push({
          r: 'ai',
          t: msg.message_content,
          sources: msg.sources?.sources || [],
          cost: parseFloat(msg.cost_yuan) || 0,
          tokens: {
            input: msg.tokens_input,
            output: msg.tokens_output,
            total: msg.tokens_total
          },
          messageId: msg.id,
          rating: msg.user_rating  // ⭐ 保存评分
        });
      }
    }

    // ⭐ 保存到localStorage（覆盖旧数据）
    if(window.saveQaMessages) {
      window.saveQaMessages();
    }

    // 重新渲染界面
    if(window.render) {
      window.render();
    }

    // 滚动到最新消息
    setTimeout(function() {
      const msgsEl = document.getElementById('qa-msgs');
      if (msgsEl) msgsEl.scrollTop = msgsEl.scrollHeight;
    }, 100);

  } catch (error) {
    console.error('加载对话失败:', error);
    alert('加载对话失败，请重试');
  }
};

/**
 * 新建对话
 */
window.qaNewConversation = function() {
  // 生成新的session_id
  const newSessionId = 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

  // 更新状态
  window.qaSidebarState.currentConversationId = null;
  sessionStorage.setItem('qa_session_id', newSessionId);

  // 清空消息
  if(window.S) {
    window.S.qaMsg = [];
  }

  // ⭐ 清除localStorage
  if(window.saveQaMessages) {
    window.saveQaMessages();
  }

  if(window.render) {
    window.render();
  }
};

/**
 * 删除对话
 */
window.qaDeleteConversation = async function(conversationId) {
  try {
    // 使用自定义确认对话框
    const confirmed = await window.showConversationDeleteConfirm();
    if(!confirmed) return;

    // 调用后端API删除
    const response = await fetch(`/api/v1/rag/conversations/${conversationId}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    if(!response.ok) {
      console.error('删除对话失败:', response.status);
      alert('删除失败，请重试');
      return;
    }

    // 如果删除的是当前对话，清空消息
    if(window.qaSidebarState.currentConversationId === conversationId) {
      window.qaSidebarState.currentConversationId = null;
      if(window.S) {
        window.S.qaMsg = [];
      }
      // 生成新的session_id
      const newSessionId = 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('qa_session_id', newSessionId);

      // ⭐ 清除localStorage
      if(window.saveQaMessages) {
        window.saveQaMessages();
      }
    }

    // 重新加载对话列表
    await qaLoadConversations();

    // 重新渲染界面
    if(window.render) {
      window.render();
    }

  } catch(error) {
    console.error('删除对话失败:', error);
    alert('删除失败，请重试');
  }
};

/**
 * 格式化时间（相对时间）
 */
window.qaFormatTimeAgo = function(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return diffMins + '分钟前';
  if (diffHours < 24) return diffHours + '小时前';
  if (diffDays < 7) return diffDays + '天前';

  // 超过7天显示具体日期
  return (date.getMonth() + 1) + '月' + date.getDate() + '日';
};

/**
 * HTML转义
 */
window.qaEscapeHtml = function(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

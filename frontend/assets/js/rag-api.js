/**
 * RAG API调用函数
 * 用于AI问答和讲义生成功能
 */

// ============================================
// 配置
// ============================================
const RAG_API_BASE = '/api/v1/rag';  // 使用相对路径

// ============================================
// AI问答功能
// ============================================

/**
 * AI问答
 * @param {string} question - 用户问题
 * @returns {Promise<object>} - 答案和相关信息
 */
async function callRAGQA(question) {
  try {
    const response = await fetch(`${RAG_API_BASE}/qa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',  // 包含cookies（认证）
      body: JSON.stringify({
        question: question,
        max_tokens: 500,
        temperature: 0.7
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('AI问答失败:', error);
    throw error;
  }
}

/**
 * 修改qaAsk函数来调用真实API
 * 替换iedahub.html中的qaAsk函数
 */
async function qaAsk(q) {
  if (!q.trim()) return;

  // 显示用户消息
  qaMessages.push({r: 'u', t: q});
  renderQA();

  // 显示加载中
  qaMessages.push({r: 'ai', t: '正在思考...', loading: true});
  renderQA();

  try {
    // 调用RAG API
    const result = await callRAGQA(q);

    // 移除加载消息
    qaMessages = qaMessages.filter(m => !m.loading);

    // 添加AI回答
    qaMessages.push({
      r: 'ai',
      t: result.answer,
      sources: result.sources,
      cost: result.cost,
      retrieval_mode: result.retrieval_mode
    });

    renderQA();

    // 滚动到底部
    const chatBox = document.getElementById('qa-chat');
    if (chatBox) {
      chatBox.scrollTop = chatBox.scrollHeight;
    }

  } catch (error) {
    // 移除加载消息
    qaMessages = qaMessages.filter(m => !m.loading);

    // 显示错误
    qaMessages.push({
      r: 'ai',
      t: '抱歉，AI服务暂时不可用，请稍后再试。错误：' + error.message
    });

    renderQA();
  }
}

// ============================================
// 讲义生成功能
// ============================================

/**
 * 生成讲义
 * @param {string} topic - 讲义主题
 * @param {string} detailLevel - 详细程度 simple/medium/detailed
 * @returns {Promise<object>} - 讲义内容
 */
async function callRAGGenerateLecture(topic, detailLevel = 'medium') {
  try {
    const response = await fetch(`${RAG_API_BASE}/lectures/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        topic: topic,
        detail_level: detailLevel
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('讲义生成失败:', error);
    throw error;
  }
}

/**
 * 测试RAG服务状态
 */
async function testRAGStatus() {
  try {
    const response = await fetch(`${RAG_API_BASE}/status`, {
      credentials: 'include'
    });
    const data = await response.json();
    console.log('RAG服务状态:', data);
    return data;
  } catch (error) {
    console.error('RAG服务连接失败:', error);
    return null;
  }
}

// ============================================
// 搜索知识库（调试用）
// ============================================

/**
 * 搜索知识库
 * @param {string} query - 搜索查询
 * @param {number} k - 返回结果数量
 */
async function searchKnowledgeBase(query, k = 3) {
  try {
    const response = await fetch(`${RAG_API_BASE}/search?query=${encodeURIComponent(query)}&k=${k}`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('搜索结果:', data);
    return data;
  } catch (error) {
    console.error('搜索失败:', error);
    throw error;
  }
}

// ============================================
// 使用示例
// ============================================

/*
// 在浏览器控制台测试：

// 1. 测试服务状态
await testRAGStatus();

// 2. 测试AI问答
const answer = await callRAGQA("什么是EDA工具？");
console.log(answer);

// 3. 测试讲义生成
const lecture = await callRAGGenerateLecture("数字电路设计基础", "medium");
console.log(lecture);

// 4. 搜索知识库
const results = await searchKnowledgeBase("时序分析", 3);
console.log(results);
*/

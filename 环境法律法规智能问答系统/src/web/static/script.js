document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chatContainer');
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const submitBtn = document.getElementById('submitBtn');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const docCount = document.getElementById('docCount');
    const welcomeMessage = document.getElementById('welcomeMessage');

    let isLoading = false;

    // 检查系统状态
    async function checkStatus() {
        try {
            const resp = await fetch('/api/status');
            const data = await resp.json();
            statusDot.className = 'status-dot online';
            statusText.textContent = '已就绪';
            if (data.db_docs_count > 0) {
                docCount.textContent = ` | ${data.db_docs_count} 个文档片段`;
            }
        } catch (e) {
            statusDot.className = 'status-dot offline';
            statusText.textContent = '服务未连接';
        }
    }

    // 添加消息到聊天
    function addMessage(type, content, sources) {
        welcomeMessage.style.display = 'none';

        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        // 将 Markdown 格式转换为 HTML
        const formatted = content
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        contentDiv.innerHTML = formatted;
        msgDiv.appendChild(contentDiv);

        if (sources && sources.length > 0 && type === 'bot') {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = '📚 来源: ' + sources.map(s =>
                `<span class="sources-tag">${s}</span>`
            ).join(' ');
            msgDiv.appendChild(sourcesDiv);
        }

        // 加载时间
        if (type === 'bot' && msgDiv.dataset) {
            // handled below
        }

        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 添加打字指示器
    function addTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message bot typing';
        div.id = 'typingIndicator';
        div.innerHTML = `
            <div class="message-content">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        `;
        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 移除打字指示器
    function removeTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    }

    // 发送查询
    async function sendQuery(query) {
        if (isLoading || !query.trim()) return;
        isLoading = true;
        submitBtn.disabled = true;

        addMessage('user', query);
        addTypingIndicator();

        try {
            const resp = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            removeTypingIndicator();

            if (!resp.ok) {
                const err = await resp.json();
                addMessage('error', `请求失败: ${err.detail || '未知错误'}`);
                return;
            }

            const data = await resp.json();
            addMessage('bot', data.answer, data.sources);

        } catch (e) {
            removeTypingIndicator();
            addMessage('error', `网络错误: ${e.message}，请检查服务是否运行`);
        } finally {
            isLoading = false;
            submitBtn.disabled = false;
            queryInput.focus();
        }
    }

    // 表单提交
    queryForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;
        queryInput.value = '';
        sendQuery(query);
    });

    // Enter提交
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            queryForm.dispatchEvent(new Event('submit'));
        }
    });

    // 初始化
    checkStatus();
});

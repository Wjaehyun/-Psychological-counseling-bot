/**
 * AI Chatbot UI - Main Application Script
 */

document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const themeToggle = document.getElementById('theme-toggle');
    const colorToggle = document.getElementById('color-toggle');

    // Sample bot responses for demo
    const botResponses = [
        "감사합니다. 그 상황이 많이 힘드셨겠네요. 조금 더 자세히 이야기해 주시겠어요?",
        "그런 감정을 느끼시는 건 자연스러운 일이에요. 스스로에게 너무 엄격하지 마세요. 😊",
        "좋은 질문이에요! 이런 상황에서는 먼저 깊은 호흡을 하고, 지금 느끼는 감정을 있는 그대로 받아들여 보세요.",
        "말씀해 주셔서 감사해요. 함께 해결책을 찾아볼게요. 혹시 이전에 비슷한 상황에서는 어떻게 대처하셨나요?",
        "정말 힘든 시간을 보내고 계시네요. 하지만 이렇게 이야기를 나누는 것 자체가 큰 용기를 보여주는 거예요. 💪"
    ];

    // Initialize theme and color
    initTheme();
    initColorTheme();
    
    // Load recent chats from database
    loadRecentChats();

    /**
     * Load recent chats from API and render in sidebar
     */
    async function loadRecentChats() {
        const container = document.getElementById('recent-chats-container');
        if (!container) return;
        
        try {
            const response = await fetch('/api/recent-chats');
            const data = await response.json();
            
            if (data.success && data.chats && data.chats.length > 0) {
                container.innerHTML = data.chats.map(chat => `
                    <div class="chat-item" data-session-id="${chat.id}">
                        <span class="chat-icon">💭</span>
                        <div class="chat-preview">
                            <span class="chat-name">${escapeHtmlSimple(chat.title)}</span>
                            <span class="chat-date">${chat.date}</span>
                        </div>
                        <button class="chat-delete-btn" data-session-id="${chat.id}" title="대화 삭제">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `
                    <div class="chat-item empty">
                        <span class="chat-icon">💬</span>
                        <div class="chat-preview">
                            <span class="chat-name">채팅 기록이 없습니다</span>
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('최근 채팅 로드 실패:', error);
            container.innerHTML = `
                <div class="chat-item error">
                    <span class="chat-icon">⚠️</span>
                    <div class="chat-preview">
                        <span class="chat-name">로드 실패</span>
                    </div>
                </div>
            `;
        }
    }
    
    // Simple HTML escape for chat titles
    function escapeHtmlSimple(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Click event for recent chat items and delete buttons
    document.addEventListener('click', async function(e) {
        // Handle delete button click
        const deleteBtn = e.target.closest('.chat-delete-btn');
        if (deleteBtn) {
            e.stopPropagation();
            const sessionId = deleteBtn.dataset.sessionId;
            await deleteChatSession(sessionId);
            return;
        }
        
        // Handle chat item click (for switching sessions)
        const chatItem = e.target.closest('.chat-item[data-session-id]');
        if (chatItem && !e.target.closest('.chat-delete-btn')) {
            const sessionId = chatItem.dataset.sessionId;
            await switchToSession(sessionId);
        }
    });
    
    /**
     * Delete a chat session
     */
    async function deleteChatSession(sessionId) {
        // Confirmation dialog
        if (!confirm('이 대화를 삭제하시겠습니까?\n삭제된 대화는 복구할 수 없습니다.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/delete-session/${sessionId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('대화가 삭제되었습니다');
                // Refresh recent chats list
                loadRecentChats();
            } else {
                showToast('삭제 실패: ' + (data.message || '알 수 없는 오류'));
            }
        } catch (error) {
            console.error('대화 삭제 중 오류:', error);
            showToast('대화 삭제 중 오류가 발생했습니다');
        }
    }
    
    /**
     * Switch to a previous chat session and load its history
     */
    async function switchToSession(sessionId) {
        try {
            // 1. Switch the active session
            const switchResponse = await fetch('/api/switch-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: parseInt(sessionId) })
            });
            
            const switchData = await switchResponse.json();
            if (!switchData.success) {
                showToast('세션 전환 실패: ' + (switchData.message || '알 수 없는 오류'));
                return;
            }
            
            // 2. Load the chat history
            const historyResponse = await fetch(`/api/chat-history/${sessionId}`);
            const historyData = await historyResponse.json();
            
            if (!historyData.success) {
                showToast('채팅 기록 로드 실패');
                return;
            }
            
            // 3. Clear current messages and load history
            const chatMessagesEl = document.getElementById('chat-messages');
            if (!chatMessagesEl) return;
            
            // Keep only the welcome message or clear all
            chatMessagesEl.innerHTML = '';
            
            // Add welcome message
            chatMessagesEl.innerHTML = `
                <div class="message bot-message">
                    <div class="message-avatar"><img src="/static/images/icon.jpg" alt="Bot"></div>
                    <div class="message-content">
                        <div class="message-bubble">
                            <p>안녕하세요! 저는 심리 상담을 도와드리는 AI 도우미입니다. 😊</p>
                            <p>오늘 어떤 이야기를 나누고 싶으신가요? 편하게 말씀해 주세요.</p>
                        </div>
                    </div>
                </div>
            `;
            
            // Add historical messages
            historyData.messages.forEach(msg => {
                const time = msg.created_at ? new Date(msg.created_at).toLocaleTimeString('ko-KR', {
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true
                }) : '';
                
                if (msg.role === 'user') {
                    chatMessagesEl.innerHTML += `
                        <div class="message user-message">
                            <div class="message-content">
                                <div class="message-bubble">
                                    <p>${escapeHtmlSimple(msg.content)}</p>
                                </div>
                                <span class="message-time">${time}</span>
                            </div>
                        </div>
                    `;
                } else if (msg.role === 'assistant') {
                    chatMessagesEl.innerHTML += `
                        <div class="message bot-message">
                            <div class="message-avatar"><img src="/static/images/icon.jpg" alt="Bot"></div>
                            <div class="message-content">
                                <div class="message-bubble">
                                    <p>${escapeHtmlSimple(msg.content)}</p>
                                </div>
                                <span class="message-time">${time}</span>
                            </div>
                        </div>
                    `;
                }
            });
            
            // Scroll to bottom
            chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
            
            // Show chat view if in survey mode
            if (typeof showChatView === 'function') {
                showChatView();
            }
            
            // Highlight selected chat item
            document.querySelectorAll('.chat-item[data-session-id]').forEach(item => {
                item.classList.remove('active');
            });
            const selectedItem = document.querySelector(`.chat-item[data-session-id="${sessionId}"]`);
            if (selectedItem) {
                selectedItem.classList.add('active');
            }
            
            showToast('이전 대화를 불러왔습니다');
            
        } catch (error) {
            console.error('세션 전환 중 오류:', error);
            showToast('세션 전환 중 오류가 발생했습니다');
        }
    }
    
    // New chat button handler
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', startNewChat);
    }
    
    /**
     * Start a new chat session
     */
    async function startNewChat() {
        try {
            // Clear server-side session
            const response = await fetch('/api/new-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            // Clear chat messages UI
            const chatMessagesEl = document.getElementById('chat-messages');
            if (chatMessagesEl) {
                chatMessagesEl.innerHTML = `
                    <div class="message bot-message">
                        <div class="message-avatar"><img src="/static/images/icon.jpg" alt="Bot"></div>
                        <div class="message-content">
                            <div class="message-bubble">
                                <p>안녕하세요! 저는 심리 상담을 도와드리는 AI 도우미입니다. 😊</p>
                                <p>오늘 어떤 이야기를 나누고 싶으신가요? 편하게 말씀해 주세요.</p>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Show chat view if in survey mode
            if (typeof showChatView === 'function') {
                showChatView();
            }
            
            // Remove active state from recent chat items
            document.querySelectorAll('.chat-item[data-session-id]').forEach(item => {
                item.classList.remove('active');
            });
            
            // Focus on input
            const messageInput = document.getElementById('message-input');
            if (messageInput) {
                messageInput.focus();
            }
            
            showToast('새 대화가 시작되었습니다');
            
            // Refresh recent chats list
            loadRecentChats();
            
        } catch (error) {
            console.error('새 대화 시작 중 오류:', error);
            showToast('새 대화 시작 중 오류가 발생했습니다');
        }
    }

    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    themeToggle.addEventListener('click', toggleTheme);
    colorToggle.addEventListener('click', toggleColorTheme);

    // 로그아웃 버튼 이벤트
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function () {
            try {
                const response = await fetch('/api/logout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = data.redirect || '/login';
                }
            } catch (error) {
                console.error('로그아웃 실패:', error);
                window.location.href = '/login';
            }
        });
    }

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // 심리조사 뷰 토글
    const surveyNavBtn = document.getElementById('survey-nav-btn');
    const chatMessagesEl = document.getElementById('chat-messages');
    const chatHeader = document.querySelector('.chat-header');
    const chatInput = document.querySelector('.chat-input-container');
    const surveyView = document.getElementById('survey-view');
    const homeNavBtn = document.querySelector('.nav-item[title="홈"]');

    if (surveyNavBtn && surveyView) {
        surveyNavBtn.addEventListener('click', function (e) {
            e.preventDefault();
            showSurveyView();
        });
    }

    if (homeNavBtn) {
        homeNavBtn.addEventListener('click', function (e) {
            e.preventDefault();
            showChatView();
        });
    }

    // 챗봇 뷰 표시
    window.showChatView = function () {
        if (chatHeader) chatHeader.style.display = 'flex';
        if (chatMessagesEl) chatMessagesEl.style.display = 'flex';
        if (chatInput) chatInput.style.display = 'block';
        if (surveyView) surveyView.style.display = 'none';

        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        if (homeNavBtn) homeNavBtn.classList.add('active');
    };

    // 심리조사 뷰 표시
    window.showSurveyView = function () {
        if (chatHeader) chatHeader.style.display = 'none';
        if (chatMessagesEl) chatMessagesEl.style.display = 'none';
        if (chatInput) chatInput.style.display = 'none';
        if (surveyView) surveyView.style.display = 'flex';

        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        if (surveyNavBtn) surveyNavBtn.classList.add('active');
    };

    // Agent selection
    document.querySelectorAll('.agent-item').forEach(item => {
        item.addEventListener('click', function () {
            document.querySelectorAll('.agent-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Nav item selection - 실제 링크가 있는 경우 페이지 이동 허용
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // # 링크만 기본 동작 막기, 실제 URL은 이동 허용
            if (href === '#') {
                e.preventDefault();
            }
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Message action buttons (copy, share, etc.)
    chatMessages.addEventListener('click', function (e) {
        const copyBtn = e.target.closest('.msg-action[title="복사"]');
        if (copyBtn) {
            const messageContent = copyBtn.closest('.message-content').querySelector('.message-bubble').innerText;
            navigator.clipboard.writeText(messageContent).then(() => {
                showToast('클립보드에 복사되었습니다');
            });
        }
    });

    /**
     * Send user message and get bot response
     */
    async function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        // Add user message
        addMessage(text, 'user');
        messageInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        try {
            // Call RAG API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            hideTypingIndicator();

            if (data.success) {
                addMessage(data.response, 'bot');
            } else {
                // Error response
                addMessage(data.message || '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.', 'bot');
            }
        } catch (error) {
            console.error('Chat API 오류:', error);
            hideTypingIndicator();
            addMessage('죄송합니다. 서버와 연결할 수 없습니다. 잠시 후 다시 시도해주세요.', 'bot');
        }
    }

    /**
     * Add message to chat
     */
    function addMessage(text, type) {
        const time = new Date().toLocaleTimeString('ko-KR', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });

        const messageHTML = type === 'user' ? `
            <div class="message user-message">
                <div class="message-content">
                    <div class="message-bubble">
                        <p>${escapeHtml(text)}</p>
                    </div>
                    <span class="message-time">${time}</span>
                </div>
            </div>
        ` : `
            <div class="message bot-message">
                <div class="message-avatar"><img src="/static/images/icon.jpg" alt="Bot"></div>
                <div class="message-content">
                    <div class="message-bubble">
                        <p>${escapeHtml(text)}</p>
                    </div>
                    <div class="message-actions">
                        <button class="msg-action" title="복사">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        </button>
                        <button class="msg-action" title="공유">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="18" cy="5" r="3"></circle>
                                <circle cx="6" cy="12" r="3"></circle>
                                <circle cx="18" cy="19" r="3"></circle>
                                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                            </svg>
                        </button>
                        <button class="msg-action" title="좋아요">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                            </svg>
                        </button>
                    </div>
                    <span class="message-time">${time}</span>
                </div>
            </div>
        `;

        chatMessages.insertAdjacentHTML('beforeend', messageHTML);
        scrollToBottom();
    }

    /**
     * Show typing indicator
     */
    function showTypingIndicator() {
        const typingHTML = `
            <div class="message bot-message" id="typing-indicator">
                <div class="message-avatar"><img src="/static/images/icon.jpg" alt="Bot"></div>
                <div class="message-content">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        chatMessages.insertAdjacentHTML('beforeend', typingHTML);
        scrollToBottom();
    }

    /**
     * Hide typing indicator
     */
    function hideTypingIndicator() {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    }

    /**
     * Scroll chat to bottom
     */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * Initialize theme from localStorage
     */
    function initTheme() {
        const savedTheme = localStorage.getItem('chatbot-theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateThemeIcon(savedTheme);
    }

    /**
     * Toggle between light and dark theme
     */
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('chatbot-theme', newTheme);
        updateThemeIcon(newTheme);
    }

    /**
     * Update theme toggle button icon
     */
    function updateThemeIcon(theme) {
        const icon = theme === 'dark' ? `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
        ` : `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
        `;
        themeToggle.innerHTML = icon;
    }

    /**
     * Initialize color theme from localStorage
     */
    function initColorTheme() {
        const savedColor = localStorage.getItem('chatbot-color') || 'gold';
        if (savedColor === 'green' || savedColor === 'brown') {
            document.documentElement.setAttribute('data-color', savedColor);
        }
        updateColorIcon(savedColor);
    }

    /**
     * Toggle between gold, green, and brown color theme
     */
    function toggleColorTheme() {
        const currentColor = document.documentElement.getAttribute('data-color') || 'gold';
        let newColor;

        // Cycle: gold -> green -> brown -> gold
        if (currentColor === 'gold' || !currentColor) {
            newColor = 'green';
        } else if (currentColor === 'green') {
            newColor = 'brown';
        } else {
            newColor = 'gold';
        }

        if (newColor === 'gold') {
            document.documentElement.removeAttribute('data-color');
        } else {
            document.documentElement.setAttribute('data-color', newColor);
        }

        localStorage.setItem('chatbot-color', newColor);
        updateColorIcon(newColor);

        const themeNames = {
            gold: '🏆 골드 테마',
            green: '🌿 세이지 그린 테마',
            brown: '🍂 웜 브라운 테마'
        };
        showToast(themeNames[newColor]);
    }

    /**
     * Update color toggle button icon
     */
    function updateColorIcon(color) {
        const icons = { gold: '🏆', green: '🌿', brown: '🍂' };
        const names = { gold: '골드', green: '그린', brown: '브라운' };
        colorToggle.innerHTML = icons[color] || '🏆';
        colorToggle.title = `색상 변경 (현재: ${icons[color] || '🏆'}${names[color] || '골드'})`;
    }

    /**
     * Show toast notification
     */
    function showToast(message) {
        // Remove existing toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--text-primary);
            color: var(--bg-primary);
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});

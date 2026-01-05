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

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Agent selection
    document.querySelectorAll('.agent-item').forEach(item => {
        item.addEventListener('click', function () {
            document.querySelectorAll('.agent-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Nav item selection
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
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
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        // Add user message
        addMessage(text, 'user');
        messageInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        // Simulate bot response
        setTimeout(() => {
            hideTypingIndicator();
            const randomResponse = botResponses[Math.floor(Math.random() * botResponses.length)];
            addMessage(randomResponse, 'bot');
        }, 1000 + Math.random() * 1000);
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
                <div class="message-avatar">🤖</div>
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
                <div class="message-avatar">🤖</div>
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

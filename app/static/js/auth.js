/**
 * Auth Pages - Login & Signup Scripts
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize color theme
    initColorTheme();

    // Password toggle
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', function () {
            const input = this.parentElement.querySelector('input');
            const type = input.type === 'password' ? 'text' : 'password';
            input.type = type;

            // Update icon
            this.innerHTML = type === 'text' ? `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                </svg>
            ` : `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                </svg>
            `;
        });
    });

    // Password strength indicator
    const passwordInput = document.getElementById('password');
    const strengthBar = document.querySelector('.strength-bar');

    if (passwordInput && strengthBar) {
        passwordInput.addEventListener('input', function () {
            const password = this.value;
            let strength = 0;

            if (password.length >= 8) strength += 25;
            if (password.match(/[a-z]/)) strength += 25;
            if (password.match(/[A-Z]/)) strength += 25;
            if (password.match(/[0-9]/) || password.match(/[^a-zA-Z0-9]/)) strength += 25;

            strengthBar.style.width = strength + '%';
        });
    }

    // Password confirmation validation
    const passwordConfirm = document.getElementById('password-confirm');
    if (passwordConfirm && passwordInput) {
        passwordConfirm.addEventListener('input', function () {
            const formGroup = this.closest('.form-group');
            if (this.value && this.value !== passwordInput.value) {
                formGroup.classList.add('error');
                formGroup.classList.remove('success');
            } else if (this.value && this.value === passwordInput.value) {
                formGroup.classList.remove('error');
                formGroup.classList.add('success');
            } else {
                formGroup.classList.remove('error', 'success');
            }
        });
    }

    // Login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Demo: just redirect to main page
            console.log('Login:', { email, password });
            showToast('로그인 성공! 🎉');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        });
    }

    // Signup form submission
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const passwordConfirmVal = document.getElementById('password-confirm').value;

            if (password !== passwordConfirmVal) {
                showToast('비밀번호가 일치하지 않습니다');
                return;
            }

            // Demo: just redirect to login page
            console.log('Signup:', { name, email, password });
            showToast('회원가입 완료! 🎉');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1000);
        });
    }

    /**
     * Initialize color theme from localStorage
     */
    function initColorTheme() {
        const savedTheme = localStorage.getItem('chatbot-theme') || 'light';
        const savedColor = localStorage.getItem('chatbot-color') || 'gold';

        document.documentElement.setAttribute('data-theme', savedTheme);
        if (savedColor === 'green' || savedColor === 'brown') {
            document.documentElement.setAttribute('data-color', savedColor);
        }
    }

    /**
     * Show toast notification
     */
    function showToast(message) {
        const existingToast = document.querySelector('.toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 40px;
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

        setTimeout(() => toast.remove(), 2500);
    }
});

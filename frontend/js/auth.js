/* MediScan AI - Authentication Module
   Handles login, signup, form validation, and session management */

const API_BASE = window.location.origin;

// ─── Login Handler ───────────────────────────────────────────────────
async function handleLogin(e) {
    e.preventDefault();
    clearErrors('login');

    const identifier = document.getElementById('login-identifier').value.trim();
    const password = document.getElementById('login-password').value;
    const remember = document.getElementById('remember-me').checked;

    // Client-side validation
    let valid = true;
    if (!identifier) {
        showFieldError('login-identifier', 'Please enter your username or email');
        valid = false;
    }
    if (!password) {
        showFieldError('login-password', 'Please enter your password');
        valid = false;
    }
    if (!valid) return;

    const btn = document.getElementById('login-btn');
    btn.disabled = true;
    btn.textContent = 'Signing in...';

    try {
        const res = await fetch(`${API_BASE}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier, password, remember })
        });
        const data = await res.json();

        if (data.success) {
            // Store session
            const storage = remember ? localStorage : sessionStorage;
            storage.setItem('mediscan_token', data.token);
            storage.setItem('mediscan_user', JSON.stringify(data.user));
            showToast('Login successful! Welcome back.', 'success');
            setTimeout(() => navigateTo('home'), 500);
        } else {
            showFormMessage('login-message', data.message, 'error');
        }
    } catch (err) {
        showFormMessage('login-message', 'Connection error. Is the backend server running?', 'error');
    }

    btn.disabled = false;
    btn.textContent = 'Sign In';
}

// ─── Signup Handler ──────────────────────────────────────────────────
async function handleSignup(e) {
    e.preventDefault();
    clearErrors('signup');

    const fullName = document.getElementById('signup-fullname').value.trim();
    const username = document.getElementById('signup-username').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirm = document.getElementById('signup-confirm').value;

    // Client-side validation
    let valid = true;
    if (!fullName || fullName.length < 2) {
        showFieldError('signup-fullname', 'Name must be at least 2 characters');
        valid = false;
    }
    if (!username || username.length < 3) {
        showFieldError('signup-username', 'Username must be at least 3 characters');
        valid = false;
    }
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showFieldError('signup-email', 'Please enter a valid email address');
        valid = false;
    }
    if (!password || password.length < 6) {
        showFieldError('signup-password', 'Password must be at least 6 characters');
        valid = false;
    }
    if (password !== confirm) {
        showFieldError('signup-confirm', 'Passwords do not match');
        valid = false;
    }
    if (!valid) return;

    const btn = document.getElementById('signup-btn');
    btn.disabled = true;
    btn.textContent = 'Creating account...';

    try {
        const res = await fetch(`${API_BASE}/api/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: fullName, username, email, password, confirm_password: confirm })
        });
        const data = await res.json();

        if (data.success) {
            showToast('Account created! Please sign in.', 'success');
            setTimeout(() => navigateTo('login'), 800);
        } else {
            showFormMessage('signup-message', data.message, 'error');
        }
    } catch (err) {
        showFormMessage('signup-message', 'Connection error. Is the backend server running?', 'error');
    }

    btn.disabled = false;
    btn.textContent = 'Create Account';
}

// ─── Session Management ──────────────────────────────────────────────
function getToken() {
    return localStorage.getItem('mediscan_token') || sessionStorage.getItem('mediscan_token');
}

function getUser() {
    const raw = localStorage.getItem('mediscan_user') || sessionStorage.getItem('mediscan_user');
    return raw ? JSON.parse(raw) : null;
}

function isLoggedIn() {
    return !!getToken();
}

function logout() {
    const token = getToken();
    if (token) {
        fetch(`${API_BASE}/api/logout`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => {});
    }
    localStorage.removeItem('mediscan_token');
    localStorage.removeItem('mediscan_user');
    sessionStorage.removeItem('mediscan_token');
    sessionStorage.removeItem('mediscan_user');
    showToast('Logged out successfully.', 'info');
    navigateTo('landing');
}

function authHeaders() {
    return {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
    };
}

// ─── Form Helpers ────────────────────────────────────────────────────
function showFieldError(fieldId, message) {
    const input = document.getElementById(fieldId);
    const error = document.getElementById(fieldId + '-error');
    if (input) input.classList.add('error');
    if (error) {
        error.textContent = message;
        error.classList.add('visible');
    }
}

function clearErrors(prefix) {
    document.querySelectorAll(`#${prefix}-form .form-input`).forEach(el => el.classList.remove('error'));
    document.querySelectorAll(`#${prefix}-form .form-error`).forEach(el => {
        el.textContent = '';
        el.classList.remove('visible');
    });
    const msg = document.getElementById(`${prefix}-message`);
    if (msg) { msg.className = 'form-message'; msg.textContent = ''; }
}

function showFormMessage(id, message, type) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = message;
        el.className = `form-message ${type}`;
    }
}

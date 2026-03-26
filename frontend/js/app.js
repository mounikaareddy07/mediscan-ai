/* MediScan AI - Main Application Controller
   SPA Router, Navigation, Toast notifications, Loading overlay */

// ─── Current Page State ──────────────────────────────────────────────
let currentPage = 'landing';
window.lastScanResult = null;

// ─── Initialize App ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    if (isLoggedIn()) {
        navigateTo('home');
    } else {
        navigateTo('landing');
    }

    // Inject assistant panel into body
    const assistantHTML = getAssistantPanelHTML();
    document.body.insertAdjacentHTML('beforeend', assistantHTML);
});

// ─── Navigation Router ──────────────────────────────────────────────
function navigateTo(page, data) {
    currentPage = page;
    const content = document.getElementById('app-content');
    updateNav();

    // Show/hide assistant toggle based on login state
    const toggle = document.getElementById('assistant-toggle');
    if (toggle) {
        toggle.classList.toggle('visible', isLoggedIn());
    }

    switch(page) {
        case 'landing':
            content.innerHTML = renderLandingPage();
            break;
        case 'login':
            content.innerHTML = renderLoginPage();
            break;
        case 'signup':
            content.innerHTML = renderSignupPage();
            break;
        case 'home':
            if (!isLoggedIn()) { navigateTo('login'); return; }
            content.innerHTML = renderHomePage();
            break;
        case 'scan':
            if (!isLoggedIn()) { navigateTo('login'); return; }
            content.innerHTML = renderScanPage();
            selectedFile = null;
            break;
        case 'result':
            if (!isLoggedIn()) { navigateTo('login'); return; }
            content.innerHTML = renderResultPage(data);
            setTimeout(() => {
                if (data && data.probabilities) {
                    initProbabilityChart(data.probabilities);
                }
            }, 100);
            break;
        case 'dashboard':
            if (!isLoggedIn()) { navigateTo('login'); return; }
            loadDashboard();
            break;
        default:
            content.innerHTML = renderLandingPage();
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ─── Render App (alias for navigateTo) ───────────────────────────────
function renderApp(page, data) {
    navigateTo(page, data);
}

// ─── Update Navigation Bar ──────────────────────────────────────────
function updateNav() {
    const navLinks = document.getElementById('nav-links');
    if (!navLinks) return;

    if (isLoggedIn()) {
        const user = getUser();
        const initial = user ? user.full_name.charAt(0).toUpperCase() : 'U';
        navLinks.innerHTML = `
            <button class="nav-link ${currentPage === 'home' ? 'active' : ''}" onclick="navigateTo('home')">Home</button>
            <button class="nav-link ${currentPage === 'scan' ? 'active' : ''}" onclick="navigateTo('scan')">Scan</button>
            <button class="nav-link ${currentPage === 'dashboard' ? 'active' : ''}" onclick="navigateTo('dashboard')">Dashboard</button>
            <div class="nav-user-badge">
                <div class="nav-user-avatar">${initial}</div>
                ${user ? user.username : 'User'}
            </div>
            <button class="nav-btn nav-btn-outline" onclick="logout()">Logout</button>
        `;
    } else {
        navLinks.innerHTML = `
            <button class="nav-btn nav-btn-outline" onclick="navigateTo('login')">Login</button>
            <button class="nav-btn nav-btn-primary" onclick="navigateTo('signup')">Sign Up</button>
        `;
    }
}

// ─── Toast Notifications ─────────────────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;

    container.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ─── Loading Overlay ─────────────────────────────────────────────────
function showLoading(text = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    const loaderText = document.getElementById('loader-text');
    if (overlay) overlay.classList.remove('hidden');
    if (loaderText) loaderText.textContent = text;
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('hidden');
}

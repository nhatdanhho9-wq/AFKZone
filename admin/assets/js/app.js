/**
 * Main Application Controller
 */

import { login, logout, isAuthenticated, getUsername } from './api.js';
import { showToast } from './ui.js';
import { loadOverviewPage } from './pages/overview.js';
import { loadLicensesPage } from './pages/licenses.js';
import { loadOrdersPage } from './pages/orders.js';
import { loadProductsPage } from './pages/products.js';
import { loadTiersPage } from './pages/tiers.js';
import { loadTrialsPage } from './pages/trials.js';
import { loadNotificationsPage } from './pages/notifications.js';
import { loadDevicesPage } from './pages/devices.js';
import { loadConnectionsPage } from './pages/connections.js';
import { loadAnalyticsPage } from './pages/analytics.js';
import { loadHealthPage } from './pages/health.js';
import { loadSettingsPage } from './pages/settings.js';

// Page registry
const PAGES = {
    'overview': loadOverviewPage,
    'licenses': loadLicensesPage,
    'orders': loadOrdersPage,
    'products': loadProductsPage,
    'tiers': loadTiersPage,
    'devices': loadDevicesPage,
    'trials': loadTrialsPage,
    'connections': loadConnectionsPage,
    'notifications': loadNotificationsPage,
    'analytics': loadAnalyticsPage,
    'health': loadHealthPage,
    'settings': loadSettingsPage
};

/**
 * Initialize app on load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (isAuthenticated()) {
        showDashboard();
    } else {
        showLogin();
    }
});

/**
 * Show login screen
 */
function showLogin() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';

    // Setup login form
    const form = document.getElementById('login-form');
    form.addEventListener('submit', handleLogin);
}

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('login-btn');
    const errorDiv = document.getElementById('login-error');

    // Show loading state
    loginBtn.disabled = true;
    loginBtn.querySelector('.btn-text').style.display = 'none';
    loginBtn.querySelector('.btn-spinner').style.display = 'inline';
    errorDiv.style.display = 'none';

    try {
        await login(username, password);
        showDashboard();
    } catch (error) {
        errorDiv.textContent = error.message || 'Login failed. Please check your credentials.';
        errorDiv.style.display = 'block';
        loginBtn.disabled = false;
        loginBtn.querySelector('.btn-text').style.display = 'inline';
        loginBtn.querySelector('.btn-spinner').style.display = 'none';
    }
}

/**
 * Show dashboard after login
 */
function showDashboard() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'flex';

    // Set username in topbar
    const username = getUsername();
    if (username) {
        document.getElementById('username-display').textContent = username;
    }

    // Setup navigation
    setupNavigation();

    // Setup user menu
    setupUserMenu();

    // Load default page (overview)
    loadPage('overview');
}

/**
 * Setup navigation listeners
 */
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;

            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Load page
            loadPage(page);
        });
    });
}

/**
 * Setup user menu dropdown
 */
function setupUserMenu() {
    const menuBtn = document.getElementById('user-menu-btn');
    const dropdown = document.getElementById('user-menu-dropdown');
    const logoutBtn = document.getElementById('logout-btn');

    menuBtn.addEventListener('click', () => {
        const isVisible = dropdown.style.display === 'block';
        dropdown.style.display = isVisible ? 'none' : 'block';
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!menuBtn.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    // Logout handler
    logoutBtn.addEventListener('click', () => {
        logout();
    });
}

/**
 * Load a page
 */
function loadPage(pageName) {
    const pageContent = document.getElementById('page-content');
    const loader = PAGES[pageName];

    if (loader) {
        try {
            loader(pageContent);
        } catch (error) {
            console.error(`Error loading page ${pageName}:`, error);
            showToast(`Failed to load ${pageName} page`, 'error');
        }
    } else {
        showPlaceholder(pageName);
    }
}

/**
 * Show placeholder for unimplemented pages
 */
function showPlaceholder(pageName) {
    const pageContent = document.getElementById('page-content');
    pageContent.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">${pageName}</h1>
            <p class="page-subtitle">This page is under construction</p>
        </div>
        <div style="
            background: white;
            padding: 3rem;
            border-radius: 8px;
            text-align: center;
            color: #6D655B;
        ">
            <p>📦 Coming soon...</p>
        </div>
    `;
}

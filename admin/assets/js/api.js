/**
 * API Client Module
 * Handles all API requests with JWT authentication
 */

const API_BASE = 'https://api.afkzone.cloud';

/**
 * Fetch wrapper with automatic JWT injection and 401 handling
 * @param {string} path - API endpoint path (e.g., '/admin/login')
 * @param {object} options - Fetch options
 * @returns {Promise<object>} - Response JSON
 */
export async function apiFetch(path, options = {}) {
    const token = localStorage.getItem('jwt');
    const headers = { ...options.headers };

    // Auto-inject JWT token if available
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Default to JSON content type
    if (!headers['Content-Type'] && options.body && typeof options.body === 'object') {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(`${API_BASE}${path}`, {
            ...options,
            headers
        });

        // Handle 401 Unauthorized - force logout
        if (response.status === 401) {
            logout();
            throw new Error('Unauthorized - session expired');
        }

        // Parse JSON response
        const data = await response.json();

        // Handle API errors
        if (!response.ok) {
            throw new Error(data.detail || data.message || `API Error: ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Login and store JWT token
 * @param {string} username
 * @param {string} password
 * @returns {Promise<object>} - Token response
 */
export async function login(username, password) {
    const data = await apiFetch('/admin/login', {
        method: 'POST',
        body: { username, password }
    });

    if (data.access_token) {
        localStorage.setItem('jwt', data.access_token);
        localStorage.setItem('username', username);
    }

    return data;
}

/**
 * Logout - clear JWT and reload
 */
export function logout() {
    localStorage.removeItem('jwt');
    localStorage.removeItem('username');
    window.location.reload();
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
export function isAuthenticated() {
    return !!localStorage.getItem('jwt');
}

/**
 * Get stored username
 * @returns {string|null}
 */
export function getUsername() {
    return localStorage.getItem('username');
}

// =============================================================================
// Admin Endpoints
// =============================================================================

/**
 * Get dashboard stats
 */
export async function getDashboardStats() {
    return await apiFetch('/admin/dashboard/stats');
}

/**
 * Get all licenses
 */
export async function getAllLicenses() {
    return await apiFetch('/admin/licenses/all');
}

/**
 * Revoke a license
 */
export async function revokeLicense(licenseKey) {
    return await apiFetch(`/admin/licenses/${licenseKey}/revoke`, {
        method: 'POST'
    });
}

/**
 * Unrevoke a license
 */
export async function unrevokeLicense(licenseKey) {
    return await apiFetch(`/admin/licenses/${licenseKey}/unrevoke`, {
        method: 'POST'
    });
}

/**
 * Extend a license
 */
export async function extendLicense(licenseKey, additionalDays) {
    return await apiFetch(`/admin/licenses/${licenseKey}/extend?additional_days=${additionalDays}`, {
        method: 'PUT'
    });
}

/**
 * Delete a license
 */
export async function deleteLicense(licenseKey) {
    return await apiFetch(`/admin/licenses/${licenseKey}`, {
        method: 'DELETE'
    });
}

/**
 * Generate a new license manually
 */
export async function generateLicense(data) {
    return await apiFetch('/admin/licenses/generate', {
        method: 'POST',
        body: data
    });
}

/**
 * Get all orders
 */
export async function getAllOrders() {
    return await apiFetch('/admin/orders');
}

/**
 * Manually complete an order
 */
export async function completeOrder(transCode) {
    return await apiFetch(`/admin/orders/${transCode}/complete`, {
        method: 'POST'
    });
}

/**
 * Get all products
 */
export async function getProducts() {
    return await apiFetch('/products?active_only=false');
}

/**
 * Create product
 */
export async function createProduct(data) {
    return await apiFetch('/admin/products', {
        method: 'POST',
        body: data
    });
}

/**
 * Update product
 */
export async function updateProduct(id, data) {
    return await apiFetch(`/admin/products/${id}`, {
        method: 'PUT',
        body: data
    });
}

/**
 * Delete product
 */
export async function deleteProduct(id) {
    return await apiFetch(`/admin/products/${id}`, {
        method: 'DELETE'
    });
}

/**
 * Enable product
 */
export async function enableProduct(id) {
    return await apiFetch(`/admin/products/${id}/enable`, {
        method: 'POST'
    });
}

/**
 * Disable product
 */
export async function disableProduct(id) {
    return await apiFetch(`/admin/products/${id}/disable`, {
        method: 'POST'
    });
}

/**
 * Get all tiers
 */
export async function getTiers() {
    return await apiFetch('/admin/tiers');
}

/**
 * Create tier
 */
export async function createTier(data) {
    return await apiFetch('/admin/tiers', {
        method: 'POST',
        body: data
    });
}

/**
 * Update tier
 */
export async function updateTier(id, data) {
    return await apiFetch(`/admin/tiers/${id}`, {
        method: 'PUT',
        body: data
    });
}

/**
 * Delete tier
 */
export async function deleteTier(id) {
    return await apiFetch(`/admin/tiers/${id}`, {
        method: 'DELETE'
    });
}

/**
 * Get device details
 */
export async function getDevices() {
    return await apiFetch('/admin/devices/detailed');
}

/**
 * Clear device slot (remove device from license)
 */
export async function clearDeviceSlot(deviceId) {
    return await apiFetch(`/admin/devices/${deviceId}`, {
        method: 'DELETE'
    });
}

/**
 * Get trial devices
 */
export async function getTrialDevices() {
    return await apiFetch('/admin/trial-devices');
}

/**
 * Delete trial device
 */
export async function deleteTrialDevice(id) {
    return await apiFetch(`/admin/trial-devices/${id}`, {
        method: 'DELETE'
    });
}

/**
 * Clear all trial devices
 */
export async function clearAllTrials() {
    return await apiFetch('/admin/trial-devices', {
        method: 'DELETE'
    });
}

/**
 * Get connections log
 */
export async function getConnections() {
    return await apiFetch('/admin/connections');
}

/**
 * Get notifications
 */
export async function getNotifications() {
    return await apiFetch('/admin/notifications');
}

/**
 * Create notification
 */
export async function createNotification(data) {
    return await apiFetch('/admin/notifications', {
        method: 'POST',
        body: data
    });
}

/**
 * Delete notification
 */
export async function deleteNotification(id) {
    return await apiFetch(`/admin/notifications/${id}`, {
        method: 'DELETE'
    });
}

/**
 * Get revenue analytics
 */
export async function getRevenueAnalytics() {
    return await apiFetch('/admin/analytics/revenue');
}

/**
 * Get system health
 */
export async function getSystemHealth() {
    return await apiFetch('/health');
}

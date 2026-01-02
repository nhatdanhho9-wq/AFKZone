/**
 * UI Helper Module
 * Toast notifications, modals, skeleton loaders
 */

/**
 * Show toast notification
 * @param {string} message
 * @param {string} type - 'success', 'error', 'info'
 * @param {number} duration - milliseconds
 */
export function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show loading skeleton in a container
 * @param {HTMLElement} container
 * @param {number} rows
 */
export function showSkeleton(container, rows = 5) {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-wrapper';

    for (let i = 0; i < rows; i++) {
        const row = document.createElement('div');
        row.className = 'skeleton';
        row.style.height = '40px';
        row.style.marginBottom = '8px';
        skeleton.appendChild(row);
    }

    container.innerHTML = '';
    container.appendChild(skeleton);
}

/**
 * Clear skeleton and show content
 * @param {HTMLElement} container
 * @param {string} html
 */
export function showContent(container, html) {
    container.innerHTML = html;
}

/**
 * Format date to readable string with time
 * @param {string} isoString
 * @returns {string}
 */
export function formatDate(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

/**
 * Format number with commas
 * @param {number} num
 * @returns {string}
 */
export function formatNumber(num) {
    return num.toLocaleString('en-US');
}

/**
 * Get status badge HTML
 * @param {string} status - 'active', 'expired', 'revoked', etc.
 * @returns {string}
 */
export function getStatusBadge(status) {
    const badgeMap = {
        'active': 'badge-success',
        'expired': 'badge-warning',
        'revoked': 'badge-danger',
        'pending': 'badge-info',
        'success': 'badge-success',
        'failed': 'badge-danger'
    };

    const badgeClass = badgeMap[status.toLowerCase()] || 'badge-info';
    return `<span class="badge ${badgeClass}">${status}</span>`;
}

/**
 * Create confirmation modal
 * @param {string} title
 * @param {string} message
 * @param {function} onConfirm
 */
export function showConfirm(title, message, onConfirm) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;

    modal.innerHTML = `
        <div class="modal-card" style="
            background: white;
            padding: 2rem;
            border-radius: 8px;
            max-width: 400px;
            width: 90%;
        ">
            <h3 style="margin-bottom: 1rem; font-size: 18px;">${title}</h3>
            <p style="margin-bottom: 1.5rem; color: #6D655B;">${message}</p>
            <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                <button id="modal-cancel" style="
                    padding: 0.5rem 1rem;
                    background: #E6DED3;
                    border-radius: 4px;
                    font-weight: 500;
                ">Cancel</button>
                <button id="modal-confirm" style="
                    padding: 0.5rem 1rem;
                    background: #C44536;
                    color: white;
                    border-radius: 4px;
                    font-weight: 500;
                ">Confirm</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    modal.querySelector('#modal-cancel').addEventListener('click', () => {
        modal.remove();
    });

    modal.querySelector('#modal-confirm').addEventListener('click', () => {
        onConfirm();
        modal.remove();
    });
}

/**
 * Debounce function for search inputs
 * @param {function} func
 * @param {number} wait
 * @returns {function}
 */
export function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Escape HTML to prevent XSS
 * @param {string} str
 * @returns {string}
 */
export function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

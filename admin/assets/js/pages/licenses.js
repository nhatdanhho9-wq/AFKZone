/**
 * Licenses Page
 * View, search, revoke, unrevoke, extend licenses
 */

import { getAllLicenses, revokeLicense, unrevokeLicense, extendLicense, deleteLicense } from '../api.js';
import { showToast, showSkeleton, formatDate, getStatusBadge, showConfirm, escapeHtml } from '../ui.js';

let licensesData = [];

export async function loadLicensesPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Licenses</h1>
            <p class="page-subtitle">Manage all license keys and activations</p>
        </div>

        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">All Licenses</h3>
                <div>
                    <input
                        type="search"
                        id="license-search"
                        placeholder="Search license key, device ID..."
                        style="padding: 0.5rem; border: 1px solid var(--border); border-radius: 4px; width: 300px;"
                    >
                </div>
            </div>
            <div id="licenses-table-wrapper"></div>
        </div>
    `;

    const tableWrapper = document.getElementById('licenses-table-wrapper');
    showSkeleton(tableWrapper, 10);

    try {
        const data = await getAllLicenses();
        licensesData = Array.isArray(data) ? data : (data.licenses || []);
        renderLicensesTable(tableWrapper, licensesData);

        // Setup search
        document.getElementById('license-search').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = licensesData.filter(lic =>
                lic.license_key?.toLowerCase().includes(query) ||
                lic.device_id?.toLowerCase().includes(query) ||
                lic.tier?.toLowerCase().includes(query)
            );
            renderLicensesTable(tableWrapper, filtered);
        });
    } catch (error) {
        console.error('Failed to load licenses:', error);
        tableWrapper.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #C44536;">
                ⚠️ Failed to load licenses: ${error.message}
            </div>
        `;
    }
}

function renderLicensesTable(container, licenses) {
    if (licenses.length === 0) {
        container.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #6D655B;">
                No licenses found
            </div>
        `;
        return;
    }

    const rows = licenses.map(lic => `
        <tr>
            <td><code class="mono">${escapeHtml(lic.license_key || 'N/A')}</code></td>
            <td>${escapeHtml(lic.tier || 'N/A')}</td>
            <td>${getStatusBadge(lic.status || 'unknown')}</td>
            <td>${escapeHtml(String(lic.device_count || 0))} / ${escapeHtml(String(lic.max_devices || 0))}</td>
            <td>${escapeHtml(formatDate(lic.created_at))}</td>
            <td>${escapeHtml(formatDate(lic.expires_at))}</td>
            <td>
                <button
                    class="action-btn"
                    onclick="handleLicenseAction('${escapeHtml(lic.license_key)}', '${escapeHtml(lic.status)}')"
                    style="padding: 0.25rem 0.75rem; background: var(--accent-2); color: white; border-radius: 4px; font-size: 12px;"
                >
                    Actions ▼
                </button>
            </td>
        </tr>
    `).join('');

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>License Key</th>
                    <th>Tier</th>
                    <th>Status</th>
                    <th>Devices</th>
                    <th>Created</th>
                    <th>Expires</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

// Global action handler (for demo - in production use event delegation)
window.handleLicenseAction = function(licenseKey, status) {
    const actions = [];

    if (status === 'active') {
        actions.push({ label: 'Revoke', action: () => handleRevoke(licenseKey) });
        actions.push({ label: 'Extend', action: () => handleExtend(licenseKey) });
    } else if (status === 'revoked') {
        actions.push({ label: 'Unrevoke', action: () => handleUnrevoke(licenseKey) });
    }

    actions.push({ label: 'Delete', action: () => handleDelete(licenseKey), danger: true });

    // Simple action menu (in production, use proper dropdown)
    const choice = prompt(`Actions for ${licenseKey}:\n${actions.map((a, i) => `${i + 1}. ${a.label}`).join('\n')}\n\nEnter number:`);
    const index = parseInt(choice) - 1;
    if (index >= 0 && index < actions.length) {
        actions[index].action();
    }
};

async function handleRevoke(licenseKey) {
    showConfirm(
        'Revoke License',
        `Are you sure you want to revoke ${licenseKey}?`,
        async () => {
            try {
                await revokeLicense(licenseKey);
                showToast('License revoked successfully', 'success');
                location.reload(); // Reload to refresh data
            } catch (error) {
                showToast(`Failed to revoke: ${error.message}`, 'error');
            }
        }
    );
}

async function handleUnrevoke(licenseKey) {
    try {
        await unrevokeLicense(licenseKey);
        showToast('License unrevoked successfully', 'success');
        location.reload();
    } catch (error) {
        showToast(`Failed to unrevoke: ${error.message}`, 'error');
    }
}

async function handleExtend(licenseKey) {
    const days = prompt('Enter additional days to extend:');
    if (!days || isNaN(days)) return;

    try {
        await extendLicense(licenseKey, parseInt(days));
        showToast(`License extended by ${days} days`, 'success');
        location.reload();
    } catch (error) {
        showToast(`Failed to extend: ${error.message}`, 'error');
    }
}

async function handleDelete(licenseKey) {
    showConfirm(
        'Delete License',
        `Are you sure you want to permanently delete ${licenseKey}? This cannot be undone.`,
        async () => {
            try {
                await deleteLicense(licenseKey);
                showToast('License deleted successfully', 'success');
                location.reload();
            } catch (error) {
                showToast(`Failed to delete: ${error.message}`, 'error');
            }
        }
    );
}

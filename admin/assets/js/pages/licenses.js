/**
 * Licenses Page
 * View, search, revoke, unrevoke, extend, create licenses
 */

import { getAllLicenses, revokeLicense, unrevokeLicense, extendLicense, deleteLicense, generateLicense, getTiers } from '../api.js';
import { showToast, showSkeleton, formatDate, getStatusBadge, showConfirm, escapeHtml } from '../ui.js';

let licensesData = [];
let tiersData = [];

export async function loadLicensesPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Licenses</h1>
            <p class="page-subtitle">Manage all license keys and activations</p>
        </div>

        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">All Licenses</h3>
                <div style="display:flex;gap:0.5rem;align-items:center;">
                    <input
                        type="search"
                        id="license-search"
                        placeholder="Search license key, device ID..."
                        style="padding: 0.5rem; border: 1px solid var(--border); border-radius: 4px; width: 250px;"
                    >
                    <button id="create-license-btn" style="padding:0.5rem 1rem;background:var(--accent-2);color:white;border-radius:4px;font-weight:500;cursor:pointer;">+ Create License</button>
                </div>
            </div>
            <div id="licenses-table-wrapper"></div>
        </div>
        <div id="license-modal" style="display:none"></div>
    `;

    const tableWrapper = document.getElementById('licenses-table-wrapper');
    showSkeleton(tableWrapper, 10);

    // Load tiers for the create modal
    try {
        const tiersResult = await getTiers();
        tiersData = Array.isArray(tiersResult) ? tiersResult : (tiersResult.tiers || []);
    } catch (e) {
        console.warn('Could not load tiers:', e);
    }

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

        // Setup create button
        document.getElementById('create-license-btn').addEventListener('click', () => showCreateLicenseModal());
    } catch (error) {
        console.error('Failed to load licenses:', error);
        tableWrapper.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #C44536;">
                ⚠️ Failed to load licenses: ${error.message}
            </div>
        `;
    }
}

// Show modal for creating a new license
function showCreateLicenseModal() {
    const modal = document.getElementById('license-modal');

    const tierOptions = tiersData.map(t =>
        `<option value="${escapeHtml(t.tier_key)}">${escapeHtml(t.tier_name)}</option>`
    ).join('');

    modal.innerHTML = `
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000">
            <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                <h3 style="margin:0 0 1rem 0;font-size:18px;">Create New License</h3>
                <form id="create-license-form">
                    <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.5rem;font-size:14px;">Tier *</label>
                        <select name="tier" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px;">
                            ${tierOptions || '<option value="">No tiers available</option>'}
                        </select>
                    </div>
                    <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.5rem;font-size:14px;">Duration (days) *</label>
                        <input type="number" name="duration_days" min="1" value="30" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px;">
                    </div>
                    <div style="margin-bottom:1rem">
                        <label style="display:block;margin-bottom:0.5rem;font-size:14px;">Max Devices (optional)</label>
                        <input type="number" name="max_devices" min="1" placeholder="Default from tier" style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px;">
                    </div>
                    <div style="margin-bottom:1.5rem">
                        <label style="display:block;margin-bottom:0.5rem;font-size:14px;">Notes (optional)</label>
                        <textarea name="notes" placeholder="Internal notes..." style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px;min-height:60px;"></textarea>
                    </div>
                    <div style="display:flex;gap:0.5rem;justify-content:flex-end">
                        <button type="button" id="cancel-create-btn" style="padding:0.5rem 1rem;background:#E6DED3;border-radius:4px;cursor:pointer;">Cancel</button>
                        <button type="submit" style="padding:0.5rem 1rem;background:var(--accent-2);color:white;border-radius:4px;cursor:pointer;">Create</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    modal.style.display = 'block';

    modal.querySelector('#cancel-create-btn').addEventListener('click', () => modal.style.display = 'none');
    modal.querySelector('#create-license-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            tier: formData.get('tier'),
            duration_days: parseInt(formData.get('duration_days'))
        };

        const maxDevices = formData.get('max_devices');
        if (maxDevices) data.max_devices = parseInt(maxDevices);

        const notes = formData.get('notes');
        if (notes) data.notes = notes;

        try {
            const result = await generateLicense(data);
            const newKey = result.license_key || result.key || 'Created';
            showToast(`License created: ${newKey}`, 'success');
            modal.style.display = 'none';
            location.reload(); // Refresh to show new license
        } catch (error) {
            showToast(`Failed to create license: ${error.message}`, 'error');
        }
    });
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
            <td style="position:relative;">
                <button
                    class="action-btn"
                    data-license="${escapeHtml(lic.license_key)}"
                    data-status="${escapeHtml(lic.status)}"
                    style="padding: 0.25rem 0.75rem; background: var(--accent-2); color: white; border-radius: 4px; font-size: 12px; cursor: pointer;"
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

    // Attach event listeners to action buttons
    container.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const licenseKey = btn.dataset.license;
            const status = btn.dataset.status;
            showActionDropdown(btn, licenseKey, status);
        });
    });
}

// Show dropdown menu for license actions
function showActionDropdown(button, licenseKey, status) {
    // Remove any existing dropdown
    closeAllDropdowns();

    const actions = [];
    if (status === 'active') {
        actions.push({ label: '🚫 Revoke', action: () => handleRevoke(licenseKey), className: '' });
        actions.push({ label: '📅 Extend', action: () => handleExtend(licenseKey), className: '' });
    } else if (status === 'revoked') {
        actions.push({ label: '✅ Unrevoke', action: () => handleUnrevoke(licenseKey), className: '' });
    }
    actions.push({ label: '🗑️ Delete', action: () => handleDelete(licenseKey), className: 'danger' });

    const dropdown = document.createElement('div');
    dropdown.className = 'license-action-dropdown';
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        right: 0;
        background: white;
        border: 1px solid var(--border);
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        min-width: 140px;
        overflow: hidden;
    `;

    actions.forEach(action => {
        const item = document.createElement('button');
        item.textContent = action.label;
        item.style.cssText = `
            display: block;
            width: 100%;
            padding: 0.6rem 1rem;
            text-align: left;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.15s;
            ${action.className === 'danger' ? 'color: #C44536;' : 'color: var(--text);'}
        `;
        item.addEventListener('mouseenter', () => {
            item.style.background = action.className === 'danger' ? '#FEE2E2' : '#F3F4F6';
        });
        item.addEventListener('mouseleave', () => {
            item.style.background = 'none';
        });
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAllDropdowns();
            action.action();
        });
        dropdown.appendChild(item);
    });

    button.parentElement.appendChild(dropdown);

    // Close on click outside
    setTimeout(() => {
        document.addEventListener('click', closeAllDropdowns, { once: true });
    }, 0);
}

function closeAllDropdowns() {
    document.querySelectorAll('.license-action-dropdown').forEach(d => d.remove());
}

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
    // Create modal for extend input
    const modal = document.createElement('div');
    modal.className = 'extend-modal-overlay';
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
        <div style="background: white; padding: 2rem; border-radius: 8px; max-width: 400px; width: 90%;">
            <h3 style="margin: 0 0 1rem 0; font-size: 18px;">Extend License</h3>
            <p style="margin: 0 0 1rem 0; color: #6D655B; font-size: 14px;">
                License: <code style="background: #F3F4F6; padding: 0.2rem 0.4rem; border-radius: 4px;">${escapeHtml(licenseKey)}</code>
            </p>
            <div style="margin-bottom: 1.5rem;">
                <label style="display: block; margin-bottom: 0.5rem; font-size: 14px;">Additional days:</label>
                <input type="number" id="extend-days-input" min="1" value="30" 
                    style="width: 100%; padding: 0.5rem; border: 1px solid var(--border); border-radius: 4px; font-size: 14px;">
            </div>
            <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                <button id="extend-cancel" style="padding: 0.5rem 1rem; background: #E6DED3; border-radius: 4px; font-weight: 500; cursor: pointer;">Cancel</button>
                <button id="extend-confirm" style="padding: 0.5rem 1rem; background: var(--accent-2); color: white; border-radius: 4px; font-weight: 500; cursor: pointer;">Extend</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    const input = modal.querySelector('#extend-days-input');
    input.focus();
    input.select();

    modal.querySelector('#extend-cancel').addEventListener('click', () => modal.remove());
    modal.querySelector('#extend-confirm').addEventListener('click', async () => {
        const days = parseInt(input.value);
        if (!days || days < 1) {
            showToast('Please enter a valid number of days', 'error');
            return;
        }

        try {
            await extendLicense(licenseKey, days);
            showToast(`License extended by ${days} days`, 'success');
            modal.remove();
            location.reload();
        } catch (error) {
            showToast(`Failed to extend: ${error.message}`, 'error');
        }
    });

    // Allow Enter to confirm
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            modal.querySelector('#extend-confirm').click();
        }
    });
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

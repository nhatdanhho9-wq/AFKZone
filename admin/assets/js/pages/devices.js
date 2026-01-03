/**
 * Devices Page - With Clear device action
 */

import { getDevices, clearDeviceSlot } from '../api.js';
import { showToast, showSkeleton, formatDate, escapeHtml, showConfirm } from '../ui.js';

let devicesData = [];

export async function loadDevicesPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Devices</h1>
            <p class="page-subtitle">View and manage registered devices</p>
        </div>
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">All Devices</h3>
            </div>
            <div id="devices-table"></div>
        </div>
    `;

    loadDevices();
}

async function loadDevices() {
    const table = document.getElementById('devices-table');
    showSkeleton(table, 8);

    try {
        const data = await getDevices();
        devicesData = Array.isArray(data) ? data : (data.devices || []);
        renderTable(devicesData);
    } catch (error) {
        table.innerHTML = `<div style="padding:2rem;text-align:center;color:#C44536">Failed to load: ${escapeHtml(error.message)}</div>`;
    }
}

function renderTable(devices) {
    const table = document.getElementById('devices-table');
    if (!devices || devices.length === 0) {
        table.innerHTML = '<div style="padding:2rem;text-align:center;color:#6D655B">No devices</div>';
        return;
    }

    const rows = devices.map(d => {
        const expiresAt = d.expires_at ? new Date(d.expires_at) : null;
        const isExpired = expiresAt && expiresAt < new Date();
        const statusBadge = isExpired ? '<span class="badge badge-warning">Expired</span>' : '<span class="badge badge-success">Active</span>';

        return `
        <tr>
            <td><code class="mono">${escapeHtml(d.device_id || 'N/A')}</code></td>
            <td>${escapeHtml(d.model || 'N/A')}</td>
            <td>${escapeHtml(d.app_version || 'N/A')}</td>
            <td>${escapeHtml(d.license_key || 'N/A')}</td>
            <td>${escapeHtml(d.tier || 'N/A')}</td>
            <td>${escapeHtml(formatDate(d.activated_at))}</td>
            <td>${escapeHtml(formatDate(d.expires_at))}</td>
            <td>${statusBadge}</td>
            <td>
                <button 
                    class="clear-device-btn"
                    data-device-id="${escapeHtml(d.device_id)}"
                    style="padding:0.25rem 0.5rem;background:var(--warn);color:white;border-radius:4px;font-size:12px;cursor:pointer;"
                >
                    Clear
                </button>
            </td>
        </tr>
        `;
    }).join('');

    table.innerHTML = `<table><thead><tr><th>Device ID</th><th>Model</th><th>App Version</th><th>License</th><th>Tier</th><th>Activated</th><th>Expires</th><th>Status</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table>`;

    // Attach event listeners to clear buttons
    table.querySelectorAll('.clear-device-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const deviceId = btn.dataset.deviceId;
            handleClearDevice(deviceId);
        });
    });
}

function handleClearDevice(deviceId) {
    showConfirm(
        'Clear Device Slot',
        `Are you sure you want to remove device "${deviceId}" from its license? This will free up a device slot.`,
        async () => {
            try {
                await clearDeviceSlot(deviceId);
                showToast('Device slot cleared successfully', 'success');
                loadDevices(); // Refresh table
            } catch (error) {
                if (error.message.includes('404') || error.message.includes('not found')) {
                    showToast('Clear device API not available on server', 'error');
                } else {
                    showToast(`Failed to clear device: ${error.message}`, 'error');
                }
            }
        }
    );
}

/**
 * Devices Page - Read-only list
 */

import { getDevices } from '../api.js';
import { showToast, showSkeleton, formatDate, escapeHtml } from '../ui.js';

let devicesData = [];

export async function loadDevicesPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Devices</h1>
            <p class="page-subtitle">View all registered devices</p>
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
            <td><code class="mono">${escapeHtml(d.device_id||'N/A')}</code></td>
            <td>${escapeHtml(d.model||'N/A')}</td>
            <td>${escapeHtml(d.app_version||'N/A')}</td>
            <td>${escapeHtml(d.license_key||'N/A')}</td>
            <td>${escapeHtml(d.tier||'N/A')}</td>
            <td>${escapeHtml(formatDate(d.activated_at))}</td>
            <td>${escapeHtml(formatDate(d.expires_at))}</td>
            <td>${statusBadge}</td>
        </tr>
        `;
    }).join('');

    table.innerHTML = `<table><thead><tr><th>Device ID</th><th>Model</th><th>App Version</th><th>License</th><th>Tier</th><th>Activated</th><th>Expires</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>`;
}

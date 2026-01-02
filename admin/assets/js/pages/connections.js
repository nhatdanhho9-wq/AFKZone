/**
 * Connections Page - Read-only list
 */

import { getConnections } from '../api.js';
import { showToast, showSkeleton, formatDate, escapeHtml } from '../ui.js';

let connectionsData = [];

export async function loadConnectionsPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Connections</h1>
            <p class="page-subtitle">View connection history and logs</p>
        </div>
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">Recent Connections</h3>
            </div>
            <div id="connections-table"></div>
        </div>
    `;

    loadConnections();
}

async function loadConnections() {
    const table = document.getElementById('connections-table');
    showSkeleton(table, 10);

    try {
        const data = await getConnections();
        connectionsData = Array.isArray(data) ? data : (data.connections || []);
        renderTable(connectionsData);
    } catch (error) {
        table.innerHTML = `<div style="padding:2rem;text-align:center;color:#C44536">Failed to load: ${escapeHtml(error.message)}</div>`;
    }
}

function renderTable(connections) {
    const table = document.getElementById('connections-table');
    if (!connections || connections.length === 0) {
        table.innerHTML = '<div style="padding:2rem;text-align:center;color:#6D655B">No connections</div>';
        return;
    }

    const rows = connections.map(c => `
        <tr>
            <td><code class="mono">${escapeHtml(c.device_fingerprint||c.device_id||'N/A')}</code></td>
            <td>${escapeHtml(c.license_key||'N/A')}</td>
            <td>${escapeHtml(c.ip_address||'N/A')}</td>
            <td>${escapeHtml(formatDate(c.connected_at||c.created_at))}</td>
            <td>${escapeHtml(formatDate(c.disconnected_at||''))}</td>
            <td>${escapeHtml(String(c.duration_seconds||0))}s</td>
        </tr>
    `).join('');

    table.innerHTML = `<table><thead><tr><th>Device</th><th>License</th><th>IP Address</th><th>Connected</th><th>Disconnected</th><th>Duration</th></tr></thead><tbody>${rows}</tbody></table>`;
}

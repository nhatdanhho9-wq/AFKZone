/**
 * Trials Page - List + Delete + Clear All
 */

import { getTrialDevices, deleteTrialDevice, clearAllTrials } from '../api.js';
import { showToast, showSkeleton, formatDate, escapeHtml, showConfirm } from '../ui.js';

let trialsData = [];

export async function loadTrialsPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Trial Devices</h1>
            <p class="page-subtitle">Manage trial license activations</p>
        </div>
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">All Trial Devices</h3>
                <button id="clear-all-btn" style="padding:0.5rem 1rem;background:var(--danger);color:white;border-radius:4px;font-weight:500">Clear All Trials</button>
            </div>
            <div id="trials-table"></div>
        </div>
    `;

    loadTrials();
    document.getElementById('clear-all-btn').addEventListener('click', handleClearAll);
}

async function loadTrials() {
    const table = document.getElementById('trials-table');
    showSkeleton(table, 8);

    try {
        const data = await getTrialDevices();
        trialsData = Array.isArray(data) ? data : (data.devices || []);
        renderTable(trialsData);
    } catch (error) {
        table.innerHTML = `<div style="padding:2rem;text-align:center;color:#C44536">Failed to load: ${escapeHtml(error.message)}</div>`;
    }
}

function renderTable(trials) {
    const table = document.getElementById('trials-table');
    if (!trials || trials.length === 0) {
        table.innerHTML = '<div style="padding:2rem;text-align:center;color:#6D655B">No trial devices</div>';
        return;
    }

    const rows = trials.map(t => `
        <tr>
            <td><code class="mono">${escapeHtml(t.device_fingerprint||'N/A')}</code></td>
            <td>${escapeHtml(t.license_key||'N/A')}</td>
            <td>${escapeHtml(formatDate(t.created_at))}</td>
            <td>
                <button onclick="window.deleteTrialBtn(${t.id})" style="padding:0.25rem 0.75rem;background:var(--danger);color:white;border-radius:4px;font-size:12px">Delete</button>
            </td>
        </tr>
    `).join('');

    table.innerHTML = `<table><thead><tr><th>Device Fingerprint</th><th>License Key</th><th>Created</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function handleClearAll() {
    showConfirm('Clear All Trials', `Delete all ${trialsData.length} trial devices?`, async () => {
        try {
            await clearAllTrials();
            showToast('All trials cleared', 'success');
            loadTrials();
        } catch (error) {
            showToast(`Failed: ${error.message}`, 'error');
        }
    });
}

window.deleteTrialBtn = function(id) {
    showConfirm('Delete Trial Device', 'Are you sure?', async () => {
        try {
            await deleteTrialDevice(id);
            showToast('Trial device deleted', 'success');
            loadTrials();
        } catch (error) {
            showToast(`Failed: ${error.message}`, 'error');
        }
    });
};

/**
 * Settings Page - Info display
 */

import { showToast, escapeHtml } from '../ui.js';

export async function loadSettingsPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Settings</h1>
            <p class="page-subtitle">System configuration and information</p>
        </div>
        
        <div style="display:grid;gap:1.5rem">
            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h3 style="margin:0 0 1rem 0;font-size:16px">System Information</h3>
                <div style="display:grid;gap:0.75rem;font-size:14px">
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Version:</span> <strong>v2.2.46</strong></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Environment:</span> <strong>Production</strong></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Server Time:</span> <strong id="server-time">-</strong></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">API Base URL:</span> <code class="mono">https://api.afkzone.cloud</code></div>
                </div>
            </div>

            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h3 style="margin:0 0 1rem 0;font-size:16px">License Configuration</h3>
                <div style="display:grid;gap:0.75rem;font-size:14px">
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Trial Duration:</span> <strong>7 days</strong></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Max Devices per License:</span> <strong>Varies by tier</strong></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">License Format:</span> <code class="mono">XXXX-XXXX-XXXX-XXXX</code></div>
                </div>
            </div>

            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h3 style="margin:0 0 1rem 0;font-size:16px">Payment Gateway</h3>
                <div style="display:grid;gap:0.75rem;font-size:14px">
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Provider:</span> <strong>Casso</strong></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Webhook Status:</span> <span class="badge badge-success">Active</span></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Currency:</span> <strong>VND</strong></div>
                </div>
            </div>

            <div style="background:white;padding:2rem;border-radius:8px;border:1px solid var(--border);text-align:center;color:#6D655B">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin:0 auto 1rem">
                    <circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6m5.2-13.2l-4.2 4.2m0 6l4.2 4.2M1 12h6m6 0h6M6.8 6.8l4.2 4.2m0 6l-4.2 4.2"/>
                </svg>
                <p style="margin:0;font-size:14px">Configuration management interface coming soon.</p>
            </div>
        </div>
    `;
    
    // Update server time
    setInterval(() => {
        const timeEl = document.getElementById('server-time');
        if (timeEl) timeEl.textContent = new Date().toLocaleString();
    }, 1000);
}

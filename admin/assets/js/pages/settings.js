/**
 * Settings Page - Info display with data source labels
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
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Version:</span> <span><strong>v2.2.46</strong> <span style="font-size:11px;color:#999;background:#F3F4F6;padding:2px 6px;border-radius:3px;margin-left:4px;">local</span></span></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Environment:</span> <span><strong>Production</strong> <span style="font-size:11px;color:#999;background:#F3F4F6;padding:2px 6px;border-radius:3px;margin-left:4px;">local</span></span></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Server Time:</span> <span><strong id="server-time">-</strong> <span style="font-size:11px;color:#10B981;background:#D1FAE5;padding:2px 6px;border-radius:3px;margin-left:4px;">live</span></span></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">API Base URL:</span> <code class="mono">https://api.afkzone.cloud</code></div>
                </div>
            </div>

            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h3 style="margin:0 0 1rem 0;font-size:16px">License Configuration</h3>
                <div style="display:grid;gap:0.75rem;font-size:14px">
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Trial Duration:</span> <span><strong>7 days</strong> <span style="font-size:11px;color:#999;background:#F3F4F6;padding:2px 6px;border-radius:3px;margin-left:4px;">local</span></span></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Max Devices per License:</span> <span><strong>Varies by tier</strong> <span style="font-size:11px;color:#3B82F6;background:#DBEAFE;padding:2px 6px;border-radius:3px;margin-left:4px;">tier-based</span></span></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">License Format:</span> <code class="mono">XXXX-XXXX-XXXX-XXXX</code></div>
                </div>
            </div>

            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h3 style="margin:0 0 1rem 0;font-size:16px">Payment Gateway</h3>
                <div style="display:grid;gap:0.75rem;font-size:14px">
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Provider:</span> <span><strong>Casso</strong> <span style="font-size:11px;color:#999;background:#F3F4F6;padding:2px 6px;border-radius:3px;margin-left:4px;">local</span></span></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Webhook Status:</span> <span class="badge badge-success">Active</span></div>
                    <div style="display:grid;grid-template-columns:200px 1fr"><span style="color:#6D655B">Currency:</span> <span><strong>VND</strong> <span style="font-size:11px;color:#999;background:#F3F4F6;padding:2px 6px;border-radius:3px;margin-left:4px;">local</span></span></div>
                </div>
            </div>

            <div style="background:white;padding:2rem;border-radius:8px;border:1px solid var(--border);text-align:center;color:#6D655B">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin:0 auto 1rem">
                    <circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6m5.2-13.2l-4.2 4.2m0 6l4.2 4.2M1 12h6m6 0h6M6.8 6.8l4.2 4.2m0 6l-4.2 4.2"/>
                </svg>
                <p style="margin:0;font-size:14px">Configuration management interface coming soon.<br><span style="font-size:12px;color:#999;">Server-reported settings will be available when backend endpoints are implemented.</span></p>
            </div>
        </div>
    `;

    // Update server time
    setInterval(() => {
        const timeEl = document.getElementById('server-time');
        if (timeEl) timeEl.textContent = new Date().toLocaleString();
    }, 1000);
}


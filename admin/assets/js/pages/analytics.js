/**
 * Analytics Page - Charts placeholder
 */

import { showToast, escapeHtml } from '../ui.js';

export async function loadAnalyticsPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Analytics</h1>
            <p class="page-subtitle">System metrics and usage statistics</p>
        </div>
        
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1.5rem;margin-bottom:2rem">
            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h4 style="margin:0 0 0.5rem 0;color:#6D655B;font-size:14px">Total Licenses</h4>
                <p style="margin:0;font-size:32px;font-weight:600;color:var(--text)">-</p>
            </div>
            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h4 style="margin:0 0 0.5rem 0;color:#6D655B;font-size:14px">Active Devices</h4>
                <p style="margin:0;font-size:32px;font-weight:600;color:var(--text)">-</p>
            </div>
            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h4 style="margin:0 0 0.5rem 0;color:#6D655B;font-size:14px">Total Revenue</h4>
                <p style="margin:0;font-size:32px;font-weight:600;color:var(--text)">-</p>
            </div>
            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <h4 style="margin:0 0 0.5rem 0;color:#6D655B;font-size:14px">Trial Users</h4>
                <p style="margin:0;font-size:32px;font-weight:600;color:var(--text)">-</p>
            </div>
        </div>

        <div style="background:white;padding:2rem;border-radius:8px;border:1px solid var(--border);text-align:center;color:#6D655B">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin:0 auto 1rem">
                <path d="M18 20V10M12 20V4M6 20v-6"/>
            </svg>
            <h3 style="margin:0 0 0.5rem 0">Charts Coming Soon</h3>
            <p style="margin:0;font-size:14px">Analytics dashboards and visualizations will be available in the next release.</p>
        </div>
    `;
}

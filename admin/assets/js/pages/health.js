/**
 * System Health Page - Status panel
 */

import { showToast, escapeHtml } from '../ui.js';

export async function loadHealthPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">System Health</h1>
            <p class="page-subtitle">Monitor system status and performance</p>
        </div>
        
        <div style="display:grid;gap:1.5rem">
            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
                    <h3 style="margin:0;font-size:16px">API Server</h3>
                    <span class="badge badge-success">Healthy</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;font-size:14px">
                    <div><span style="color:#6D655B">Uptime:</span> <strong>-</strong></div>
                    <div><span style="color:#6D655B">Requests/min:</span> <strong>-</strong></div>
                    <div><span style="color:#6D655B">Avg Response:</span> <strong>-</strong></div>
                </div>
            </div>

            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
                    <h3 style="margin:0;font-size:16px">Database</h3>
                    <span class="badge badge-success">Healthy</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;font-size:14px">
                    <div><span style="color:#6D655B">Connections:</span> <strong>-</strong></div>
                    <div><span style="color:#6D655B">Query Time:</span> <strong>-</strong></div>
                    <div><span style="color:#6D655B">Storage:</span> <strong>-</strong></div>
                </div>
            </div>

            <div style="background:white;padding:1.5rem;border-radius:8px;border:1px solid var(--border)">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
                    <h3 style="margin:0;font-size:16px">License Server</h3>
                    <span class="badge badge-success">Healthy</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;font-size:14px">
                    <div><span style="color:#6D655B">Active:</span> <strong>-</strong></div>
                    <div><span style="color:#6D655B">Validations/min:</span> <strong>-</strong></div>
                    <div><span style="color:#6D655B">Cache Hit:</span> <strong>-</strong></div>
                </div>
            </div>

            <div style="background:white;padding:2rem;border-radius:8px;border:1px solid var(--border);text-align:center;color:#6D655B">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin:0 auto 1rem">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                </svg>
                <p style="margin:0;font-size:14px">Real-time monitoring data will be available when backend metrics endpoints are implemented.</p>
            </div>
        </div>
    `;
}

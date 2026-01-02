/**
 * Overview Page
 * KPI cards + analytics dashboard
 */

import { getDashboardStats, getRevenueAnalytics, getSystemHealth } from '../api.js';
import { showToast, showSkeleton, formatNumber, formatDate } from '../ui.js';

export async function loadOverviewPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Overview</h1>
            <p class="page-subtitle">System dashboard and key metrics</p>
        </div>

        <div id="kpi-section"></div>

        <div id="charts-section" style="margin-top: 2rem;">
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 8px;
                text-align: center;
                color: #6D655B;
            ">
                <p>📊 Charts and analytics will be displayed here</p>
                <p style="font-size: 12px; margin-top: 0.5rem;">Revenue trends, license growth, device activity</p>
            </div>
        </div>
    `;

    const kpiSection = document.getElementById('kpi-section');
    showSkeleton(kpiSection, 3);

    try {
        const stats = await getDashboardStats();
        renderKPIs(kpiSection, stats);
    } catch (error) {
        console.error('Failed to load dashboard stats:', error);
        kpiSection.innerHTML = `
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 8px;
                text-align: center;
                color: #C44536;
            ">
                <p>⚠️ Failed to load dashboard stats</p>
                <p style="font-size: 12px; margin-top: 0.5rem;">${error.message}</p>
            </div>
        `;
    }
}

function renderKPIs(container, stats) {
    // Extract metrics from stats response
    const totalLicenses = stats.total_licenses || 0;
    const activeLicenses = stats.active_licenses || 0;
    const expiredLicenses = stats.expired_licenses || 0;
    const revokedLicenses = stats.revoked_licenses || 0;
    const pendingOrders = stats.pending_orders || 0;
    const revenue30d = stats.revenue_30d || 0;

    container.innerHTML = `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Licenses</div>
                <div class="kpi-value">${formatNumber(totalLicenses)}</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Active Licenses</div>
                <div class="kpi-value">${formatNumber(activeLicenses)}</div>
                <div class="kpi-delta positive">
                    ${totalLicenses > 0 ? Math.round((activeLicenses / totalLicenses) * 100) : 0}% of total
                </div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Expired Licenses</div>
                <div class="kpi-value">${formatNumber(expiredLicenses)}</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Revoked Licenses</div>
                <div class="kpi-value">${formatNumber(revokedLicenses)}</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Revenue (30d)</div>
                <div class="kpi-value">${formatNumber(revenue30d)} VND</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Pending Orders</div>
                <div class="kpi-value">${formatNumber(pendingOrders)}</div>
            </div>
        </div>
    `;
}

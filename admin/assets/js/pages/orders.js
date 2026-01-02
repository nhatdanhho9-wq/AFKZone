/**
 * Orders Page
 * View and manage bank orders
 */

import { getAllOrders, completeOrder } from '../api.js';
import { showToast, showSkeleton, formatDate, getStatusBadge, showConfirm, escapeHtml } from '../ui.js';

let ordersData = [];

export async function loadOrdersPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Orders</h1>
            <p class="page-subtitle">Bank transfer and payment orders</p>
        </div>

        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">All Orders</h3>
                <div>
                    <select id="order-status-filter" style="padding: 0.5rem; border: 1px solid var(--border); border-radius: 4px;">
                        <option value="">All Statuses</option>
                        <option value="pending">Pending</option>
                        <option value="success">Success</option>
                        <option value="failed">Failed</option>
                    </select>
                </div>
            </div>
            <div id="orders-table-wrapper"></div>
        </div>
    `;

    const tableWrapper = document.getElementById('orders-table-wrapper');
    showSkeleton(tableWrapper, 10);

    try {
        const data = await getAllOrders();
        ordersData = Array.isArray(data) ? data : (data.orders || []);
        renderOrdersTable(tableWrapper, ordersData);

        // Setup filter
        document.getElementById('order-status-filter').addEventListener('change', (e) => {
            const status = e.target.value;
            const filtered = status
                ? ordersData.filter(order => order.status?.toLowerCase() === status)
                : ordersData;
            renderOrdersTable(tableWrapper, filtered);
        });
    } catch (error) {
        console.error('Failed to load orders:', error);
        tableWrapper.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #C44536;">
                ⚠️ Failed to load orders: ${error.message}
            </div>
        `;
    }
}

function renderOrdersTable(container, orders) {
    if (orders.length === 0) {
        container.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #6D655B;">
                No orders found
            </div>
        `;
        return;
    }

    const rows = orders.map(order => `
        <tr>
            <td><code class="mono">${escapeHtml(order.trans_code || 'N/A')}</code></td>
            <td>${escapeHtml(order.tier || 'N/A')}</td>
            <td>${escapeHtml(order.amount ? order.amount.toLocaleString() : 'N/A')} VND</td>
            <td>${getStatusBadge(order.status || 'unknown')}</td>
            <td>${escapeHtml(formatDate(order.created_at))}</td>
            <td>
                ${order.status === 'pending' ? `
                    <button
                        class="action-btn"
                        onclick="handleCompleteOrder('${escapeHtml(order.trans_code)}')"
                        style="padding: 0.25rem 0.75rem; background: var(--success); color: white; border-radius: 4px; font-size: 12px;"
                    >
                        Complete
                    </button>
                ` : '-'}
            </td>
        </tr>
    `).join('');

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Trans Code</th>
                    <th>Tier</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

window.handleCompleteOrder = function(transCode) {
    showConfirm(
        'Complete Order',
        `Manually mark order ${transCode} as completed?`,
        async () => {
            try {
                await completeOrder(transCode);
                showToast('Order completed successfully', 'success');
                // Reload orders table without full page reload
                const tableWrapper = document.getElementById('orders-table-wrapper');
                const data = await getAllOrders();
                ordersData = Array.isArray(data) ? data : (data.orders || []);
                renderOrdersTable(tableWrapper, ordersData);
            } catch (error) {
                showToast(`Failed to complete order: ${error.message}`, 'error');
            }
        }
    );
};

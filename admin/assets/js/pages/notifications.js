/**
 * Notifications Page - Full CRUD
 */

import { getNotifications, createNotification, deleteNotification } from '../api.js';
import { showToast, showSkeleton, formatDate, escapeHtml, showConfirm } from '../ui.js';

let notificationsData = [];

export async function loadNotificationsPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Notifications</h1>
            <p class="page-subtitle">Manage system notifications for users</p>
        </div>
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">All Notifications</h3>
                <button id="create-notif-btn" style="padding:0.5rem 1rem;background:var(--accent-2);color:white;border-radius:4px;font-weight:500">+ Create Notification</button>
            </div>
            <div id="notifications-table"></div>
        </div>
        <div id="notif-modal" style="display:none"></div>
    `;

    loadNotifications();
    document.getElementById('create-notif-btn').addEventListener('click', () => showNotifModal());
}

async function loadNotifications() {
    const table = document.getElementById('notifications-table');
    showSkeleton(table, 8);

    try {
        const data = await getNotifications();
        notificationsData = Array.isArray(data) ? data : (data.notifications || []);
        renderTable(notificationsData);
    } catch (error) {
        table.innerHTML = `<div style="padding:2rem;text-align:center;color:#C44536">Failed to load</div>`;
    }
}

function renderTable(notifications) {
    const table = document.getElementById('notifications-table');
    if (!notifications || notifications.length === 0) {
        table.innerHTML = '<div style="padding:2rem;text-align:center;color:#6D655B">No notifications</div>';
        return;
    }

    const rows = notifications.map(n => `
        <tr>
            <td><strong>\${escapeHtml(n.title||'N/A')}</strong></td>
            <td>\${escapeHtml(n.message||'')}</td>
            <td><span class="badge badge-\${n.type||'info'}">\${escapeHtml(n.type||'info')}</span></td>
            <td>\${escapeHtml(n.target||'all')}</td>
            <td>\${escapeHtml(formatDate(n.expires_at))}</td>
            <td>\${escapeHtml(formatDate(n.created_at))}</td>
            <td>
                <button onclick="window.deleteNotifBtn(\${n.id})" style="padding:0.25rem 0.75rem;background:var(--danger);color:white;border-radius:4px;font-size:12px">Delete</button>
            </td>
        </tr>
    `).join('');

    table.innerHTML = `<table><thead><tr><th>Title</th><th>Message</th><th>Type</th><th>Target</th><th>Expires</th><th>Created</th><th>Actions</th></tr></thead><tbody>\${rows}</tbody></table>`;
}

function showNotifModal() {
    const modal = document.getElementById('notif-modal');
    modal.innerHTML = `
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000">
            <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                <h3 style="margin-bottom:1rem">Create Notification</h3>
                <form id="notif-form">
                    <div style="margin-bottom:1rem"><label>Title</label><input name="title" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="margin-bottom:1rem"><label>Message</label><textarea name="message" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px;min-height:80px"></textarea></div>
                    <div style="margin-bottom:1rem"><label>Type</label><select name="type" style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"><option>info</option><option>warning</option><option>success</option></select></div>
                    <div style="margin-bottom:1rem"><label>Target</label><input name="target" value="all" style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="display:flex;gap:0.5rem;justify-content:flex-end">
                        <button type="button" id="cancel-notif-btn" style="padding:0.5rem 1rem;background:#E6DED3;border-radius:4px">Cancel</button>
                        <button type="submit" style="padding:0.5rem 1rem;background:var(--accent-2);color:white;border-radius:4px">Create</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    modal.style.display = 'block';

    document.getElementById('cancel-notif-btn').addEventListener('click', () => modal.style.display = 'none');
    document.getElementById('notif-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            title: formData.get('title'),
            message: formData.get('message'),
            type: formData.get('type'),
            target: formData.get('target')
        };

        try {
            await createNotification(data);
            showToast('Notification created', 'success');
            modal.style.display = 'none';
            loadNotifications();
        } catch (error) {
            showToast(`Failed: \${error.message}`, 'error');
        }
    });
}

window.deleteNotifBtn = function(id) {
    showConfirm('Delete Notification', 'Are you sure?', async () => {
        try {
            await deleteNotification(id);
            showToast('Notification deleted', 'success');
            loadNotifications();
        } catch (error) {
            showToast(`Failed: \${error.message}`, 'error');
        }
    });
};

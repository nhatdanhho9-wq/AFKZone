/**
 * Tiers Page - Full CRUD
 */

import { getTiers, createTier, updateTier, deleteTier } from '../api.js';
import { showToast, showSkeleton, escapeHtml, showConfirm } from '../ui.js';

let tiersData = [];

export async function loadTiersPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Tiers</h1>
            <p class="page-subtitle">Manage license tiers and categories</p>
        </div>
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">All Tiers</h3>
                <button id="create-tier-btn" style="padding:0.5rem 1rem;background:var(--accent-2);color:white;border-radius:4px;font-weight:500">+ Create Tier</button>
            </div>
            <div id="tiers-table"></div>
        </div>
        <div id="tier-modal" style="display:none"></div>
    `;

    loadTiers();
    document.getElementById('create-tier-btn').addEventListener('click', () => showTierModal());
}

async function loadTiers() {
    const table = document.getElementById('tiers-table');
    showSkeleton(table, 5);

    try {
        const data = await getTiers();
        tiersData = Array.isArray(data) ? data : (data.tiers || []);
        renderTable(tiersData);
    } catch (error) {
        table.innerHTML = `<div style="padding:2rem;text-align:center;color:#C44536">Failed to load: \${escapeHtml(error.message)}</div>`;
    }
}

function renderTable(tiers) {
    const table = document.getElementById('tiers-table');
    if (!tiers || tiers.length === 0) {
        table.innerHTML = '<div style="padding:2rem;text-align:center;color:#6D655B">No tiers</div>';
        return;
    }

    const rows = tiers.map(t => `
        <tr>
            <td><code class="mono">\${escapeHtml(t.tier_key||'N/A')}</code></td>
            <td><strong>\${escapeHtml(t.tier_name||'N/A')}</strong></td>
            <td>\${escapeHtml(t.description||'')}</td>
            <td>\${escapeHtml(String(t.display_order||0))}</td>
            <td><span class="badge \${t.is_active?'badge-success':'badge-warning'}">\${t.is_active?'Active':'Inactive'}</span></td>
            <td>
                <button onclick="window.editTier(\${t.id})" style="padding:0.25rem 0.5rem;background:var(--accent-2);color:white;border-radius:4px;font-size:12px;margin-right:4px">Edit</button>
                <button onclick="window.deleteTierBtn(\${t.id})" style="padding:0.25rem 0.5rem;background:var(--danger);color:white;border-radius:4px;font-size:12px">Delete</button>
            </td>
        </tr>
    `).join('');

    table.innerHTML = `<table><thead><tr><th>Key</th><th>Name</th><th>Description</th><th>Order</th><th>Status</th><th>Actions</th></tr></thead><tbody>\${rows}</tbody></table>`;
}

function showTierModal(tier = null) {
    const modal = document.getElementById('tier-modal');
    const isEdit = !!tier;

    modal.innerHTML = `
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000">
            <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                <h3 style="margin-bottom:1rem">\${isEdit?'Edit':'Create'} Tier</h3>
                <form id="tier-form">
                    <div style="margin-bottom:1rem"><label>Tier Key</label><input name="tier_key" value="\${escapeHtml(tier?.tier_key||'')}" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="margin-bottom:1rem"><label>Tier Name</label><input name="tier_name" value="\${escapeHtml(tier?.tier_name||'')}" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="margin-bottom:1rem"><label>Description</label><textarea name="description" style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px;min-height:80px">\${escapeHtml(tier?.description||'')}</textarea></div>
                    <div style="margin-bottom:1rem"><label>Display Order</label><input name="display_order" type="number" value="\${tier?.display_order||0}" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="margin-bottom:1rem"><label><input type="checkbox" name="is_active" \${tier?.is_active?'checked':''} style="margin-right:0.5rem">Active</label></div>
                    <div style="display:flex;gap:0.5rem;justify-content:flex-end">
                        <button type="button" id="cancel-tier-btn" style="padding:0.5rem 1rem;background:#E6DED3;border-radius:4px">Cancel</button>
                        <button type="submit" style="padding:0.5rem 1rem;background:var(--accent-2);color:white;border-radius:4px">Save</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    modal.style.display = 'block';

    document.getElementById('cancel-tier-btn').addEventListener('click', () => modal.style.display = 'none');
    document.getElementById('tier-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            tier_key: formData.get('tier_key'),
            tier_name: formData.get('tier_name'),
            description: formData.get('description'),
            display_order: parseInt(formData.get('display_order')),
            is_active: formData.get('is_active') === 'on'
        };

        try {
            if (isEdit) {
                await updateTier(tier.id, data);
                showToast('Tier updated', 'success');
            } else {
                await createTier(data);
                showToast('Tier created', 'success');
            }
            modal.style.display = 'none';
            loadTiers();
        } catch (error) {
            showToast(`Failed: \${error.message}`, 'error');
        }
    });
}

window.editTier = function(id) {
    const tier = tiersData.find(t => t.id === id);
    if (tier) showTierModal(tier);
};

window.deleteTierBtn = function(id) {
    showConfirm('Delete Tier', 'Are you sure?', async () => {
        try {
            await deleteTier(id);
            showToast('Tier deleted', 'success');
            loadTiers();
        } catch (error) {
            showToast(`Failed: \${error.message}`, 'error');
        }
    });
};

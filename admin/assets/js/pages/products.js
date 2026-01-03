/**
 * Products Page - Full CRUD
 */

import { getProducts, createProduct, updateProduct, deleteProduct, enableProduct, disableProduct, getTiers } from '../api.js';
import { showToast, showSkeleton, formatDate, formatNumber, escapeHtml, showConfirm } from '../ui.js';

let productsData = [];
let tiersData = [];

export async function loadProductsPage(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Products</h1>
            <p class="page-subtitle">Manage product catalog and pricing</p>
        </div>
        <div class="table-container">
            <div class="table-header">
                <h3 class="table-title">All Products</h3>
                <button id="create-product-btn" style="padding:0.5rem 1rem;background:var(--accent-2);color:white;border-radius:4px;font-weight:500">+ Create Product</button>
            </div>
            <div id="products-table"></div>
        </div>
        <div id="product-modal" style="display:none"></div>
    `;

    loadProducts();
    loadTiersData();
    document.getElementById('create-product-btn').addEventListener('click', () => showProductModal());
}

async function loadProducts() {
    const table = document.getElementById('products-table');
    showSkeleton(table, 8);

    try {
        const data = await getProducts();
        productsData = Array.isArray(data) ? data : (data.products || []);
        renderTable(productsData);
    } catch (error) {
        table.innerHTML = `<div style="padding:2rem;text-align:center;color:#C44536">Failed to load: ${escapeHtml(error.message)}</div>`;
    }
}

async function loadTiersData() {
    try {
        const data = await getTiers();
        tiersData = Array.isArray(data) ? data : (data.tiers || []);
    } catch (error) {
        console.error('Failed to load tiers:', error);
    }
}

function renderTable(products) {
    // Sort by tier display_order + duration (newest not at bottom)
    products.sort((a, b) => {
        // Find tier display_order
        const tierA = tiersData.find(t => t.tier_key === a.tier);
        const tierB = tiersData.find(t => t.tier_key === b.tier);
        const orderA = tierA?.display_order || 999;
        const orderB = tierB?.display_order || 999;

        if (orderA !== orderB) return orderA - orderB;
        return b.duration_days - a.duration_days; // Descending duration
    });

    const table = document.getElementById('products-table');
    if (!products || products.length === 0) {
        table.innerHTML = '<div style="padding:2rem;text-align:center;color:#6D655B">No products</div>';
        return;
    }

    const rows = products.map(p => `
        <tr>
            <td><strong>${escapeHtml(p.name||'N/A')}</strong></td>
            <td>${escapeHtml(p.tier||'N/A')}</td>
            <td>${formatNumber(p.price||0)} VND</td>
            <td>${escapeHtml(String(p.duration_days||0))} days</td>
            <td>${escapeHtml(String(p.max_devices||0))}</td>
            <td><span class="badge ${p.is_active?'badge-success':'badge-warning'}">${p.is_active?'Active':'Disabled'}</span></td>
            <td>
                <button onclick="window.editProduct(${p.id})" style="padding:0.25rem 0.5rem;background:var(--accent-2);color:white;border-radius:4px;font-size:12px;margin-right:4px">Edit</button>
                <button onclick="window.toggleProduct(${p.id},${p.is_active})" style="padding:0.25rem 0.5rem;background:var(--warn);color:white;border-radius:4px;font-size:12px;margin-right:4px">${p.is_active?'Disable':'Enable'}</button>
                <button onclick="window.deleteProductBtn(${p.id})" style="padding:0.25rem 0.5rem;background:var(--danger);color:white;border-radius:4px;font-size:12px">Delete</button>
            </td>
        </tr>
    `).join('');

    table.innerHTML = `<table><thead><tr><th>Name</th><th>Tier</th><th>Price</th><th>Duration</th><th>Devices</th><th>Status</th><th>Actions</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function showProductModal(product = null) {
    const modal = document.getElementById('product-modal');
    const isEdit = !!product;

    modal.innerHTML = `
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000">
            <div style="background:white;padding:2rem;border-radius:8px;max-width:500px;width:90%">
                <h3 style="margin-bottom:1rem">${isEdit?'Edit':'Create'} Product</h3>
                <form id="product-form">
                    <div style="margin-bottom:1rem"><label>Name</label><input name="name" value="${escapeHtml(product?.name||'')}" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="margin-bottom:1rem">
                        <label>Tier</label>
                        <select name="tier" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px">
                            ${tiersData.map(t => `<option value="${t.tier_key}" ${product?.tier === t.tier_key ? 'selected' : ''}>${escapeHtml(t.tier_name)}</option>`).join('')}
                        </select>
                    </div>
                    <div style="margin-bottom:1rem"><label>Price (VND)</label><input name="price" type="number" value="${product?.price||0}" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="margin-bottom:1rem"><label>Duration (days)</label><input name="duration_days" type="number" value="${product?.duration_days||0}" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="margin-bottom:1rem"><label>Max Devices</label><input name="max_devices" type="number" value="${product?.max_devices||1}" required style="width:100%;padding:0.5rem;border:1px solid var(--border);border-radius:4px"></div>
                    <div style="display:flex;gap:0.5rem;justify-content:flex-end">
                        <button type="button" id="cancel-btn" style="padding:0.5rem 1rem;background:#E6DED3;border-radius:4px">Cancel</button>
                        <button type="submit" style="padding:0.5rem 1rem;background:var(--accent-2);color:white;border-radius:4px">Save</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    modal.style.display = 'block';

    document.getElementById('cancel-btn').addEventListener('click', () => modal.style.display = 'none');
    document.getElementById('product-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            name: formData.get('name'),
            tier: formData.get('tier'),
            price: parseInt(formData.get('price')),
            duration_days: parseInt(formData.get('duration_days')),
            max_devices: parseInt(formData.get('max_devices'))
        };

        try {
            if (isEdit) {
                await updateProduct(product.id, data);
                showToast('Product updated', 'success');
            } else {
                await createProduct(data);
                showToast('Product created', 'success');
            }
            modal.style.display = 'none';
            loadProducts();
        } catch (error) {
            showToast(`Failed: ${error.message}`, 'error');
        }
    });
}

window.editProduct = function(id) {
    const product = productsData.find(p => p.id === id);
    if (product) showProductModal(product);
};

window.toggleProduct = async function(id, isActive) {
    try {
        if (isActive) {
            await disableProduct(id);
            showToast('Product disabled', 'success');
        } else {
            await enableProduct(id);
            showToast('Product enabled', 'success');
        }
        loadProducts();
    } catch (error) {
        showToast(`Failed: ${error.message}`, 'error');
    }
};

window.deleteProductBtn = function(id) {
    showConfirm('Delete Product', 'Are you sure?', async () => {
        try {
            await deleteProduct(id);
            showToast('Product deleted', 'success');
            loadProducts();
        } catch (error) {
            showToast(`Failed: ${error.message}`, 'error');
        }
    });
};

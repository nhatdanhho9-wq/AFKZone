#!/usr/bin/env python3
"""
Fix admin dashboard sort/filter - the issue is that loadProducts/loadLicenses/loadOrders
do NOT set cachedProducts/cachedLicenses/cachedOrders properly before calling render functions.
"""
import re

def fix_sort_filter():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak_fix', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # The issue: original load functions set data but custom render functions
    # override them before caching. We need to ensure cached data is set correctly.
    
    fix_js = '''
<script>
// ==================== FIX: Initialize cached data on page load ====================
let cachedProducts = [];
let cachedLicenses = [];
let cachedOrders = [];
let cachedTiers = [];

// Product sort state
let productSortField = 'id';
let productSortAsc = true;

// License sort state
let licenseSortField = 'id';
let licenseSortAsc = true;

// Order sort state  
let orderSortField = 'created_at';
let orderSortAsc = false;

// Tier sort state
let tierSortField = 'id';
let tierSortAsc = true;

// ========== FIX loadProducts ==========
const _origLoadProducts = window.loadProducts;
window.loadProducts = async function() {
    try {
        const res = await fetch(`${API_BASE}/admin/products`, {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        const data = await res.json();
        cachedProducts = data.products || data || [];
        console.log('📦 Cached', cachedProducts.length, 'products');
        renderProductsTable();
    } catch (e) {
        console.error('Error loading products:', e);
    }
};

function sortProducts(field) {
    if (productSortField === field) {
        productSortAsc = !productSortAsc;
    } else {
        productSortField = field;
        productSortAsc = true;
    }
    renderProductsTable();
}

function renderProductsTable() {
    if (!cachedProducts || cachedProducts.length === 0) {
        console.warn('⚠️ No products to render');
        return;
    }
    
    const sorted = [...cachedProducts].sort((a, b) => {
        let valA = a[productSortField];
        let valB = b[productSortField];
        if (typeof valA === 'string') valA = valA?.toLowerCase() || '';
        if (typeof valB === 'string') valB = valB?.toLowerCase() || '';
        if (valA < valB) return productSortAsc ? -1 : 1;
        if (valA > valB) return productSortAsc ? 1 : -1;
        return 0;
    });
    
    const tbody = document.getElementById('products-table');
    if (!tbody) return;
    
    tbody.innerHTML = sorted.map(p => {
        const statusClass = p.is_active ? 'status-active' : 'status-inactive';
        const statusText = p.is_active ? 'Hoạt động' : 'Tắt';
        return `<tr>
            <td>${p.id}</td>
            <td>${p.name || '-'}</td>
            <td><span class="tier-badge tier-${p.tier}">${p.tier}</span></td>
            <td>${p.duration_days} ngày</td>
            <td>${Number(p.price).toLocaleString('vi-VN')}đ</td>
            <td>${p.max_devices === -1 ? '∞' : p.max_devices}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-action btn-edit" onclick="editProduct(${p.id})">Sửa</button>
                <button class="btn btn-action ${p.is_active ? 'btn-warning' : 'btn-success'}" onclick="${p.is_active ? 'disableProduct' : 'enableProduct'}(${p.id})">${p.is_active ? 'Tắt' : 'Bật'}</button>
                <button class="btn btn-action btn-delete" onclick="deleteProduct(${p.id})">Xóa</button>
            </td>
        </tr>`;
    }).join('');
    console.log('✅ Rendered', sorted.length, 'products');
}

// ========== FIX loadLicenses ==========
const _origLoadLicenses = window.loadLicenses;
window.loadLicenses = async function() {
    try {
        const res = await fetch(`${API_BASE}/admin/licenses`, {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        cachedLicenses = await res.json();
        console.log('🔑 Cached', cachedLicenses.length, 'licenses');
        renderLicensesTable();
    } catch (e) {
        console.error('Error loading licenses:', e);
    }
};

function sortLicenses(field) {
    if (licenseSortField === field) {
        licenseSortAsc = !licenseSortAsc;
    } else {
        licenseSortField = field;
        licenseSortAsc = true;
    }
    renderLicensesTable();
}

function renderLicensesTable() {
    if (!cachedLicenses || cachedLicenses.length === 0) {
        console.warn('⚠️ No licenses to render');
        const tbody = document.getElementById('licenses-table');
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">Không có license nào</td></tr>';
        return;
    }
    
    const sorted = [...cachedLicenses].sort((a, b) => {
        let valA = a[licenseSortField];
        let valB = b[licenseSortField];
        if (typeof valA === 'string') valA = valA?.toLowerCase() || '';
        if (typeof valB === 'string') valB = valB?.toLowerCase() || '';
        if (valA < valB) return licenseSortAsc ? -1 : 1;
        if (valA > valB) return licenseSortAsc ? 1 : -1;
        return 0;
    });
    
    const tbody = document.getElementById('licenses-table');
    if (!tbody) return;
    
    tbody.innerHTML = sorted.map(l => {
        const expDate = l.expires_at ? new Date(l.expires_at).toLocaleDateString('vi-VN') : '-';
        const isExpired = l.expires_at && new Date(l.expires_at) < new Date();
        const statusClass = l.is_revoked ? 'status-inactive' : (isExpired ? 'status-pending' : 'status-active');
        const statusText = l.is_revoked ? 'Thu hồi' : (isExpired ? 'Hết hạn' : 'Hoạt động');
        return `<tr>
            <td><code style="font-size:11px">${l.license_key}</code></td>
            <td><span class="tier-badge tier-${l.tier}">${l.tier || '-'}</span></td>
            <td>${l.device_count || 0}/${l.max_devices === -1 ? '∞' : l.max_devices}</td>
            <td>${expDate}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-action btn-view" onclick="viewLicenseDevices('${l.license_key}')">Devices</button>
                <button class="btn btn-action btn-delete" onclick="revokeLicense('${l.license_key}')">Thu hồi</button>
            </td>
        </tr>`;
    }).join('');
    console.log('✅ Rendered', sorted.length, 'licenses');
}

// ========== FIX loadOrders ==========
const _origLoadOrders = window.loadOrders;
window.loadOrders = async function() {
    try {
        const res = await fetch(`${API_BASE}/admin/orders`, {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        cachedOrders = await res.json();
        console.log('📋 Cached', cachedOrders.length, 'orders');
        renderOrdersTable();
    } catch (e) {
        console.error('Error loading orders:', e);
    }
};

function sortOrders(field) {
    if (orderSortField === field) {
        orderSortAsc = !orderSortAsc;
    } else {
        orderSortField = field;
        orderSortAsc = true;
    }
    renderOrdersTable();
}

function renderOrdersTable() {
    if (!cachedOrders || cachedOrders.length === 0) {
        console.warn('⚠️ No orders to render');
        const tbody = document.getElementById('orders-table');
        if (tbody) tbody.innerHTML = '<tr><td colspan="9" style="text-align:center">Không có đơn hàng nào</td></tr>';
        return;
    }
    
    const sorted = [...cachedOrders].sort((a, b) => {
        let valA = a[orderSortField];
        let valB = b[orderSortField];
        if (typeof valA === 'string') valA = valA?.toLowerCase() || '';
        if (typeof valB === 'string') valB = valB?.toLowerCase() || '';
        if (valA < valB) return orderSortAsc ? -1 : 1;
        if (valA > valB) return orderSortAsc ? 1 : -1;
        return 0;
    });
    
    const tbody = document.getElementById('orders-table');
    if (!tbody) return;
    
    tbody.innerHTML = sorted.map(o => {
        const statusClass = o.payment_status === 'success' ? 'status-active' : (o.payment_status === 'pending' ? 'status-pending' : 'status-inactive');
        const statusText = o.payment_status === 'success' ? 'Thành công' : (o.payment_status === 'pending' ? 'Chờ thanh toán' : o.payment_status);
        const createdAt = o.created_at ? new Date(o.created_at).toLocaleString('vi-VN') : '-';
        const paidAt = o.paid_at ? new Date(o.paid_at).toLocaleString('vi-VN') : '-';
        return `<tr>
            <td><code>${o.order_id || o.id}</code></td>
            <td><span class="tier-badge tier-${o.tier}">${o.tier}</span></td>
            <td>${o.duration_days} ngày</td>
            <td>${Number(o.amount || 0).toLocaleString('vi-VN')}đ</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${o.license_key ? `<code style="font-size:10px">${o.license_key}</code>` : '-'}</td>
            <td>${createdAt}</td>
            <td>${paidAt}</td>
            <td></td>
        </tr>`;
    }).join('');
    console.log('✅ Rendered', sorted.length, 'orders');
}

console.log('✅ Sort/Filter functions loaded and fixed!');
</script>
'''
    
    # Remove any existing fix scripts to avoid duplicates
    content = re.sub(r'<script>\s*// ==================== FIX: Initialize cached data.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script>\s*// ==================== FIX PRODUCTS SORT.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script>\s*// ==================== SORTING FUNCTIONS.*?</script>', '', content, flags=re.DOTALL)
    
    # Add new script before </body>
    content = content.replace('</body>', fix_js + '\n</body>')
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed sort/filter functions!")
    print("✅ Now cached data is properly initialized before rendering.")

if __name__ == '__main__':
    fix_sort_filter()

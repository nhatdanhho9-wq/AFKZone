#!/usr/bin/env python3
"""
Fix admin dashboard sort functions to properly cache and render data
"""
import re

def fix_sort_functions():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak_sort', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # ============================================
    # FIX: Override loadProducts to cache data properly
    # ============================================
    fix_products_js = '''
<script>
// ==================== FIX PRODUCTS SORT ====================
let productSortField = 'id';
let productSortAsc = true;

// Intercept loadProducts to cache data
const origLoadProducts = typeof loadProducts !== 'undefined' ? loadProducts : null;
if (origLoadProducts) {
    window.loadProducts = async function() {
        try {
            const res = await fetch(`${API_BASE}/admin/products`, {
                headers: {'Authorization': `Bearer ${authToken}`}
            });
            const data = await res.json();
            cachedProducts = data.products || data || [];
            renderProducts();
        } catch (e) {
            console.error('Error loading products:', e);
        }
    };
}

function sortProducts(field) {
    if (productSortField === field) {
        productSortAsc = !productSortAsc;
    } else {
        productSortField = field;
        productSortAsc = true;
    }
    renderProducts();
}

function renderProducts() {
    if (!cachedProducts || !cachedProducts.length) {
        console.log('⚠️ No cached products to render');
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
        const btnText = p.is_active ? 'Tắt' : 'Bật';
        const btnAction = p.is_active ? `deleteProduct(${p.id})` : `enableProduct(${p.id})`;
        
        return `<tr>
            <td>${p.id}</td>
            <td>${p.name || '-'}</td>
            <td>${p.tier}</td>
            <td>${p.duration_days} ngày</td>
            <td>${Number(p.price).toLocaleString('vi-VN')}đ</td>
            <td>${p.max_devices === -1 ? '∞' : p.max_devices}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-action btn-edit" onclick="editProduct(${p.id})">Sửa</button>
                <button class="btn btn-action ${p.is_active ? 'btn-delete' : 'btn-edit'}" onclick="${btnAction}">${btnText}</button>
                <button class="btn btn-action btn-delete" onclick="deleteProductPermanent(${p.id})">Xóa</button>
            </td>
        </tr>`;
    }).join('');
    
    console.log('✅ Rendered', sorted.length, 'products');
}

// ==================== FIX LICENSES SORT ====================  
let licenseSortField = 'license_key';
let licenseSortAsc = true;

const origLoadLicenses = typeof loadLicenses !== 'undefined' ? loadLicenses : null;
if (origLoadLicenses) {
    window.loadLicenses = async function() {
        try {
            const res = await fetch(`${API_BASE}/admin/licenses`, {
                headers: {'Authorization': `Bearer ${authToken}`}
            });
            cachedLicenses = await res.json();
            renderLicenses();
        } catch (e) {
            console.error('Error loading licenses:', e);
        }
    };
}

function sortLicenses(field) {
    if (licenseSortField === field) {
        licenseSortAsc = !licenseSortAsc;
    } else {
        licenseSortField = field;
        licenseSortAsc = true;
    }
    renderLicenses();
}

function renderLicenses() {
    if (!cachedLicenses || !cachedLicenses.length) {
        console.log('⚠️ No cached licenses to render');
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
        const statusClass = l.is_revoked ? 'status-inactive' : (isExpired ? 'status-pending' : (l.is_active ? 'status-active' : 'status-inactive'));
        const statusText = l.is_revoked ? 'Thu hồi' : (isExpired ? 'Hết hạn' : (l.is_active ? 'Hoạt động' : 'Tắt'));
        
        return `<tr>
            <td><code style="font-size:11px">${l.license_key}</code></td>
            <td>${l.tier || '-'}</td>
            <td>${l.device_count || 0}/${l.max_devices || '-'}</td>
            <td>${expDate}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-action btn-view" onclick="viewLicenseDevices('${l.license_key}')">Devices</button>
                ${l.is_revoked ? 
                    `<button class="btn btn-action btn-edit" onclick="restoreLicense('${l.license_key}')">Khôi phục</button>` :
                    `<button class="btn btn-action btn-delete" onclick="revokeLicense('${l.license_key}')">Thu hồi</button>`
                }
                <button class="btn btn-action btn-delete" onclick="deleteLicense('${l.license_key}')">Xóa</button>
            </td>
        </tr>`;
    }).join('');
    
    console.log('✅ Rendered', sorted.length, 'licenses');
}

// ==================== FIX ORDERS SORT ====================
let orderSortField = 'created_at';
let orderSortAsc = false;

const origLoadOrders = typeof loadOrders !== 'undefined' ? loadOrders : null;
if (origLoadOrders) {
    window.loadOrders = async function() {
        try {
            const res = await fetch(`${API_BASE}/admin/orders`, {
                headers: {'Authorization': `Bearer ${authToken}`}
            });
            cachedOrders = await res.json();
            renderOrders();
        } catch (e) {
            console.error('Error loading orders:', e);
        }
    };
}

function sortOrders(field) {
    if (orderSortField === field) {
        orderSortAsc = !orderSortAsc;
    } else {
        orderSortField = field;
        orderSortAsc = true;
    }
    renderOrders();
}

function renderOrders() {
    if (!cachedOrders || !cachedOrders.length) {
        console.log('⚠️ No cached orders to render');
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
            <td>${o.tier}</td>
            <td>${o.duration_days} ngày</td>
            <td>${Number(o.amount || 0).toLocaleString('vi-VN')}đ</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${o.license_key ? `<code style="font-size:10px">${o.license_key}</code>` : '-'}</td>
            <td>${createdAt}</td>
            <td>${paidAt}</td>
            <td>
                ${o.payment_status === 'pending' ? 
                    `<button class="btn btn-action btn-edit" onclick="completeOrder('${o.order_id}')">Hoàn thành</button>` : 
                    ''}
            </td>
        </tr>`;
    }).join('');
    
    console.log('✅ Rendered', sorted.length, 'orders');
}

console.log('✅ Sort/Render functions loaded successfully');
</script>
'''
    
    # Remove any existing sort function definitions to avoid duplicates
    content = re.sub(r'<script>\s*// ==================== FIX PRODUCTS SORT.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script>\s*// ==================== SORTING FUNCTIONS.*?</script>', '', content, flags=re.DOTALL)
    
    # Add new script before </body>
    content = content.replace('</body>', fix_products_js + '\n</body>')
    print("✅ Added fixed sort/render functions")
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ DONE!")

if __name__ == '__main__':
    fix_sort_functions()

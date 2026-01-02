#!/usr/bin/env python3
"""
Complete fix for admin dashboard:
1. Fix tab-tiers display:none inline style
2. Add sortable headers to all tables (Products, Licenses, Orders, Devices)
3. Add search/filter for all tables
"""

def fix_all():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak_complete', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # ============================================
    # 1. FIX tab-tiers inline display:none
    # ============================================
    # Remove style="display: none;" or style="display:none;"
    old_tier_div = '<div id="tab-tiers" class="tab-content" style="display: none;">'
    new_tier_div = '<div id="tab-tiers" class="tab-content">'
    content = content.replace(old_tier_div, new_tier_div)
    
    old_tier_div2 = '<div id="tab-tiers" class="tab-content" style="display:none;">'
    content = content.replace(old_tier_div2, new_tier_div)
    
    # Also fix any other variant
    import re
    content = re.sub(r'<div id="tab-tiers" class="tab-content"[^>]*style="[^"]*display:\s*none[^"]*"[^>]*>', 
                     '<div id="tab-tiers" class="tab-content">', content)
    print("✅ Fixed tab-tiers display:none")
    
    # ============================================
    # 2. Update showTab to handle tiers properly  
    # ============================================
    # Find the originalShowTab function and add tiers case
    if "case 'tiers':" not in content:
        old_show_tab = '''function showTab(tabName) {
            console.log('🔄 showTab called with:', tabName);'''
        new_show_tab = '''function showTab(tabName) {
            console.log('🔄 showTab called with:', tabName);
            
            // Handle tiers tab specially
            if (tabName === 'tiers') {
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
                const tiersTab = document.getElementById('tab-tiers');
                if (tiersTab) {
                    tiersTab.classList.add('active');
                    tiersTab.style.display = 'block';
                }
                loadTiers();
                return;
            }'''
        content = content.replace(old_show_tab, new_show_tab)
        print("✅ Added tiers case to showTab function")
    
    # ============================================
    # 3. Add sortable headers to Products table
    # ============================================
    old_products_header = '''<thead>
                            <tr>
                                <th>ID</th>
                                <th>Tên</th>
                                <th>Tier</th>
                                <th>Thời hạn</th>
                                <th>Giá</th>
                                <th>Max Devices</th>
                                <th>Trạng thái</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>'''
    new_products_header = '''<thead>
                            <tr>
                                <th onclick="sortProducts('id')" style="cursor:pointer">ID ↕</th>
                                <th onclick="sortProducts('name')" style="cursor:pointer">Tên ↕</th>
                                <th onclick="sortProducts('tier')" style="cursor:pointer">Tier ↕</th>
                                <th onclick="sortProducts('duration_days')" style="cursor:pointer">Thời hạn ↕</th>
                                <th onclick="sortProducts('price')" style="cursor:pointer">Giá ↕</th>
                                <th onclick="sortProducts('max_devices')" style="cursor:pointer">Max Devices ↕</th>
                                <th onclick="sortProducts('is_active')" style="cursor:pointer">Trạng thái ↕</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>'''
    content = content.replace(old_products_header, new_products_header)
    print("✅ Added sortable headers to Products table")
    
    # ============================================
    # 4. Add sortable headers to Licenses table  
    # ============================================
    old_licenses_header = '''<thead>
                            <tr>
                                <th>License Key</th>
                                <th>Tier</th>
                                <th>Devices</th>
                                <th>Hết hạn</th>
                                <th>Trạng thái</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>'''
    new_licenses_header = '''<thead>
                            <tr>
                                <th onclick="sortLicenses('license_key')" style="cursor:pointer">License Key ↕</th>
                                <th onclick="sortLicenses('tier')" style="cursor:pointer">Tier ↕</th>
                                <th>Devices</th>
                                <th onclick="sortLicenses('expires_at')" style="cursor:pointer">Hết hạn ↕</th>
                                <th onclick="sortLicenses('is_active')" style="cursor:pointer">Trạng thái ↕</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>'''
    content = content.replace(old_licenses_header, new_licenses_header)
    print("✅ Added sortable headers to Licenses table")
    
    # ============================================
    # 5. Add sortable headers to Orders table
    # ============================================
    old_orders_header = '''<thead>
                            <tr>
                                <th>Mã đơn</th>
                                <th>Gói</th>
                                <th>Thời hạn</th>
                                <th>Số tiền</th>
                                <th>Trạng thái</th>
                                <th>License</th>
                                <th>Ngày tạo</th>
                                <th>Ngày thanh toán</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>'''
    new_orders_header = '''<thead>
                            <tr>
                                <th onclick="sortOrders('order_id')" style="cursor:pointer">Mã đơn ↕</th>
                                <th onclick="sortOrders('tier')" style="cursor:pointer">Gói ↕</th>
                                <th onclick="sortOrders('duration_days')" style="cursor:pointer">Thời hạn ↕</th>
                                <th onclick="sortOrders('amount')" style="cursor:pointer">Số tiền ↕</th>
                                <th onclick="sortOrders('payment_status')" style="cursor:pointer">Trạng thái ↕</th>
                                <th>License</th>
                                <th onclick="sortOrders('created_at')" style="cursor:pointer">Ngày tạo ↕</th>
                                <th onclick="sortOrders('paid_at')" style="cursor:pointer">Ngày thanh toán ↕</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>'''
    content = content.replace(old_orders_header, new_orders_header)
    print("✅ Added sortable headers to Orders table")
    
    # ============================================
    # 6. Add JavaScript sort functions
    # ============================================
    sort_js = '''
<script>
// ==================== SORTING FUNCTIONS ====================
let licenseSortField = 'license_key';
let licenseSortAsc = true;
let cachedLicenses = [];

let orderSortField = 'created_at';
let orderSortAsc = false;
let cachedOrders = [];

function sortLicenses(field) {
    if (licenseSortField === field) {
        licenseSortAsc = !licenseSortAsc;
    } else {
        licenseSortField = field;
        licenseSortAsc = true;
    }
    renderLicenses();
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

// Override loadLicenses to cache data
const originalLoadLicenses = typeof loadLicenses !== 'undefined' ? loadLicenses : null;
if (originalLoadLicenses) {
    loadLicenses = async function() {
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

function renderLicenses() {
    if (!cachedLicenses.length) return;
    
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
}

console.log('✅ Sort functions loaded');
</script>
'''
    
    if 'sortLicenses' not in content:
        content = content.replace('</body>', sort_js + '\n</body>')
        print("✅ Added sort JavaScript functions")
    
    # ============================================
    # 7. Add search boxes
    # ============================================
    # Add search box for licenses
    old_license_header = '''<div class="card-header">
                <h2>Quản lý License</h2>'''
    new_license_header = '''<div class="card-header">
                <h2>Quản lý License</h2>
                <input type="text" id="license-search" placeholder="🔍 Tìm license key..." onkeyup="filterLicenses()" style="padding:8px 12px; border:1px solid #ddd; border-radius:4px; margin-right:10px;">'''
    content = content.replace(old_license_header, new_license_header)
    
    # Add filter function
    filter_js = '''
<script>
function filterLicenses() {
    const search = document.getElementById('license-search').value.toLowerCase();
    const rows = document.querySelectorAll('#licenses-table tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(search) ? '' : 'none';
    });
}

function filterProducts() {
    const search = document.getElementById('product-search')?.value.toLowerCase() || '';
    const rows = document.querySelectorAll('#products-table tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(search) ? '' : 'none';
    });
}
</script>
'''
    if 'filterLicenses' not in content:
        content = content.replace('</body>', filter_js + '\n</body>')
        print("✅ Added filter functions")
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ ALL DONE! Refresh admin dashboard.")

if __name__ == '__main__':
    fix_all()

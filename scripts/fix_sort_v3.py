#!/usr/bin/env python3
"""
Fix admin dashboard sort - use CORRECT element IDs!
- products-tbody (not products-table)
- licenses-tbody (not licenses-table)
- orders-table (correct)
"""
import re

def fix_sort():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak_v2', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Remove ALL previous fix scripts
    content = re.sub(r'<script>\s*// ==================== FIX.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script>\s*// ==================== SORT.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script>\s*let productSortField.*?console\.log.*?</script>', '', content, flags=re.DOTALL)
    
    # New comprehensive fix script
    fix_js = '''
<script>
// ==================== SORT FIX V3 - CORRECT IDs ====================
console.log('🔧 Loading sort fix v3...');

// Cache for sorting
let cachedProducts = [];
let cachedLicenses = [];
let cachedOrders = [];

// Sort states
let productSort = {field: 'id', asc: true};
let licenseSort = {field: 'id', asc: true};
let orderSort = {field: 'created_at', asc: false};

// ========== PRODUCTS SORT ==========
function sortProducts(field) {
    console.log('📦 sortProducts called:', field);
    if (productSort.field === field) {
        productSort.asc = !productSort.asc;
    } else {
        productSort.field = field;
        productSort.asc = true;
    }
    
    // Get current data from table
    const tbody = document.getElementById('products-tbody');
    if (!tbody) { console.error('products-tbody not found!'); return; }
    
    // If cachedProducts is empty, parse from current table
    if (!cachedProducts.length) {
        console.log('⚠️ Parsing products from table...');
        const rows = tbody.querySelectorAll('tr');
        cachedProducts = Array.from(rows).map(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length < 7) return null;
            return {
                id: parseInt(cells[0].textContent) || 0,
                name: cells[1].textContent || '',
                tier: cells[2].textContent.trim() || '',
                duration_days: parseInt(cells[3].textContent) || 0,
                price: parseInt(cells[4].textContent.replace(/[^0-9]/g, '')) || 0,
                max_devices: cells[5].textContent.includes('Không') ? -1 : parseInt(cells[5].textContent) || 0,
                is_active: cells[6].textContent.includes('Hoạt động'),
                _html: row.outerHTML
            };
        }).filter(p => p !== null);
    }
    
    if (!cachedProducts.length) {
        console.warn('No products to sort');
        return;
    }
    
    // Sort
    const sorted = [...cachedProducts].sort((a, b) => {
        let va = a[productSort.field];
        let vb = b[productSort.field];
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return productSort.asc ? -1 : 1;
        if (va > vb) return productSort.asc ? 1 : -1;
        return 0;
    });
    
    // Re-render using cached HTML
    tbody.innerHTML = sorted.map(p => p._html).join('');
    console.log('✅ Products sorted by', productSort.field, productSort.asc ? 'ASC' : 'DESC');
}

// ========== LICENSES SORT ==========
function sortLicenses(field) {
    console.log('🔑 sortLicenses called:', field);
    if (licenseSort.field === field) {
        licenseSort.asc = !licenseSort.asc;
    } else {
        licenseSort.field = field;
        licenseSort.asc = true;
    }
    
    const tbody = document.getElementById('licenses-tbody');
    if (!tbody) { console.error('licenses-tbody not found!'); return; }
    
    // Parse from table
    if (!cachedLicenses.length) {
        console.log('⚠️ Parsing licenses from table...');
        const rows = tbody.querySelectorAll('tr');
        cachedLicenses = Array.from(rows).map(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length < 6) return null;
            return {
                license_key: cells[0].textContent.trim() || '',
                tier: cells[1].textContent.trim() || '',
                expires_at: cells[5]?.textContent?.trim() || '',
                _html: row.outerHTML
            };
        }).filter(l => l !== null);
    }
    
    if (!cachedLicenses.length) {
        console.warn('No licenses to sort');
        return;
    }
    
    const sorted = [...cachedLicenses].sort((a, b) => {
        let va = a[licenseSort.field];
        let vb = b[licenseSort.field];
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return licenseSort.asc ? -1 : 1;
        if (va > vb) return licenseSort.asc ? 1 : -1;
        return 0;
    });
    
    tbody.innerHTML = sorted.map(l => l._html).join('');
    console.log('✅ Licenses sorted');
}

// ========== ORDERS SORT ==========
function sortOrders(field) {
    console.log('📋 sortOrders called:', field);
    if (orderSort.field === field) {
        orderSort.asc = !orderSort.asc;
    } else {
        orderSort.field = field;
        orderSort.asc = true;
    }
    
    const tbody = document.getElementById('orders-table');
    if (!tbody) { console.error('orders-table not found!'); return; }
    
    // Parse from table
    if (!cachedOrders.length) {
        console.log('⚠️ Parsing orders from table...');
        const rows = tbody.querySelectorAll('tr');
        cachedOrders = Array.from(rows).map(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length < 7) return null;
            return {
                order_id: cells[0].textContent.trim() || '',
                tier: cells[1].textContent.trim() || '',
                duration_days: parseInt(cells[2].textContent) || 0,
                amount: parseInt(cells[3].textContent.replace(/[^0-9]/g, '')) || 0,
                payment_status: cells[4].textContent.trim() || '',
                created_at: cells[6].textContent.trim() || '',
                paid_at: cells[7]?.textContent?.trim() || '',
                _html: row.outerHTML
            };
        }).filter(o => o !== null);
    }
    
    if (!cachedOrders.length) {
        console.warn('No orders to sort');
        return;
    }
    
    const sorted = [...cachedOrders].sort((a, b) => {
        let va = a[orderSort.field];
        let vb = b[orderSort.field];
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return orderSort.asc ? -1 : 1;
        if (va > vb) return orderSort.asc ? 1 : -1;
        return 0;
    });
    
    tbody.innerHTML = sorted.map(o => o._html).join('');
    console.log('✅ Orders sorted');
}

// ========== CLEAR CACHE ON TAB CHANGE ==========
const origShowTab = window.showTab;
window.showTab = function(tabName) {
    // Clear cache so it re-parses fresh data after reload
    cachedProducts = [];
    cachedLicenses = [];
    cachedOrders = [];
    if (origShowTab) origShowTab(tabName);
};

console.log('✅ Sort fix v3 loaded! Using correct element IDs.');
</script>
'''
    
    # Add before </body>
    content = content.replace('</body>', fix_js + '\n</body>')
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Sort fix v3 applied with correct element IDs!")
    print("   - products-tbody")
    print("   - licenses-tbody")  
    print("   - orders-table")

if __name__ == '__main__':
    fix_sort()

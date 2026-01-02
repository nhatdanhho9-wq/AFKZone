#!/usr/bin/env python3
"""
Fix admin dashboard features:
1. Add delete license button
2. Fix revoke to actually block client
3. Add sort to products
"""

def main():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add delete license button next to revoke button
    old_revoke = '''<button class="btn btn-danger" onclick="revokeLicense('${l.license_key}')" style="padding: 5px 10px; font-size: 12px;">Thu hồi</button>'''
    new_revoke = '''<button class="btn btn-warning" onclick="revokeLicense('${l.license_key}')" style="padding: 3px 8px; font-size: 11px;">Thu hồi</button>
                                <button class="btn btn-danger" onclick="deleteLicense('${l.license_key}')" style="padding: 3px 8px; font-size: 11px;">Xóa</button>'''
    content = content.replace(old_revoke, new_revoke)
    
    # Also fix encoded version
    old_revoke_enc = '''<button class="btn btn-danger" onclick="revokeLicense('${l.license_key}')" style="padding: 5px 10px; font-size: 12px;">Thu hß╗ôi</button>'''
    content = content.replace(old_revoke_enc, new_revoke)
    
    # 2. Add deleteLicense function
    delete_license_js = '''
        async function deleteLicense(licenseKey) {
            if (!confirm('XÓA VĨNH VIỄN license này? Hành động không thể hoàn tác!')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/licenses/${encodeURIComponent(licenseKey)}`, {
                    method: 'DELETE',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã xóa license!');
                    loadLicenses();
                } else {
                    const error = await res.json();
                    alert('Lỗi: ' + (error.detail || 'Không thể xóa license'));
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }
'''
    
    # 3. Add sort buttons to products table header
    old_products_header = '''<th>ID</th>
                        <th>Tên</th>'''
    new_products_header = '''<th style="cursor: pointer;" onclick="sortProducts('id')">ID ↕</th>
                        <th style="cursor: pointer;" onclick="sortProducts('name')">Tên ↕</th>'''
    content = content.replace(old_products_header, new_products_header)
    
    # Also fix encoded
    old_products_header_enc = '''<th>ID</th>
                        <th>T├¬n</th>'''
    content = content.replace(old_products_header_enc, new_products_header)
    
    # 4. Add sortProducts function and product sorting state
    sort_products_js = '''
        let productSortField = 'id';
        let productSortAsc = true;
        let cachedProducts = [];
        
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
            const sorted = [...cachedProducts].sort((a, b) => {
                let valA = a[productSortField];
                let valB = b[productSortField];
                if (typeof valA === 'string') valA = valA.toLowerCase();
                if (typeof valB === 'string') valB = valB.toLowerCase();
                if (valA < valB) return productSortAsc ? -1 : 1;
                if (valA > valB) return productSortAsc ? 1 : -1;
                return 0;
            });
            
            const tbody = document.getElementById('products-tbody');
            tbody.innerHTML = sorted.map(p => `
                <tr>
                    <td>${p.id}</td>
                    <td>${p.name}</td>
                    <td><span class="badge badge-${p.tier === 'pro' ? 'purple' : p.tier === 'enterprise' ? 'warning' : 'info'}">${p.tier}</span></td>
                    <td>${p.duration_days} ngày</td>
                    <td>${formatMoney(p.price)}đ</td>
                    <td>${p.max_devices === -1 ? 'Không giới hạn' : p.max_devices}</td>
                    <td><span class="badge badge-${p.is_active ? 'success' : 'danger'}">${p.is_active ? 'Hoạt động' : 'Tắt'}</span></td>
                    <td>
                        <button class="btn btn-primary" onclick="editProduct(${p.id})" style="padding: 5px 10px; font-size: 12px;">Sửa</button>
                        <button class="btn btn-${p.is_active ? 'warning' : 'success'}" onclick="${p.is_active ? 'disableProduct' : 'enableProduct'}(${p.id})" style="padding: 5px 10px; font-size: 12px;">${p.is_active ? 'Tắt' : 'Bật'}</button>
                        <button class="btn btn-danger" onclick="deleteProduct(${p.id})" style="padding: 5px 10px; font-size: 12px;">Xóa</button>
                    </td>
                </tr>
            `).join('');
        }
'''
    
    # 5. Modify loadProducts to use cachedProducts
    old_loadProducts_start = '''async function loadProducts() {
            try {
                const res = await fetch(`${API_BASE}/products`);'''
    new_loadProducts_start = '''async function loadProducts() {
            try {
                const res = await fetch(`${API_BASE}/products?include_inactive=true`);'''
    content = content.replace(old_loadProducts_start, new_loadProducts_start)
    
    # Insert JavaScript functions before closing </script>
    script_close = content.rfind('</script>')
    if script_close > 0:
        content = content[:script_close] + delete_license_js + sort_products_js + '\n    ' + content[script_close:]
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Admin dashboard updated!")
    print("Changes:")
    print("  1. Added delete license button")
    print("  2. Added sortable product columns")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Comprehensive fix for admin dashboard:
1. Fix trial_devices endpoint to show actual trial data
2. Fix license activated_at display
3. Add sort for products
"""

def main():
    # Fix app.py - trial devices endpoint
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # 1. Fix trial devices endpoint to query correct table
    old_trial = '''@app.get("/admin/trial-devices")
async def get_trial_devices(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get all trial devices"""
    try:
        result = db.execute(text("SELECT id, device_fingerprint, created_at FROM trial_devices ORDER BY created_at DESC")).fetchall()
        return [{
            "id": r[0],
            "device_fingerprint": r[1],
            "created_at": r[2].strftime('%d/%m/%Y %H:%M') if r[2] else None
        } for r in result]
    except Exception as e:
        return []'''
    
    new_trial = '''@app.get("/admin/trial-devices")
async def get_trial_devices(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get all trial devices - from trial_devices table"""
    try:
        # Query trial_devices table
        result = db.execute(text("""
            SELECT td.id, td.device_fingerprint, td.created_at,
                   l.license_key, l.expires_at
            FROM trial_devices td
            LEFT JOIN licenses l ON l.license_key LIKE 'AFK-TRIAL-%' 
                AND l.license_key IN (
                    SELECT ld.license_key FROM license_devices ld 
                    WHERE ld.device_id = td.device_fingerprint
                )
            ORDER BY td.created_at DESC
        """)).fetchall()
        
        devices = []
        for r in result:
            devices.append({
                "id": r[0],
                "device_fingerprint": r[1],
                "created_at": r[2].strftime('%d/%m/%Y %H:%M') if r[2] else None,
                "license_key": r[3] if len(r) > 3 else None,
                "expires_at": r[4].strftime('%d/%m/%Y') if len(r) > 4 and r[4] else None
            })
        
        return devices
    except Exception as e:
        print(f"Error getting trial devices: {e}")
        # Fallback - just get from trial_devices
        try:
            result = db.execute(text("SELECT id, device_fingerprint, created_at FROM trial_devices ORDER BY created_at DESC")).fetchall()
            return [{"id": r[0], "device_fingerprint": r[1], "created_at": r[2].strftime('%d/%m/%Y %H:%M') if r[2] else None} for r in result]
        except:
            return []'''
    
    if old_trial in content:
        content = content.replace(old_trial, new_trial)
        print("Fixed trial devices endpoint")
    
    # 2. Fix license list to show activated status based on device count
    # Already done in previous fix, just ensure it's correct
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    # Now fix admin_dashboard.html
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 3. Add sort buttons to products table
    old_header = '''<th>ID</th>
                        <th>Tên</th>
                        <th>Tier</th>'''
    new_header = '''<th style="cursor:pointer" onclick="sortProducts('id')">ID ↕</th>
                        <th style="cursor:pointer" onclick="sortProducts('name')">Tên ↕</th>
                        <th style="cursor:pointer" onclick="sortProducts('tier')">Tier ↕</th>'''
    
    if old_header in html:
        html = html.replace(old_header, new_header)
        print("Added sort to product headers")
    
    # 4. Fix license "Kích hoạt" column to show "Đã kích hoạt" if device_count > 0
    old_kich_hoat = '''<td>${l.activated_at || 'Chưa kích hoạt'}</td>'''
    new_kich_hoat = '''<td>${l.device_count > 0 ? (l.activated_at || 'Đã kích hoạt') : 'Chưa kích hoạt'}</td>'''
    
    if old_kich_hoat in html:
        html = html.replace(old_kich_hoat, new_kich_hoat)
        print("Fixed license activation display")
    
    # 5. Add product sort functions
    sort_js = '''
        // Product sorting
        let productSortField = 'id';
        let productSortAsc = false;
        let allProducts = [];
        
        function sortProducts(field) {
            if (productSortField === field) {
                productSortAsc = !productSortAsc;
            } else {
                productSortField = field;
                productSortAsc = true;
            }
            renderSortedProducts();
        }
        
        function renderSortedProducts() {
            const sorted = [...allProducts].sort((a, b) => {
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
    
    # Insert before closing script tag
    if 'function sortProducts' not in html:
        script_close = html.rfind('</script>')
        if script_close > 0:
            html = html[:script_close] + sort_js + '\n    ' + html[script_close:]
            print("Added product sort functions")
    
    # 6. Modify loadProducts to store products and use sort
    old_load_products = '''async function loadProducts() {
            try {
                const res = await fetch(`${API_BASE}/products?include_inactive=true`);'''
    new_load_products = '''async function loadProducts() {
            try {
                const res = await fetch(`${API_BASE}/products?include_inactive=true&_t=${Date.now()}`);'''
    
    if old_load_products in html:
        html = html.replace(old_load_products, new_load_products)
    
    # Find and update the products rendering to use allProducts
    # This is complex, let's just add a line to store products
    old_products_map = '''const products = await res.json();
                document.getElementById('products-tbody').innerHTML = products.map'''
    new_products_map = '''const products = await res.json();
                allProducts = products;  // Store for sorting
                document.getElementById('products-tbody').innerHTML = products.map'''
    
    if old_products_map in html:
        html = html.replace(old_products_map, new_products_map)
        print("Modified loadProducts to store for sorting")
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("\nAll fixes applied!")
    print("Summary:")
    print("  1. Trial devices endpoint fixed to show actual data")
    print("  2. License activation status shows 'Đã kích hoạt' if device_count > 0")
    print("  3. Product table has sortable columns (ID, Tên, Tier)")

if __name__ == "__main__":
    main()


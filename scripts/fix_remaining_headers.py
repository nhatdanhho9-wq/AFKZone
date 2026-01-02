#!/usr/bin/env python3
"""
Fix sortable headers for Products and Licenses using exact matches
"""
import re

def fix_remaining_headers():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find Products table headers - look for the pattern more flexibly
    # <th>ID</th>  -> <th onclick="sortProducts('id')" style="cursor:pointer">ID ↕</th>
    
    products_th_mapping = [
        ('<th>ID</th>', '<th onclick="sortProducts(\'id\')" style="cursor:pointer">ID ↕</th>'),
        ('<th>Tên</th>', '<th onclick="sortProducts(\'name\')" style="cursor:pointer">Tên ↕</th>'),
        ('<th>Tier</th>', '<th onclick="sortProducts(\'tier\')" style="cursor:pointer">Tier ↕</th>'),
        ('<th>Thời hạn</th>', '<th onclick="sortProducts(\'duration_days\')" style="cursor:pointer">Thời hạn ↕</th>'),
        ('<th>Giá</th>', '<th onclick="sortProducts(\'price\')" style="cursor:pointer">Giá ↕</th>'),
        ('<th>Max Devices</th>', '<th onclick="sortProducts(\'max_devices\')" style="cursor:pointer">Max Devices ↕</th>'),
        ('<th>Trạng thái</th>', '<th onclick="sortProducts(\'is_active\')" style="cursor:pointer">Trạng thái ↕</th>'),
    ]
    
    for old, new in products_th_mapping:
        if old in content and 'sortProducts' not in content.split(old)[0][-100:]:  # Not already replaced nearby
            content = content.replace(old, new, 1)  # Only first occurrence
    
    print("✅ Updated Products headers")
    
    # Find Licenses table headers
    licenses_th_mapping = [
        ('<th>License Key</th>', '<th onclick="sortLicenses(\'license_key\')" style="cursor:pointer">License Key ↕</th>'),
        ('<th>Hết hạn</th>', '<th onclick="sortLicenses(\'expires_at\')" style="cursor:pointer">Hết hạn ↕</th>'),
    ]
    
    for old, new in licenses_th_mapping:
        if old in content:
            content = content.replace(old, new, 1)
    
    print("✅ Updated Licenses headers")
    
    # Add Products search box if not exists
    if 'product-search' not in content:
        old_products_card = '<h2>Quản lý Sản phẩm</h2>'
        new_products_card = '''<h2>Quản lý Sản phẩm</h2>
                <input type="text" id="product-search" placeholder="🔍 Tìm kiếm..." onkeyup="filterProducts()" style="padding:8px 12px; border:1px solid #ddd; border-radius:4px; margin-right:10px;">'''
        content = content.replace(old_products_card, new_products_card)
        print("✅ Added Products search box")
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ DONE!")

if __name__ == '__main__':
    fix_remaining_headers()

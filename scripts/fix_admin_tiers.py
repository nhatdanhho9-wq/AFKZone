#!/usr/bin/env python3
"""
Fix admin dashboard:
1. Add test1, test2 tiers to dropdowns
2. Make sure buttons work
"""

import re

def fix_admin_dashboard():
    # Read file
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 1. Add test1, test2 to product-tier dropdown
    old_product_tier = '''<select id="product-tier">
                        <option value="basic">Basic</option>
                        <option value="pro">Pro</option>
                        <option value="enterprise">Enterprise</option>
                    </select>'''
    
    new_product_tier = '''<select id="product-tier">
                        <option value="basic">Basic</option>
                        <option value="pro">Pro</option>
                        <option value="enterprise">Enterprise</option>
                        <option value="test1">Test Tier 1</option>
                        <option value="test2">Test Tier 2</option>
                    </select>'''
    
    content = content.replace(old_product_tier, new_product_tier)
    print("✅ Added test1, test2 to product-tier dropdown")
    
    # 2. Add test1, test2 to license-tier dropdown if exists
    old_license_tier = '''<select id="license-tier">
                        <option value="basic">Basic</option>
                        <option value="pro">Pro</option>
                        <option value="enterprise">Enterprise</option>
                    </select>'''
    
    new_license_tier = '''<select id="license-tier">
                        <option value="basic">Basic</option>
                        <option value="pro">Pro</option>
                        <option value="enterprise">Enterprise</option>
                        <option value="test1">Test Tier 1</option>
                        <option value="test2">Test Tier 2</option>
                    </select>'''
    
    if old_license_tier in content:
        content = content.replace(old_license_tier, new_license_tier)
        print("✅ Added test1, test2 to license-tier dropdown")
    else:
        print("⚠️ license-tier dropdown not found with expected format")
    
    # 3. Check toggleProduct function exists
    if 'toggleProduct' in content:
        print("✅ toggleProduct function exists")
    else:
        print("⚠️ toggleProduct function not found")
    
    # 4. Check deleteProduct function exists
    if 'deleteProduct' in content:
        print("✅ deleteProduct function exists")
    else:
        print("⚠️ deleteProduct function not found")
    
    # Save
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ DONE! Refresh admin dashboard to see changes.")

if __name__ == '__main__':
    fix_admin_dashboard()

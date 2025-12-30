#!/usr/bin/env python3
"""Fix admin dashboard to use new endpoints and fix status display"""

def main():
    print("Fixing admin dashboard...")
    
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Fix loadLicenses to use /admin/licenses/all
    old_licenses = "const res = await fetch(`${API_BASE}/admin/licenses?limit=100`,"
    new_licenses = "const res = await fetch(`${API_BASE}/admin/licenses/all`,"
    content = content.replace(old_licenses, new_licenses)
    
    # 2. Fix loadDevices to use /admin/devices/detailed
    old_devices = "const res = await fetch(`${API_BASE}/admin/users?limit=100`,"
    new_devices = "const res = await fetch(`${API_BASE}/admin/devices/detailed`,"
    content = content.replace(old_devices, new_devices)
    
    # 3. Fix devices data parsing
    old_users = "const users = data.users || [];"
    new_users = "const users = data.devices || data.users || [];"
    content = content.replace(old_users, new_users)
    
    # 4. Fix status check - use status from API directly
    old_revoked = "const isRevoked = l.is_revoked || false;"
    new_revoked = "const isRevoked = l.status === 'revoked';"
    content = content.replace(old_revoked, new_revoked)
    
    # 5. Add device_count and source columns to license table
    old_license_row = '''<td>${l.max_devices === -1 ? 'Không giới hạn' : (l.max_devices || 'N/A')}</td>'''
    new_license_row = '''<td>${l.max_devices === -1 ? 'Không giới hạn' : (l.max_devices || 'N/A')} <small>(${l.device_count || 0} đang dùng)</small></td>'''
    content = content.replace(old_license_row, new_license_row)
    
    # Also fix encoded version
    old_license_row_enc = '''<td>${l.max_devices === -1 ? 'Kh├┤ng giß╗¢i hß║ín' : (l.max_devices || 'N/A')}</td>'''
    new_license_row_enc = '''<td>${l.max_devices === -1 ? 'Không giới hạn' : (l.max_devices || 'N/A')} <small>(${l.device_count || 0} đang dùng)</small></td>'''
    content = content.replace(old_license_row_enc, new_license_row_enc)
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Admin dashboard fixed!")
    print("Changes made:")
    print("  1. loadLicenses now uses /admin/licenses/all")
    print("  2. loadDevices now uses /admin/devices/detailed")
    print("  3. Fixed status check for revoked licenses")
    print("  4. Added device count to max_devices column")

if __name__ == "__main__":
    main()


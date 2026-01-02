#!/usr/bin/env python3
"""Fix expires_at display in admin dashboard"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix expires_at parsing - API already returns formatted string
    old_parsing = '''let expiresAt = 'Chưa kích hoạt';
                    let activatedAt = 'Chưa kích hoạt';
                    
                    if (l.expires_at) {
                        if (typeof l.expires_at === 'number') {
                            expiresAt = new Date(l.expires_at).toLocaleString('vi-VN');
                        } else {
                            expiresAt = new Date(l.expires_at).toLocaleString('vi-VN');
                        }
                    }'''
    
    new_parsing = '''let expiresAt = 'Chưa kích hoạt';
                    let activatedAt = 'Chưa kích hoạt';
                    
                    // API already returns formatted date string: "HH:MM:SS DD/MM/YYYY" or "DD/MM/YYYY"
                    if (l.expires_at) {
                        expiresAt = l.expires_at;
                    } else {
                        expiresAt = 'Chưa kích hoạt';
                    }'''
    
    if old_parsing in content:
        content = content.replace(old_parsing, new_parsing)
        print("Fixed expires_at parsing")
    
    # Also fix isExpired check - don't parse if already string
    old_expired_check = '''const isExpired = l.expires_at && (typeof l.expires_at === 'number' ? l.expires_at < Date.now() : new Date(l.expires_at) < new Date());'''
    
    new_expired_check = '''// Check if expired - API returns formatted string, so check status field instead
                    const isExpired = l.status === 'expired';'''
    
    if old_expired_check in content:
        content = content.replace(old_expired_check, new_expired_check)
        print("Fixed isExpired check")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()


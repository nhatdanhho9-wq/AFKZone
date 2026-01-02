#!/usr/bin/env python3
"""Fix date parsing in admin dashboard frontend"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix date parsing for activated_at
    old_parsing = '''// Check if license is activated
                    if (l.device_count > 0 || l.activated_at) {
                        if (l.activated_at) {
                            if (typeof l.activated_at === 'number') {
                                activatedAt = new Date(l.activated_at).toLocaleString('vi-VN');
                            } else {
                                activatedAt = new Date(l.activated_at).toLocaleString('vi-VN');
                            }
                        } else {
                            // If device_count > 0 but no activated_at, show "Đã kích hoạt"
                            activatedAt = 'Đã kích hoạt';
                        }
                    } else {
                        activatedAt = 'Chưa kích hoạt';
                    }'''
    
    new_parsing = '''// Check if license is activated
                    if (l.device_count > 0 || l.activated_at) {
                        if (l.activated_at) {
                            // API already returns formatted date string: "HH:MM:SS DD/MM/YYYY"
                            activatedAt = l.activated_at;
                        } else {
                            // If device_count > 0 but no activated_at, show "Đã kích hoạt"
                            activatedAt = 'Đã kích hoạt';
                        }
                    } else {
                        activatedAt = 'Chưa kích hoạt';
                    }'''
    
    if old_parsing in content:
        content = content.replace(old_parsing, new_parsing)
        print("Fixed date parsing for activated_at")
    else:
        print("Pattern not found, trying alternative...")
        # Try simpler fix
        if 'activatedAt = new Date(l.activated_at)' in content:
            # Just use the string as-is if it's already formatted
            content = content.replace(
                'activatedAt = new Date(l.activated_at).toLocaleString(\'vi-VN\');',
                'activatedAt = l.activated_at; // Already formatted by API'
            )
            print("Applied simpler fix")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()


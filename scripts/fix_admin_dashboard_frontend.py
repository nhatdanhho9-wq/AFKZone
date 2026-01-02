#!/usr/bin/env python3
"""Fix admin dashboard frontend:
1. Fix activation display - show "Đã kích hoạt" if device_count > 0 or activated_at
2. Improve device info display
"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix activation display logic
    old_activation = '''if (l.activated_at) {
                        if (typeof l.activated_at === 'number') {
                            activatedAt = new Date(l.activated_at).toLocaleString('vi-VN');
                        } else {
                            activatedAt = new Date(l.activated_at).toLocaleString('vi-VN');
                        }
                    }'''
    
    new_activation = '''// Check if license is activated
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
    
    if old_activation in content:
        content = content.replace(old_activation, new_activation)
        print("Fixed activation display logic")
    
    # Fix device info display - show tier from license
    old_device_display = '''<td>${d.device_id || 'N/A'}</td>
                            <td>${d.model || 'N/A'}</td>
                            <td>${d.app_version || 'N/A'}</td>
                            <td><code>${d.license_key || 'N/A'}</code></td>
                            <td>${d.tier || 'N/A'}</td>
                            <td>${d.last_seen || 'N/A'}</td>'''
    
    # Check if this pattern exists
    if 'd.model ||' in content:
        # Update to show tier from license
        content = content.replace(
            '<td>${d.tier || \'N/A\'}</td>',
            '<td><span class="badge badge-info">${d.tier || \'N/A\'}</span></td>'
        )
        print("Fixed device tier display")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()


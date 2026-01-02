#!/usr/bin/env python3
"""Fix device display in admin dashboard"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix device mapping
    old_display = '''tbody.innerHTML = users.map(u => `
                    <tr>
                        <td><code>${u.device_id || 'N/A'}</code></td>
                        <td>${u.device_model || 'N/A'}</td>
                        <td>${u.app_version || 'N/A'}</td>
                        <td><code>${u.license_key || 'N/A'}</code></td>
                        <td>${u.license_tier || 'N/A'}</td>
                        <td>${u.last_seen ? new Date(u.last_seen).toLocaleString('vi-VN') : 'N/A'}</td>
                        <td>
                            <button class="btn btn-danger" onclick="removeDevice('${u.device_id}')" style="padding: 5px 10px; font-size: 12px;">Xóa</button>
                        </td>
                    </tr>
                `).join('');'''
    
    new_display = '''tbody.innerHTML = users.map(u => `
                    <tr>
                        <td><code>${u.device_id || 'N/A'}</code></td>
                        <td>${u.model || 'N/A'}</td>
                        <td>${u.app_version || 'N/A'}</td>
                        <td><code>${u.license_key || 'N/A'}</code></td>
                        <td><span class="badge badge-info">${u.tier || 'N/A'}</span></td>
                        <td>${u.activated_at || 'N/A'}</td>
                        <td>
                            <button class="btn btn-danger" onclick="removeDevice('${u.device_id}')" style="padding: 5px 10px; font-size: 12px;">Xóa</button>
                        </td>
                    </tr>
                `).join('');'''
    
    if old_display in content:
        content = content.replace(old_display, new_display)
        print("Fixed device display mapping")
    else:
        print("Pattern not found, trying alternative...")
        # Try individual replacements
        if 'u.license_tier' in content:
            content = content.replace('u.license_tier', 'u.tier')
            print("Fixed tier field")
        if 'u.device_model' in content:
            content = content.replace('u.device_model', 'u.model')
            print("Fixed model field")
        if 'u.last_seen' in content and 'new Date(u.last_seen)' in content:
            content = content.replace(
                '${u.last_seen ? new Date(u.last_seen).toLocaleString(\'vi-VN\') : \'N/A\'}',
                '${u.activated_at || \'N/A\'}'
            )
            print("Fixed last_seen to activated_at")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()


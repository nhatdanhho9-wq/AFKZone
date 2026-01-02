#!/usr/bin/env python3
"""Add unrevoke button to admin dashboard"""

def main():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add unrevoke function
    unrevoke_js = '''
        async function unrevokeLicense(licenseKey) {
            if (!confirm('Khôi phục license này? Client sẽ có thể sử dụng lại.')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/licenses/${encodeURIComponent(licenseKey)}/unrevoke`, {
                    method: 'POST',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã khôi phục license!');
                    loadLicenses();
                } else {
                    const error = await res.json();
                    alert('Lỗi: ' + (error.detail || 'Không thể khôi phục license'));
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }
'''
    
    # Update the license row to show different buttons based on status
    old_buttons = '''<button class="btn btn-warning" onclick="revokeLicense('${l.license_key}')" style="padding: 3px 8px; font-size: 11px;">Thu hồi</button>
                                <button class="btn btn-danger" onclick="deleteLicense('${l.license_key}')" style="padding: 3px 8px; font-size: 11px;">Xóa</button>'''
    
    new_buttons = '''${l.status === 'revoked' ? 
                                    `<button class="btn btn-success" onclick="unrevokeLicense('${l.license_key}')" style="padding: 3px 8px; font-size: 11px;">Khôi phục</button>` :
                                    `<button class="btn btn-warning" onclick="revokeLicense('${l.license_key}')" style="padding: 3px 8px; font-size: 11px;">Thu hồi</button>`
                                }
                                <button class="btn btn-danger" onclick="deleteLicense('${l.license_key}')" style="padding: 3px 8px; font-size: 11px;">Xóa</button>'''
    
    content = content.replace(old_buttons, new_buttons)
    
    # Insert unrevoke JS
    script_close = content.rfind('</script>')
    if script_close > 0:
        content = content[:script_close] + unrevoke_js + '\n    ' + content[script_close:]
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Added unrevoke button!")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""Fix revokeLicense function to use correct endpoint"""

def main():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and fix revokeLicense function
    old_revoke = '''async function revokeLicense(licenseKey) {
            if (!confirm('Thu hồi license này?')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/licenses/${encodeURIComponent(licenseKey)}/revoke`, {
                    method: 'POST',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã thu hồi license!');
                    loadLicenses();
                } else {
                    const error = await res.json();
                    alert('Lỗi: ' + (error.detail || 'Không thể thu hồi license'));
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }'''
    
    # Check if it exists, if not try to find the encoded version
    if old_revoke not in content:
        # Try to find any revokeLicense function and replace it
        import re
        pattern = r'async function revokeLicense\(licenseKey\) \{[^}]+\}'
        
        new_revoke = '''async function revokeLicense(licenseKey) {
            if (!confirm('Thu hồi license này? Client sẽ không thể sử dụng license này nữa.')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/licenses/${encodeURIComponent(licenseKey)}/revoke`, {
                    method: 'POST',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã thu hồi license! Client sẽ bị chặn khi check license lần tới.');
                    loadLicenses();
                } else {
                    const error = await res.json();
                    alert('Lỗi: ' + (error.detail || 'Không thể thu hồi license'));
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }'''
        
        # Simple string replacement for common patterns
        old_patterns = [
            "async function revokeLicense(licenseKey)",
            "async function revokeLicense(licenseKey) {"
        ]
        
        for p in old_patterns:
            if p in content:
                # Find the full function
                start = content.find(p)
                if start > 0:
                    # Find matching closing brace
                    brace_count = 0
                    end = start
                    found_first = False
                    for i, c in enumerate(content[start:]):
                        if c == '{':
                            brace_count += 1
                            found_first = True
                        elif c == '}':
                            brace_count -= 1
                            if found_first and brace_count == 0:
                                end = start + i + 1
                                break
                    
                    old_func = content[start:end]
                    content = content.replace(old_func, new_revoke)
                    print(f"Replaced revokeLicense function")
                    break
    else:
        content = content.replace(old_revoke, old_revoke)  # No change needed
        print("revokeLicense function already correct")
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()


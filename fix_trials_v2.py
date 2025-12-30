#!/usr/bin/env python3
"""Fix trials display"""

def main():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find loadTrials function and fix it
    import re
    
    # Pattern to find the loadTrials function
    pattern = r'async function loadTrials\(\) \{[^}]+(?:\{[^}]*\}[^}]*)*\}'
    
    new_func = '''async function loadTrials() {
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                const data = await res.json();
                const devices = data.devices || data || [];
                const tbody = document.getElementById('trials-tbody');
                
                if (!devices || devices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #999;">Không có trial device nào</td></tr>';
                    return;
                }
                
                tbody.innerHTML = devices.map(d => `
                    <tr>
                        <td>${d.id}</td>
                        <td style="font-family: monospace; font-size: 11px;">${d.device_fingerprint || 'N/A'}</td>
                        <td style="font-family: monospace; font-size: 11px; color: #007bff;">${d.license_key || 'N/A'}</td>
                        <td>${d.created_at || 'N/A'}</td>
                        <td><button class="btn btn-danger" onclick="removeTrial(${d.id})" style="padding: 5px 10px; font-size: 12px;">Xóa</button></td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Error loading trials:', e);
                document.getElementById('trials-tbody').innerHTML = `<tr><td colspan="5" style="text-align: center; color: red;">Lỗi: ${e.message}</td></tr>`;
            }
        }'''
    
    # Simple replacement - find start and end
    start_marker = 'async function loadTrials()'
    start_idx = html.find(start_marker)
    
    if start_idx > 0:
        # Find the end of the function by counting braces
        brace_count = 0
        end_idx = start_idx
        found_first = False
        
        for i, c in enumerate(html[start_idx:]):
            if c == '{':
                brace_count += 1
                found_first = True
            elif c == '}':
                brace_count -= 1
                if found_first and brace_count == 0:
                    end_idx = start_idx + i + 1
                    break
        
        old_func = html[start_idx:end_idx]
        html = html.replace(old_func, new_func)
        print("Replaced loadTrials function")
    else:
        print("loadTrials function not found!")
    
    # Also update the table header for trials
    old_header = '''<thead>
                    <tr>
                        <th>ID</th>
                        <th>Device Fingerprint</th>
                        <th>IP Address</th>
                        <th>License Key</th>
                        <th>Created At</th>
                        <th>Thao tác</th>
                    </tr>
                </thead>'''
    
    new_header = '''<thead>
                    <tr>
                        <th>ID</th>
                        <th>Device Fingerprint</th>
                        <th>License Key</th>
                        <th>Created At</th>
                        <th>Thao tác</th>
                    </tr>
                </thead>'''
    
    if old_header in html:
        html = html.replace(old_header, new_header)
        print("Updated table header")
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Done!")

if __name__ == "__main__":
    main()


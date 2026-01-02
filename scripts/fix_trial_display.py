#!/usr/bin/env python3
"""Fix trial devices display in admin dashboard"""

def main():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find and fix loadTrialDevices function
    old_load = '''async function loadTrialDevices() {
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                const devices = await res.json();
                
                if (devices.length === 0) {
                    document.getElementById('trial-devices-tbody').innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px; color: #666;">Không có thiết bị dùng thử</td></tr>';
                    return;
                }
                
                document.getElementById('trial-devices-tbody').innerHTML = devices.map(d => `
                    <tr>
                        <td>${d.id}</td>
                        <td style="font-family: monospace; font-size: 12px;">${d.device_fingerprint}</td>
                        <td>${d.created_at || 'N/A'}</td>
                        <td>
                            <button class="btn btn-danger" onclick="removeTrialDevice(${d.id})" style="padding: 5px 10px; font-size: 12px;">Xóa</button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Error loading trial devices:', e);
                document.getElementById('trial-devices-tbody').innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px; color: red;">Lỗi tải dữ liệu</td></tr>';
            }
        }'''
    
    new_load = '''async function loadTrialDevices() {
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                const data = await res.json();
                const devices = data.devices || data || [];
                
                if (devices.length === 0) {
                    document.getElementById('trial-devices-tbody').innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px; color: #666;">Không có thiết bị dùng thử</td></tr>';
                    return;
                }
                
                document.getElementById('trial-devices-tbody').innerHTML = devices.map(d => `
                    <tr>
                        <td>${d.id}</td>
                        <td style="font-family: monospace; font-size: 11px;">${d.device_fingerprint}</td>
                        <td style="font-family: monospace; font-size: 11px; color: #007bff;">${d.license_key || 'N/A'}</td>
                        <td>${d.created_at || 'N/A'}</td>
                        <td>
                            <button class="btn btn-danger" onclick="removeTrialDevice(${d.id})" style="padding: 5px 10px; font-size: 12px;">Xóa</button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Error loading trial devices:', e);
                document.getElementById('trial-devices-tbody').innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px; color: red;">Lỗi tải dữ liệu</td></tr>';
            }
        }'''
    
    if old_load in html:
        html = html.replace(old_load, new_load)
        print("Fixed loadTrialDevices function")
    else:
        print("loadTrialDevices function not found, trying alternative fix")
    
    # Also fix the trial devices table header
    old_header = '''<th>ID</th>
                            <th>Device Fingerprint</th>
                            <th>Created At</th>
                            <th>Thao tác</th>'''
    new_header = '''<th>ID</th>
                            <th>Device Fingerprint</th>
                            <th>License Key</th>
                            <th>Created At</th>
                            <th>Thao tác</th>'''
    
    if old_header in html:
        html = html.replace(old_header, new_header)
        print("Fixed trial devices table header")
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Done!")

if __name__ == "__main__":
    main()


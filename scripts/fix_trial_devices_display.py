#!/usr/bin/env python3
"""Fix trial devices display in admin dashboard"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix 1: Add IP Address column and fix colspan
    old_display = '''if (!devices || devices.length === 0) {
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
                `).join('');'''
    
    new_display = '''if (!devices || devices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #999;">Không có trial device nào</td></tr>';
                    return;
                }
                
                tbody.innerHTML = devices.map(d => `
                    <tr>
                        <td>${d.id || 'N/A'}</td>
                        <td style="font-family: monospace; font-size: 11px;">${d.device_fingerprint || 'N/A'}</td>
                        <td>${d.ip_address || 'N/A'}</td>
                        <td style="font-family: monospace; font-size: 11px; color: #007bff;">${d.license_key || 'N/A'}</td>
                        <td>${d.created_at || 'N/A'}</td>
                        <td><button class="btn btn-danger" onclick="removeTrialDevice(${d.id})" style="padding: 5px 10px; font-size: 12px;">Xóa</button></td>
                    </tr>
                `).join('');'''
    
    if old_display in content:
        content = content.replace(old_display, new_display)
        print("Fixed trial devices display")
    
    # Fix 2: Rename function from deleteTrial to removeTrialDevice for consistency
    if 'async function deleteTrial' in content:
        content = content.replace('async function deleteTrial(', 'async function removeTrialDevice(')
        print("Renamed deleteTrial to removeTrialDevice")
    
    # Fix 3: Also check error message colspan
    old_error = '<tr><td colspan="5" style="text-align: center; color: red;">Lỗi:'
    new_error = '<tr><td colspan="6" style="text-align: center; color: red;">Lỗi:'
    if old_error in content:
        content = content.replace(old_error, new_error)
        print("Fixed error message colspan")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()


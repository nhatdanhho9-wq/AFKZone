#!/usr/bin/env python3
"""Final fix for trial devices display"""

def main():
    with open('/app/admin_dashboard.html', 'r') as f:
        content = f.read()
    
    # Fix loadTrials to have better error handling and ensure it works
    old_function = '''async function loadTrials() {
            console.log('Loading trial devices...');
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                console.log('Trial devices response status:', res.status);
                const data = await res.json();
                console.log('Trial devices data:', data);
                const devices = data.devices || data || [];
                console.log('Trial devices count:', devices.length);
                const tbody = document.getElementById('trials-tbody');
                
                if (!devices || devices.length === 0) {
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
                `).join('');
            } catch (e) {
                console.error('Error loading trials:', e);
                document.getElementById('trials-tbody').innerHTML = `<tr><td colspan="6" style="text-align: center; color: red;">Lỗi: ${e.message}</td></tr>`;
            }
        }'''
    
    new_function = '''async function loadTrials() {
            console.log('🔄 Loading trial devices...');
            const tbody = document.getElementById('trials-tbody');
            if (!tbody) {
                console.error('❌ trials-tbody not found!');
                return;
            }
            
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Đang tải...</td></tr>';
            
            try {
                if (!authToken) {
                    throw new Error('Chưa đăng nhập');
                }
                
                console.log('📡 Calling API:', `${API_BASE}/admin/trial-devices`);
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                
                console.log('📥 Response status:', res.status);
                
                if (!res.ok) {
                    const errorText = await res.text();
                    throw new Error(`HTTP ${res.status}: ${errorText}`);
                }
                
                const data = await res.json();
                console.log('✅ Response data:', data);
                
                const devices = data.devices || data || [];
                console.log('📊 Trial devices count:', devices.length);
                
                if (!devices || devices.length === 0) {
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
                `).join('');
                
                console.log('✅ Trial devices loaded successfully!');
            } catch (e) {
                console.error('❌ Error loading trials:', e);
                const errorMsg = e.message || 'Unknown error';
                if (tbody) {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: red; padding: 20px;">Lỗi: ${errorMsg}<br><small>Mở Console (F12) để xem chi tiết</small></td></tr>`;
                }
            }
        }'''
    
    if old_function in content:
        content = content.replace(old_function, new_function)
        print("Updated loadTrials with better error handling")
    else:
        # Try to find and replace just the function body
        if 'async function loadTrials()' in content:
            # Find the function and replace
            import re
            pattern = r'async function loadTrials\(\) \{.*?\n        \}'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, new_function, content, flags=re.DOTALL)
                print("Replaced loadTrials function using regex")
            else:
                print("Could not find loadTrials function to replace")
    
    with open('/app/admin_dashboard.html', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()


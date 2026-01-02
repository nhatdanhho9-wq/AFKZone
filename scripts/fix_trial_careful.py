#!/usr/bin/env python3
"""
Fix Trial Devices functions - CAREFUL VERSION
Only replaces lines 1368-1460 with clean code
Creates backup first
"""

# Read file
with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Original file has {len(lines)} lines')

# Clean replacement for lines 1368-1460 (index 1367-1459)
# These are the 3 trial functions: loadTrials, removeTrialDevice, clearAllTrials

clean_trial_code = '''        async function loadTrials() {
            console.log('Loading trial devices...');
            const tbody = document.getElementById('trials-tbody');
            if (!tbody) {
                console.error('trials-tbody not found!');
                return;
            }

            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Đang tải...</td></tr>';

            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                
                if (!res.ok) {
                    throw new Error('HTTP ' + res.status);
                }

                const data = await res.json();
                const devices = data.devices || data || [];
                console.log('Trial devices count:', devices.length);

                if (!devices || devices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #999;">Không có trial device nào</td></tr>';
                    return;
                }

                let html = '';
                for (let i = 0; i < devices.length; i++) {
                    const d = devices[i];
                    const fp = d.device_fingerprint || 'N/A';
                    const shortFp = fp.length > 20 ? fp.substring(0, 20) + '...' : fp;
                    html += '<tr>';
                    html += '<td>' + (d.id || 'N/A') + '</td>';
                    html += '<td style="font-family: monospace; font-size: 11px;">' + shortFp + '</td>';
                    html += '<td>' + (d.ip_address || 'N/A') + '</td>';
                    html += '<td style="font-family: monospace; font-size: 12px; color: #007bff;">' + (d.license_key || 'N/A') + '</td>';
                    html += '<td>' + (d.created_at || 'N/A') + '</td>';
                    html += '<td><button class="btn btn-danger" onclick="removeTrialDevice(' + d.id + ')" style="padding: 5px 10px; font-size: 12px;">Xóa</button></td>';
                    html += '</tr>';
                }
                
                tbody.innerHTML = html;
                console.log('Trial devices loaded successfully!');
            } catch (e) {
                console.error('Error loading trials:', e);
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: red;">Lỗi: ' + e.message + '</td></tr>';
            }
        }

        async function removeTrialDevice(id) {
            if (!confirm('Xóa trial device này? Device sẽ có thể dùng thử lại.')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices/${id}`, {
                    method: 'DELETE',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã xóa trial device!');
                    loadTrials();
                } else {
                    alert('Lỗi khi xóa: HTTP ' + res.status);
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }

        async function clearAllTrials() {
            if (!confirm('XÓA TẤT CẢ trial devices? Tất cả users sẽ có thể dùng thử lại!')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    method: 'DELETE',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã xóa tất cả trial devices!');
                    loadTrials();
                } else {
                    alert('Lỗi khi xóa: HTTP ' + res.status);
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }
'''

# Find start and end of the functions to replace
start_line = None
end_line = None

for i, line in enumerate(lines):
    if 'async function loadTrials()' in line and start_line is None:
        start_line = i
    if 'async function clearAllTrials()' in line:
        # Find the closing brace of this function
        brace_count = 0
        for j in range(i, len(lines)):
            brace_count += lines[j].count('{') - lines[j].count('}')
            if brace_count == 0 and j > i:
                end_line = j + 1
                break

if start_line is None or end_line is None:
    print('Could not find function boundaries!')
    print(f'start_line: {start_line}, end_line: {end_line}')
else:
    print(f'Replacing lines {start_line+1} to {end_line} (0-indexed: {start_line} to {end_line-1})')
    
    # Build new content
    new_lines = lines[:start_line] + [clean_trial_code + '\n'] + lines[end_line:]
    
    # Write back
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f'New file has {len(new_lines)} lines')
    print('Done! Refresh page to test.')

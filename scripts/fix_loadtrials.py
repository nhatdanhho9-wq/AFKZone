#!/usr/bin/env python3
"""
Fix Trial Devices Tab - NUCLEAR OPTION
Vấn đề: Code bị lẫn lộn trên cùng dòng, không thể repair
Giải pháp: Xóa toàn bộ từ "async function loadTrials" đến cuối, viết lại hoàn toàn
"""

import re

def fix_admin_dashboard():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Tìm vị trí bắt đầu của loadTrials
    match = re.search(r'\n        async function loadTrials\(\)', content)
    
    if not match:
        print('❌ Không tìm thấy loadTrials function')
        return
    
    start_pos = match.start()
    
    # Tìm </script> đầu tiên sau vị trí này
    script_end_match = re.search(r'\n    </script>', content[start_pos:])
    if script_end_match:
        script_end_pos = start_pos + script_end_match.start()
    else:
        print('❌ Không tìm thấy </script>')
        return
    
    # Code mới hoàn chỉnh - clean
    new_code = '''
        async function loadTrials() {
            console.log('🔄 Loading trial devices...');

            const tbody = document.getElementById('trials-tbody');
            if (!tbody) {
                console.error('❌ trials-tbody not found!');
                return;
            }

            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Đang tải...</td></tr>';

            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });

                console.log('📥 Response status:', res.status);

                if (!res.ok) {
                    throw new Error('HTTP ' + res.status);
                }

                const data = await res.json();
                console.log('✅ Response data:', data);

                const devices = data.devices || data || [];
                console.log('📊 Trial devices count:', devices.length);

                if (!devices || devices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #999;">Không có trial device nào</td></tr>';
                    return;
                }

                let html = '';
                for (let i = 0; i < devices.length; i++) {
                    const d = devices[i];
                    console.log('🔄 Rendering device:', d);
                    const fingerprint = d.device_fingerprint || 'N/A';
                    const shortFingerprint = fingerprint.length > 20 ? fingerprint.substring(0, 20) + '...' : fingerprint;
                    
                    html += '<tr>';
                    html += '<td>' + (d.id || 'N/A') + '</td>';
                    html += '<td style="font-family: monospace; font-size: 11px;">' + shortFingerprint + '</td>';
                    html += '<td>' + (d.ip_address || 'N/A') + '</td>';
                    html += '<td style="font-family: monospace; font-size: 12px; color: #007bff;">' + (d.license_key || 'N/A') + '</td>';
                    html += '<td>' + (d.created_at || 'N/A') + '</td>';
                    html += '<td><button class="btn btn-danger" onclick="removeTrialDevice(' + d.id + ')" style="padding: 5px 10px; font-size: 12px;">Xóa</button></td>';
                    html += '</tr>';
                }

                console.log('📝 Generated HTML length:', html.length);
                tbody.innerHTML = html;
                console.log('✅ Trial devices loaded successfully!');

            } catch (e) {
                console.error('❌ Error loading trials:', e);
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: red;">Lỗi: ' + e.message + '</td></tr>';
            }
        }

        async function removeTrialDevice(id) {
            if (!confirm('Xóa trial device này? Device sẽ có thể dùng thử lại.')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices/` + id, {
                    method: 'DELETE',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã xóa trial device!');
                    loadTrials();
                } else {
                    alert('Lỗi khi xóa: ' + res.status);
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
                    alert('Lỗi khi xóa: ' + res.status);
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }
'''
    
    # Ghép lại file
    new_content = content[:start_pos] + new_code + '\n    </script>' + content[script_end_pos + len('\n    </script>'):]
    
    # backup
    with open('/app/admin_dashboard.html.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Verify
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        verify_content = f.read()
    
    line_count = verify_content.count('\n')
    
    print(f'✅ File đã được fix! Số dòng mới: {line_count}')
    print('🔄 Vui lòng refresh trang admin (Ctrl+F5) để xem kết quả')

if __name__ == '__main__':
    fix_admin_dashboard()

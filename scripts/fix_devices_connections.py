#!/usr/bin/env python3
"""
Fix loadDevices and loadConnections functions
"""

import re

def fix_functions():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # New clean loadDevices function
    new_loadDevices = '''        async function loadDevices() {
            try {
                const res = await fetch(`${API_BASE}/admin/users?limit=100`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                const data = await res.json();
                const users = data.users || [];
                const tbody = document.getElementById('devices-tbody');

                if (users.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #999;">Không có thiết bị nào</td></tr>';
                    return;
                }

                tbody.innerHTML = users.map(u => `
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
                `).join('');
            } catch (e) {
                console.error('Error loading devices:', e);
                document.getElementById('devices-tbody').innerHTML = '<tr><td colspan="7" style="text-align: center; color: red; padding: 20px;">Lỗi: ' + e.message + '</td></tr>';
            }
        }'''

    # New clean loadConnections function  
    new_loadConnections = '''        async function loadConnections() {
            try {
                const res = await fetch(`${API_BASE}/admin/connections?limit=100`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                const data = await res.json();
                const connections = data.connections || [];
                const tbody = document.getElementById('connections-tbody');

                if (connections.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px; color: #999;">Không có kết nối nào</td></tr>';
                    return;
                }

                tbody.innerHTML = connections.map(c => `
                    <tr>
                        <td><code>${c.device_id || 'N/A'}</code></td>
                        <td><code>${c.peer_id || 'N/A'}</code></td>
                        <td>${c.connection_type || 'N/A'}</td>
                        <td>${c.ip_address || 'N/A'}</td>
                        <td>${c.connected_at ? new Date(c.connected_at).toLocaleString('vi-VN') : 'N/A'}</td>
                        <td>${c.disconnected_at ? new Date(c.disconnected_at).toLocaleString('vi-VN') : 'Đang kết nối'}</td>
                        <td>${c.duration_seconds ? formatDuration(c.duration_seconds) : 'N/A'}</td>
                        <td><code>${c.license_key || 'N/A'}</code></td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Error loading connections:', e);
                document.getElementById('connections-tbody').innerHTML = '<tr><td colspan="8" style="text-align: center; color: red; padding: 20px;">Lỗi: ' + e.message + '</td></tr>';
            }
        }'''

    # Find and replace loadDevices
    start_match = re.search(r'\n        async function loadDevices\(\)', content)
    if start_match:
        start = start_match.start()
        # Find next function
        remaining = content[start + 1:]
        end_match = re.search(r'\n        async function loadConnections\(\)', remaining)
        if end_match:
            end = start + 1 + end_match.start()
            content = content[:start] + '\n' + new_loadDevices + '\n\n' + content[end:]
            print('✅ Fixed loadDevices()')
        else:
            print('❌ Could not find end of loadDevices')
    else:
        print('❌ Could not find loadDevices')
    
    # Find and replace loadConnections
    start_match = re.search(r'\n        async function loadConnections\(\)', content)
    if start_match:
        start = start_match.start()
        remaining = content[start + 1:]
        # Find next function (searchConnections or removeDevice)
        end_match = re.search(r'\n        (async function|function) (searchConnections|removeDevice|formatDuration)', remaining)
        if end_match:
            end = start + 1 + end_match.start()
            content = content[:start] + '\n' + new_loadConnections + '\n\n' + content[end:]
            print('✅ Fixed loadConnections()')
        else:
            print('❌ Could not find end of loadConnections')
    else:
        print('❌ Could not find loadConnections')
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('🔄 Vui lòng refresh trang admin để xem kết quả')

if __name__ == '__main__':
    fix_functions()

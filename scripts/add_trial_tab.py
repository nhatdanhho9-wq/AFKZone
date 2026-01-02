#!/usr/bin/env python3
"""
Add Trial Devices Tab to Admin Dashboard
Read the original clean file and add Trial Devices tab
"""

import re

# Read original file
with open('/home/automation/license-api/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Trial button to nav-tabs
nav_tabs_pattern = r'(<button class="nav-tab" onclick="showTab\(\'orders\'\)">💳 Đơn hàng</button>\s*</div>)'
nav_tabs_replacement = r'''<button class="nav-tab" onclick="showTab('orders')">💳 Đơn hàng</button>
                <button class="nav-tab" onclick="showTab('trials')">🎁 Trial Devices</button>
            </div>'''
content = re.sub(nav_tabs_pattern, nav_tabs_replacement, content)

# 2. Add Trial tab content HTML (before </div> that closes dashboard-screen)
# Find the Connections tab and add Trial tab after it
connections_end_pattern = r'(<!-- Orders Tab -->[\s\S]*?</div>\s*</div>\s*</div>)'
# Actually let's find safer position - before </div>\s*</div>\s*\n\s*<!-- Product Modal -->
trial_html = '''
            <!-- Trial Devices Tab -->
            <div id="tab-trials" class="tab-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2>🎁 Quản lý Trial Devices</h2>
                    <button class="btn btn-danger" onclick="clearAllTrials()">🗑️ Xóa tất cả</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Device Fingerprint</th>
                                <th>IP Address</th>
                                <th>License Key</th>
                                <th>Ngày tạo</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>
                        <tbody id="trials-tbody">
                            <tr><td colspan="6" style="text-align: center; padding: 20px;">Đang tải...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
'''

# Find position to insert - after Connections tab, before closing divs
# Look for: </div>\s*</div>\s*</div>\s*\n\s*<!-- Product Modal -->
insert_pattern = r'(</div>\s*</div>\s*</div>\s*\n\s*<!-- Product Modal -->)'
if re.search(insert_pattern, content):
    content = re.sub(insert_pattern, trial_html + r'\n    </div>\n    </div>\n\n    <!-- Product Modal -->', content)
    print('✅ Added Trial tab HTML')
else:
    # Try alternative - find end of tab-connections
    alt_pattern = r'(</tbody>\s*</table>\s*</div>\s*</div>\s*</div>\s*</div>\s*\n\s*<!-- Product Modal -->)'
    if re.search(alt_pattern, content):
        content = re.sub(alt_pattern, r'</tbody>\n                </table>\n            </div>\n        </div>' + trial_html + r'\n        </div>\n    </div>\n\n    <!-- Product Modal -->', content)
        print('✅ Added Trial tab HTML (alt pattern)')
    else:
        print('❌ Could not find position for Trial tab HTML')

# 3. Add trials case to showTab function
showtab_pattern = r"(else if \(tabName === 'orders'\) loadOrders\(\);)"
showtab_replacement = r"else if (tabName === 'orders') loadOrders();\n            else if (tabName === 'trials') loadTrials();"
content = re.sub(showtab_pattern, showtab_replacement, content)
print('✅ Added trials to showTab')

# 4. Add Trial functions before </script>
trial_functions = '''

        // ==================== TRIAL DEVICES FUNCTIONS ====================
        async function loadTrials() {
            console.log('Loading trial devices...');
            const tbody = document.getElementById('trials-tbody');
            if (!tbody) return;

            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">Đang tải...</td></tr>';

            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (!res.ok) throw new Error('HTTP ' + res.status);

                const data = await res.json();
                const devices = data.devices || data || [];

                if (!devices.length) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #999;">Không có trial device nào</td></tr>';
                    return;
                }

                tbody.innerHTML = devices.map(d => `
                    <tr>
                        <td>${d.id || 'N/A'}</td>
                        <td style="font-family: monospace; font-size: 11px;">${(d.device_fingerprint || 'N/A').substring(0, 20)}...</td>
                        <td>${d.ip_address || 'N/A'}</td>
                        <td style="font-family: monospace; font-size: 12px; color: #007bff;">${d.license_key || 'N/A'}</td>
                        <td>${d.created_at || 'N/A'}</td>
                        <td><button class="btn btn-danger" onclick="removeTrialDevice(${d.id})" style="padding: 5px 10px; font-size: 12px;">Xóa</button></td>
                    </tr>
                `).join('');
            } catch (e) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: red; padding: 20px;">Lỗi: ' + e.message + '</td></tr>';
            }
        }

        async function removeTrialDevice(id) {
            if (!confirm('Xóa trial device này?')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices/${id}`, {
                    method: 'DELETE',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã xóa!');
                    loadTrials();
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }

        async function clearAllTrials() {
            if (!confirm('XÓA TẤT CẢ trial devices?')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    method: 'DELETE',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã xóa tất cả!');
                    loadTrials();
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }
'''

# Insert before </script>
content = content.replace('    </script>', trial_functions + '    </script>')
print('✅ Added Trial functions')

# Write output
with open('/tmp/admin_dashboard_new.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ File saved to /app/admin_dashboard.html')
print('🔄 Refresh page to see changes')

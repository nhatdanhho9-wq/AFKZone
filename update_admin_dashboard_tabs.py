#!/usr/bin/env python3
"""Update admin dashboard with Trial Devices tab and fix Connections"""

def main():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add Trial Devices tab button
    old_tabs = '''<button class="nav-tab" onclick="showTab('orders')">💳 Đơn hàng</button>'''
    new_tabs = '''<button class="nav-tab" onclick="showTab('orders')">💳 Đơn hàng</button>
            <button class="nav-tab" onclick="showTab('trials')">🎁 Trial Devices</button>'''
    content = content.replace(old_tabs, new_tabs)
    
    # 2. Add Trial Devices tab content (before closing container div)
    trial_tab_content = '''
        <!-- Trial Devices Tab -->
        <div id="trials-tab" class="tab-content">
            <div class="section-header">
                <h2>🎁 Quản lý Trial Devices</h2>
                <button class="btn btn-danger" onclick="clearAllTrials()">🗑️ Xóa tất cả</button>
            </div>
            <table class="data-table">
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
'''
    
    # Find position to insert (before </div> of container)
    orders_tab_end = content.find('<!-- Orders Tab -->')
    if orders_tab_end > 0:
        # Find the closing </div> of orders tab
        next_div_close = content.find('</div>', orders_tab_end + 500)
        if next_div_close > 0:
            content = content[:next_div_close + 6] + trial_tab_content + content[next_div_close + 6:]
    
    # 3. Add loadTrials and clearAllTrials functions
    trials_js = '''
        // ==================== TRIAL DEVICES ====================
        async function loadTrials() {
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices`, {
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                const data = await res.json();
                const devices = data.devices || [];
                const tbody = document.getElementById('trials-tbody');
                
                if (devices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #999;">Không có trial device nào</td></tr>';
                    return;
                }
                
                tbody.innerHTML = devices.map(d => `
                    <tr>
                        <td>${d.id}</td>
                        <td><code>${d.device_fingerprint}</code></td>
                        <td>${d.ip_address || 'N/A'}</td>
                        <td><code>${d.license_key || 'N/A'}</code></td>
                        <td>${d.created_at || 'N/A'}</td>
                        <td>
                            <button class="btn btn-danger" onclick="deleteTrial(${d.id})" style="padding: 5px 10px; font-size: 12px;">Xóa</button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Error loading trials:', e);
                document.getElementById('trials-tbody').innerHTML = `<tr><td colspan="6" style="text-align: center; color: red;">Lỗi: ${e.message}</td></tr>`;
            }
        }
        
        async function deleteTrial(id) {
            if (!confirm('Xóa trial device này? Device sẽ có thể dùng thử lại.')) return;
            try {
                const res = await fetch(`${API_BASE}/admin/trial-devices/${id}`, {
                    method: 'DELETE',
                    headers: {'Authorization': `Bearer ${authToken}`}
                });
                if (res.ok) {
                    alert('Đã xóa trial device!');
                    loadTrials();
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
                }
            } catch (e) {
                alert('Lỗi: ' + e.message);
            }
        }
'''
    
    # 4. Fix showTab to include trials
    old_showTab = "else if (tabName === 'orders') loadOrders();"
    new_showTab = "else if (tabName === 'orders') loadOrders();\\n            else if (tabName === 'trials') loadTrials();"
    content = content.replace(old_showTab, new_showTab.replace('\\n', '\n'))
    
    # 5. Fix loadConnections to use new endpoint
    old_connections = "const res = await fetch(`${API_BASE}/admin/connections`,"
    # Already correct, just make sure it exists
    
    # Insert trials JS before the closing </script>
    script_close = content.rfind('</script>')
    if script_close > 0:
        content = content[:script_close] + trials_js + '\n    ' + content[script_close:]
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Admin dashboard updated with Trial Devices tab!")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Add completeOrder function to admin dashboard
This allows manually completing orders from the Orders tab
"""
import re

def add_complete_order():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak_order', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Add completeOrder function
    complete_order_js = '''
<script>
// ==================== COMPLETE ORDER FUNCTION ====================
async function completeOrder(transCode) {
    console.log('📦 Completing order:', transCode);
    const confirmed = await afkConfirm('Hoàn thành đơn hàng này? Sẽ tạo license và kích hoạt cho khách hàng.');
    if (!confirmed) return;
    
    try {
        const res = await fetch(`${API_BASE}/admin/orders/${transCode}/complete`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (res.ok) {
            const data = await res.json();
            if (data.success) {
                alert(`✅ Hoàn thành đơn hàng!\\n\\nLicense: ${data.license_key}\\nGói: ${data.tier.toUpperCase()} - ${data.duration_days} ngày`);
                loadOrders(); // Refresh orders
            } else {
                alert('⚠️ ' + (data.message || 'Order đã được xử lý trước đó'));
            }
        } else {
            const error = await res.json();
            alert('❌ Lỗi: ' + (error.detail || 'Không thể hoàn thành đơn hàng'));
        }
    } catch (e) {
        console.error('Error completing order:', e);
        alert('❌ Lỗi kết nối: ' + e.message);
    }
}

console.log('✅ completeOrder function loaded!');
</script>
'''
    
    # Remove any existing completeOrder script
    content = re.sub(r'<script>\s*// ==================== COMPLETE ORDER FUNCTION.*?</script>', '', content, flags=re.DOTALL)
    
    # Add before </body>
    content = content.replace('</body>', complete_order_js + '\n</body>')
    
    # Also need to update the loadOrders function to add complete button for pending orders
    # Find and update the orders table rendering
    # The original loadOrders renders orders without a complete button
    
    # Add a fix to update order rows with complete button
    fix_orders_js = '''
<script>
// ==================== FIX ORDERS TABLE WITH COMPLETE BUTTON ====================
const origLoadOrders2 = window.loadOrders;
window.loadOrders = async function() {
    try {
        const res = await fetch(`${API_BASE}/admin/orders`, {
            headers: {'Authorization': `Bearer ${authToken}`}
        });
        const data = await res.json();
        const orders = data.orders || [];
        
        console.log('📋 Loaded', orders.length, 'orders');
        
        const tbody = document.getElementById('orders-table');
        if (!tbody) {
            console.error('orders-table not found!');
            return;
        }
        
        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#666">Không có đơn hàng nào</td></tr>';
            return;
        }
        
        tbody.innerHTML = orders.map(o => {
            const statusClass = o.status === 'success' ? 'status-active' : (o.status === 'pending' ? 'status-pending' : 'status-inactive');
            const statusText = o.status === 'success' ? 'Thành công' : (o.status === 'pending' ? 'Chờ thanh toán' : o.status);
            const createdAt = o.created_at ? new Date(o.created_at).toLocaleString('vi-VN') : '-';
            const paidAt = o.paid_at ? new Date(o.paid_at).toLocaleString('vi-VN') : '-';
            
            // Add complete button for pending orders
            let actionHtml = '';
            if (o.status === 'pending') {
                actionHtml = `<button class="btn btn-success" onclick="completeOrder('${o.trans_code}')" style="padding:5px 10px;font-size:12px">Hoàn thành</button>`;
            }
            
            return `<tr>
                <td><code style="font-size:11px">${o.trans_code}</code></td>
                <td><span class="badge badge-info">${o.tier || '-'}</span></td>
                <td>${o.duration_days || 0} ngày</td>
                <td>${o.amount ? o.amount.toLocaleString('vi-VN') + 'đ' : '-'}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>${o.license_key ? `<code style="font-size:10px">${o.license_key}</code>` : '<em>-</em>'}</td>
                <td style="font-size:11px">${createdAt}</td>
                <td style="font-size:11px">${paidAt}</td>
                <td>${actionHtml}</td>
            </tr>`;
        }).join('');
        
    } catch (e) {
        console.error('Error loading orders:', e);
        const tbody = document.getElementById('orders-table');
        if (tbody) tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:red">Lỗi tải đơn hàng</td></tr>';
    }
};

console.log('✅ Orders table with complete button loaded!');
</script>
'''
    
    content = re.sub(r'<script>\s*// ==================== FIX ORDERS TABLE WITH COMPLETE BUTTON.*?</script>', '', content, flags=re.DOTALL)
    content = content.replace('</body>', fix_orders_js + '\n</body>')
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Added completeOrder function!")
    print("✅ Updated orders table with 'Hoàn thành' button for pending orders!")

if __name__ == '__main__':
    add_complete_order()

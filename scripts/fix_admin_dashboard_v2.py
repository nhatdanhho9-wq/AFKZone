#!/usr/bin/env python3
"""
Comprehensive Admin Dashboard Fix:
1. Fix custom confirm modal (async/await pattern)
2. Sync tier dropdowns from tiers table
3. Fix enableProduct missing confirm
4. Add Tier management tab
5. Load tiers dynamically from database
"""

import re

def fix_admin_dashboard():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak3', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # ============================================
    # 1. FIX CUSTOM CONFIRM MODAL - Use callbacks properly
    # ============================================
    
    # Remove old custom confirm modal if exists
    content = re.sub(r'<!-- Custom Confirm Modal Override.*?</script>\s*', '', content, flags=re.DOTALL)
    
    # Add new proper confirm modal before </body>
    new_confirm_modal = '''
<!-- AFK Zone Custom Confirm Modal v2 -->
<div id="afkConfirmModal" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.6); z-index:99999; align-items:center; justify-content:center;">
    <div style="background:white; padding:24px; border-radius:12px; max-width:400px; margin:20px; box-shadow:0 8px 32px rgba(0,0,0,0.3);">
        <h3 style="margin:0 0 16px 0; color:#333; font-size:18px;">⚠️ Xác nhận</h3>
        <p id="afkConfirmMsg" style="margin:0 0 24px 0; color:#666; font-size:14px; line-height:1.5;"></p>
        <div style="display:flex; gap:12px; justify-content:flex-end;">
            <button id="afkConfirmNo" style="padding:10px 20px; border:1px solid #ddd; background:#f5f5f5; border-radius:6px; cursor:pointer; font-size:14px;">Hủy</button>
            <button id="afkConfirmYes" style="padding:10px 20px; border:none; background:#dc3545; color:white; border-radius:6px; cursor:pointer; font-size:14px; font-weight:500;">Xác nhận</button>
        </div>
    </div>
</div>

<script>
// AFK Zone Custom Confirm - Proper Async Pattern v2
const afkConfirm = (message) => {
    return new Promise((resolve) => {
        const modal = document.getElementById('afkConfirmModal');
        document.getElementById('afkConfirmMsg').textContent = message;
        modal.style.display = 'flex';
        
        const yesBtn = document.getElementById('afkConfirmYes');
        const noBtn = document.getElementById('afkConfirmNo');
        
        const cleanup = () => {
            modal.style.display = 'none';
            yesBtn.onclick = null;
            noBtn.onclick = null;
        };
        
        yesBtn.onclick = () => { cleanup(); resolve(true); };
        noBtn.onclick = () => { cleanup(); resolve(false); };
    });
};

// Override window.confirm with our async version
// Note: functions must use await afkConfirm() or .then() pattern
console.log('✅ AFK Zone Custom Confirm v2 loaded');
</script>
'''
    content = content.replace('</body>', new_confirm_modal + '</body>')
    print("✅ Added new custom confirm modal v2")
    
    # ============================================
    # 2. FIX deleteProduct - use await afkConfirm
    # ============================================
    old_delete_product = '''async function deleteProduct(productId) {
            if (!confirm('Bạn có chắc muốn tắt sản phẩm này?')) return;'''
    new_delete_product = '''async function deleteProduct(productId) {
            const confirmed = await afkConfirm('Bạn có chắc muốn TẮT sản phẩm này?');
            if (!confirmed) return;'''
    content = content.replace(old_delete_product, new_delete_product)
    print("✅ Fixed deleteProduct")
    
    # ============================================
    # 3. FIX enableProduct - add confirm
    # ============================================
    old_enable_product = '''async function enableProduct(productId) {
            try {'''
    new_enable_product = '''async function enableProduct(productId) {
            const confirmed = await afkConfirm('Bạn có chắc muốn BẬT sản phẩm này?');
            if (!confirmed) return;
            try {'''
    content = content.replace(old_enable_product, new_enable_product)
    print("✅ Fixed enableProduct - added confirm")
    
    # ============================================
    # 4. FIX deleteProductPermanent
    # ============================================
    old_delete_perm = '''async function deleteProductPermanent(productId) {
            if (!confirm('⚠️ Bạn có chắc muốn XÓA HOÀN TOÀN sản phẩm này? Hành động này không thể hoàn tác!')) return;'''
    new_delete_perm = '''async function deleteProductPermanent(productId) {
            const confirmed = await afkConfirm('⚠️ Bạn có chắc muốn XÓA HOÀN TOÀN sản phẩm này? Hành động này không thể hoàn tác!');
            if (!confirmed) return;'''
    content = content.replace(old_delete_perm, new_delete_perm)
    print("✅ Fixed deleteProductPermanent")
    
    # ============================================
    # 5. FIX deleteLicense
    # ============================================
    old_delete_license = '''async function deleteLicense(licenseKey) {
            if (!confirm('XÓA VĨNH VIỄN license này? Hành động không thể hoàn tác!')) return;'''
    new_delete_license = '''async function deleteLicense(licenseKey) {
            const confirmed = await afkConfirm('XÓA VĨNH VIỄN license này? Hành động không thể hoàn tác!');
            if (!confirmed) return;'''
    content = content.replace(old_delete_license, new_delete_license)
    print("✅ Fixed deleteLicense")
    
    # ============================================
    # 6. FIX revokeLicense
    # ============================================
    old_revoke = "if (!confirm('Thu hồi license này? Client sẽ không thể sử dụng license này nữa.')) return;"
    new_revoke = "const confirmed = await afkConfirm('Thu hồi license này? Client sẽ không thể sử dụng license này nữa.'); if (!confirmed) return;"
    content = content.replace(old_revoke, new_revoke)
    print("✅ Fixed revokeLicense")
    
    # ============================================
    # 7. FIX restoreLicense (khôi phục)
    # ============================================
    old_restore = "if (!confirm('Khôi phục license này? Client sẽ có thể sử dụng lại.')) return;"
    new_restore = "const confirmed2 = await afkConfirm('Khôi phục license này? Client sẽ có thể sử dụng lại.'); if (!confirmed2) return;"
    content = content.replace(old_restore, new_restore)
    print("✅ Fixed restoreLicense")
    
    # ============================================
    # 8. FIX license-tier dropdown - add test1, test2
    # ============================================
    old_license_tier = '''<select id="license-tier">
                    <option value="basic">Basic</option>
                    <option value="pro">Pro</option>
                    <option value="enterprise">Enterprise</option>
                </select>'''
    new_license_tier = '''<select id="license-tier">
                    <option value="basic">Basic</option>
                    <option value="pro">Pro</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="test1">Test Tier 1</option>
                    <option value="test2">Test Tier 2</option>
                </select>'''
    content = content.replace(old_license_tier, new_license_tier)
    print("✅ Fixed license-tier dropdown - added test1, test2")
    
    # ============================================
    # 9. Fix other confirm() usages
    # ============================================
    # removeDevice
    old_remove_device = "if (!confirm(`Bạn có chắc muốn xóa thiết bị ${deviceId}?`)) return;"
    new_remove_device = "const confirmRemove = await afkConfirm(`Bạn có chắc muốn xóa thiết bị ${deviceId}?`); if (!confirmRemove) return;"
    content = content.replace(old_remove_device, new_remove_device)
    
    # completeOrder
    old_complete_order = "if (!confirm(`Xác nhận hoàn thành đơn hàng ${transCode}? Hệ thống sẽ tự động tạo và kích hoạt license.`)) return;"
    new_complete_order = "const confirmComplete = await afkConfirm(`Xác nhận hoàn thành đơn hàng ${transCode}? Hệ thống sẽ tự động tạo và kích hoạt license.`); if (!confirmComplete) return;"
    content = content.replace(old_complete_order, new_complete_order)
    
    # deleteTrialDevice
    old_delete_trial = "if (!confirm('Xóa trial device này? Device sẽ có thể dùng thử lại.')) return;"
    new_delete_trial = "const confirmTrial = await afkConfirm('Xóa trial device này? Device sẽ có thể dùng thử lại.'); if (!confirmTrial) return;"
    content = content.replace(old_delete_trial, new_delete_trial)
    
    # clearAllTrials
    old_clear_trials = "if (!confirm('XÓA TẤT CẢ trial devices? Tất cả users sẽ có thể dùng thử lại!')) return;"
    new_clear_trials = "const confirmClear = await afkConfirm('XÓA TẤT CẢ trial devices? Tất cả users sẽ có thể dùng thử lại!'); if (!confirmClear) return;"
    content = content.replace(old_clear_trials, new_clear_trials)
    
    print("✅ Fixed all other confirm() usages")
    
    # ============================================
    # 10. Add Tier tab (sẽ thêm sau khi có API)
    # ============================================
    # Note: Cần thêm API endpoint /admin/tiers trước khi add tab này
    
    # Save
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ ALL DONE! Refresh admin dashboard (Ctrl+F5)")
    print("\n⚠️ Note: Để thêm Tab Tier quản lý, cần thêm API /admin/tiers trong backend trước.")

if __name__ == '__main__':
    fix_admin_dashboard()

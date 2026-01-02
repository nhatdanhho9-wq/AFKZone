#!/usr/bin/env python3
"""
Fix admin dashboard: Add custom confirm modal that ALWAYS shows
Simple approach - inject at the END of the file
"""

def fix_confirm_dialogs():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/admin_dashboard.html.bak2', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Add custom confirm modal override BEFORE </body>
    custom_confirm = '''
<!-- Custom Confirm Modal Override - ALWAYS visible -->
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
(function() {
    // Custom confirm that ALWAYS shows a visible modal
    let pendingResolve = null;
    
    const modal = document.getElementById('afkConfirmModal');
    const msgEl = document.getElementById('afkConfirmMsg');
    const yesBtn = document.getElementById('afkConfirmYes');
    const noBtn = document.getElementById('afkConfirmNo');
    
    yesBtn.onclick = function() {
        modal.style.display = 'none';
        if (pendingResolve) pendingResolve(true);
        pendingResolve = null;
    };
    
    noBtn.onclick = function() {
        modal.style.display = 'none';
        if (pendingResolve) pendingResolve(false);
        pendingResolve = null;
    };
    
    modal.onclick = function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
            if (pendingResolve) pendingResolve(false);
            pendingResolve = null;
        }
    };
    
    // Override window.confirm
    window.confirm = function(message) {
        return new Promise(function(resolve) {
            pendingResolve = resolve;
            msgEl.textContent = message;
            modal.style.display = 'flex';
        });
    };
    
    console.log('✅ Custom confirm modal installed');
})();
</script>
'''
    
    # Check if already added
    if 'afkConfirmModal' in content:
        print("⚠️ Custom confirm modal already exists, skipping...")
    else:
        content = content.replace('</body>', custom_confirm + '</body>')
        print("✅ Added custom confirm modal")
    
    # Save
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ DONE! Refresh admin dashboard (Ctrl+F5)")

if __name__ == '__main__':
    fix_confirm_dialogs()

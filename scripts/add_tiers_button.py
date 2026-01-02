#!/usr/bin/env python3
"""Add Tiers nav button properly"""

def add_tiers_button():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already exists
    if "showTab('tiers')\">" in content:
        print("⚠️ Tiers button already exists!")
        return
    
    # Find trials button and add tiers before it
    old = '''<button class="nav-tab" onclick="showTab('trials')">🎁 Trial Devices</button>'''
    new = '''<button class="nav-tab" onclick="showTab('tiers')">📋 Tiers</button>
            <button class="nav-tab" onclick="showTab('trials')">🎁 Trial Devices</button>'''
    
    if old in content:
        content = content.replace(old, new)
        print("✅ Added Tiers button before Trials")
    else:
        # Try alternate - add after orders
        old2 = '''<button class="nav-tab" onclick="showTab('orders')">💳 Đơn hàng</button>'''
        new2 = '''<button class="nav-tab" onclick="showTab('orders')">💳 Đơn hàng</button>
                <button class="nav-tab" onclick="showTab('tiers')">📋 Tiers</button>'''
        if old2 in content:
            content = content.replace(old2, new2)
            print("✅ Added Tiers button after Orders")
        else:
            print("❌ Could not find nav button location")
            return
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ DONE!")

if __name__ == '__main__':
    add_tiers_button()

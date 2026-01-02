#!/usr/bin/env python3
"""
Fix Tier tab ID and navigation button
"""

def fix_tier_tab():
    with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Fix the tab content ID: tiers-tab -> tab-tiers
    content = content.replace('id="tiers-tab"', 'id="tab-tiers"')
    content = content.replace("getElementById('tiers-tab')", "getElementById('tab-tiers')")
    print("✅ Fixed tab ID: tiers-tab -> tab-tiers")
    
    # 2. Check if nav tab button exists, if not add it properly
    if "showTab('tiers')\">Tiers</button>" in content:
        print("⚠️ Tiers nav button already exists")
    else:
        # Find the connections tab button and add tier after it
        old_nav = "onclick=\"showTab('connections')\">Kết nối</button>"
        new_nav = old_nav + "\n                <button class=\"nav-tab\" onclick=\"showTab('tiers')\">Tiers</button>"
        content = content.replace(old_nav, new_nav)
        print("✅ Added Tiers nav button after Kết nối")
    
    # 3. Make sure showTab function handles 'tiers' properly
    # The original showTab uses format: tab-{name}
    
    with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ DONE! Refresh page to see Tiers tab")

if __name__ == '__main__':
    fix_tier_tab()

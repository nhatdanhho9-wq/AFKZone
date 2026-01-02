#!/usr/bin/env python3
"""
Fix Admin Dashboard HTML Structure
- Tab Orders bị đóng sớm, thiếu table content
- Tab Connections nằm sau Trial nhưng Table của Orders lại nằm giữa
"""

import re

with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original file length: {len(content)}")

# Problem: The Orders tab is split - header is at one place, table is at another
# We need to find and restructure

# Strategy: Find the correct structure and rebuild

# Find each tab div
tabs = [
    ('tab-dashboard', 'Dashboard'),
    ('tab-products', 'Sản phẩm'),
    ('tab-licenses', 'Licenses'),
    ('tab-devices', 'Thiết bị'),
    ('tab-orders', 'Đơn hàng'),
    ('tab-connections', 'Kết nối'),
    ('tab-trials', 'Trial')
]

for tab_id, name in tabs:
    matches = list(re.finditer(rf'<div id="{tab_id}"', content))
    print(f"{tab_id}: {len(matches)} occurrences")

# Find orphaned Orders table
orders_table_match = re.search(r'<th>Mã đơn</th>', content)
if orders_table_match:
    print(f"Orders table header at position: {orders_table_match.start()}")
    
# Find tab-orders position
tab_orders_match = re.search(r'<div id="tab-orders"', content)
if tab_orders_match:
    print(f"tab-orders div at position: {tab_orders_match.start()}")
    # Check if orders table is inside or outside
    if orders_table_match and orders_table_match.start() > tab_orders_match.start():
        # Check for closing div between them
        between = content[tab_orders_match.start():orders_table_match.start()]
        close_divs = between.count('</div>')
        open_divs = between.count('<div')
        print(f"Between tab-orders and table: {open_divs} opens, {close_divs} closes")

# The fix: Need to move the orders table into the correct tab-orders div
# First, extract the orphaned table section
orphan_table_pattern = r'''(\n                <div class="table-container">\s*<table>\s*<thead>\s*<tr>\s*<th>Mã đơn</th>.*?</table>\s*</div>\s*</div>)'''

match = re.search(orphan_table_pattern, content, re.DOTALL)
if match:
    print(f"Found orphan orders table section (length: {len(match.group(1))})")
    orphan_section = match.group(1)
    
    # Remove it from current position
    content = content.replace(orphan_section, '')
    
    # Find where tab-orders should end (before tab-trials or tab-connections)
    # Actually we need to insert it into tab-orders properly
    
    # Find pattern: the </div> that closes tab-orders prematurely
    # It's after the search-box div for orders
    pattern_to_fix = r'(<input type="text" id="order-search"[^>]*>)\s*</div>\s*</div>\s*(\s*<!-- Trial Devices Tab -->)'
    
    def replace_orders(m):
        # Remove the premature </div></div> and add the orders table content
        # The orphan_section already has </div></div> at the end for closing
        return m.group(1) + '\n                </div>' + orphan_section + '\n\n            ' + m.group(2)
    
    new_content = re.sub(pattern_to_fix, replace_orders, content, flags=re.DOTALL)
    
    if new_content != content:
        content = new_content
        print("✅ Moved orders table into correct position")
    else:
        print("❌ Could not find pattern to fix orders")
else:
    print("❌ Could not find orphan orders table")

# Write result
with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"New file length: {len(content)}")
print("Done. Refresh page to test.")

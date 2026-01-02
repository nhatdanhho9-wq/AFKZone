#!/usr/bin/env python3
"""
Fix Trial Tab Nesting Issue
tab-trials bị lồng bên trong tab-orders, cần move ra ngoài
"""

with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Tìm tab-trials và move ra ngoài tab-orders
# Vấn đề: tab-trials nằm bên trong tab-orders
# Cần: close tab-orders trước, rồi mới đến tab-trials

# Pattern: tìm </div>\s*</div>\s*<!-- Trial Devices Tab --> và thay bằng đóng đúng
import re

# Approach: tìm pattern của Orders tab closing và Trial tab opening
# Fix: thêm closing tags đúng chỗ

# Xem cấu trúc hiện tại
orders_match = re.search(r'<div id="tab-orders"[^>]*>', content)
trials_match = re.search(r'<div id="tab-trials"[^>]*>', content)

if orders_match and trials_match:
    print(f"tab-orders starts at position: {orders_match.start()}")
    print(f"tab-trials starts at position: {trials_match.start()}")
    
    # Tìm pattern: vị trí trials đang nằm sau orders mà không có closing đúng
    # Cần chèn </div> để đóng orders trước khi mở trials
    
    # Tìm "<!-- Trial Devices Tab -->" và thêm </div></div> trước nó
    
    # Pattern hiện tại có thể là:
    # ...orders content...</div></div> <!-- Trial... (WRONG - trials inside orders)
    # Cần: ...orders content...</div></div></div> <!-- Trial... (close orders properly)
    
    # Check content between orders and trials
    between = content[orders_match.end():trials_match.start()]
    print(f"Content between orders and trials ({len(between)} chars)")
    
    # Count divs to understand nesting
    open_divs = between.count('<div')
    close_divs = between.count('</div>')
    print(f"Between orders and trials: {open_divs} opens, {close_divs} closes")
    
    # If trials is nested, we need to add </div> before it
    # Tìm vị trí ngay trước <!-- Trial Devices Tab -->
    trial_comment = content.find('<!-- Trial Devices Tab -->')
    if trial_comment > 0:
        # Check 100 chars trước
        before_trial = content[trial_comment-100:trial_comment]
        print(f"Before trial comment: {repr(before_trial)}")
        
        # Đếm </div> ngay trước trial comment - nếu thiếu thì thêm
        # Cần có 2 </div> để đóng table-container và tab-orders
        
        # Strategy: thêm </div> ngay trước <!-- Trial Devices Tab -->
        # để đóng tab-orders
        if '</div>\n            </div>\n\n            <!-- Trial' not in content:
            # Thiếu closing div
            new_content = content.replace(
                '<!-- Trial Devices Tab -->',
                '</div>\n\n            <!-- Trial Devices Tab -->'
            )
            
            with open('/app/admin_dashboard.html', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ Added missing </div> before Trial tab")
        else:
            print("Closing divs seem OK, checking further...")
            
            # Alternative fix: find and fix the actual nesting
            # The issue might be that tab-trials is missing its own closing structure
            pass
else:
    print("Could not find tab patterns")

print("Done. Refresh page to test.")

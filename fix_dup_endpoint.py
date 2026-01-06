#!/usr/bin/env python3
"""Disable duplicate analytics endpoint"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Replace only the FIRST occurrence
old_str = '@app.get("/admin/analytics/revenue")'
new_str = '# DISABLED_DUP: @app.get("/admin/analytics/revenue_v1")'

# Find first occurrence and replace only that one
idx = content.find(old_str)
if idx != -1:
    content = content[:idx] + new_str + content[idx + len(old_str):]
    with open('/app/app.py', 'w') as f:
        f.write(content)
    print("SUCCESS: First occurrence disabled")
else:
    print("Pattern not found")

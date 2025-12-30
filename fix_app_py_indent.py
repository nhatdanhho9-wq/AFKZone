#!/usr/bin/env python3
"""Fix indentation error in app.py line 204"""

with open('/app/app.py', 'r') as f:
    lines = f.readlines()

# Check lines around 204
print('Current lines 200-210:')
for i in range(199, min(210, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')

# Find the function containing line 204
for i in range(200, 210):
    if 'def generate_licenses' in lines[i-1] or '@app.post("/generate")' in lines[i-3]:
        # This is in the generate_licenses function
        # Line 203 should be: if admin_key != "afkzone-admin-2025":
        # Line 204 should be:     raise HTTPException...
        # But it seems line 204 has wrong indentation
        
        # Check line 203
        if i < len(lines) and 'if admin_key' in lines[i-1]:
            # Line 204 should be indented 8 spaces (inside if block)
            if i < len(lines):
                original_line = lines[i]
                stripped = original_line.lstrip()
                if stripped.startswith('if req.tier') or stripped.startswith('raise'):
                    # Should be indented 8 spaces
                    lines[i] = '        ' + stripped
                    print(f'\n✅ Fixed line {i+1}:')
                    print(f'Before: {repr(original_line)}')
                    print(f'After: {repr(lines[i])}')
                    break

# Write back
with open('/app/app.py', 'w') as f:
    f.writelines(lines)

# Verify
import ast
try:
    with open('/app/app.py', 'r') as f:
        code = f.read()
    ast.parse(code)
    print('\n✅ Python syntax is now valid!')
except SyntaxError as e:
    print(f'\n❌ Still has syntax error: {e}')
    print(f'Line {e.lineno}: {e.text}')


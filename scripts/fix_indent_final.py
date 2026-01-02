#!/usr/bin/env python3
"""Fix indentation error in app.py"""

with open('/app/app.py', 'r') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')
print('\nLines 200-210:')
for i in range(199, min(210, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')

# Based on app.py.original structure:
# Line 202: def generate_licenses(...)
# Line 203:     if admin_key != "REDACTED_ADMIN_KEY":
# Line 204:         raise HTTPException(status_code=401, detail="Unauthorized")
# Line 205:     if req.tier not in DEVICE_LIMITS...

# Fix line 204 - should be raise with 8 spaces
if len(lines) > 203:
    line_204 = lines[203]
    # If line 204 has "if req.tier", it's wrong - should be "raise HTTPException"
    if 'if req.tier' in line_204:
        # This line should be the raise statement
        lines[203] = '        raise HTTPException(status_code=401, detail="Unauthorized")\n'
        print('\n✅ Fixed line 204: Changed to raise statement')
    elif 'raise HTTPException' in line_204 and not line_204.startswith('        '):
        # Fix indentation
        lines[203] = '        ' + line_204.lstrip()
        print('\n✅ Fixed line 204: Fixed indentation')

# Fix line 205 - should be if with 4 spaces
if len(lines) > 204:
    line_205 = lines[204]
    if 'if req.tier' in line_205 and not line_205.startswith('    '):
        lines[204] = '    ' + line_205.lstrip()
        print('✅ Fixed line 205: Fixed indentation')

# Write back
with open('/app/app.py', 'w') as f:
    f.writelines(lines)

# Verify syntax
import ast
try:
    with open('/app/app.py', 'r') as f:
        code = f.read()
    ast.parse(code)
    print('\n✅ Python syntax is valid!')
except SyntaxError as e:
    print(f'\n❌ Still has syntax error: {e}')
    print(f'Line {e.lineno}: {e.text}')



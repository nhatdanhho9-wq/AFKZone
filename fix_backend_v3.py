#!/usr/bin/env python3
"""
Fix backend - insert endpoints AFTER verify_token definition (around line 441)
"""

with open('/app/app.py', 'r') as f:
    lines = f.readlines()

# Find verify_token line
verify_token_line = None
admin_login_line = None
products_section_line = None

for i, line in enumerate(lines):
    if 'def verify_token' in line:
        verify_token_line = i
    elif '@app.post("/admin/login")' in line:
        admin_login_line = i
    elif '# ==================== PRODUCTS MANAGEMENT' in line:
        products_section_line = i

print(f'verify_token at line: {verify_token_line+1 if verify_token_line else "NOT FOUND"}')
print(f'admin_login at line: {admin_login_line+1 if admin_login_line else "NOT FOUND"}')
print(f'products_section at line: {products_section_line+1 if products_section_line else "NOT FOUND"}')

content = ''.join(lines)
changes = []

# 1. Fix ProductUpdate class
old_product_update = '''class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    max_devices: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    description: Optional[str] = None'''

new_product_update = '''class ProductUpdate(BaseModel):
    name: Optional[str] = None
    tier: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[int] = None
    max_devices: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    description: Optional[str] = None'''

if old_product_update in content:
    content = content.replace(old_product_update, new_product_update)
    changes.append('Added tier/duration_days to ProductUpdate')

# 2. Fix update_product handler
old_handler = '''    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.price is not None:
        updates.append("price=:price")
        params["price"] = product.price'''

new_handler = '''    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.tier is not None:
        updates.append("tier=:tier")
        params["tier"] = product.tier
    if product.duration_days is not None:
        updates.append("duration_days=:days")
        params["days"] = product.duration_days
    if product.price is not None:
        updates.append("price=:price")
        params["price"] = product.price'''

if old_handler in content:
    content = content.replace(old_handler, new_handler)
    changes.append('Added tier/duration_days to update_product')

# 3. Add /admin/licenses endpoint AFTER PRODUCTS MANAGEMENT section begins
# Products section starts around line 481, which is AFTER verify_token (line 441)
admin_licenses = '''
@app.get("/admin/licenses")
def list_licenses_admin(
    page: int = 1,
    limit: int = 100,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: List all licenses with JWT auth"""
    offset = (page - 1) * limit
    results = db.execute(text("""
        SELECT * FROM licenses 
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
    """), {"limit": limit, "offset": offset}).fetchall()
    
    total = db.execute(text("SELECT COUNT(*) FROM licenses")).scalar()
    
    licenses = []
    for r in results:
        licenses.append({
            "license_key": r[1] if len(r) > 1 else None,
            "tier": r[2] if len(r) > 2 else None,
            "duration_days": r[3] if len(r) > 3 else None,
            "activated_at": r[4].isoformat() if len(r) > 4 and r[4] else None,
            "expires_at": r[5].isoformat() if len(r) > 5 and r[5] else None,
            "device_id": r[6] if len(r) > 6 else None,
            "max_devices": r[7] if len(r) > 7 else None,
            "is_revoked": r[9] if len(r) > 9 else False,
            "is_trial": r[11] if len(r) > 11 else False
        })
    
    return {"total": total or 0, "licenses": licenses}

@app.delete("/admin/devices/{device_id}")
def delete_device(
    device_id: str,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Remove device from license"""
    db.execute(text("DELETE FROM license_devices WHERE device_id=:device_id"), {"device_id": device_id})
    db.commit()
    return {"success": True, "message": f"Device {device_id} removed successfully"}

'''

# Insert after PRODUCTS MANAGEMENT section header (after verify_token)
if '@app.get("/admin/licenses")' not in content:
    marker = '# ==================== PRODUCTS MANAGEMENT ===================='
    if marker in content:
        content = content.replace(marker, marker + admin_licenses)
        changes.append('Added /admin/licenses and device delete endpoints')

# Write back
with open('/app/app.py', 'w') as f:
    f.write(content)

# Verify
import ast
try:
    ast.parse(content)
    print('\n✅ All fixes applied:')
    for change in changes:
        print(f'  - {change}')
    print('✅ Python syntax valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')
    exit(1)

# Double check positions
lines = content.split('\n')
verify_line = None
for i, line in enumerate(lines):
    if 'def verify_token' in line:
        verify_line = i
        break

if verify_line:
    errors = []
    for i in range(verify_line):
        if 'Depends(verify_token)' in lines[i]:
            errors.append(f'Line {i+1}')
    
    if errors:
        print(f'❌ Endpoints before verify_token: {errors}')
    else:
        print('✅ All endpoints after verify_token')

# Find our new endpoints
for i, line in enumerate(lines):
    if '@app.get("/admin/licenses")' in line:
        print(f'✅ /admin/licenses at line {i+1}')
    elif '@app.delete("/admin/devices' in line:
        print(f'✅ DELETE /admin/devices at line {i+1}')


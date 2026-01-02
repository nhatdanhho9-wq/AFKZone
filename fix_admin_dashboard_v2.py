#!/usr/bin/env python3
"""Complete fix for admin dashboard - properly positioned"""

with open('/app/app.py', 'r') as f:
    content = f.read()

changes = []

# Check if fixes already applied
if 'duration_days: Optional[int] = None' in content and 'class ProductUpdate' in content:
    if 'tier: Optional[str] = None' not in content[content.find('class ProductUpdate'):content.find('class ProductUpdate')+200]:
        # Need to add tier
        old_update = '''class ProductUpdate(BaseModel):
    name: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[int] = None'''
        new_update = '''class ProductUpdate(BaseModel):
    name: Optional[str] = None
    tier: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[int] = None'''
        if old_update in content:
            content = content.replace(old_update, new_update)
            changes.append('Added tier to ProductUpdate')
    else:
        print('✅ ProductUpdate already has tier and duration_days')

# Check PUT endpoint
if 'def update_product' in content:
    if 'product.tier' not in content[content.find('def update_product'):content.find('def update_product')+500]:
        # Need to add tier and duration_days handling
        old_handling = '''    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.price is not None:'''
        new_handling = '''    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.tier is not None:
        updates.append("tier=:tier")
        params["tier"] = product.tier
    if product.duration_days is not None:
        updates.append("duration_days=:days")
        params["days"] = product.duration_days
    if product.price is not None:'''
        
        if old_handling in content:
            content = content.replace(old_handling, new_handling)
            changes.append('Added tier and duration_days to PUT endpoint')
    else:
        print('✅ PUT endpoint already handles tier and duration_days')

# Add /admin/licenses endpoint (after /list, before /trial)
if '@app.get("/admin/licenses")' not in content:
    if '@app.post("/trial/generate")' in content:
        pos = content.find('@app.post("/trial/generate")')
        if pos > 0:
            licenses_endpoint = '''@app.get("/admin/licenses")
def list_licenses_admin(
    page: int = 1,
    limit: int = 100,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: List all licenses (using JWT)"""
    offset = (page - 1) * limit
    results = db.execute(text("""
        SELECT * FROM licenses 
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
    """), {"limit": limit, "offset": offset}).fetchall()
    
    total = db.execute(text("SELECT COUNT(*) FROM licenses")).scalar()
    
    licenses = []
    for r in results:
        license_data = {
            "license_key": r[1] if len(r) > 1 else None,
            "tier": r[2] if len(r) > 2 else None,
            "duration_days": r[3] if len(r) > 3 else None,
            "activated_at": r[4].isoformat() if len(r) > 4 and r[4] else None,
            "expires_at": r[5].isoformat() if len(r) > 5 and r[5] else None,
            "device_id": r[6] if len(r) > 6 else None,
            "max_devices": r[7] if len(r) > 7 else None,
            "is_revoked": r[9] if len(r) > 9 else False,
            "is_trial": r[11] if len(r) > 11 else False
        }
        licenses.append(license_data)
    
    return {"total": total or 0, "licenses": licenses}

'''
            content = content[:pos] + licenses_endpoint + '\n' + content[pos:]
            changes.append('Added /admin/licenses endpoint')

# Add device delete endpoint (after /admin/users)
if '@app.delete("/admin/devices/{device_id}")' not in content:
    if 'def get_users(' in content:
        # Find end of get_users function
        func_start = content.find('def get_users(')
        func_end = content.find('\n# ====================', func_start)
        if func_end > 0:
            device_delete = '''

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
            content = content[:func_end] + device_delete + content[func_end:]
            changes.append('Added device delete endpoint')

with open('/app/app.py', 'w') as f:
    f.write(content)

# Verify
import ast
try:
    ast.parse(content)
    if changes:
        print('✅ All fixes applied:')
        for change in changes:
            print(f'  - {change}')
    else:
        print('✅ All fixes already applied')
    print('✅ Python syntax is valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')
    exit(1)


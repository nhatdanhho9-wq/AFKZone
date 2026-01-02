#!/usr/bin/env python3
"""
Fix backend endpoints correctly - ensuring all endpoints are AFTER verify_token definition
"""

with open('/app/app.py', 'r') as f:
    content = f.read()

changes = []

# 1. Fix ProductUpdate class to include tier and duration_days
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

# 2. Fix update_product to handle tier and duration_days
old_update_handler = '''    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.price is not None:
        updates.append("price=:price")
        params["price"] = product.price'''

new_update_handler = '''    if product.name:
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

if old_update_handler in content:
    content = content.replace(old_update_handler, new_update_handler)
    changes.append('Added tier/duration_days handling in update_product')

# 3. Add pricing table sync to create_product
old_create_return = '''    db.commit()
    return {"success": True, "message": "Product created successfully"}

@app.put("/admin/products/{product_id}")'''

new_create_return = '''    db.commit()
    
    # Sync pricing table
    try:
        db.execute(text("""
            INSERT INTO pricing (tier, duration_days, price)
            VALUES (:tier, :days, :price)
            ON CONFLICT (tier, duration_days) DO UPDATE SET price=:price
        """), {
            "tier": product.tier,
            "days": product.duration_days,
            "price": product.price
        })
        db.commit()
    except Exception as e:
        print(f"Warning: Could not sync pricing table: {e}")
    
    return {"success": True, "message": "Product created successfully"}

@app.put("/admin/products/{product_id}")'''

if old_create_return in content:
    content = content.replace(old_create_return, new_create_return)
    changes.append('Added pricing sync to create_product')

# 4. Add pricing table sync to update_product
old_update_return = '''    return {"success": True, "message": "Product updated successfully"}

@app.delete("/admin/products/{product_id}")'''

new_update_return = '''    # Sync pricing table if tier, duration, or price changed
    if any([product.tier is not None, product.duration_days is not None, product.price is not None]):
        try:
            result = db.execute(text("SELECT tier, duration_days, price FROM products WHERE id=:id"), {"id": product_id}).fetchone()
            if result:
                tier = product.tier if product.tier is not None else result[0]
                days = product.duration_days if product.duration_days is not None else result[1]
                price = product.price if product.price is not None else result[2]
                db.execute(text("""
                    INSERT INTO pricing (tier, duration_days, price)
                    VALUES (:tier, :days, :price)
                    ON CONFLICT (tier, duration_days) DO UPDATE SET price=:price
                """), {"tier": tier, "days": days, "price": price})
                db.commit()
        except Exception as e:
            print(f"Warning: Could not sync pricing table: {e}")
    
    return {"success": True, "message": "Product updated successfully"}

@app.delete("/admin/products/{product_id}")'''

if old_update_return in content:
    content = content.replace(old_update_return, new_update_return)
    changes.append('Added pricing sync to update_product')

# 5. Add /admin/licenses endpoint (AFTER existing /list endpoint, BEFORE /trial/generate)
# This is IMPORTANT - must be after verify_token is defined
admin_licenses_endpoint = '''
@app.get("/admin/licenses")
def list_licenses_admin(
    page: int = 1,
    limit: int = 100,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: List all licenses (using JWT auth)"""
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

'''

# Insert after /list endpoint
if '@app.get("/admin/licenses")' not in content:
    # Find /trial/generate which comes after /list
    trial_pos = content.find('@app.post("/trial/generate")')
    if trial_pos > 0:
        content = content[:trial_pos] + admin_licenses_endpoint + content[trial_pos:]
        changes.append('Added /admin/licenses endpoint')

# 6. Add device delete endpoint (AFTER /admin/users, BEFORE LICENSE MANAGEMENT section)
device_delete_endpoint = '''
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

if '@app.delete("/admin/devices/{device_id}")' not in content:
    # Find LICENSE MANAGEMENT section
    license_mgmt_pos = content.find('# ==================== LICENSE MANAGEMENT ====================')
    if license_mgmt_pos > 0:
        content = content[:license_mgmt_pos] + device_delete_endpoint + '\n' + content[license_mgmt_pos:]
        changes.append('Added device delete endpoint')

# Write back
with open('/app/app.py', 'w') as f:
    f.write(content)

# Verify syntax
import ast
try:
    ast.parse(content)
    print('✅ All fixes applied successfully:')
    for change in changes:
        print(f'  - {change}')
    print('✅ Python syntax is valid')
except SyntaxError as e:
    print(f'❌ Syntax error at line {e.lineno}: {e.text}')
    print(f'Error: {e}')
    exit(1)

# Verify verify_token position
lines = content.split('\n')
verify_line = None
for i, line in enumerate(lines):
    if 'def verify_token' in line:
        verify_line = i
        break

if verify_line:
    # Check no endpoint uses verify_token before it's defined
    error_found = False
    for i in range(verify_line):
        if 'Depends(verify_token)' in lines[i]:
            print(f'❌ ERROR: Line {i+1} uses verify_token before definition!')
            error_found = True
    
    if not error_found:
        print('✅ All endpoints correctly positioned after verify_token')
else:
    print('❌ ERROR: verify_token not found!')


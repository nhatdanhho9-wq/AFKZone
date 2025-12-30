#!/usr/bin/env python3
"""Clean fix for admin dashboard - properly positioned after verify_token"""

with open('/app/app.py', 'r') as f:
    content = f.read()

changes = []

# 1. Fix ProductUpdate class
if 'class ProductUpdate(BaseModel):' in content:
    old_class = '''class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    max_devices: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    description: Optional[str] = None'''
    
    new_class = '''class ProductUpdate(BaseModel):
    name: Optional[str] = None
    tier: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[int] = None
    max_devices: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    description: Optional[str] = None'''
    
    if old_class in content:
        content = content.replace(old_class, new_class)
        changes.append('Updated ProductUpdate class')

# 2. Fix PUT endpoint to handle tier and duration_days
if 'def update_product(' in content:
    old_handling = '''    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.price is not None:
        updates.append("price=:price")
        params["price"] = product.price
    if product.max_devices is not None:
        updates.append("max_devices=:devices")
        params["devices"] = product.max_devices
    if product.is_active is not None:
        updates.append("is_active=:active")
        params["active"] = product.is_active
    if product.display_order is not None:
        updates.append("display_order=:order")
        params["order"] = product.display_order
    if product.description is not None:
        updates.append("description=:desc")
        params["desc"] = product.description

    if updates:'''
    
    new_handling = '''    if product.name:
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
        params["price"] = product.price
    if product.max_devices is not None:
        updates.append("max_devices=:devices")
        params["devices"] = product.max_devices
    if product.is_active is not None:
        updates.append("is_active=:active")
        params["active"] = product.is_active
    if product.display_order is not None:
        updates.append("display_order=:order")
        params["order"] = product.display_order
    if product.description is not None:
        updates.append("description=:desc")
        params["desc"] = product.description

    if updates:'''
    
    if old_handling in content:
        content = content.replace(old_handling, new_handling)
        changes.append('Updated PUT endpoint to handle tier and duration_days')

# 3. Add pricing sync to create_product
if 'def create_product(' in content:
    old_commit = '''    db.commit()
    return {"success": True, "message": "Product created successfully"}'''
    
    # Check if sync already exists
    if 'INSERT INTO pricing' not in content[content.find('def create_product('):content.find('def create_product(')+500]:
        new_commit = '''    db.commit()
    
    # Sync pricing table
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
    
    return {"success": True, "message": "Product created successfully"}'''
        
        if old_commit in content:
            content = content.replace(old_commit, new_commit)
            changes.append('Added pricing sync to create_product')

# 4. Add pricing sync to update_product
if 'def update_product(' in content:
    # Check if sync already exists
    if 'pricing' not in content[content.find('def update_product('):content.find('def update_product(')+1000].lower():
        old_return = '''    return {"success": True, "message": "Product updated successfully"}'''
        
        new_return = '''    # Sync pricing table if tier, duration_days, or price changed
        if any([product.tier is not None, product.duration_days is not None, product.price is not None]):
            # Get current product values
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
    
    return {"success": True, "message": "Product updated successfully"}'''
        
        # Find the return statement in update_product function
        update_func_start = content.find('def update_product(')
        update_func_end = content.find('\n@app.', update_func_start)
        if update_func_end > 0:
            func_body = content[update_func_start:update_func_end]
            if old_return in func_body and 'pricing' not in func_body.lower():
                content = content.replace(old_return, new_return)
                changes.append('Added pricing sync to update_product')

# 5. Add /admin/licenses endpoint (after /list, before /trial/generate)
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

# 6. Add device delete endpoint (after /admin/users, before LICENSE MANAGEMENT comment)
if '@app.delete("/admin/devices/{device_id}")' not in content:
    if '# ==================== LICENSE MANAGEMENT ====================' in content:
        pos = content.find('# ==================== LICENSE MANAGEMENT ====================')
        if pos > 0:
            device_delete = '''@app.delete("/admin/devices/{device_id}")
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
            content = content[:pos] + device_delete + '\n' + content[pos:]
            changes.append('Added device delete endpoint')

with open('/app/app.py', 'w') as f:
    f.write(content)

# Verify syntax
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
    print(f'Line {e.lineno}: {e.text}')
    exit(1)


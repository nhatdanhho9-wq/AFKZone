#!/usr/bin/env python3
"""Complete fix for admin dashboard issues"""

with open('/app/app.py', 'r') as f:
    content = f.read()

changes = []

# 1. Fix ProductUpdate to include duration_days and tier
if 'class ProductUpdate(BaseModel):' in content:
    old_update = '''class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    max_devices: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    description: Optional[str] = None'''
    
    new_update = '''class ProductUpdate(BaseModel):
    name: Optional[str] = None
    tier: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[int] = None
    max_devices: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    description: Optional[str] = None'''
    
    if old_update in content:
        content = content.replace(old_update, new_update)
        changes.append('Added tier and duration_days to ProductUpdate')
    
    # Update the PUT endpoint to handle duration_days and tier
    if 'def update_product(product_id: int, product: ProductUpdate' in content:
        old_updates = '''    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.price is not None:
        updates.append("price=:price")
        params["price"] = product.price
    if product.max_devices is not None:
        updates.append("max_devices=:devices")
        params["devices"] = product.max_devices'''
        
        new_updates = '''    if product.name:
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
        params["devices"] = product.max_devices'''
        
        if old_updates in content:
            content = content.replace(old_updates, new_updates)
            changes.append('Updated PUT endpoint to handle tier and duration_days')
        
        # Also sync pricing table when updating
        old_commit = '''    if updates:
        db.execute(text(f"UPDATE products SET {', '.join(updates)} WHERE id=:id"), params)
        db.commit()

    return {"success": True, "message": "Product updated successfully"}'''
        
        new_commit = '''    if updates:
        db.execute(text(f"UPDATE products SET {', '.join(updates)} WHERE id=:id"), params)
        db.commit()
        
        # Sync pricing table if tier or duration_days or price changed
        if product.tier is not None or product.duration_days is not None or product.price is not None:
            # Get current product
            result = db.execute(text("SELECT tier, duration_days, price FROM products WHERE id=:id"), {"id": product_id}).fetchone()
            if result:
                tier = product.tier if product.tier is not None else result[0]
                days = product.duration_days if product.duration_days is not None else result[1]
                price = product.price if product.price is not None else result[2]
                
                # Update or insert pricing
                db.execute(text("""
                    INSERT INTO pricing (tier, duration_days, price)
                    VALUES (:tier, :days, :price)
                    ON CONFLICT (tier, duration_days) DO UPDATE SET price=:price
                """), {"tier": tier, "days": days, "price": price})
                db.commit()

    return {"success": True, "message": "Product updated successfully"}'''
        
        if old_commit in content:
            content = content.replace(old_commit, new_commit)
            changes.append('Added pricing table sync on product update')

# 2. Add /admin/licenses endpoint (using JWT)
if '@app.get("/admin/licenses")' not in content:
    # Find insertion point after /list endpoint
    if '@app.get("/list")' in content:
        pos = content.find('}', content.find('@app.get("/list")'))
        if pos > 0:
            next_line = content.find('\n@app.', pos)
            if next_line > 0:
                licenses_endpoint = '''

@app.get("/admin/licenses")
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
                content = content[:next_line] + licenses_endpoint + content[next_line:]
                changes.append('Added /admin/licenses endpoint with JWT')

# 3. Add device delete endpoint
if '@app.delete("/admin/devices/{device_id}")' not in content:
    # Find insertion point after /admin/users
    if '@app.get("/admin/users")' in content:
        pos = content.find('}', content.find('@app.get("/admin/users")'))
        if pos > 0:
            next_line = content.find('\n# ====================', pos)
            if next_line > 0:
                device_delete_endpoint = '''

@app.delete("/admin/devices/{device_id}")
def delete_device(
    device_id: str,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Remove device from license"""
    # Remove from license_devices
    db.execute(text("""
        DELETE FROM license_devices WHERE device_id=:device_id
    """), {"device_id": device_id})
    
    db.commit()
    
    return {"success": True, "message": f"Device {device_id} removed successfully"}

'''
                content = content[:next_line] + device_delete_endpoint + content[next_line:]
                changes.append('Added device delete endpoint')

with open('/app/app.py', 'w') as f:
    f.write(content)

# Verify
import ast
try:
    ast.parse(content)
    print('✅ All fixes applied successfully:')
    for change in changes:
        print(f'  - {change}')
    print('✅ Python syntax is valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')
    exit(1)


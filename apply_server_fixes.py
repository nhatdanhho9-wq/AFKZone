#!/usr/bin/env python3
"""Apply all server fixes for v2.2.15"""

import re

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix update_product to sync pricing table
old_update = '''@app.put("/admin/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Update product"""
    updates = []
    params = {"id": product_id}

    if product.name:
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

    if updates:
        db.execute(text(f"UPDATE products SET {', '.join(updates)} WHERE id=:id"), params)
        db.commit()

    return {"success": True, "message": "Product updated successfully"}'''

new_update = '''@app.put("/admin/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Update product - syncs pricing table"""
    updates = []
    params = {"id": product_id}
    price_updated = False
    tier = None
    duration_days = None

    # Get current product info
    current = db.execute(text("SELECT tier, duration_days FROM products WHERE id=:id"), {"id": product_id}).fetchone()
    if current:
        tier = current[0]
        duration_days = current[1]

    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.price is not None:
        updates.append("price=:price")
        params["price"] = product.price
        price_updated = True
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
    if product.tier:
        tier = product.tier
        updates.append("tier=:tier")
        params["tier"] = product.tier
    if product.duration_days:
        duration_days = product.duration_days
        updates.append("duration_days=:days")
        params["days"] = product.duration_days

    if updates:
        db.execute(text(f"UPDATE products SET {', '.join(updates)} WHERE id=:id"), params)
        
        # Sync pricing table if price was updated
        if price_updated and tier and duration_days:
            # Check if pricing entry exists
            pricing_exists = db.execute(
                text("SELECT COUNT(*) FROM pricing WHERE tier=:tier AND duration_days=:days"),
                {"tier": tier, "days": duration_days}
            ).scalar()
            
            if pricing_exists > 0:
                # Update existing pricing
                db.execute(
                    text("UPDATE pricing SET price=:price WHERE tier=:tier AND duration_days=:days"),
                    {"price": product.price, "tier": tier, "days": duration_days}
                )
            else:
                # Create new pricing entry
                db.execute(
                    text("INSERT INTO pricing (tier, duration_days, price) VALUES (:tier, :days, :price)"),
                    {"tier": tier, "days": duration_days, "price": product.price}
                )
        
        db.commit()

    return {"success": True, "message": "Product updated successfully"}'''

if old_update in content:
    content = content.replace(old_update, new_update)
    print('✅ Updated update_product endpoint')

# 2. Fix create_product to sync pricing
old_create = '''@app.post("/admin/products")
def create_product(product: ProductCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Create new product"""
    db.execute(text("""
        INSERT INTO products (name, tier, duration_days, price, max_devices, is_active, display_order, description)
        VALUES (:name, :tier, :days, :price, :devices, :active, :order, :desc)
    """), {
        "name": product.name,
        "tier": product.tier,
        "days": product.duration_days,
        "price": product.price,
        "devices": product.max_devices,
        "active": product.is_active,
        "order": product.display_order,
        "desc": product.description
    })
    db.commit()
    return {"success": True, "message": "Product created successfully"}'''

new_create = '''@app.post("/admin/products")
def create_product(product: ProductCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Create new product - syncs pricing table"""
    db.execute(text("""
        INSERT INTO products (name, tier, duration_days, price, max_devices, is_active, display_order, description)
        VALUES (:name, :tier, :days, :price, :devices, :active, :order, :desc)
    """), {
        "name": product.name,
        "tier": product.tier,
        "days": product.duration_days,
        "price": product.price,
        "devices": product.max_devices,
        "active": product.is_active,
        "order": product.display_order,
        "desc": product.description
    })
    
    # Sync pricing table
    pricing_exists = db.execute(
        text("SELECT COUNT(*) FROM pricing WHERE tier=:tier AND duration_days=:days"),
        {"tier": product.tier, "days": product.duration_days}
    ).scalar()
    
    if pricing_exists == 0:
        # Create pricing entry
        db.execute(
            text("INSERT INTO pricing (tier, duration_days, price) VALUES (:tier, :days, :price)"),
            {"tier": product.tier, "days": product.duration_days, "price": product.price}
        )
    
    db.commit()
    return {"success": True, "message": "Product created successfully"}'''

if old_create in content:
    content = content.replace(old_create, new_create)
    print('✅ Updated create_product endpoint')

# 3. Add enable_product endpoint
enable_endpoint = '''
@app.post("/admin/products/{product_id}/enable")
def enable_product(product_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Enable product"""
    db.execute(text("UPDATE products SET is_active=TRUE WHERE id=:id"), {"id": product_id})
    db.commit()
    return {"success": True, "message": "Product enabled successfully"}
'''

# Add after delete_product
if '@app.delete("/admin/products/{product_id}")' in content and '@app.post("/admin/products/{product_id}/enable")' not in content:
    # Find the end of delete_product function
    delete_end = content.find('return {"success": True, "message": "Product deleted successfully"}', content.find('@app.delete("/admin/products/{product_id}")'))
    if delete_end > 0:
        # Find the next @app or def
        next_line = content.find('\n@app.', delete_end)
        if next_line > 0:
            content = content[:next_line] + enable_endpoint + content[next_line:]
            print('✅ Added enable_product endpoint')

# 4. Fix payment/bank/create to use products table as fallback
old_payment = '''price_result = db.execute(text("SELECT price FROM pricing WHERE tier=:tier AND duration_days=:days"), {"tier": req.tier, "days": req.duration_days}).fetchone()
    if not price_result:
        raise HTTPException(status_code=400, detail="Invalid tier or duration")'''

new_payment = '''# Try pricing table first
    price_result = db.execute(
        text("SELECT price FROM pricing WHERE tier=:tier AND duration_days=:days"),
        {"tier": req.tier, "days": req.duration_days}
    ).fetchone()
    
    # If not found, try products table
    if not price_result:
        price_result = db.execute(
            text("SELECT price FROM products WHERE tier=:tier AND duration_days=:days AND is_active=TRUE ORDER BY id DESC LIMIT 1"),
            {"tier": req.tier, "days": req.duration_days}
        ).fetchone()
    
    if not price_result:
        raise HTTPException(status_code=400, detail="Invalid tier or duration")'''

if old_payment in content:
    content = content.replace(old_payment, new_payment)
    print('✅ Updated payment/bank/create endpoint')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ All server fixes applied')


#!/usr/bin/env python3
"""
Fix all issues for v2.2.15:
1. Sync pricing table when product price is updated
2. Add endpoint to enable/disable products
3. Fix admin dashboard endpoints
"""

# This will be applied to app.py on server
FIXES = {
    'update_product_sync_pricing': '''
@app.put("/admin/products/{product_id}")
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

    return {"success": True, "message": "Product updated successfully"}
''',
    
    'create_product_sync_pricing': '''
@app.post("/admin/products")
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
    return {"success": True, "message": "Product created successfully"}
''',
    
    'enable_product': '''
@app.post("/admin/products/{product_id}/enable")
def enable_product(product_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Enable product"""
    db.execute(text("UPDATE products SET is_active=TRUE WHERE id=:id"), {"id": product_id})
    db.commit()
    return {"success": True, "message": "Product enabled successfully"}
''',
    
    'fix_payment_api': '''
# Update /payment/bank/create to use products table if pricing not found
@app.post("/payment/bank/create")
def bank_transfer_create(req: BankTransferRequest, db: Session = Depends(get_db)):
    # Try pricing table first
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
        raise HTTPException(status_code=400, detail="Invalid tier or duration")
    
    price, date_part = price_result[0], datetime.now().strftime("%y%m%d")
    count = (db.execute(text("SELECT COUNT(*) FROM bank_orders WHERE trans_code LIKE :pattern"), {"pattern": f"AFK{req.tier.upper()}{req.duration_days}{date_part}%"}).fetchone() or (0,))[0]
    trans_code = f"AFK{req.tier.upper()}{req.duration_days}{date_part}{count+1:03d}"
    qr_url = f"https://img.vietqr.io/image/{BANK_CONFIG['bank_id']}-{BANK_CONFIG['account_no']}-compact2.png?amount={price}&addInfo={trans_code}&accountName={BANK_CONFIG['account_name']}"
    db.execute(text("INSERT INTO bank_orders (trans_code,device_id,tier,duration_days,amount,bank_account,qr_url,status,created_at) VALUES (:code,:dev,:tier,:dur,:amt,:acc,:qr,'pending',NOW())"), {"code":trans_code,"dev":req.device_id,"tier":req.tier,"dur":req.duration_days,"amt":price,"acc":BANK_CONFIG['account_no'],"qr":qr_url})
    db.commit()
    return {"trans_code":trans_code,"amount":price,"qr_url":qr_url,"bank_info":{"bank_name":"MB Bank","account_no":BANK_CONFIG['account_no'],"account_name":BANK_CONFIG['account_name'],"content":trans_code},"message":f"Chuyển khoản {price:,}đ với nội dung: {trans_code}","expires_in":600}
'''
}

print("✅ Fix scripts ready")


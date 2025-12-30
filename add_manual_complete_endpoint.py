#!/usr/bin/env python3
"""Add manual complete order endpoint for admin"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Add endpoint after other admin endpoints
endpoint_code = '''
@app.post("/admin/orders/{trans_code}/complete")
def manual_complete_order(
    trans_code: str,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Manually complete a bank order"""
    import secrets
    from datetime import datetime, timedelta
    
    # Get order
    order = db.execute(text("SELECT * FROM bank_orders WHERE trans_code=:code"), {"code": trans_code}).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order[8] == 'success':  # status column
        return {"success": False, "message": "Order already completed", "license_key": order[9]}
    
    trans_code_db, device_id, tier, duration_days, amount = order[0], order[1], order[3], order[4], order[5]
    
    # Generate license key
    license_key = f"AFK-{secrets.token_hex(16).upper()}"
    
    # Create license
    expires_at = datetime.now() + timedelta(days=duration_days)
    max_devices = 5 if tier == 'basic' else -1
    
    result = db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, expires_at, is_active, created_at)
        VALUES (:key, :tier, :days, :max, :exp, TRUE, NOW())
        RETURNING id
    """), {"key": license_key, "tier": tier, "days": duration_days, "max": max_devices, "exp": expires_at})
    
    license_id = result.fetchone()[0]
    
    # Activate license for device
    db.execute(text("""
        INSERT INTO license_devices (license_id, device_id, activated_at)
        VALUES (:lid, :did, NOW())
    """), {"lid": license_id, "did": device_id})
    
    # Update order status
    db.execute(text("""
        UPDATE bank_orders 
        SET status='success', license_key=:key, paid_at=NOW()
        WHERE trans_code=:code
    """), {"key": license_key, "code": trans_code})
    
    db.commit()
    
    return {
        "success": True,
        "message": "Order completed successfully",
        "license_key": license_key,
        "tier": tier,
        "duration_days": duration_days
    }

@app.get("/admin/orders")
def get_all_orders(
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 50
):
    """Admin: Get all bank orders"""
    query = "SELECT * FROM bank_orders"
    params = {}
    
    if status:
        query += " WHERE status=:status"
        params["status"] = status
    
    query += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = limit
    
    orders = db.execute(text(query), params).fetchall()
    
    return {
        "orders": [
            {
                "trans_code": o[0],
                "device_id": o[1],
                "tier": o[3],
                "duration_days": o[4],
                "amount": o[5],
                "status": o[8],
                "license_key": o[9],
                "created_at": o[11].isoformat() if o[11] else None,
                "paid_at": o[12].isoformat() if o[12] else None
            }
            for o in orders
        ]
    }

'''

# Find a good place to insert (after other admin endpoints)
marker = '@app.get("/admin/connections")'
if marker in content:
    pos = content.rfind('\n\n', 0, content.find(marker))
    content = content[:pos] + '\n' + endpoint_code + content[pos:]
    print("✅ Added manual complete order endpoints")
else:
    # Fallback: add before health check
    marker2 = '@app.get("/health")'
    if marker2 in content:
        pos = content.find(marker2)
        content = content[:pos] + endpoint_code + '\n\n' + content[pos:]
        print("✅ Added manual complete order endpoints (before health)")

with open('/app/app.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('✅ Syntax valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')


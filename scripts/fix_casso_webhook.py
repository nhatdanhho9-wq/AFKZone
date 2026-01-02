#!/usr/bin/env python3
"""
Fix Casso webhook - use 'orders' table instead of 'payments'
Also add complete NEW license creation logic
"""

import re

def fix_casso_webhook():
    with open('/app/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/app.py.bak_casso', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Find and replace the entire casso webhook function
    old_webhook = '''@app.post("/webhook/casso")
async def casso_webhook_handler(request: Request, db: Session = Depends(get_db)):
    """Casso webhook - handle payment notifications"""
    try:
        body = await request.json()

        # Verify webhook signature if needed
        # ... existing verification code ...

        # Get payment from trans_code in description
        description = body.get("description", "")
        trans_code = None

        # Extract trans_code from description
        if "AFKZONE" in description or "RENEW" in description:
            parts = description.split()
            for part in parts:
                if "AFK" in part or "RENEW" in part:
                    trans_code = part
                    break

        if not trans_code:
            return {"success": False, "error": "Trans code not found"}

        # Get payment record
        payment = db.execute(text(
            "SELECT * FROM payments WHERE trans_code=:code AND status='pending'"
        ), {"code": trans_code}).fetchone()

        if not payment:
            return {"success": False, "error": "Payment not found or already processed"}

        # Check amount matches
        if body.get("amount") != payment[4]:  # amount column
            return {"success": False, "error": "Amount mismatch"}

        payment_type = payment[11] if len(payment) > 11 else "new"  # payment_type column

        if payment_type == "renew":
            # EXTEND existing license
            license_key = payment[7]  # license_key from payment
            duration_days = payment[3]  # duration_days

            license_data = db.execute(text(
                "SELECT expires_at FROM licenses WHERE license_key=:key"
            ), {"key": license_key}).fetchone()

            if license_data:
                current_exp_timestamp = license_data[0]
                current_exp = datetime.fromtimestamp(current_exp_timestamp / 1000)
                new_exp = current_exp + timedelta(days=duration_days)
                new_exp_timestamp = int(new_exp.timestamp() * 1000)

                db.execute(text(
                    "UPDATE licenses SET expires_at=:exp WHERE license_key=:key"
                ), {"exp": new_exp_timestamp, "key": license_key})

                # Update payment status
                db.execute(text(
                    "UPDATE payments SET status='success', completed_at=NOW(), bank_trans_id=:tid WHERE trans_code=:code"
                ), {"tid": body.get("id"), "code": trans_code})

                db.commit()

                return {
                    "success": True,
                    "type": "renew",
                    "license_key": license_key,
                    "new_expires_at": new_exp_timestamp
                }

        else:
            # NEW license (existing code)
            # ... existing new license creation code ...
            pass

    except Exception as e:
        return {"success": False, "error": str(e)}'''
    
    new_webhook = '''@app.post("/webhook/casso")
@app.get("/webhook/casso")  # Allow GET for testing
async def casso_webhook_handler(request: Request, db: Session = Depends(get_db)):
    """Casso webhook - handle payment notifications from bank transfer"""
    import logging
    logging.info("=== CASSO WEBHOOK RECEIVED ===")
    
    try:
        if request.method == "GET":
            return {"status": "webhook active", "message": "Use POST to send payment data"}
        
        body = await request.json()
        logging.info(f"Webhook body: {body}")
        
        # Casso sends data in 'data' array
        transactions = body.get("data", [body])  # Handle both formats
        
        results = []
        for txn in transactions:
            description = txn.get("description", "")
            amount = txn.get("amount", 0)
            
            logging.info(f"Processing: description={description}, amount={amount}")
            
            # Extract order_id from description (format: AFKZONE_xxx or just search for order_id pattern)
            order_id = None
            
            # Try different patterns
            import re
            # Pattern 1: AFKZONE_xxx
            match = re.search(r'AFKZONE[_\\s]*(\\w+)', description, re.IGNORECASE)
            if match:
                order_id = f"AFKZONE_{match.group(1)}"
            
            # Pattern 2: Any alphanumeric code
            if not order_id:
                match = re.search(r'([A-Z0-9]{8,})', description)
                if match:
                    order_id = match.group(1)
            
            if not order_id:
                results.append({"error": "Order ID not found in description", "description": description})
                continue
            
            logging.info(f"Found order_id: {order_id}")
            
            # Find order in database
            order = db.execute(text(
                "SELECT * FROM orders WHERE order_id=:oid AND payment_status='pending'"
            ), {"oid": order_id}).fetchone()
            
            if not order:
                # Try partial match
                order = db.execute(text(
                    "SELECT * FROM orders WHERE order_id LIKE :oid AND payment_status='pending'"
                ), {"oid": f"%{order_id}%"}).fetchone()
            
            if not order:
                results.append({"error": "Order not found or already processed", "order_id": order_id})
                continue
            
            # order columns: id, order_id, device_id, device_fingerprint, tier, duration_days, amount, ...
            order_amount = order[6]  # amount column
            device_id = order[2]
            tier = order[4]
            duration_days = order[5]
            
            # Check amount (allow some tolerance for fees)
            if abs(amount - order_amount) > 1000:  # Allow 1000 VND tolerance
                results.append({"error": f"Amount mismatch: got {amount}, expected {order_amount}", "order_id": order_id})
                continue
            
            # Generate license key
            import secrets
            license_key = f"AFK-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
            
            # Calculate expiry
            from datetime import datetime, timedelta
            expires_at = int((datetime.now() + timedelta(days=duration_days)).timestamp() * 1000)
            
            # Create license
            db.execute(text("""
                INSERT INTO licenses (license_key, tier, max_devices, expires_at, is_active, created_at)
                VALUES (:key, :tier, 2, :exp, TRUE, NOW())
            """), {"key": license_key, "tier": tier, "exp": expires_at})
            
            # Update order
            db.execute(text("""
                UPDATE orders SET payment_status='success', paid_at=NOW(), license_key=:key
                WHERE order_id=:oid
            """), {"key": license_key, "oid": order_id})
            
            db.commit()
            
            logging.info(f"License created: {license_key} for order {order_id}")
            
            results.append({
                "success": True,
                "order_id": order_id,
                "license_key": license_key,
                "expires_at": expires_at
            })
        
        return {"success": True, "results": results}
    
    except Exception as e:
        import traceback
        logging.error(f"Webhook error: {e}")
        logging.error(traceback.format_exc())
        return {"success": False, "error": str(e)}'''
    
    if old_webhook in content:
        content = content.replace(old_webhook, new_webhook)
        print("✅ Replaced casso webhook with fixed version")
    else:
        print("⚠️ Old webhook pattern not found, trying to add new one...")
        # Find @app.post("/webhook/casso") and replace the function
        pattern = r'@app\.post\("/webhook/casso"\).*?(?=\n# Add to app\.py|\n@app\.|$)'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_webhook + '\n', content, flags=re.DOTALL)
            print("✅ Replaced webhook using regex")
        else:
            print("❌ Could not find webhook to replace")
    
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ DONE! Restart container to apply changes")

if __name__ == '__main__':
    fix_casso_webhook()

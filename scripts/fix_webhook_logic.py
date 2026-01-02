#!/usr/bin/env python3
"""Fix webhook to use new license logic"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Find and replace webhook logic
old_webhook = '''        for t in transactions:
            amount,desc,tid = int(t.get("amount",0)),t.get("description","").upper(),t.get("tid","")
            order = db.execute(text("SELECT * FROM bank_orders WHERE trans_code=:code AND status='pending'"),{"code":desc}).fetchone()
            if not order or amount!=order[5]: continue
            key,now,exp = f"AFK-{secrets.token_hex(8).upper()}",datetime.now(),datetime.now()+timedelta(days=order[4])
            db.execute(text("INSERT INTO licenses (license_key,tier,duration_days,activated_at,expires_at,device_id,created_at,is_trial,last_check) VALUES (:key,:tier,:dur,:now,:exp,:dev,:now,FALSE,:now)"),{"key":key,"tier":order[3],"dur":order[4],"now":now,"exp":exp,"dev":order[2]})
            db.execute(text("UPDATE bank_orders SET status='success',license_key=:key,paid_at=:now,bank_tid=:tid WHERE trans_code=:code"),{"key":key,"now":now,"tid":tid,"code":desc})
            db.commit()
            print(f"✅ License: {key} for {order[2]}")'''

new_webhook = '''        for t in transactions:
            amount = int(t.get("amount", 0))
            desc = t.get("description", "").upper()
            tid = t.get("tid", "")
            
            # Try to find trans_code in description
            trans_code = None
            if "AFK" in desc:
                # Extract trans_code from description
                parts = desc.split()
                for part in parts:
                    if part.startswith("AFK"):
                        trans_code = part
                        break
            
            if not trans_code:
                print(f"⚠️ No trans_code found in: {desc}")
                continue
            
            # Find order
            order = db.execute(text("SELECT * FROM bank_orders WHERE trans_code=:code AND status='pending'"), {"code": trans_code}).fetchone()
            
            if not order:
                print(f"⚠️ Order not found or already completed: {trans_code}")
                continue
            
            if amount != order[5]:
                print(f"⚠️ Amount mismatch: expected {order[5]}, got {amount}")
                continue
            
            # Generate license
            license_key = f"AFK-{secrets.token_hex(16).upper()}"
            tier = order[3]
            duration_days = order[4]
            device_id = order[1]
            
            # Create license in licenses table
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
                SET status='success', license_key=:key, paid_at=NOW(), bank_tid=:tid
                WHERE trans_code=:code
            """), {"key": license_key, "tid": tid, "code": trans_code})
            
            db.commit()
            print(f"✅ Webhook completed order {trans_code}: License {license_key} for device {device_id[:20]}...")'''

if old_webhook in content:
    content = content.replace(old_webhook, new_webhook)
    print("✅ Fixed webhook logic")
else:
    print("❌ Webhook code not found or already updated")

with open('/app/app.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('✅ Syntax valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')


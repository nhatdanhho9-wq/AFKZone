#!/usr/bin/env python3
"""
API Update Script v2.2.3
Updates 3 critical endpoints in ~/license-api/app.py for multi-device support
"""

import re
import sys
from pathlib import Path

# New /products endpoint with display formatting
NEW_PRODUCTS = '''@app.get("/products")
def get_products(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all products with formatted display fields"""
    query = "SELECT * FROM products WHERE is_active=TRUE ORDER BY display_order, id" if active_only else "SELECT * FROM products ORDER BY display_order, id"
    results = db.execute(text(query)).fetchall()

    products = []
    for r in results:
        price, max_dev = r[4], r[5]

        # Format display_price
        if price == 0:
            display_price = "Miễn phí"
        elif price >= 1000:
            display_price = f"{price // 1000}.000đ"
        else:
            display_price = f"{price}đ"

        # Format max_devices_display
        if max_dev == -1:
            max_devices_display = "Vô cực"
        else:
            max_devices_display = f"{max_dev} thiết bị"

        products.append({
            "id": r[0],
            "name": r[1],
            "tier": r[2],
            "duration_days": r[3],
            "price": r[4],
            "display_price": display_price,  # NEW!
            "max_devices": r[5],
            "max_devices_display": max_devices_display,  # NEW!
            "is_active": r[6],
            "display_order": r[7],
            "description": r[8]
        })

    return {"products": products}'''

# New /activate endpoint with multi-device support
NEW_ACTIVATE = '''@app.post("/activate")
def activate_license(req: ActivateRequest, db: Session = Depends(get_db)):
    """Activate license - supports multi-device for unlimited tiers"""

    # Get license info
    lic = db.execute(
        text("SELECT license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked FROM licenses WHERE license_key=:key"),
        {"key": req.license_key}
    ).fetchone()

    if not lic:
        raise HTTPException(404, "License không tồn tại")
    if lic[6]:  # is_revoked
        raise HTTPException(403, "License đã thu hồi")

    key, tier, days, act_at, exp_at, max_dev, _ = lic

    # First activation ever
    if not act_at:
        now = datetime.now()
        exp = now + timedelta(days=days)

        db.execute(
            text("UPDATE licenses SET activated_at=:a, expires_at=:e WHERE license_key=:k"),
            {"a": now, "e": exp, "k": key}
        )
        db.execute(
            text("INSERT INTO license_devices (license_key, device_id, activated_at, last_check) VALUES (:k, :d, :a, :a)"),
            {"k": key, "d": req.device_id, "a": now}
        )
        db.commit()

        return {
            "status": "activated",
            "tier": tier,
            "activated_at": now.isoformat(),
            "expires_at": exp.isoformat(),
            "device_limit": max_dev,
            **SERVER_CONFIGS
        }

    # Check expiry
    exp = exp_at if isinstance(exp_at, datetime) else datetime.fromisoformat(str(exp_at))
    if datetime.now() > exp:
        raise HTTPException(410, "Đã hết hạn")

    # Check if this device already activated
    exist = db.execute(
        text("SELECT id FROM license_devices WHERE license_key=:k AND device_id=:d"),
        {"k": key, "d": req.device_id}
    ).fetchone()

    if exist:
        # Device already activated - update last_check
        db.execute(
            text("UPDATE license_devices SET last_check=NOW() WHERE license_key=:k AND device_id=:d"),
            {"k": key, "d": req.device_id}
        )
        db.commit()
        return {
            "status": "active",
            "tier": tier,
            "expires_at": exp.isoformat(),
            "device_limit": max_dev,
            **SERVER_CONFIGS
        }

    # New device - check limit
    if max_dev != -1:  # NOT unlimited
        cnt = db.execute(
            text("SELECT COUNT(*) FROM license_devices WHERE license_key=:k AND is_active=TRUE"),
            {"k": key}
        ).scalar()

        if cnt >= max_dev:
            raise HTTPException(403, f"Đã đủ {max_dev} thiết bị")

    # Activate new device (unlimited OR within limit)
    db.execute(
        text("INSERT INTO license_devices (license_key, device_id, activated_at, last_check) VALUES (:k, :d, NOW(), NOW())"),
        {"k": key, "d": req.device_id}
    )
    db.commit()

    total = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key=:k"),
        {"k": key}
    ).scalar()

    return {
        "status": "activated",
        "tier": tier,
        "expires_at": exp.isoformat(),
        "device_limit": max_dev,
        "devices_count": total,
        **SERVER_CONFIGS
    }'''

# New /check endpoint using license_devices table
NEW_CHECK = '''@app.post("/check")
def check_license(req: ActivateRequest, db: Session = Depends(get_db)):
    """Check if license is valid for this device"""

    # Use license_devices table
    r = db.execute(
        text("""
            SELECT l.tier, l.expires_at, l.max_devices
            FROM licenses l
            JOIN license_devices ld ON l.license_key = ld.license_key
            WHERE l.license_key=:k AND ld.device_id=:d AND ld.is_active=TRUE
        """),
        {"k": req.license_key, "d": req.device_id}
    ).fetchone()

    if not r:
        raise HTTPException(404, "License không hợp lệ")

    exp = r[1] if isinstance(r[1], datetime) else datetime.fromisoformat(str(r[1]))
    if datetime.now() > exp:
        raise HTTPException(410, "Đã hết hạn")

    # Update last_check
    db.execute(
        text("UPDATE license_devices SET last_check=NOW() WHERE license_key=:k AND device_id=:d"),
        {"k": req.license_key, "d": req.device_id}
    )
    db.commit()

    return {
        "status": "active",
        "tier": r[0],
        "expires_at": exp.isoformat(),
        "device_limit": r[2],
        **SERVER_CONFIGS
    }'''


def find_function_block(content, function_name):
    """Find the complete function block including decorator"""
    # Pattern to match @app.METHOD("path") followed by def function_name
    pattern = rf'(@app\.\w+\([^)]*\)\s*\n\s*def\s+{function_name}\s*\([^)]*\):.*?)(?=\n@app\.|$)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1), match.start(1), match.end(1)
    return None, None, None


def update_app_py(file_path):
    """Update the app.py file with new endpoint implementations"""

    # Read original file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    updates_made = []

    # Update /products endpoint
    print("Updating /products endpoint...")
    old_block, start, end = find_function_block(content, 'get_products')
    if old_block:
        content = content[:start] + NEW_PRODUCTS + content[end:]
        updates_made.append('get_products')
        print("✓ Updated get_products")
    else:
        print("✗ Could not find get_products function")

    # Update /activate endpoint
    print("Updating /activate endpoint...")
    old_block, start, end = find_function_block(content, 'activate_license')
    if old_block:
        content = content[:start] + NEW_ACTIVATE + content[end:]
        updates_made.append('activate_license')
        print("✓ Updated activate_license")
    else:
        print("✗ Could not find activate_license function")

    # Update /check endpoint
    print("Updating /check endpoint...")
    old_block, start, end = find_function_block(content, 'check_license')
    if old_block:
        content = content[:start] + NEW_CHECK + content[end:]
        updates_made.append('check_license')
        print("✓ Updated check_license")
    else:
        print("✗ Could not find check_license function")

    if not updates_made:
        print("\n❌ No functions were updated. Check function names.")
        return False

    # Write updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ Successfully updated {len(updates_made)}/3 endpoints: {', '.join(updates_made)}")
    return True


def main():
    app_py_path = Path.home() / 'license-api' / 'app.py'

    if not app_py_path.exists():
        print(f"❌ Error: {app_py_path} not found")
        sys.exit(1)

    print(f"Updating {app_py_path}...")
    print("=" * 60)

    success = update_app_py(app_py_path)

    if success:
        print("\n" + "=" * 60)
        print("✅ API update complete!")
        print("\nNext steps:")
        print("1. docker cp ~/license-api/app.py afkzone-license-api:/app/app.py")
        print("2. docker restart afkzone-license-api")
        print("3. curl https://api.afkzone.cloud/products | python3 -m json.tool")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

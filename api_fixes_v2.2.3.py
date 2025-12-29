# API Fixes for v2.2.3 - Complete Multi-Device & Dynamic Pricing
# Apply this to ~/license-api/app.py

# ============================================
# 1. NEW /products endpoint with display fields
# ============================================

NEW_PRODUCTS_ENDPOINT = '''
@app.get("/products")
def get_products(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all products with formatted display fields"""
    query = "SELECT * FROM products WHERE is_active=TRUE ORDER BY display_order, id" if active_only else "SELECT * FROM products ORDER BY display_order, id"
    results = db.execute(text(query)).fetchall()

    products = []
    for r in results:
        price = r[4]
        max_devices = r[5]

        # Format display_price
        if price == 0:
            display_price = "Miễn phí"
        elif price >= 1000000:
            display_price = f"{price // 1000000}.{(price % 1000000) // 100000}M"
        elif price >= 1000:
            display_price = f"{price // 1000}.000đ"
        else:
            display_price = f"{price}đ"

        # Format max_devices_display
        if max_devices == -1:
            max_devices_display = "Vô cực"
        elif max_devices == 1:
            max_devices_display = "1 thiết bị"
        else:
            max_devices_display = f"{max_devices} thiết bị"

        products.append({
            "id": r[0],
            "name": r[1],
            "tier": r[2],
            "duration_days": r[3],
            "price": r[4],
            "display_price": display_price,
            "max_devices": r[5],
            "max_devices_display": max_devices_display,
            "is_active": r[6],
            "display_order": r[7],
            "description": r[8]
        })

    return {"products": products}
'''

# ============================================
# 2. NEW /activate endpoint with multi-device
# ============================================

NEW_ACTIVATE_ENDPOINT = '''
@app.post("/activate")
def activate_license(req: ActivateRequest, db: Session = Depends(get_db)):
    """Activate license - supports multi-device for unlimited tiers"""

    # Get license info
    license_data = db.execute(
        text("SELECT license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked FROM licenses WHERE license_key=:key"),
        {"key": req.license_key}
    ).fetchone()

    if not license_data:
        raise HTTPException(status_code=404, detail="License key không tồn tại")

    if license_data[6]:
        raise HTTPException(status_code=403, detail="License đã bị thu hồi")

    license_key, tier, duration_days, activated_at, expires_at, max_devices, _ = license_data

    # First activation
    if not activated_at:
        now = datetime.now()
        new_expires = now + timedelta(days=duration_days)

        db.execute(
            text("UPDATE licenses SET activated_at=:act, expires_at=:exp WHERE license_key=:key"),
            {"act": now, "exp": new_expires, "key": license_key}
        )

        db.execute(
            text("INSERT INTO license_devices (license_key, device_id, activated_at, last_check) VALUES (:key, :dev, :act, :act)"),
            {"key": license_key, "dev": req.device_id, "act": now}
        )

        db.commit()

        return {
            "status": "activated",
            "tier": tier,
            "activated_at": now.isoformat(),
            "expires_at": new_expires.isoformat(),
            "device_limit": max_devices,
            "message": f"Activated. Limit: {'Unlimited' if max_devices == -1 else max_devices}",
            **SERVER_CONFIGS
        }

    # Check expiry
    exp_date = expires_at if isinstance(expires_at, datetime) else datetime.fromisoformat(str(expires_at))
    if datetime.now() > exp_date:
        raise HTTPException(status_code=410, detail="License đã hết hạn")

    # Check if device already activated
    existing = db.execute(
        text("SELECT id FROM license_devices WHERE license_key=:key AND device_id=:dev"),
        {"key": license_key, "dev": req.device_id}
    ).fetchone()

    if existing:
        db.execute(
            text("UPDATE license_devices SET last_check=NOW() WHERE license_key=:key AND device_id=:dev"),
            {"key": license_key, "dev": req.device_id}
        )
        db.commit()
        return {
            "status": "active",
            "tier": tier,
            "expires_at": exp_date.isoformat(),
            "device_limit": max_devices,
            **SERVER_CONFIGS
        }

    # New device - check limit
    if max_devices != -1:
        count = db.execute(
            text("SELECT COUNT(*) FROM license_devices WHERE license_key=:key AND is_active=TRUE"),
            {"key": license_key}
        ).scalar()

        if count >= max_devices:
            raise HTTPException(403, f"Đã đủ {max_devices} thiết bị")

    # Activate new device
    db.execute(
        text("INSERT INTO license_devices (license_key, device_id, activated_at, last_check) VALUES (:key, :dev, NOW(), NOW())"),
        {"key": license_key, "dev": req.device_id}
    )
    db.commit()

    total = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key=:key"),
        {"key": license_key}
    ).scalar()

    return {
        "status": "activated",
        "tier": tier,
        "expires_at": exp_date.isoformat(),
        "device_limit": max_devices,
        "devices_count": total,
        "message": f"Activated {total}/{max_devices if max_devices > 0 else 'Unlimited'}",
        **SERVER_CONFIGS
    }
'''

# ============================================
# 3. NEW /check endpoint
# ============================================

NEW_CHECK_ENDPOINT = '''
@app.post("/check")
def check_license(req: ActivateRequest, db: Session = Depends(get_db)):
    """Check if license is valid for this device"""

    # Check in license_devices table
    result = db.execute(
        text("""
            SELECT l.tier, l.expires_at, l.max_devices
            FROM licenses l
            JOIN license_devices ld ON l.license_key = ld.license_key
            WHERE l.license_key=:key AND ld.device_id=:dev AND ld.is_active=TRUE
        """),
        {"key": req.license_key, "dev": req.device_id}
    ).fetchone()

    if not result:
        raise HTTPException(404, "License không hợp lệ cho thiết bị này")

    exp_date = result[1] if isinstance(result[1], datetime) else datetime.fromisoformat(str(result[1]))
    if datetime.now() > exp_date:
        raise HTTPException(410, "License đã hết hạn")

    # Update last_check
    db.execute(
        text("UPDATE license_devices SET last_check=NOW() WHERE license_key=:key AND device_id=:dev"),
        {"key": req.license_key, "dev": req.device_id}
    )
    db.commit()

    return {
        "status": "active",
        "tier": result[0],
        "expires_at": exp_date.isoformat(),
        "device_limit": result[2],
        **SERVER_CONFIGS
    }
'''

print("""
========================================
API Fixes v2.2.3 - Summary
========================================

Changes:
1. /products - Added display_price & max_devices_display
2. /activate - Multi-device support with proper limits
3. /check - Uses license_devices table

To apply:
- Manually update ~/license-api/app.py
- Or use sed/awk to replace endpoints
- Restart container: docker restart afkzone-license-api

Files:
- Backup: app.py.backup_before_fix_all
- Database: license_devices table created
""")

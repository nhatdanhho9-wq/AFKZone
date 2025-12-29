# 📋 MANUAL API UPDATE v2.2.3 - Complete Guide

**Vấn đề:** Auto-update app.py quá phức tạp do file lớn (500+ lines)

**Giải pháp:** Manual update 3 endpoints quan trọng

---

## ✅ Đã làm xong:

1. ✅ **Database Migration**
   - Created table `license_devices`
   - Added column `max_devices` to `licenses`
   - Migrated 3 existing devices

2. ✅ **Backup**
   - `~/license-api/app.py.backup_before_fix_all`

---

## 🔧 CÒN PHẢI LÀM (Manual):

### Option A: Quick Fix - Replace 3 Endpoints

SSH vào Ubuntu và edit file:
```bash
ssh ubuntu
cd ~/license-api
nano app.py  # Hoặc vim app.py
```

**Tìm và thay thế 3 endpoints sau:**

#### 1. `/products` endpoint (khoảng dòng 67-84)

**TÌM:**
```python
@app.get("/products")
def get_products(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all products (public API - for app)"""
    query = "SELECT * FROM products WHERE is_active=TRUE ORDER BY display_order, id" if active_only else "SELECT * FROM products ORDER BY display_order, id"
    results = db.execute(text(query)).fetchall()
    return {
        "products": [
            {
                "id": r[0],
                "name": r[1],
                "tier": r[2],
                "duration_days": r[3],
                "price": r[4],
                "max_devices": r[5],
                "is_active": r[6],
                "display_order": r[7],
                "description": r[8]
            } for r in results
        ]
    }
```

**THAY BẰNG:**
```python
@app.get("/products")
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

    return {"products": products}
```

---

#### 2. `/activate` endpoint (khoảng dòng 50-85)

**THAY TOÀN BỘ function `activate_license` BẰNG:**

```python
@app.post("/activate")
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
    }
```

---

#### 3. `/check` endpoint (khoảng dòng 90-100)

**THAY TOÀN BỘ function `check_license` BẰNG:**

```python
@app.post("/check")
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
    }
```

---

### Sau khi sửa xong:

```bash
# 1. Copy file vào container
docker cp ~/license-api/app.py afkzone-license-api:/app/app.py

# 2. Restart container
docker restart afkzone-license-api

# 3. Test API
curl https://api.afkzone.cloud/products | python3 -m json.tool
```

---

### Option B: Script Tự Động (Nếu Option A quá lâu)

```bash
# Download fixed app.py from Windows PC
# Copy từ D:\rustdesk-dev\api_fixed_complete.py (tôi sẽ tạo)

scp api_fixed_complete.py automation@172.26.31.115:~/license-api/app.py
ssh ubuntu "docker cp ~/license-api/app.py afkzone-license-api:/app/app.py && docker restart afkzone-license-api"
```

---

## ✅ Kiểm tra sau khi update:

```bash
# 1. Check container logs
docker logs afkzone-license-api --tail 50

# 2. Test products endpoint
curl https://api.afkzone.cloud/products

# Expected output phải có:
# {
#   "products": [
#     {
#       ...
#       "display_price": "Miễn phí",  ← MỚI!
#       "max_devices_display": "Vô cực"  ← MỚI!
#     }
#   ]
# }

# 3. Test unlimited license activate
curl -X POST https://api.afkzone.cloud/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "AFK-UNLIMITED-8EDE71B4E8ADFB8B", "device_id": "test_device_2"}'

# Expected: Status 200 (không bị reject nữa!)
```

---

## 📱 Sau đó: Update Flutter Code

(Sẽ làm tiếp sau khi API ready)

---

**Status:** ⏳ Chờ manual update API hoặc tôi tạo file hoàn chỉnh?

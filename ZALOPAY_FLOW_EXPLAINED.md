# 💳 ZaloPay Payment Flow - AFK Zone v2.0.6

## 🎯 Current Implementation (Backend Only)

### 1. Create Payment Order

**User Action:**
```
User chọn: Pro - 30 ngày (100.000đ)
```

**App Request:**
```http
POST https://api.afkzone.cloud/payment/create
Content-Type: application/json

{
  "tier": "pro",
  "duration_days": 30,
  "device_id": "abc123..."
}
```

**Backend Process:**
```python
# 1. Lookup price from database
price = 100000  # Pro 30 days

# 2. Create ZaloPay order
trans_id = "251228_1735366800"  # yymmdd_timestamp
order = {
  "app_id": 2553,
  "app_trans_id": trans_id,
  "amount": 100000,
  "item": "AFK Zone pro 30d",
  "callback_url": "https://api.afkzone.cloud/payment/callback"
}

# 3. Generate HMAC signature
mac = hmac_sha256(order_data, zalopay_key1)

# 4. Send to ZaloPay
response = POST https://sb-openapi.zalopay.vn/v2/create

# 5. Save order to database
INSERT INTO orders (order_id, tier, amount, status='pending')
```

**Response to App:**
```json
{
  "order_id": "251228_1735366800",
  "amount": 100000,
  "zp_trans_token": "abc...",
  "order_url": "https://sbgateway.zalopay.vn/openinapp?order=..."
}
```

---

### 2. User Payment

**User Action:**
```
1. App mở order_url trong browser/ZaloPay app
2. User login ZaloPay
3. User confirm payment 100.000đ
4. User pay thành công
```

**❌ PROBLEM:** App không biết user đã thanh toán!

---

### 3. ZaloPay Webhook Callback

**ZaloPay → Backend:**
```http
POST https://api.afkzone.cloud/payment/callback
Content-Type: application/json
X-Signature: hmac_sha256(...)

{
  "data": "{...}",  # Encrypted order data
  "mac": "signature..."
}
```

**Backend Process:**
```python
# 1. Verify signature
if hmac_sha256(data) != mac:
    return error

# 2. Parse order data
order_id = "251228_1735366800"
device_id = "abc123..."
tier = "pro"
duration = 30

# 3. Auto-generate license key
license_key = "AFK-" + random_hex(8)  # AFK-24319667E12FC237
expires = now + 30 days

# 4. Save to database
INSERT INTO licenses (
  license_key,
  tier='pro',
  device_id='abc123...',
  expires_at=now+30days,
  activated_at=now
)

# 5. Update order status
UPDATE orders SET status='success', license_key='AFK-2431...'

# 6. ❌ MISSING: Notify user!
# Should send FCM notification or SMS
```

**Response to ZaloPay:**
```json
{
  "return_code": 1,
  "return_message": "success"
}
```

---

## ❌ Current Problems

### Problem 1: User không biết license key

**Flow hiện tại:**
```
User pay → Backend tạo key → Lưu DB → ???
                                    ↓
                          User KHÔNG nhận được key!
```

**Workaround:**
- User phải inbox Zalo: 0823333374
- Admin query DB: `SELECT license_key FROM orders WHERE device_id='...'`
- Admin gửi key qua Zalo

### Problem 2: Flutter chưa có UI payment

**Thiếu:**
- Không có màn hình chọn tier/duration
- Không có button "Mua License"
- Không có logic call `/payment/create`
- Không có logic mở `order_url`

### Problem 3: Không có FCM notification

**Thiếu:**
- Firebase credentials chưa có
- Backend không gửi notification khi payment success
- App không receive notification

---

## ✅ Complete Flow (Cần Implement)

### Phase 1: Add Payment UI (Flutter)

```dart
// 1. Payment selection screen
class PaymentPage extends StatelessWidget {
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Tier selection: Basic, Pro, Enterprise
        TierCard(tier: 'pro', price: '100k/month'),

        // Duration selection: 30, 90, 180, 365 days
        DurationSelector(),

        // Pay button
        ElevatedButton(
          onPressed: () async {
            // Call API
            final result = await LicenseService.createPayment(
              tier: 'pro',
              durationDays: 30,
              deviceId: deviceId,
            );

            // Open ZaloPay
            await launch(result['order_url']);

            // ⏳ Wait for payment...
            showDialog(
              child: Text('Đang chờ thanh toán...')
            );
          },
          child: Text('Thanh toán ZaloPay - 100.000đ')
        )
      ]
    );
  }
}
```

### Phase 2: Add FCM Notification

**Backend (payment_callback):**
```python
# After creating license key
import firebase_admin
from firebase_admin import messaging

# Get FCM token for device
fcm_token = db.execute(
  "SELECT fcm_token FROM fcm_tokens WHERE device_id=:dev",
  {"dev": device_id}
).fetchone()[0]

# Send notification
message = messaging.Message(
  notification=messaging.Notification(
    title='Thanh toán thành công!',
    body=f'License: {license_key}\nHạn dùng: 30 ngày'
  ),
  data={
    'type': 'payment_success',
    'license_key': license_key,
    'tier': 'pro',
    'expires_at': expires.isoformat()
  },
  token=fcm_token
)

messaging.send(message)
```

**Flutter (receive notification):**
```dart
// Listen for FCM messages
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  if (message.data['type'] == 'payment_success') {
    final licenseKey = message.data['license_key'];

    // Auto-activate license
    await LicenseService.activateLicense(licenseKey, deviceId);

    // Show success dialog
    showDialog(
      child: AlertDialog(
        title: Text('Thanh toán thành công!'),
        content: Text('License: $licenseKey\nĐã kích hoạt tự động!'),
      )
    );
  }
});
```

### Phase 3: Add Polling Fallback

**Nếu FCM fail, app polling:**
```dart
// After opening ZaloPay order_url
Timer.periodic(Duration(seconds: 5), (timer) async {
  // Check payment status
  final result = await http.get(
    'https://api.afkzone.cloud/payment/status?order_id=$orderId'
  );

  if (result['status'] == 'success') {
    timer.cancel();
    final licenseKey = result['license_key'];
    await LicenseService.activateLicense(licenseKey, deviceId);
    showSuccessDialog(licenseKey);
  }

  // Timeout after 10 minutes
  if (timer.tick > 120) {  // 5s * 120 = 10 min
    timer.cancel();
    showTimeoutDialog();
  }
});
```

---

## 🎯 Recommended Implementation Order

### v2.0.6 (Current - Phase 1)
- ✅ Backend API complete
- ❌ **Manual process:** User inbox Zalo để nhận key

### v2.0.7 (Next)
- [ ] Add Firebase/FCM credentials
- [ ] Implement FCM notification on payment success
- [ ] Add Flutter payment UI
- [ ] Test end-to-end flow

### v2.0.8 (Future)
- [ ] Add SMS notification (backup)
- [ ] Add email notification
- [ ] Add in-app order history
- [ ] Add refund handling

---

## 💡 Quick Fix for v2.0.6

**Add endpoint to check payment status:**

```python
@app.get("/payment/status")
def payment_status(order_id: str, db: Session = Depends(get_db)):
    order = db.execute(
        text("SELECT * FROM orders WHERE order_id=:id"),
        {"id": order_id}
    ).fetchone()

    if not order:
        raise HTTPException(404, "Order not found")

    return {
        "order_id": order_id,
        "status": order[8],  # payment_status
        "license_key": order[9] if order[8] == "success" else None,
        "tier": order[3],
        "amount": order[6]
    }
```

**Flutter polling:**
```dart
// After opening ZaloPay
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => PaymentWaitingPage(orderId: orderId)
  )
);
```

---

## 📊 Database Schema

**Orders table:**
```sql
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(50) UNIQUE,      -- ZaloPay trans_id
  device_id VARCHAR(255),            -- User device
  tier VARCHAR(20),                   -- basic/pro/enterprise
  duration_days INTEGER,              -- 30/90/180/365
  amount INTEGER,                     -- Price in VND
  zp_trans_token TEXT,                -- ZaloPay token
  zp_order_url TEXT,                  -- Payment URL
  payment_status VARCHAR(20),         -- pending/success/failed
  license_key VARCHAR(50),            -- Generated after payment
  created_at TIMESTAMP,
  paid_at TIMESTAMP
);
```

**Query payment for device:**
```sql
SELECT license_key, tier, paid_at
FROM orders
WHERE device_id = 'abc123...'
  AND payment_status = 'success'
ORDER BY paid_at DESC
LIMIT 1;
```

---

## 🔒 Security Notes

1. **HMAC Signature:** All ZaloPay requests verified với key2
2. **Order ID:** Unique per transaction (yymmdd_timestamp)
3. **Device ID:** Tied to license key (prevent sharing)
4. **Callback URL:** HTTPS only, public accessible
5. **Idempotency:** Callback check `order.status != 'success'` để avoid duplicate

---

**Current Status:** Backend hoàn thành, cần implement Flutter UI + FCM trong v2.0.7.

**Manual workaround:** User inbox Zalo: 0823333374 sau khi thanh toán.

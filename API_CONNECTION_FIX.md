# API CONNECTION FIX - v2.2.1

**Ngày:** 29/12/2025
**Vấn đề:** App không kết nối được API (Connection refused port 57326)

---

## ✅ PHÂN TÍCH

### API Server Status:
```
✅ Docker: afkzone-license-api - UP
✅ Port: 443 (HTTPS)
✅ SSL: Valid
✅ Endpoints working:
   - POST /trial/check → 200 OK
   - GET /products → 200 OK
   - POST /trial/generate → Should work
```

### Flutter Code:
```
✅ payment_service.dart: API_URL = 'https://api.afkzone.cloud'
✅ license_service.dart: API_URL = 'https://api.afkzone.cloud'
✅ custom_config.json: "api": "https://api.afkzone.cloud"
```

**Kết luận:** Code ĐÚNG, API server OK!

---

## 🔍 NGUYÊN NHÂN

### Port 57326 là gì?

**Port 57326 = OUTGOING ephemeral port (bình thường)**
- Khi app kết nối ra ngoài, OS tự động chọn random port (49152-65535)
- App opens port 57326 (local) → connects to api.afkzone.cloud:443 (remote)

### Lỗi "Connection refused" nghĩa là:
1. **App đang dùng cache cũ** hoặc code cũ
2. **APK build từ version trước** khi chưa có API fix
3. **Device có VPN/Proxy** chặn HTTPS
4. **Firewall** block outgoing HTTPS

---

## 🔧 GIẢI PHÁP

### Option 1: Uninstall app cũ + Install v2.2.1 mới

```bash
# 1. Uninstall app hiện tại
adb uninstall com.afkzone.remote

# 2. Download APK v2.2.1 từ GitHub
# https://github.com/nhatdanhho9-wq/rustdesk/releases/tag/v2.2.1

# 3. Install APK mới
adb install afkzone-v2.2.1-aarch64.apk

# 4. Clear app data
adb shell pm clear com.afkzone.remote
```

### Option 2: Build local và test

```bash
cd D:\rustdesk-dev\flutter

# 1. Clean cache
flutter clean
flutter pub get

# 2. Build APK
flutter build apk --release

# 3. Install
adb install build/app/outputs/flutter-apk/app-release.apk
```

### Option 3: Test trên device/emulator khác

Thử device hoặc emulator khác để loại trừ vấn đề:
- VPN/Proxy trên device hiện tại
- Firewall settings
- Network restrictions

---

## 🧪 TEST API MANUALLY

### Test từ device:

```bash
# Option A: Termux on Android
pkg install curl
curl https://api.afkzone.cloud/products

# Option B: Browser on Android
# Open: https://api.afkzone.cloud/products
# Should see JSON response
```

### Expected response:
```json
{
  "products": [
    {
      "id": 1,
      "name": "Basic 7 ngày",
      "tier": "basic",
      "duration_days": 7,
      "price": 1000,
      "max_devices": 2,
      ...
    }
  ]
}
```

---

## 📊 DEBUGGING STEPS

### 1. Check APK version

```bash
# Extract APK info
adb shell dumpsys package com.afkzone.remote | grep versionName

# Should show: v2.2.1
```

### 2. Check API URL in app

Add debug logging:

```dart
// In payment_screen.dart hoặc license_service.dart
print('API_URL: ${LicenseService.API_URL}');  // Should print: https://api.afkzone.cloud
```

### 3. Check network permissions

`flutter/android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
```

### 4. Check for HTTPS certificate issues

```dart
// Temporarily bypass SSL (ONLY FOR TESTING!)
// In http.post calls, add:
HttpClient httpClient = HttpClient()
  ..badCertificateCallback = ((X509Certificate cert, String host, int port) => true);
```

---

## ✅ RECOMMENDED FIX

**Bước 1:** Uninstall app hiện tại
```
Settings → Apps → AFK Zone → Uninstall
```

**Bước 2:** Download v2.2.1 APK từ GitHub Releases
```
https://github.com/nhatdanhho9-wq/rustdesk/releases/tag/v2.2.1
→ Download: afkzone-v2.2.1-aarch64.apk
```

**Bước 3:** Install APK mới
```
Tap APK file → Install
```

**Bước 4:** Test lại
```
Open app → Thử "DÙNG THỬ 7 NGÀY MIỄN PHÍ"
→ Should work now!
```

---

## 🎯 NEXT STEPS (SAU KHI FIX)

1. ✅ Test trial generation
2. ✅ Test payment flow
3. ✅ Test license activation
4. 🔄 Add dynamic pricing (update payment_screen.dart)
5. 🔄 Add notification bell
6. 🔄 Add "Gia hạn" button

---

**Status:** Đang chờ test v2.2.1 APK mới từ GitHub
**Expected:** API connection should work after reinstall

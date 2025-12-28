# ⚠️ Fix "AFK Zone Input - Controlled by restricted setting"

## 🔍 Nguyên nhân

Android 13+ **block accessibility services** từ apps cài ngoài Google Play Store để bảo vệ user khỏi malware.

**AFK Zone Input** là Accessibility Service (cần cho remote control), nên bị block.

---

## ✅ Giải pháp

### Option 1: Enable qua Settings (Khuyến nghị)

1. **Mở Settings** → Apps → AFK Zone
2. Scroll xuống **"Special app access"** hoặc **"Advanced"**
3. Tìm **"Restricted settings"**
4. Toggle ON **"Allow restricted settings"**
5. Quay lại **Settings → Accessibility**
6. Enable **"AFK Zone Input"**

### Option 2: Enable qua ADB (Developer)

```bash
# Connect phone via USB, enable USB debugging
adb devices

# Grant accessibility permission
adb shell settings put secure enabled_accessibility_services com.carriez.flutter_hbb/.InputService

# Grant restricted settings exemption
adb shell pm grant com.carriez.flutter_hbb android.permission.BIND_ACCESSIBILITY_SERVICE
```

### Option 3: Tạm thời tắt Device Admin (Nếu có)

Nếu phone có Device Admin/MDM:
1. Settings → Security → Device admin apps
2. Tắt tất cả device admin
3. Enable AFK Zone Input
4. Bật lại device admin

---

## 📱 Screenshot Guide

**Step 1:** Settings → Apps → AFK Zone → Advanced
**Step 2:** "Allow restricted settings" → Toggle ON
**Step 3:** Settings → Accessibility → AFK Zone Input → Toggle ON

---

## ⚙️ Code Changes (Đã áp dụng)

Updated `accessibility_service_config.xml`:
```xml
<accessibility-service
    android:accessibilityFlags="flagDefault|flagRequestAccessibilityButton"
    android:settingsActivity=".MainActivity"/>
```

Updated description:
```
"Allow remote control of your device through AFK Zone when screen sharing is active"
```

---

## 🎯 Alternative: Sign APK with System Certificate

Để bypass hoàn toàn (cần root):
1. Sign APK với system certificate
2. Install as system app
3. Accessibility auto-enabled

**Không khuyến nghị** - Chỉ dùng cho enterprise deployment.

---

## 💡 User Communication

**Thông báo trong app:**
```
⚠️ Accessibility Service bị chặn bởi Android 13+

Để sử dụng remote control:
1. Mở Settings → Apps → AFK Zone
2. Bật "Allow restricted settings"
3. Quay lại Accessibility và bật "AFK Zone Input"

Hoặc liên hệ hỗ trợ: Zalo 0823333374
```

---

## 🔧 Testing

**Test trên:**
- ✅ Android 11, 12 - Không có vấn đề
- ⚠️ Android 13, 14 - Cần enable qua Settings
- ⚠️ Xiaomi MIUI 14+ - Cần thêm "Autostart" permission
- ⚠️ Samsung One UI 5+ - Cần disable "Restricted mode"

---

Vấn đề này **không thể fix 100% bằng code** vì là Android security policy.

Best practice: Hướng dẫn user enable trong first-time setup tutorial.

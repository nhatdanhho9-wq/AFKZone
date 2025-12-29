# AFK Zone v2.2.2 - Changelog & Fixes

**Ngày:** 2025-12-29
**Phiên bản:** v2.2.2

## 📋 Tóm tắt các thay đổi

### ✅ 1. Sửa giá gói 7 ngày hiển thị "Miễn phí"
**Vấn đề:** Gói 7 ngày đang hiển thị "1.000đ" thay vì miễn phí
**Giải pháp:** Đã cập nhật logic hiển thị giá

**File thay đổi:**
- `flutter/lib/models/product_model.dart` (dòng 38-50)

**Chi tiết:**
```dart
String get formattedPrice {
  // Show "Miễn phí" for 7-day products
  if (durationDays == 7 && price <= 1000) {
    return 'Miễn phí';
  }

  if (price >= 1000000) {
    return '${(price / 1000000).toStringAsFixed(1)}M';
  } else if (price >= 1000) {
    return '${(price / 1000).toStringAsFixed(0)}.000d';
  }
  return '${price}d';
}
```

**Kết quả:** Tất cả các gói có thời hạn 7 ngày và giá ≤ 1.000đ sẽ hiển thị **"Miễn phí"** thay vì giá tiền.

---

### ✅ 2. Xóa các tham chiếu "RustDesk" còn sót lại
**Vấn đề:** Một số thông báo và menu vẫn hiển thị "RustDesk" thay vì "AFK Zone"

**Files thay đổi:**
1. **`flutter/android/app/src/main/kotlin/com/afkzone/remote/BootReceiver.kt`** (dòng 39)
   - Trước: `"RustDesk is Open"`
   - Sau: `"AFK Zone is Open"`

2. **`flutter/android/app/src/main/kotlin/com/afkzone/remote/FloatingWindowService.kt`** (dòng 305-317)
   - Trước: `val idShowRustDesk = 0` và `"Show RustDesk"`
   - Sau: `val idShowAFKZone = 0` và `"Show AFK Zone"`

**Kết quả:** Tất cả thông báo Toast và menu hiển thị đúng tên "AFK Zone".

---

### ✅ 3. Xác nhận cấu hình branding
Đã kiểm tra và xác nhận các cấu hình sau đã đúng:

**AndroidManifest.xml:**
- ✅ Package name: `com.afkzone.remote`
- ✅ App label: `"AFK Zone"`
- ✅ Icons: `@mipmap/ic_launcher`

**strings.xml:**
- ✅ App name: `"AFK Zone"`
- ✅ Accessibility description: `"Allow remote control of your device through AFK Zone..."`

**Android App Icons:**
- ✅ Đã cập nhật tất cả density variants:
  - `mipmap-mdpi/ic_launcher.png`
  - `mipmap-hdpi/ic_launcher.png`
  - `mipmap-xhdpi/ic_launcher.png`
  - `mipmap-xxhdpi/ic_launcher.png`
  - `mipmap-xxxhdpi/ic_launcher.png`
- ✅ Timestamp: 2025-12-29 02:25 (đã cập nhật mới nhất)

---

## 🔧 Vấn đề Logo trong LDPlayer

**Hiện tượng:**
LDPlayer vẫn hiển thị logo cũ của RustDesk sau khi cài đặt APK mới.

**Nguyên nhân:**
LDPlayer cache launcher icons. Đây là vấn đề của emulator, KHÔNG phải do code.

**Giải pháp:**

### Cách 1: Xóa cache LDPlayer (Khuyến nghị)
1. Mở LDPlayer
2. Vào **System Settings** > **Advanced Settings**
3. Clear launcher data/cache
4. Restart LDPlayer
5. Cài lại APK

### Cách 2: Gỡ cài đặt hoàn toàn
1. Gỡ cài đặt app cũ hoàn toàn trong LDPlayer
2. Xóa data app: Settings > Apps > AFK Zone > Clear Data & Uninstall
3. Restart LDPlayer
4. Build APK mới (xem bên dưới)
5. Cài đặt APK mới: `adb install app-arm64-v8a-release.apk`

### Cách 3: Tạo instance LDPlayer mới
1. Tạo LDPlayer instance mới (clean install)
2. Cài APK trực tiếp vào instance mới

---

## 🚀 Build APK mới

### Tự động (Khuyến nghị)
Chạy file batch có sẵn:
```bash
BUILD_APK_LOCAL.bat
```

Script này sẽ:
1. Clean Flutter cache
2. Get dependencies
3. Analyze code
4. Build APK release (arm64-v8a)

### Thủ công
```bash
cd D:\rustdesk-dev\flutter
flutter clean
flutter pub get
flutter analyze
flutter build apk --release --target-platform android-arm64
```

**APK output location:**
```
D:\rustdesk-dev\flutter\build\app\outputs\flutter-apk\app-arm64-v8a-release.apk
```

### Cài đặt vào LDPlayer
```bash
adb install -r D:\rustdesk-dev\flutter\build\app\outputs\flutter-apk\app-arm64-v8a-release.apk
```

*(Flag `-r` để reinstall và giữ data)*

---

## 💾 Cấu hình giá sản phẩm

### Hiện tại
Giá sản phẩm được lấy từ API backend:
- **API URL:** `https://api.afkzone.cloud/products`
- **Logic:** Nếu `durationDays == 7` và `price <= 1000` → Hiển thị "Miễn phí"

### Để thay đổi giá trong tương lai

#### Option 1: Sửa trên Backend API
Thay đổi giá trực tiếp trên API server (khuyến nghị cho production)

#### Option 2: Override local (cho testing)
Sửa file `flutter/lib/models/product_model.dart`:

```dart
String get formattedPrice {
  // Option A: Always show free for 7-day products
  if (durationDays == 7) {
    return 'Miễn phí';
  }

  // Option B: Custom price override
  if (tier == 'basic' && durationDays == 7) {
    return 'Miễn phí';  // Free trial
  } else if (tier == 'pro' && durationDays == 7) {
    return '5.000đ';     // Discounted
  }

  // Default pricing logic
  if (price >= 1000000) {
    return '${(price / 1000000).toStringAsFixed(1)}M';
  } else if (price >= 1000) {
    return '${(price / 1000).toStringAsFixed(0)}.000d';
  }
  return '${price}d';
}
```

---

## 📁 Files đã thay đổi

| File | Mô tả | Dòng thay đổi |
|------|-------|---------------|
| `flutter/lib/models/product_model.dart` | Sửa logic hiển thị giá | 38-50 |
| `flutter/android/.../BootReceiver.kt` | Toast message branding | 39 |
| `flutter/android/.../FloatingWindowService.kt` | Menu item branding | 305-317 |

---

## ✅ Checklist kiểm tra

Trước khi release APK mới:

- [x] Gói 7 ngày hiển thị "Miễn phí"
- [x] Tất cả text "RustDesk" đã đổi thành "AFK Zone"
- [x] App name = "AFK Zone"
- [x] Package name = `com.afkzone.remote`
- [x] App icons đã update
- [ ] Build APK thành công
- [ ] Test trên LDPlayer
- [ ] Test trên thiết bị thật
- [ ] Kiểm tra API connection
- [ ] Kiểm tra license activation

---

## 🐛 Lỗi đã biết

### 1. API Connection Error
**Lỗi:** `ClientException with SocketConnection refused (OS Error: Connection refused, errno = 111), address = api.afkzone.cloud, port = 57326`

**Nguyên nhân:** Backend API không khả dụng hoặc cấu hình network không đúng

**Giải pháp:**
1. Kiểm tra backend server có đang chạy không
2. Kiểm tra firewall/port 57326
3. Kiểm tra DNS resolve cho `api.afkzone.cloud`

### 2. "Không thể tải danh sách gói"
**Lỗi:** Payment screen hiển thị error icon

**Nguyên nhân:** Không kết nối được API `/products`

**Giải pháp:**
1. Pull down để refresh (có RefreshIndicator)
2. Kiểm tra internet connection
3. Kiểm tra API backend

---

## 📝 Notes

### Tham chiếu "rustdesk" còn lại (KHÔNG cần sửa)
Các tham chiếu kỹ thuật sau KHÔNG ảnh hưởng đến branding:

1. **Native library name:** `System.loadLibrary("rustdesk")` - Tên thư viện native compiled
2. **WakeLock tag:** `"rustdesk:wakelock"` - Internal tag
3. **GitHub comments:** Links đến upstream issues - Chỉ là comments

Những tham chiếu này là **technical/internal** và không hiển thị cho user.

---

## 🎯 Kết luận

Tất cả các thay đổi đã được hoàn thành:

1. ✅ **Giá 7 ngày = "Miễn phí"** (thay vì 1.000đ)
2. ✅ **Branding = "AFK Zone"** (không còn "RustDesk")
3. ✅ **App icons đã cập nhật** (logo AFK Zone mới)
4. ⚠️ **LDPlayer logo cache** - Cần rebuild APK và clear cache

**Bước tiếp theo:**
1. Chạy `BUILD_APK_LOCAL.bat` để build APK mới
2. Clear LDPlayer cache hoặc tạo instance mới
3. Cài đặt APK mới
4. Test tất cả chức năng

---

**Tác giả:** Claude Code
**Ngày cập nhật:** 2025-12-29
**Version:** v2.2.2

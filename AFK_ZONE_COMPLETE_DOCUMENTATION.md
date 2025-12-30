# AFK Zone - Complete Documentation

**Last Updated:** 2025-12-31  
**Current Version:** `v2.2.28+228`  
**Status:** ✅ Production Ready

---

## 📋 Mục Lục

1. [Tổng Quan Dự Án](#tổng-quan-dự-án)
2. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
3. [License Management System](#license-management-system)
4. [Payment Integration](#payment-integration)
5. [Admin Dashboard](#admin-dashboard)
6. [Server Configuration](#server-configuration)
7. [UI/UX Features](#uiux-features)
8. [API Endpoints](#api-endpoints)
9. [Database Schema](#database-schema)
10. [Build & Deployment](#build--deployment)
11. [Known Issues & Fixes](#known-issues--fixes)
12. [Version History](#version-history)

---

## 🎯 Tổng Quan Dự Án

AFK Zone là một ứng dụng remote desktop dựa trên RustDesk, được tùy chỉnh với:
- **License Management System** - Quản lý license theo tier (Basic, Pro, Enterprise)
- **Multi-device Support** - Hỗ trợ nhiều thiết bị trên 1 license
- **Payment Integration** - Tích hợp thanh toán qua ZaloPay và chuyển khoản ngân hàng
- **Admin Dashboard** - Quản lý sản phẩm, license, thiết bị, đơn hàng
- **Auto Server Configuration** - Tự động cấu hình server từ license

---

## 🏗️ Kiến Trúc Hệ Thống

### Frontend (Flutter)
- **Platform:** Flutter (Mobile: Android/iOS, Desktop: Windows/macOS/Linux)
- **State Management:** Provider, GetX
- **Storage:** SharedPreferences
- **Network:** HTTP (REST API)

### Backend (FastAPI)
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **Authentication:** JWT
- **Payment Gateway:** ZaloPay, Casso (Bank Transfer)

### Infrastructure
- **Server:** Ubuntu Server
- **Containerization:** Docker, Docker Compose
- **Reverse Proxy:** Nginx
- **RustDesk Server:** HBBS (ID Server), HBBR (Relay Server)

---

## 🔐 License Management System

### License Tiers

| Tier | Max Devices | Pricing |
|------|-------------|---------|
| **Basic** | 2 devices | 60k (30 days), 150k (90 days) |
| **Pro** | 5 devices | 100k (30 days), 250k (90 days) |
| **Enterprise** | Unlimited (-1) | 200k (30 days), 500k (90 days) |
| **Trial** | 2 devices | Free (7 days) |

### License Flow

#### 1. Trial Activation
```
User clicks "Dùng thử 7 ngày"
  ↓
Check if device already used trial (/trial/check)
  ↓
If not used: Generate trial license (/trial/generate)
  ↓
Activate license (/activate)
  ↓
Save to SharedPreferences
  ↓
Auto-apply server configs
```

#### 2. License Purchase
```
User selects product
  ↓
Create bank order (/payment/bank/create)
  ↓
Display QR code
  ↓
User transfers money
  ↓
Casso webhook (/payment/bank/webhook)
  ↓
Create license with correct max_devices
  ↓
Activate on device
  ↓
Display success dialog
```

#### 3. License Activation (Multi-device)
```
User enters license key
  ↓
Call /activate with license_key + device_id
  ↓
Check if device already activated
  ↓
If not: Check max_devices limit
  ↓
If OK: Insert into license_devices
  ↓
Return license info
```

### License Storage (SharedPreferences)

```dart
{
  "afk_license_key": "AFK-XXXXXXXX",
  "afk_license_tier": "pro",
  "afk_license_active": true,
  "afk_license_expires_at": 1234567890,
  "afk_max_devices": 5,
  "device_id": "sha256_hash",
  "id_server": "id.afkzone.cloud",
  "relay_server": "id.afkzone.cloud",
  "api_server": "https://api.afkzone.cloud",
  "public_key": "EXOW136uTrC0PYYrkavoJH7SjkFlzPjB+vzzpvjsybw="
}
```

### License Validation

- **On App Start:** Check license validity
- **Background Check:** Every 24 hours
- **Endpoint:** `POST /check`
- **Response:** License status, expires_at, max_devices

---

## 💳 Payment Integration

### Bank Transfer Flow

1. **Create Order** (`POST /payment/bank/create`)
   - Generate `trans_code` (e.g., `AFKPRO90251231005`)
   - Create QR code with amount and trans_code
   - Save order to `bank_orders` table

2. **User Transfers Money**
   - User scans QR code
   - Transfers money with trans_code in description

3. **Webhook Processing** (`POST /payment/bank/webhook`)
   - Casso sends webhook with signature
   - Verify signature (HMAC-SHA512)
   - Extract trans_code from description
   - Find order in database
   - Create license with correct max_devices
   - Activate on device
   - Update order status to 'success'

4. **Manual Complete** (`POST /admin/orders/{trans_code}/complete`)
   - Admin manually completes pending orders
   - Same logic as webhook

### ZaloPay Integration (Future)

- Endpoint: `POST /payment/create`
- Status: Not yet implemented

---

## 🎛️ Admin Dashboard

### Features

1. **Dashboard**
   - Total licenses, active licenses, expired licenses
   - Total revenue (today, this month, all time)
   - Server stats (connections, bandwidth)

2. **Product Management** (`/admin/products`)
   - Create/Edit/Delete products
   - Set tier, duration, price, max_devices
   - Enable/Disable products
   - Auto-sync to `pricing` table

3. **License Management** (`/admin/licenses`)
   - View all licenses (manual + purchased)
   - Filter by tier, status
   - Revoke/Unrevoke licenses
   - Delete licenses
   - Generate single licenses

4. **Device Management** (`/admin/devices`)
   - View all devices
   - See device_id, license_key, tier
   - Delete devices

5. **Order Management** (`/admin/orders`)
   - View all bank orders
   - Filter by status
   - Manual complete pending orders
   - See license_key after completion

6. **Trial Devices** (`/admin/trial-devices`)
   - View all trial devices
   - Delete trial devices
   - Clear all trials

7. **Connections** (`/admin/connections`)
   - View connection history
   - Status: Not yet implemented (client-side logging needed)

### Authentication

- **Login:** `POST /admin/login`
- **JWT Token:** Valid for 24 hours
- **Protected Endpoints:** All `/admin/*` endpoints require JWT

---

## ⚙️ Server Configuration

### Default Server Configs

```dart
const String AFK_DEFAULT_ID_SERVER = 'id.afkzone.cloud';
const String AFK_DEFAULT_RELAY_SERVER = 'id.afkzone.cloud';
const String AFK_DEFAULT_API_SERVER = 'https://api.afkzone.cloud';
const String AFK_DEFAULT_KEY = 'EXOW136uTrC0PYYrkavoJH7SjkFlzPjB+vzzpvjsybw=';
```

### Auto-Apply Logic

1. **On App Start** (`flutter/lib/main.dart`)
   ```dart
   // Always apply default AFK Zone server configs first
   await _applyDefaultServerConfigs();
   
   // Then, if a license is active, override with license-specific configs
   await _applyLicenseServerConfigs();
   ```

2. **From License Response**
   - When license is activated, server configs are saved to SharedPreferences
   - Auto-applied on next app start

3. **Developer Mode**
   - Tap version 7 times to enable
   - Shows ID/Relay Server settings
   - Hidden by default for security

---

## 🎨 UI/UX Features

### License Page

- **Manual Activation:** Input license key
- **Trial Activation:** "Dùng thử 7 ngày" button
- **Purchase History:** View past purchases
- **License Recovery:** Recover license using transaction code

### Payment Screen

- **Dynamic Pricing:** Fetched from API
- **Pull-to-Refresh:** Refresh product list
- **Tier Sections:** Basic, Pro, Enterprise
- **Free Trial:** Special handling for 7-day free trial

### Settings Page

- **License Information:**
  - License key (with copy button)
  - Tier, expiration date
  - Device count (X / Y)
  - Logout license button
- **Developer Mode:** Tap version 7 times
- **ID/Relay Server:** Hidden by default, shown in Developer Mode

### Remote Page

- **System Keyboard:** Reverted from custom keyboard
- **Menu Toolbar:** Overlay on content
- **FAB Button:** Draggable menu button
- **Password Dialog:** Fixed positioning

### Payment Success Dialog

- **License Key:** Displayed with copy button
- **Package Info:** Tier, duration, max_devices
- **Auto-activation:** Automatically activated on device
- **Instructions:** How to activate on other devices

---

## 🔌 API Endpoints

### Public Endpoints

#### License
- `POST /activate` - Activate license key
- `POST /check` - Check license validity
- `GET /license/info?license_key=XXX` - Get license info
- `POST /license/logout` - Logout device from license
- `POST /license/recover` - Recover license using trans_code

#### Trial
- `POST /trial/generate` - Generate 7-day trial
- `POST /trial/check` - Check if device used trial

#### Products
- `GET /products` - Get all products
- `GET /products/{id}` - Get product details

#### Payment
- `POST /payment/bank/create` - Create bank order
- `POST /payment/bank/webhook` - Casso webhook
- `GET /payment/bank/status?trans_code=XXX` - Check payment status

#### User
- `GET /user/history?device_id=XXX` - Get purchase history

### Admin Endpoints (JWT Required)

#### Authentication
- `POST /admin/login` - Admin login
- `GET /admin` - Serve admin dashboard HTML

#### Dashboard
- `GET /admin/dashboard/stats` - Get dashboard statistics

#### Products
- `GET /admin/products` - List all products
- `POST /admin/products` - Create product
- `PUT /admin/products/{id}` - Update product
- `DELETE /admin/products/{id}` - Soft delete product
- `POST /admin/products/{id}/enable` - Re-enable product
- `DELETE /admin/products/{id}/permanent` - Permanent delete

#### Licenses
- `GET /admin/licenses/all` - List all licenses
- `POST /admin/licenses/generate` - Generate single license
- `POST /admin/licenses/{license_key}/revoke` - Revoke license
- `POST /admin/licenses/{license_key}/unrevoke` - Unrevoke license
- `DELETE /admin/licenses/{license_key}` - Delete license

#### Devices
- `GET /admin/devices/detailed` - List all devices
- `DELETE /admin/devices/{device_id}` - Delete device

#### Orders
- `GET /admin/orders` - List all orders
- `POST /admin/orders/{trans_code}/complete` - Manual complete order

#### Trial Devices
- `GET /admin/trial-devices` - List all trial devices
- `DELETE /admin/trial-devices/{id}` - Delete trial device
- `DELETE /admin/trial-devices` - Clear all trials

#### Connections
- `POST /connection/log` - Log connection event (client-side)

---

## 🗄️ Database Schema

### Tables

#### `licenses`
```sql
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL,
    duration_days INTEGER NOT NULL,
    max_devices INTEGER NOT NULL,
    activated_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255)
);
```

#### `license_devices`
```sql
CREATE TABLE license_devices (
    id SERIAL PRIMARY KEY,
    license_key VARCHAR(255) NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    activated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(license_key, device_id)
);
```

#### `trial_devices`
```sql
CREATE TABLE trial_devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    license_key VARCHAR(255),
    used_at TIMESTAMP DEFAULT NOW()
);
```

#### `bank_orders`
```sql
CREATE TABLE bank_orders (
    id SERIAL PRIMARY KEY,
    trans_code VARCHAR(255) UNIQUE NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    duration_days INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    bank_account VARCHAR(50),
    qr_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    license_key VARCHAR(255),
    bank_tid VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP
);
```

#### `products`
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    duration_days INTEGER NOT NULL,
    price INTEGER NOT NULL,
    max_devices INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `pricing`
```sql
CREATE TABLE pricing (
    id SERIAL PRIMARY KEY,
    tier VARCHAR(50) NOT NULL,
    duration_days INTEGER NOT NULL,
    price INTEGER NOT NULL,
    UNIQUE(tier, duration_days)
);
```

#### `admin_users`
```sql
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `connection_logs`
```sql
CREATE TABLE connection_logs (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255),
    license_key VARCHAR(255),
    action VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 Build & Deployment

### Flutter Build

#### Android
```bash
cd flutter
flutter build apk --release
```

#### iOS
```bash
cd flutter
flutter build ios --release
```

#### Desktop
```bash
cd flutter
flutter build windows --release
flutter build macos --release
flutter build linux --release
```

### Version Management

- **Version Format:** `MAJOR.MINOR.PATCH+BUILD`
- **File:** `flutter/pubspec.yaml`
- **Example:** `version: 2.2.28+228`

### GitHub Actions Workflow

- **Trigger:** Push tag `v*.*.*`
- **Builds:** Android APK, iOS, Windows, macOS, Linux
- **Artifacts:** Uploaded to GitHub Releases

### Server Deployment

#### API Server
```bash
cd /root/license-api
docker-compose up -d
```

#### RustDesk Server
```bash
docker-compose up -d hbbs hbbr
```

---

## 🐛 Known Issues & Fixes

### v2.2.28 Fixes

#### 1. Key Mismatch ✅
- **Issue:** Default key in code didn't match server
- **Fix:** Updated `AFK_DEFAULT_KEY` to `EXOW136uTrC0PYYrkavoJH7SjkFlzPjB+vzzpvjsybw=`

#### 2. Keyboard Not Working ✅
- **Issue:** Custom keyboard was buggy
- **Fix:** Reverted to system keyboard

#### 3. Multi-device Activation ✅
- **Issue:** License only activated on 1 device
- **Fix:** Fixed `/activate` endpoint to properly check and increment device_count

#### 4. Max Devices Wrong ✅
- **Issue:** All licenses had max_devices = 1
- **Fix:** 
  - Fixed webhook to use `get_max_devices_for_tier()`
  - Fixed manual complete endpoint
  - Updated all existing licenses in database

#### 5. Device ID Extraction ✅
- **Issue:** Webhook used `order[1]` (trans_code) instead of `order[2]` (device_id)
- **Fix:** Changed to `order[2]` in both webhook and manual complete

#### 6. License Info Endpoint ✅
- **Issue:** Used `license_id` instead of `license_key`
- **Fix:** Rewrote `/license/info` to use `license_key`

### Previous Fixes

#### v2.2.27
- Fixed ID/Relay Server display (Developer Mode)
- Fixed password dialog positioning
- Fixed FAB button
- Fixed menu toolbar

#### v2.2.26
- Fixed keyboard input handling
- Fixed admin dashboard license display
- Fixed trial device management

#### v2.2.25
- Added purchase history
- Added license recovery
- Fixed admin dashboard data sync

#### v2.2.24
- Fixed DNS prefetch
- Fixed custom keyboard implementation
- Fixed send text bar

#### v2.2.23
- Reverted to system keyboard
- Fixed password dialog
- Fixed menu toolbar

#### v2.2.22
- Restored ID/Relay Server settings
- Implemented Developer Mode (tap version 7 times)

#### v2.2.21
- Added license logout
- Added device count display
- Fixed server configuration auto-apply

---

## 📝 Version History

### v2.2.28 (2025-12-31)
- ✅ Fixed key mismatch
- ✅ Reverted to system keyboard
- ✅ Fixed multi-device activation
- ✅ Fixed max_devices for all tiers
- ✅ Fixed device_id extraction in webhook
- ✅ Fixed license info endpoint
- ✅ Set default FPS to 90
- ⚠️ **Known Issue:** License mới tạo đã hiển thị 2/5 devices (do device_id extraction bug - đã fix)
- ⚠️ **Known Issue:** Device ID hiển thị mã đơn hàng trong admin dashboard (do webhook bug - đã fix)

### v2.2.27 (2025-12-30)
- ✅ Fixed ID/Relay Server display
- ✅ Fixed password dialog
- ✅ Fixed FAB button
- ✅ Fixed menu toolbar
- ✅ Fixed keyboard input

### v2.2.26 (2025-12-30)
- ✅ Fixed admin dashboard
- ✅ Fixed trial device management
- ✅ Fixed license revoke/unrevoke

### v2.2.25 (2025-12-30)
- ✅ Added purchase history
- ✅ Added license recovery
- ✅ Fixed admin dashboard sync

### v2.2.24 (2025-12-30)
- ✅ Added DNS prefetch
- ✅ Fixed custom keyboard
- ✅ Fixed send text bar

### v2.2.23 (2025-12-30)
- ✅ Reverted to system keyboard
- ✅ Fixed password dialog
- ✅ Fixed menu toolbar

### v2.2.22 (2025-12-30)
- ✅ Restored ID/Relay Server settings
- ✅ Implemented Developer Mode

### v2.2.21 (2025-12-30)
- ✅ Added license logout
- ✅ Added device count display
- ✅ Fixed server configuration

### v2.2.20 (2025-12-29)
- ✅ Fixed payment webhook
- ✅ Fixed manual order completion
- ✅ Fixed admin dashboard orders

### v2.2.19 (2025-12-29)
- ✅ Fixed build errors
- ✅ Fixed admin dashboard

### v2.2.18 (2025-12-29)
- ✅ Fixed Gradle build
- ✅ Fixed admin dashboard endpoints

### v2.2.17 (2025-12-29)
- ✅ Fixed API 502 error
- ✅ Fixed admin dashboard login

### v2.2.16 (2025-12-29)
- ✅ Fixed admin dashboard deployment
- ✅ Fixed product management

### v2.2.15 (2025-12-29)
- ✅ Fixed menu toolbar
- ✅ Fixed keyboard

### v2.2.14 (2025-12-29)
- ✅ Fixed Mac app name
- ✅ Fixed admin dashboard

### v2.2.13 (2025-12-29)
- ✅ Complete license management
- ✅ Server configuration auto-apply
- ✅ Payment integration

---

## 🎨 Tier Management & Customization

### Current Tier System

Hiện tại hệ thống sử dụng **hardcoded tier names** trong code:
- `basic` → Display: "BASIC"
- `pro` → Display: "PRO"
- `enterprise` → Display: "ENTERPRISE"

### Tier Display Logic

**Flutter (`flutter/lib/models/product_model.dart`):**
```dart
String get tierDisplayName {
  if (name != null && name!.isNotEmpty) {
    return name!;  // Use name from API if available
  }
  return tier.toUpperCase();  // Fallback to tier name
}
```

**Backend (`app.py`):**
- Products table có `name` field
- API `/products` trả về `name` field
- Nếu `name` null → fallback to `tier.toUpperCase()`

### Proposed Tier Renaming

User muốn đổi tên các gói:
- **Gói Trải Nghiệm** (1 ngày, 3 ngày, hoặc miễn phí xem quảng cáo)
- **Gói Nông Dân** (thay cho Basic)
- **Gói Cao Thủ** (thay cho Pro)
- **Gói Trại Cày** (thay cho Enterprise)

### Implementation Options

#### Option 1: Use `name` Field (Recommended)
- Update `products.name` in database
- API sẽ tự động trả về `name`
- Client sẽ hiển thị `name` thay vì `tier`

#### Option 2: Add `display_name` Field
- Add new column `display_name` to `products` table
- Update API to return `display_name`
- Update client to use `display_name`

#### Option 3: Tier Mapping Table
- Create `tier_display_names` table
- Map tier → display_name
- Update API to join and return display_name

### Current Issues

1. **Tier Template:** Mỗi tier đang có template riêng trong UI
   - Cần refactor để dùng dynamic template
   - Template dựa trên `name` hoặc `tier`
   - **Location:** `flutter/lib/mobile/pages/payment_screen.dart`

2. **Admin Dashboard:** Chưa có UI để đổi tên tier
   - Cần thêm field "Display Name" trong product form
   - Hoặc thêm tier management section
   - **Location:** `admin_dashboard.html` → Product form

3. **Database Cleanup:** 
   - Product IDs không sequential (do xóa/tạo nhiều lần)
   - Cần reset auto-increment hoặc cleanup
   - **Solution:** 
     ```sql
     -- Reset product ID sequence
     SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));
     ```

4. **Device ID Display Issue (Fixed in v2.2.28):**
   - **Problem:** Admin dashboard hiển thị mã đơn hàng (trans_code) thay vì device_id
   - **Root Cause:** Webhook used `order[1]` (trans_code) instead of `order[2]` (device_id)
   - **Fix:** Changed to `order[2]` in both webhook and manual complete
   - **Impact:** Existing licenses may have wrong device_id (need cleanup)

5. **License Device Count Issue (Fixed in v2.2.28):**
   - **Problem:** License mới tạo đã hiển thị 2/5 devices
   - **Root Cause:** Webhook saved trans_code as device_id
   - **Fix:** Fixed device_id extraction
   - **Impact:** Existing licenses may have duplicate/wrong device entries

---

## 🔮 Future Improvements

### Tier Management
- [ ] Add custom tier names in admin dashboard
- [ ] Support tier renaming (e.g., "Gói Trải Nghiệm", "Gói Nông Dân", "Gói Cao Thủ", "Gói Trại Cày")
- [ ] Dynamic tier display in UI
- [ ] Tier template refactoring

### Payment
- [ ] Implement ZaloPay integration
- [ ] Add payment history in app
- [ ] Auto-fill license after payment completion

### Admin Dashboard
- [ ] Add tier management UI
- [ ] Add bulk operations
- [ ] Add export functionality
- [ ] Add analytics charts

### Client Features
- [ ] Connection logging
- [ ] Usage statistics
- [ ] Device management UI
- [ ] License sharing

### Performance
- [ ] Optimize FPS (currently 90, can go to 120)
- [ ] Optimize bitrate
- [ ] Reduce latency
- [ ] Improve P2P connection rate

---

## 🧹 Database Cleanup & Maintenance

### Cleanup Scripts

#### 1. Fix Wrong Device IDs
```sql
-- Find licenses with trans_code as device_id
SELECT license_key, device_id 
FROM license_devices 
WHERE device_id LIKE 'AFK%' 
  AND LENGTH(device_id) < 50;

-- Delete wrong entries (trans_code entries)
DELETE FROM license_devices 
WHERE device_id LIKE 'AFK%' 
  AND LENGTH(device_id) < 50;

-- Re-activate licenses with correct device_id from bank_orders
INSERT INTO license_devices (license_key, device_id, activated_at)
SELECT bo.license_key, bo.device_id, bo.paid_at
FROM bank_orders bo
WHERE bo.status = 'success' 
  AND bo.license_key IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM license_devices ld 
    WHERE ld.license_key = bo.license_key 
      AND ld.device_id = bo.device_id
  );
```

#### 2. Reset Product ID Sequence
```sql
SELECT setval('products_id_seq', (SELECT MAX(id) FROM products));
```

#### 3. Cleanup Orphaned Records
```sql
-- Remove license_devices without license
DELETE FROM license_devices 
WHERE license_key NOT IN (SELECT license_key FROM licenses);

-- Remove bank_orders without device_id
DELETE FROM bank_orders 
WHERE device_id IS NULL OR device_id = '';
```

### Maintenance Queries

#### Check License Device Count
```sql
SELECT 
    l.license_key,
    l.tier,
    l.max_devices,
    COUNT(ld.device_id) as device_count
FROM licenses l
LEFT JOIN license_devices ld ON l.license_key = ld.license_key
GROUP BY l.license_key, l.tier, l.max_devices
HAVING COUNT(ld.device_id) > l.max_devices AND l.max_devices != -1;
```

#### Check Wrong Device IDs
```sql
SELECT 
    ld.license_key,
    ld.device_id,
    CASE 
        WHEN ld.device_id LIKE 'AFK%' AND LENGTH(ld.device_id) < 50 THEN 'TRANS_CODE'
        WHEN LENGTH(ld.device_id) = 64 THEN 'SHA256_HASH'
        ELSE 'UNKNOWN'
    END as device_id_type
FROM license_devices ld
WHERE ld.device_id LIKE 'AFK%' AND LENGTH(ld.device_id) < 50;
```

---

## 📞 Support & Contact

- **API Server:** `https://api.afkzone.cloud`
- **Admin Dashboard:** `https://api.afkzone.cloud/admin`
- **ID Server:** `id.afkzone.cloud`
- **Relay Server:** `id.afkzone.cloud`

---

## 📄 License

This project is based on RustDesk and is customized for AFK Zone.

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-31  
**Maintained by:** AFK Zone Development Team


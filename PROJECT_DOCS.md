# AFK Zone - Project Documentation

## Overview
AFK Zone is a remote desktop application based on RustDesk, customized with license management, payment integration, and admin dashboard.

## Architecture

### Client (Flutter)
- **Platform**: Android, iOS, Windows, macOS, Linux
- **Main Entry**: `flutter/lib/main.dart`
- **License Service**: `flutter/lib/common/license_service.dart`
- **Payment WebSocket**: `flutter/lib/common/payment_websocket_service.dart`

### Backend (FastAPI)
- **API URL**: `https://api.afkzone.cloud`
- **Database**: PostgreSQL
- **Container**: `afkzone-license-api`

---

## Key Features

### 1. License System
- **Activation**: Device fingerprint + license key
- **Tiers**: Dynamic loading from `/tiers` API
- **Products**: Loaded from `/products` API
- **Trial**: 7-day free trial per device

### 2. Payment Flow (WebSocket)
```
User selects product → Create order → Show QR code
    ↓
User pays via bank transfer → Casso webhook
    ↓
Backend creates license → WebSocket notify client
    ↓
Client shows popup → Auto-activate → Back to home
```

### 3. Admin Dashboard
- **URL**: `https://api.afkzone.cloud/admin`
- **Features**:
  - Products CRUD
  - Licenses management
  - Orders tracking
  - Devices monitoring
  - Tier management
  - Sortable/filterable tables

---

## API Endpoints

### Public
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/products` | GET | List active products |
| `/tiers` | GET | List active tiers |
| `/license/activate` | POST | Activate license |
| `/license/validate` | POST | Validate license |
| `/payment/create-bank-order` | POST | Create payment order |
| `/payment/status/{order_id}` | GET | Check payment status |
| `/ws/payment/{order_id}` | WebSocket | Real-time payment notification |

### Admin (requires auth)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/products` | CRUD | Manage products |
| `/admin/licenses` | CRUD | Manage licenses |
| `/admin/orders` | GET | View orders |
| `/admin/tiers` | CRUD | Manage tiers |
| `/admin/devices` | GET | View devices |
| `/webhook/casso` | POST | Casso payment webhook |

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `products` | License packages |
| `licenses` | Issued licenses |
| `orders` | Payment orders |
| `tiers` | Product tier definitions |
| `devices` | Registered devices |
| `trial_devices` | Trial usage tracking |
| `connection_logs` | Connection history |

---

## Key Files

### Flutter Client
```
flutter/lib/
├── common/
│   ├── license_service.dart      # License API calls
│   └── payment_websocket_service.dart  # WebSocket client
├── services/
│   ├── product_service.dart      # Product API
│   ├── payment_service.dart      # Payment API
│   └── cart_service.dart         # Shopping cart
├── models/
│   └── product_model.dart        # Product data model
├── mobile/pages/
│   ├── license_page.dart         # License management UI
│   ├── payment_screen.dart       # Product selection
│   └── payment_qr_screen.dart    # QR payment + WebSocket
```

### Backend (on server)
```
/app/
├── app.py                  # FastAPI application
├── admin_dashboard.html    # Admin UI
└── scripts/                # Fix scripts
```

---

## Recent Changes (v2.2.36 - v2.2.38)

### v2.2.38 - WebSocket Payment Integration
- Integrate WebSocket into `payment_qr_screen.dart`
- Real-time license popup when payment complete
- Auto-activate license on device
- "Hoàn tất & Sử dụng" button → back to home

### v2.2.37 - WebSocket Service
- Add `payment_websocket_service.dart`
- Add `web_socket_channel` dependency
- Backend WebSocket endpoint `/ws/payment/{order_id}`

### v2.2.36 - Dynamic Tier Loading
- `fetchProductsByTier()` loads tiers dynamically
- Removed hardcoded tier list

---

## Build & Deploy

### GitHub Actions
- **Workflow**: `.github/workflows/flutter-build.yml`
- **Trigger**: Push tag `v2.x.x`
- **Outputs**: APK, IPA, DMG, EXE, AppImage

### Server Deployment
```bash
# SSH to server
ssh automation@172.26.31.115

# Docker commands
docker restart afkzone-license-api
docker logs afkzone-license-api --tail 50
docker exec afkzone-license-api python3 /app/script.py
```

---

## Environment

### Flutter Version
- SDK: 3.24.5
- Dart: ^3.1.0

### Rust Version
- Default: 1.75
- macOS: 1.81

### Key Dependencies
- `http: ^1.1.0`
- `shared_preferences: ^2.2.2`
- `web_socket_channel: ^2.4.0`
- `qr_flutter: ^4.1.0`

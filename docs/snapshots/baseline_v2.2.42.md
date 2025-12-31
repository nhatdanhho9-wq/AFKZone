# Phase 0 Baseline Snapshot

**Date**: 2026-01-01  
**Baseline Tag**: v2.2.42  
**Purpose**: Capture current state before Phase 1 (Security) execution

---

## Git State
- **Current Branch**: main
- **Latest Commit**: 49c7ff5da (fix: use tier names instead of product names, add ProMax/SuperVVIP colors)
- **Latest Tag**: v2.2.42

---

## Server State

### API (afkzone-license-api)
- **Container**: afkzone-license-api
- **Image**: Custom FastAPI
- **Port**: 8080 → 8000
- **File**: ~/license-api/app.py (deployed from server_app.py)
- **Last Deploy**: 2026-01-01 00:30 (clean deploy after corruption)

### Database (afkzone-postgres)
- **Container**: afkzone-postgres
- **Type**: PostgreSQL
- **User**: afkzone
- **Database**: afkzone

---

## Key Files Snapshot

### Backend
- `server_app.py` (89KB) - Main API server
- Endpoints: ~60 total (see docs/api_contract.md)

### Flutter
- `flutter/lib/mobile/pages/payment_screen.dart` - Payment UI
- `flutter/lib/mobile/pages/license_page.dart` - License display
- `flutter/lib/common/license_service.dart` - API client
- `flutter/lib/services/product_service.dart` - Product/tier fetching

### Database Schema
Key tables:
- `licenses` - License records
- `license_devices` - Device activations
- `bank_orders` - Payment orders
- `products` - Product definitions
- `tiers` - Tier definitions
- `pricing` - Legacy pricing (deprecated)

---

## Known Issues (at baseline)
1. ✅ FIXED: Logout not clearing device slots
2. ✅ FIXED: QR code corrupt response
3. ✅ FIXED: Tier names showing product names
4. ⚠️ PENDING: Secrets hardcoded in code
5. ⚠️ PENDING: Keystore in repo
6. ⚠️ PENDING: Webhook signature disabled

---

## Reproducibility
To restore this baseline:
```bash
git checkout v2.2.42
docker restart afkzone-license-api
```

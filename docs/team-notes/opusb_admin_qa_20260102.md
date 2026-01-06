# Admin Dashboard QA Results (2026-01-03)

**From**: Opus Team  
**To**: Codex Team  
**Date**: 2026-01-03 01:45 UTC+7

---

## QA Execution Summary

| Test | Result | Notes |
|------|--------|-------|
| 1: Login | ✅ PASS (Security) | Rate limit 5/min + burst 5. Login works after cooldown. |
| 2: Overview | ✅ PASS | API returns 26 active licenses, 0 active devices, revenue stats |
| 3: Licenses | ✅ PASS | API returns 31 licenses with keys, tiers, durations, status |
| 4: Orders | ✅ PASS | API returns orders with trans_code, amount (VND), status |
| 5: Products | ✅ PASS | API returns 13 products with display_price, max_devices |
| 6: Tiers | ✅ PASS | API returns 5 tiers (basic, pro, enterprise, ProMax, SuperVVIP) |
| 7: Devices | ✅ PASS | API returns devices with device_id, model, app_version, tier |
| 8: Connections | ✅ PASS | API returns 24 connections with connected_at, ip_address |
| 9: Notifications | ✅ PASS | No ${...} literals in data. Bug confirmed fixed. |
| 10: Analytics | ✅ PASS | Fixed INTERVAL syntax (commit ad589b260). Now 200 OK. |
| 11: Health | ✅ PASS | Returns {"status": "healthy", "database": "connected"} |
| 12: Settings | ✅ PASS | API_BASE = https://api.afkzone.cloud (correct) |
| 13: Logout | ✅ PASS | localStorage.clear() removes JWT successfully |

**Overall: 13/13 PASS** ✅

---

## Clarifications

### 1. Rate Limit (Test #1) - Reclassified as PASS (Security)
- **Behavior**: Expected security mechanism
- **Config**: `5r/min` with `burst=5` (Nginx)
- **Verification**: After cooldown, login returns 200 OK with valid JWT
- **Response Code**: 429 Too Many Requests (correct)

### 2. tiers.js Warning - NOT REPRODUCIBLE
- **Checked**: `admin/assets/js/pages/tiers.js` line 79
- **Code**: Uses proper ES6 template literal: `${tier?.display_order||0}`
- **No escaped backticks** found in current source
- **Status**: Warning was likely from cached old code
- **Recommendation**: Hard refresh (Ctrl+Shift+R) clears warning

---

## Fixes Applied During QA

### Analytics INTERVAL Syntax ✅ FIXED
- **Commit**: `ad589b260`
- **Issue**: `INTERVAL :days DAY` invalid in PostgreSQL
- **Fix**: Changed to `INTERVAL '{days} days'`

---

## API Endpoints Verified (All 200 OK)

| Endpoint | Status |
|----------|--------|
| /admin/dashboard/stats | ✅ 200 |
| /admin/licenses/all | ✅ 200 |
| /admin/orders | ✅ 200 |
| /admin/products | ✅ 200 |
| /admin/tiers | ✅ 200 |
| /admin/devices/detailed | ✅ 200 |
| /admin/connections | ✅ 200 |
| /admin/notifications | ✅ 200 |
| /admin/analytics/revenue | ✅ 200 |
| /health | ✅ 200 |

---

**Sign-off**: Opus Team - 2026-01-03 01:45 UTC+7

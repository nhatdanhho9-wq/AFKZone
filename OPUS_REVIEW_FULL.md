AFK Zone / RustDesk - Full Review Summary and API Mapping

Scope
- Local repo: d:\rustdesk-dev
- Server: automation@172.26.31.115
- License API: ~/license-api/app.py
- Containers: hbbs, hbbr, afkzone-license-api, afkzone-postgres
- No code changes made during this review

Executive Summary (action-first)
Critical
1) Webhook signature verification is effectively disabled (accept-all in code). This allows fake payments to create licenses.
   Location: ~/license-api/app.py:379
2) Secrets and admin keys are hardcoded in server code.
   Locations: ~/license-api/app.py:203, 218, 322, 423
3) App signing materials are stored in repo.
   Locations: flutter/afkzone-release.jks, keystore_base64.txt

High
4) Client calls multiple endpoints that do not exist on the server (404/422).
5) Payment success flow stores prefs with different keys than LicenseWrapper expects, so user can be stuck as "not licensed".
6) /activate response fields do not match what client reads (device_limit vs max_devices) and expires_at type mismatch.
7) Connection logging endpoint and payload mismatch (client uses /connection/log with JSON; server only has /admin/connections/log with query params).

Medium
8) Duplicate route definitions: /admin/licenses/{license_key}/extend exists twice.
9) Missing hbb_common submodule contents locally (build will fail if not initialized).

Detailed Client <-> Server API Mapping
Legend:
- Server present: yes/no/partial
- Impact: what user will see
- Fix: suggested direction (server or client)

| ID | Client file:line | Method + path | Server present | Mismatch / notes | Impact | Suggested fix |
|----|------------------|---------------|----------------|------------------|--------|---------------|
| 1 | flutter/lib/common/license_service.dart:187 | POST /license/logout | No | Endpoint missing | Logout fails (404) | Add endpoint or remove client call |
| 2 | flutter/lib/common/license_service.dart:214 | GET /license/info | No | Endpoint missing | Settings license info empty | Add endpoint or remove UI |
| 3 | flutter/lib/common/license_service.dart:255 | POST /license/recover | No | Endpoint missing | Recover flow fails | Add endpoint |
| 4 | flutter/lib/common/license_service.dart:234 | GET /user/history | No | Endpoint missing | Purchase history fails | Add endpoint |
| 5 | flutter/lib/services/product_service.dart:83 | GET /tiers | No | Endpoint missing | Tier names empty, UI fallback | Add /tiers or drop call |
| 6 | flutter/lib/common/payment_websocket_service.dart:38 | WS /ws/payment/{order_id} | No | Endpoint missing | WebSocket payment never connects | Add WS or disable WS |
| 7 | flutter/lib/common/license_service.dart:283 | POST /connection/log (JSON) | No | Server has /admin/connections/log with query params | Connection logs fail | Align endpoint or payload |
| 8 | flutter/lib/models/model.dart:287 | logConnection -> remote_id | Partial | Server expects peer_id, connection_type | Logs unusable | Align field names |
| 9 | flutter/lib/mobile/pages/payment_qr_screen.dart:153 | save afk_license_key | Partial | LicenseWrapper reads license_key | User stays unlicensed | Save license_key or update wrapper |
|10 | flutter/lib/mobile/pages/payment_qr_screen.dart:167 | read result['max_devices'] | Partial | Server returns device_limit | Max devices wrong | Read device_limit or change server |
|11 | flutter/lib/mobile/pages/payment_qr_screen.dart:168 | expires_at -> setInt | Partial | Server returns ISO string | Runtime error or wrong expiry | Parse ISO -> timestamp |
|12 | flutter/lib/common/license_service.dart:8 | API URL | Yes | Using https://api.afkzone.cloud | OK | OK |
|13 | flutter/lib/services/payment_service.dart:5 | POST /payment/bank/create | Yes | OK | Bank order works | OK |
|14 | flutter/lib/services/payment_service.dart:23 | GET /payment/bank/status | Yes | OK | Polling works | OK |
|15 | flutter/lib/common/license_service.dart:146 | POST /payment/create | Yes | OK | ZaloPay create works | OK if used |
|16 | flutter/lib/common/license_service.dart:40 | POST /trial/check | Yes | OK | Trial check works | OK |
|17 | flutter/lib/common/license_service.dart:66 | POST /trial/generate | Yes | OK | Trial generate works | OK |
|18 | flutter/lib/common/license_service.dart:103 | POST /activate | Yes | Returns device_limit, expires_at ISO | Client expects max_devices, int | Fix response mapping |
|19 | flutter/lib/common/license_service.dart:132 | POST /check | Yes | OK | LicenseWrapper works | OK |
|20 | flutter/lib/services/notification_service.dart:13 | GET /notifications?device_id= | Partial | Client uses fingerprint; server expects devices.device_id | Notifications may be empty | Align device_id source |

Server-Side Notes (license-api)
- /activate, /check use license_devices table and return device_limit + expires_at ISO string.
- /payment/bank/webhook signature verification block exists but is commented; note says "accept all requests to test".
- Hardcoded admin key: "REDACTED_ADMIN_KEY".
- Hardcoded JWT secret: "REDACTED_JWT_SECRET".
- Hardcoded fallback token for Casso webhook if env not set.
- Duplicate route: /admin/licenses/{license_key}/extend appears twice.

Local Repo Notes
- Submodule libs/hbb_common is configured but empty locally; Rust build will fail unless initialized.
- App signing keys are present in repo (security risk for commercial distribution).

Suggested Priority Fix Order
1) Re-enable webhook signature verification and move secrets to env.
2) Fix mismatched endpoints between client and server (license info/logout/recover/history, tiers, WS).
3) Fix payment success prefs and response mapping (license_key, device_limit, expires_at).
4) Resolve duplicate admin route and standardize connection logging endpoint.
5) Remove signing keys from repo and rotate if leaked.



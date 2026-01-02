# Codex Smoke Test Report - Phase 2/3 (Full)

Date: 2026-01-01 16:00
Base URL: http://172.26.31.115:21120

## Results

| Test | Method | Status | Expected | Notes |
|------|--------|--------|----------|-------|
| GET / | GET | 200 | 200 |  |
| GET /health | GET | 200 | 200 |  |
| GET /products | GET | 200 | 200 |  |
| GET /tiers | GET | 200 | 200 |  |
| GET /webhook/casso | GET | 200 | 200 |  |
| POST /payment/bank/webhook (no signature) | POST | 401 | 401 |  |
| POST /webhook/casso (empty data) | POST | 200 | 200 |  |
| GET /admin/licenses/all | GET | 200 | 200 |  |
| GET /admin/licenses (JWT) | GET | 200 | 200 |  |
| GET /admin/devices/detailed | GET | 200 | 200 |  |
| GET /admin/trial-devices | GET | 200 | 200 |  |
| GET /admin/notifications | GET | 200 | 200 |  |
| GET /admin/licenses (admin_key) | GET | 403 | JWT_REQUIRED |  |
| POST /payment/bank/create | POST | 200 | 200 |  |
| GET /payment/bank/status | GET | 200 | 200 |  |
| GET /license/info | GET | 200 | 200 |  |
| GET /user/history | GET | 200 | 200 |  |
| POST /license/logout | POST | 200 | 200 |  |
| POST /connection/log (connect) | POST | 200 | 200 |  |
| POST /connection/log (disconnect) | POST | 200 | 200 |  |
| POST /license/recover (pending trans_code) | POST | 400 | 400 |  |
| PUT /admin/licenses/{key}/extend | PUT | 200 | 200 |  |
| POST /admin/licenses/airdrop | POST | 200 | 200 |  |

## Summary
- Unexpected failures: 0
- Skipped: 0

## Notes
- /payment/bank/webhook without signature returning 401 is expected (strict mode).
- /admin/licenses with admin_key returned 403; JWT-only is expected per decision.
- bank_order trans_code used: AFKBASIC3260101001

## Re-test
- 2026-01-01 16:05: GET `/user/history` returns 200 after SQL fix.

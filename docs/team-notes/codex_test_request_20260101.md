# Codex Test Request - Phase 2 Verification

Date: 2026-01-01
Owner: Codex Team
Purpose: Run runtime smoke tests for Phase 2 (server + docs alignment).

## Required Access
- Base URL for testing (staging or production).
- SSH host/user and confirmation that key-based access is allowed.
- Confirm whether production-safe tests are allowed (read-only vs write endpoints).

## Required Auth
- Admin JWT token (preferred) or admin username/password to obtain JWT.
- ADMIN_KEY if any admin_key-based endpoints are still in use.

## Required Test Data
- One active license_key with known tier + duration_days.
- One device_id tied to that license (and device_fingerprint if available).
- One product_id for user renew flow (optional but recommended).
- One bank order trans_code (pending and/or success) for bank status checks.
- One order_id for WebSocket payment notification test (optional).
- Webhook secret (CASSO_WEBHOOK_TOKEN) OR approval to test only missing-signature = 401.

## Safety / Constraints
- Do not run payment creation against real money.
- Use test data only (staging preferred).
- No deploy/restart without explicit request.
- All writes must be reversible or cleanable by Opus team.

## Planned Smoke Checklist
- GET /, GET /health, GET /products, GET /tiers, GET /version/check
- GET /webhook/casso (active check)
- POST /payment/bank/webhook (missing signature => 401)
- POST /license/logout, GET /license/info, GET /user/history, POST /license/recover
- POST /connection/log (connect + disconnect)
- GET /notifications
- Admin: GET /admin/licenses/all, PUT /admin/licenses/{key}/extend, POST /admin/licenses/airdrop

## Output
- codex_test_report_20260101.md with pass/fail + evidence.

## Sign-off
Codex Team

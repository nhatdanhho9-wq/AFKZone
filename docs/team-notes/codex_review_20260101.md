# Codex Review - Phase 2 API Contract Lock

Date: 2026-01-01
Status: Issues found (not approved)

## Findings (ordered by severity)

1) HIGH - License expiry math assumes epoch ms in a timestamp column
   - Impact: `/admin/licenses/{license_key}/extend` can crash or extend wrong dates if `licenses.expires_at` is a timestamp (Postgres schema shows timestamp). This is also inconsistent with ISO 8601 policy.
   - Evidence: `server_app.py:1398`, `server_app.py:1408`, `server_app.py:1414`
   - Required fix: use `to_datetime(result[0])` and write a real `datetime` back to `expires_at`.

2) HIGH - Bulk/Airdrop writes epoch ms into `licenses.expires_at`
   - Impact: `bulk-create` and `airdrop` insert millisecond integers into a timestamp column, causing invalid data and downstream parsing inconsistencies.
   - Evidence: `server_app.py:1236`, `server_app.py:1239`, `server_app.py:1269`, `server_app.py:1272`
   - Required fix: write `datetime` values (not epoch ms) into `expires_at`.

3) MEDIUM - OpenAPI global auth is incorrect for public endpoints
   - Impact: `security` at top applies to all paths, so clients will think `/check`, `/trial/*`, `/health`, etc require auth.
   - Evidence: `docs/openapi.yaml:17`
   - Required fix: set `security: []` on public endpoints, and only require `BearerAuth` on admin endpoints.

4) MEDIUM - OpenAPI request schema mismatch for `/connection/log`
   - Impact: Spec only allows `device_id`, `peer_id`, `connection_type`, but server/client use `remote_id`, `action`, `license_key`, `ip_address`.
   - Evidence: `docs/openapi.yaml:511`, `server_app.py:1958`
   - Required fix: update OpenAPI schema to include actual request fields.

5) LOW - OpenAPI missing `fingerprint` query param for `/user/history`
   - Impact: Spec is incomplete; client uses `fingerprint` in query.
   - Evidence: `docs/openapi.yaml:323`, `server_app.py:1889`
   - Required fix: add `fingerprint` optional query param.

6) LOW - Client compatibility gap still open (Phase 3)
   - Impact: WebSocket now returns ISO 8601 `expires_at` but Flutter still expects epoch ms.
   - Evidence: `server_app.py:1628`, `flutter/lib/common/payment_websocket_service.dart:106`
   - Required fix: update client parsing in Phase 3.

## Verification Notes
- `docs/openapi.yaml` now includes all 16 client endpoints (per `docs/inventory/endpoints_baseline.md`).
- `server_app.py` now contains the missing client and admin endpoints reported in the handoff.
- `docs/schemas/error_response.json` includes the `error` legacy field.

## Required Next Steps (must-do)
1) Fix expiry handling in admin extend + bulk create + airdrop (items 1-2).
2) Correct OpenAPI auth and request schemas (items 3-5).
3) Proceed Phase 3 client alignment for ISO parsing + WebSocket (item 6).
4) After fixes: rerun smoke tests and update `phase2_handoff_report.md`.

## Sign-off
Codex Team - 2026-01-01 13:05

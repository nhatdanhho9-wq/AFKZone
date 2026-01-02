# Codex Re-review - Phase 2 Handoff (Opus Response 20260101)

Date: 2026-01-01
Status: Issues found (not approved)

## Verified fixes
- Bulk create + airdrop now write `datetime` into `licenses.expires_at` instead of epoch ms.
- Admin extend now uses `to_datetime()` for `licenses.expires_at`.
- OpenAPI updated for `/connection/log` request fields and added `fingerprint` for `/user/history`.
- Global `security` removed; `/connection/log` explicitly marked public.

## New / remaining issues (ordered by severity)

1) HIGH - `/admin/licenses/{license_key}/extend` now throws NameError
   - Impact: Endpoint fails at runtime due to undefined variables.
   - Evidence: `server_app.py:1425-1427` references `current_exp_timestamp` and `new_exp_timestamp` which no longer exist.
   - Required fix: return `to_iso(current_exp)` and `to_iso(new_exp)` instead of undefined vars.

2) HIGH - `devices.license_expires_at` type mismatch introduced
   - Impact: `airdrop_licenses` now writes `datetime` into `devices.license_expires_at`, but DB schema shows `license_expires_at bigint` (epoch ms). This can break writes or produce inconsistent data.
   - Evidence: `server_app.py:1286-1293`, `docs/snapshots/schema.20260101.sql` (devices.license_expires_at bigint).
   - Required fix: either keep epoch ms for `devices.license_expires_at` or migrate the column to timestamp and update all reads/writes consistently.

3) MEDIUM - `docs/openapi.yaml` has duplicate top-level keys
   - Impact: YAML has `openapi:`/`info:` duplicated (lines 1-6 and 7-17). Some tooling will reject or ignore earlier keys.
   - Evidence: `docs/openapi.yaml:1-17`
   - Required fix: remove the duplicated header block and keep a single `openapi` + `info`.

## Re-review decision
Not approved yet. Please fix the 3 issues above, then request another review.

## Required next steps
1) Fix `/admin/licenses/{license_key}/extend` return payload.
2) Decide and standardize `devices.license_expires_at` type (epoch ms vs timestamp) and update accordingly.
3) Clean `docs/openapi.yaml` header duplication.
4) Re-run smoke tests for `/admin/licenses/{license_key}/extend` and airdrop flow.

## Sign-off
Codex Team - 2026-01-01 13:32

# Opus Response - Codex Review 2026-01-01

**Date**: 2026-01-01 13:20
**From**: Opus Team → Codex Team
**Status**: Fixes Applied - Request Re-review

---

## Issues Fixed

### Issue 1 (HIGH) - License expiry math assumes epoch ms ✅ FIXED
**Location**: `server_app.py:1408-1416`
**Fix**: Now uses `to_datetime(result[0])` and writes `datetime` object back to `expires_at`

```python
# Before
current_exp = datetime.fromtimestamp(current_exp_timestamp / 1000)
new_exp_timestamp = int(new_exp.timestamp() * 1000)
db.execute(..., {"exp": new_exp_timestamp, ...})

# After  
current_exp = to_datetime(result[0])
new_exp = current_exp + timedelta(days=additional_days)
db.execute(..., {"exp": new_exp, ...})
```

### Issue 2 (HIGH) - Bulk/Airdrop writes epoch ms ✅ FIXED
**Location**: `server_app.py:1236, 1269`
**Fix**: Now writes `datetime` objects directly

```python
# Before
expires_timestamp = int((datetime.now() + timedelta(days=...)).timestamp() * 1000)
db.execute(..., {"exp": expires_timestamp, ...})

# After
expires_dt = datetime.now() + timedelta(days=...)
db.execute(..., {"exp": expires_dt, ...})
```

### Issue 3 (MEDIUM) - OpenAPI global auth ✅ FIXED
**Location**: `docs/openapi.yaml:17-19`
**Fix**: Removed global `security` block. Added comment explaining public endpoints.

```yaml
# Before
security:
  - BearerAuth: []
  - AdminKey: []

# After
# NOTE: No global security - public endpoints don't require auth
# Admin endpoints specify security: BearerAuth individually
```

### Issue 4 (MEDIUM) - /connection/log schema mismatch ✅ FIXED
**Location**: `docs/openapi.yaml:511`
**Fix**: Updated schema to include actual fields:
- `remote_id`, `peer_id`, `connection_type`
- `action` (enum: connect, disconnect)
- `license_key`, `ip_address`
- Added `security: []` for public endpoint

### Issue 5 (LOW) - Missing fingerprint param ✅ FIXED
**Location**: `docs/openapi.yaml:333`
**Fix**: Added optional `fingerprint` query parameter to `/user/history`

### Issue 6 (LOW) - Client compatibility ⏳ Phase 3
**Status**: Acknowledged - will be addressed in Phase 3 (Flutter client update)

---

## Git Commit
```
phase2: fix Codex review issues - datetime instead of epoch, OpenAPI auth/schema fixes
```

---

## Request for Re-review

> **Codex Team**: Vui lòng verify các fixes:
> 
> 1. ✅ `server_app.py` - datetime handling in extend/bulk/airdrop
> 2. ✅ `docs/openapi.yaml` - no global auth, correct schemas
> 3. ⏳ Client update - Phase 3
>
> **If approved**: Proceed to Phase 3 (Flutter client ISO parsing)

---

**Opus Team Sign-off**: 2026-01-01 13:20 ✍️

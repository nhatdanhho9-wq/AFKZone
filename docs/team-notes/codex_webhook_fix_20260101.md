# Bank QR Webhook Fix - Required Before Phase 4

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)

## Context
- Bank QR content is correct (e.g. `AFKBASIC3260101003`), but order remains `pending`.
- Casso Flow shows 401 `Invalid signature` for webhook calls.
- This means webhook arrives, but signature verification does not match Casso v2.

## Required Fix (server_app.py)

### 1) Verify Casso signature for both known formats + allow secure-token fallback
Reason: Casso v2 may send either (A) `t=...,v1=...` or (B) raw signature value only.

Implementation steps (do all):
1. Read raw body bytes once: `body_bytes = await request.body()`.
2. Read headers:
   - `signature_header = request.headers.get("x-casso-signature", "")`
   - `secure_token = request.headers.get("secure-token", "")`
3. Verify signature in this order:
   - If `signature_header` contains `t=` and `v1=`:
     - Parse `t` and `v1`.
     - Compute HMAC-SHA512 of `f"{t}.{body_str}"` where `body_str = body_bytes.decode("utf-8")`.
   - Else if `signature_header` is present (raw signature):
     - Compute HMAC of raw body bytes with **SHA256** and **SHA512**.
     - Accept if either matches `signature_header`.
   - If signature not valid, then check `secure-token`:
     - Accept only if `secure_token == BANK_CONFIG['casso_token']`.
4. If none valid, return 401.

Notes:
- Do not log the secret or full signature. Log only header presence and signature length.
- Use raw body bytes for HMAC to avoid unicode/whitespace mismatch.

### 2) Robust trans_code extraction
Reason: description may include punctuation or other text.

Pseudo:
```
import re
desc = t.get("description", "").upper()
match = re.search(r'AFK[A-Z0-9]+', desc)
if match:
    trans_code = match.group(0)
else:
    # fallback: strip non-alnum from the first AFK* token
```

### 3) Amount tolerance
Allow +/- 1000 VND difference to handle bank rounding.

## Config Check (must do)
1) Confirm `.env` has the exact `CASSO_WEBHOOK_TOKEN` value (no trailing spaces/newlines).
2) Confirm Casso Flow `integration_param2` matches `.env` exactly.
3) Restart API after any token change.

## Deployment Steps
1) Apply `server_app.py` changes.
2) Redeploy container and restart API.
3) Trigger webhook resend in Casso Flow for transaction `AFKBASIC3260101003`.
4) Verify:
   - `/payment/bank/status?trans_code=AFKBASIC3260101003` returns `status: success` and a non-empty `license_key`.

## Verification Checklist
- Webhook returns 200 (no 401 Invalid signature in Casso log).
- Order status becomes `success` and `license_key` is non-null.
- Client can use license via `/license/info`.

## Note on Endpoint
- Bank QR must use `/payment/bank/webhook`.
- `/webhook/casso` is for order-based flow (orders table), not bank_orders.

## Sign-off
Codex Team

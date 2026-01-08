# Mobile UI Config: Signing, Caching, Rollback

This document defines how clients safely consume `mobile_ui_config`.

## Envelope

The server returns:

- `payload`: the actual config (validated by JSON Schema)
- `signature`: `{alg,key_id,sig}` signature over the canonical JSON of `payload`

## Canonicalization

To avoid platform differences, signatures are computed over **canonical JSON**:

- UTF-8
- Object keys sorted lexicographically at every level
- No insignificant whitespace
- Arrays preserved order

Recommendation:

- Backend uses a canonical JSON serializer.
- Client implements canonicalization or uses a library with deterministic encoding.

## Signature algorithm

- `alg`: `ed25519`
- `sig`: base64 over the raw signature bytes
- `key_id`: identifies which public key to use (supports rotation)

### Key management

- Clients ship with a **public key set** (or fetch a pinned key set) and accept only known `key_id`.
- Admin dashboard never stores private keys in the database.
- Signing is done by a separate **signing job/service** with restricted access.

## Client acceptance rules

Client accepts a config only if all conditions hold:

1. JSON validates against `mobile_ui_config.schema.json`
2. `payload.kill_switch` is false
3. Signature verifies for `payload`
4. `payload.issued_at` is not in the far future (clock skew allowed)
5. `payload.revision` >= cached revision (prevents rollback attacks)

If any condition fails:

- Use cached last-known-good config (LKG), if present
- Else use baked-in defaults

## Caching rules

- Cache key: `mobile_ui_config:lkg`
- Cache lifetime: **`payload.ttl_seconds`**
- Refresh strategy:
  - On app start: fetch config
  - Periodically: background refresh at `ttl_seconds / 2` (with jitter)
  - On hard failures: exponential backoff

## Rollback rules

Rollback is an **admin action** that produces a new signed config with a **higher revision** that references an older content state.

Rule: **clients never accept lower revision**.

Implementation options:

- **Option A (recommended)**: store config rows with `revision` increment; rollback creates a new revision with previous content.
- **Option B**: store snapshots; rollback creates a new snapshot row with new revision.

## Kill switch

`payload.kill_switch=true` instructs the client to fall back to baked-in defaults.

Use cases:

- Bad config shipped
- Emergency disable a module

Kill switch must still be signed.


# AFK Zone - Codex Plan Execution

## Phase 0: Freeze and Baseline ✅ COMPLETE
- [x] Tag baseline: `baseline-20260101`
- [x] Snapshots created & redacted

## Phase 1: Security and Secrets ✅ COMPLETE (STRICT)

### Strict Requirements
- [x] Removed all fallbacks (Admin, JWT, Bank, Zalo)
- [x] Added `require_env()` check - API fails if vars missing
- [x] Implemented Strict Webhook Verification (401 if invalid/missing signature)

### Repo & Server
- [x] Keystore removed from repo
- [x] .env.example updated with all required vars (no defaults)
- [x] Server .env updated
- [x] Verified verification logic on server

### Deployment
- [x] Server deployed with strict code
- [x] API restarted successfully

## Phase 2: API Contract Lock (NEXT)
- [ ] Review `docs/api_contract.md`
- [ ] Freeze field names (server response format)
- [ ] Remove unused endpoints

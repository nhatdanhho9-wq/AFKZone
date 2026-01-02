Phase 1 - Security Hardening (Opus Instructions)

Purpose
- Remove all hardcoded secrets
- Re-enable webhook verification
- Eliminate leaked signing keys from repo

Checklist
[ ] Move all secrets to env (server)
[ ] Rotate secrets (JWT, admin key, Casso token)
[ ] Enforce webhook signature verification
[ ] Remove keystore files from repo
[ ] Add validation checks (grep) to confirm no secrets in code
[ ] Deploy and verify critical flows still work

Server Tasks
1) Move secrets to env
- admin key (formerly "REDACTED_ADMIN_KEY")
- JWT secret (formerly hardcoded SECRET_KEY)
- Casso webhook token (formerly fallback in code)

2) Rotate secrets
- Generate new values for all three
- Update server .env
- Restart license-api container

3) Re-enable webhook verification
- Remove "accept all requests" block
- Ensure invalid signature returns error

4) Verify runtime
- Create bank order
- Trigger webhook with invalid signature (expect reject)
- Trigger valid webhook (expect success)

Repo Tasks
1) Remove keystore artifacts
- flutter/afkzone-release.jks
- keystore_base64.txt

2) Add .gitignore entries if needed
- *.jks
- keystore_base64.txt

3) Confirm no secrets in repo
- rg -n "afkzone-admin|SECRET_KEY|CASSO|keystore|jwt"

Definition of Done
- No secrets hardcoded in codebase
- Webhook rejects invalid signatures
- Keystore removed and rotated
- Security grep checks return zero hits

Notes
- If production depends on old admin key, coordinate cutover with team.
- Keep a secure backup of new keystore (not in Git).



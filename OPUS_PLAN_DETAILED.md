AFK Zone / RustDesk - Detailed Plan for Clean Structure and Stable Releases

Owner and Roles
- Project Director: You (final decisions, priorities, budget)
- Project Manager + Engineering Manager: Codex (this plan, scope control, quality gate, release readiness)
- Opus Team: Implementation team (backend, frontend, ops, QA) executing tasks below

Typical Roles in a Project (for clarity)
- Product Owner: defines business goals and user requirements
- Project Manager: schedule, risk, deliverables
- Engineering Manager: technical quality and delivery
- Tech Lead/Architect: architecture decisions and code standards
- Backend Engineer: API, DB, integrations
- Frontend/Mobile Engineer: Flutter UI and services
- DevOps/SRE: deployment, monitoring, secrets
- QA: test plans, regression, release sign-off

Goal
Build a clean, predictable, and debuggable project structure with a stable API contract so fixes do not re-break prior issues. This plan is designed to eliminate recurring regressions if followed without shortcuts.

Outcome Definition (what "clean and clear" means)
- Single source of truth for API contract and field names
- No hardcoded secrets or signing keys in repo
- One consistent time format for expires_at (chosen once and used everywhere)
- No duplicate routes or overlapping logic
- Clear folder structure with scripts, docs, and services separated
- Release process with smoke tests and rollback plan

Target Repo Structure (end state)
Note: Use this structure if you keep everything in one repo.

repo-root/
  docs/
    api_contract.md
    release_checklist.md
    adr/ (architecture decisions)
  client/
    flutter/ (current flutter/ contents)
  server/
    license-api/ (current ~/license-api, moved or submodule)
  rust-core/
    src/ and libs/ (current rustdesk code)
  scripts/
    maintenance/ (db cleanup, migrations)
    admin/ (dashboard helpers)
  infra/
    docker/ (compose, env samples)
  tools/
    lint/ (optional)

If you cannot move folders now, at least create:
- docs/api_contract.md (single source of truth)
- scripts/ (move all fix_*.py, add_*.py, check_*.py)

Phase 0 - Freeze and Baseline (0.5 to 1 day)
Objectives
- Prevent new regressions while fixing root problems
- Capture current state (code, schema, env)
Tasks
- Tag baseline state in Git
- Snapshot server app.py, docker-compose, and DB schema
- List all endpoints currently in server and client
Deliverables
- Baseline tag
- Inventory of endpoints and schema
Done Criteria
- Baseline recorded and reproducible

Phase 1 - Security and Secrets (1 day)
Objectives
- Remove immediate risk vectors
Tasks
- Re-enable webhook signature verification (remove accept-all)
- Move admin key, JWT secret, Casso token to env
- Rotate keys/secrets and update deployment env
- Remove keystore from repo and rotate if leaked
Deliverables
- No secrets in code
- Webhook signature enforced
Done Criteria
- Grep for secrets returns none in code
- Webhook rejects invalid signatures

Phase 2 - API Contract Lock (1 to 2 days)
Objectives
- Stop client/server drift
Tasks
- Write docs/api_contract.md (endpoints, payloads, response fields)
- Decide which endpoints to keep or remove:
  /license/info
  /license/logout
  /license/recover
  /user/history
  /tiers
  /ws/payment/{order_id}
  /connection/log
- Decide canonical fields:
  max_devices vs device_limit (choose one)
  expires_at format (choose one)
Deliverables
- Signed API contract
Done Criteria
- Opus team and PM sign off on contract

Phase 3 - Backend Stabilization (2 to 4 days)
Objectives
- Server strictly matches contract
Tasks
- Add/remove endpoints according to contract
- Normalize expires_at storage and serialization
  Recommended: store epoch_ms in DB, return epoch_ms in API
- Remove duplicate routes (admin extend)
- Unify connection logging endpoint and payload
- Ensure notifications logic uses correct device_id
Deliverables
- Server endpoints aligned to contract
- No duplicate routes
Done Criteria
- Contract checks pass for all endpoints

Phase 4 - Client Alignment (2 to 4 days)
Objectives
- Flutter uses contract with no fallback hacks
Tasks
- Align prefs keys to one canonical set (license_key, device_id, afk_license_active, afk_license_expires_at)
- Align max_devices/device_limit usage
- Align expires_at parsing (match contract format)
- Decide: keep WebSocket payment or remove
- If /tiers not in contract, remove tier fetch
Deliverables
- Client passes smoke tests
Done Criteria
- No client calls to missing endpoints

Phase 5 - Data Migration (0.5 to 1 day)
Objectives
- Avoid old data causing new errors
Tasks
- Migrate expires_at to the chosen format
- Clean license_devices where device_id is wrong
- Normalize devices table so notifications and status work
Deliverables
- Migration scripts
Done Criteria
- DB queries match contract expectations

Phase 6 - Regression Safety (2 days)
Objectives
- Prevent "fix one thing, break another"
Tasks
- Add smoke test scripts for 5 core flows:
  1) Trial check + generate
  2) Activate + check
  3) Bank order create + status
  4) Products list
  5) Notifications list
- Require these tests before merge/release
Deliverables
- smoke_tests.sh (or python) documented in docs/release_checklist.md
Done Criteria
- Tests pass on staging before prod

Phase 7 - Release Process (1 day)
Objectives
- Controlled releases with rollback
Tasks
- Staging deploy, run smoke tests
- Define rollback procedure (docker image tag + DB backup)
- Release checklist for each deploy
Deliverables
- release_checklist.md
Done Criteria
- Release can be rolled back within 30 minutes

Key Decisions to Lock Early (must not drift)
- Single API contract for both server and client
- Canonical expires_at format
- Canonical max_devices field
- Single endpoint for connection logging
- Single flow for payment notifications (WS or polling)

Definition of Done for Any Fix
- Reproduction steps documented
- Fix implemented
- Regression test added or updated
- Contract still matches
- Staging smoke tests pass
- Release note added

Communication and Control
- Daily status: what changed, what is blocked, risk updates
- Weekly plan review with Project Director
- No hotfix on prod without updating contract or tests

Risk Register (top risks)
- API contract drift (mitigation: contract gate)
- Secrets leakage (mitigation: env-only, rotate)
- Data format mismatch (mitigation: migration + strict checks)
- Untracked scripts creeping into prod (mitigation: scripts/ folder + review rules)

Success Metrics
- Zero regressions on last 3 releases
- 100 percent smoke test pass rate before prod
- No missing endpoint errors in logs
- Mean time to debug under 30 minutes

Final Note
This plan is intentionally strict. If Opus follows it without skipping contract and test gates, the project will become stable, clean, and easy to debug.


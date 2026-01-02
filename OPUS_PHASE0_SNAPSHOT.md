Phase 0 - Freeze and Baseline (Opus Instructions + Snapshot)

Purpose
- Capture a stable baseline before any further fixes.
- Provide a single place for Opus to check what is done and what is missing.

How Opus should use this file
1) Open this file first.
2) Verify each checklist item.
3) Fill in missing sections with actual values.
4) Only after all items are complete, continue to Phase 1.

Status Summary (current review)
Done (partial)
- Server reachable: automation@172.26.31.115
- app.py exists at ~/license-api/app.py
- Endpoint inventory draft exists in this file
- Client endpoint inventory draft exists in this file

Missing
- Baseline Git tag (ex: baseline-YYYYMMDD)
- Server snapshot files committed (app.py, docker-compose, env)
- DB schema export saved
- Formal inventory files saved under docs/

Checklist (Phase 0)
[ ] Create baseline tag in Git (example: baseline-YYYYMMDD)
[ ] Snapshot server app.py -> docs/snapshots/app.py.YYYYMMDD
[ ] Snapshot docker-compose.yml -> docs/snapshots/docker-compose.YYYYMMDD.yml
[ ] Snapshot env -> docs/snapshots/env.YYYYMMDD.txt (remove secrets before commit)
[ ] Export DB schema -> docs/snapshots/schema.YYYYMMDD.sql
[ ] Save server endpoint list -> docs/inventory/server_endpoints.md
[ ] Save client endpoint list -> docs/inventory/client_endpoints.md
[ ] Record working tree state (git status) -> docs/snapshots/git_status.YYYYMMDD.txt

Commands (Opus can copy)
Local (repo root)
- git tag -a baseline-YYYYMMDD -m "baseline snapshot"
- git status -sb > docs/snapshots/git_status.YYYYMMDD.txt

Server (replace SSH key path if needed)
- ssh -i C:\Users\admin\.ssh\id_rsa_ubuntu automation@172.26.31.115 "cat ~/license-api/app.py" > docs/snapshots/app.py.YYYYMMDD
- ssh -i C:\Users\admin\.ssh\id_rsa_ubuntu automation@172.26.31.115 "cat ~/license-api/docker-compose.yml" > docs/snapshots/docker-compose.YYYYMMDD.yml
- ssh -i C:\Users\admin\.ssh\id_rsa_ubuntu automation@172.26.31.115 "cat ~/.env" > docs/snapshots/env.YYYYMMDD.txt

DB schema export (example, on server)
- pg_dump -s -U postgres -h localhost -p 5433 afkzone_license > schema.YYYYMMDD.sql
- scp schema.YYYYMMDD.sql automation@172.26.31.115:~/schema.YYYYMMDD.sql
- scp automation@172.26.31.115:~/schema.YYYYMMDD.sql docs/snapshots/schema.YYYYMMDD.sql

Server Endpoint Inventory (draft from review)
Public
- GET /
- POST /activate
- POST /check
- POST /generate
- GET /list
- POST /trial/generate
- POST /trial/check
- POST /payment/create
- POST /payment/callback
- GET /version/check
- GET /health
- POST /payment/bank/create
- POST /payment/bank/webhook
- GET /payment/bank/status
- GET /products
- POST /heartbeat
- POST /user/license/renew
- POST /webhook/casso
- GET /notifications

Admin (JWT)
- POST /admin/login
- POST /admin/products
- PUT /admin/products/{product_id}
- DELETE /admin/products/{product_id}
- GET /admin/dashboard/stats
- GET /admin/users
- POST /admin/licenses/bulk-create
- POST /admin/licenses/airdrop
- POST /admin/licenses/{license_key}/revoke
- PUT /admin/licenses/{license_key}/extend
- GET /admin/analytics/revenue
- POST /admin/notifications
- GET /admin/notifications
- DELETE /admin/notifications/{notification_id}
- GET /admin/connections
- POST /admin/connections/log
- DELETE /admin/devices/{device_id}
- GET /admin/devices/{device_id}
- POST /admin/licenses/generate

Client Endpoint Inventory (draft from review)
- POST /trial/check
- POST /trial/generate
- POST /activate
- POST /check
- GET /version/check
- POST /payment/create
- POST /payment/bank/create
- GET /payment/bank/status
- GET /products
- GET /tiers
- GET /notifications
- POST /license/logout
- GET /license/info
- POST /license/recover
- GET /user/history
- POST /connection/log
- WS /ws/payment/{order_id}

Mismatch List (must be resolved after Phase 0)
- /license/logout (client) missing on server
- /license/info (client) missing on server
- /license/recover (client) missing on server
- /user/history (client) missing on server
- /connection/log (client) missing on server
- /tiers (client) missing on server
- /ws/payment/{order_id} (client) missing on server

Notes for Opus
- Do not fix anything before Phase 0 checklist is complete.
- Baseline tag is required for rollback.
- Use a consistent YYYYMMDD for snapshot files.


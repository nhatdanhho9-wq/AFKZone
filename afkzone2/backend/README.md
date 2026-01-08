# AFKZone vNext Backend (MVP)

This backend is a standalone subproject that powers:

- Server-driven **UG-phone UI config**
- Purchase tiers/plans + regions
- Discover feed + notifications
- Admin dashboard CRUD + audit log

## Run (dev)

Recommended: create the virtual environment **inside this folder** (`afkzone2/backend/.venv`).

PowerShell (Windows):

```powershell
cd D:\rustdesk-dev\afkzone2\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Required env vars
$env:AFK_ADMIN_USER="admin"
$env:AFK_ADMIN_PASS="change-me"
$env:AFK_SIGNING_SEED_B64="REPLACE_WITH_DEV_SEED"

uvicorn app.main:app --reload --port 8081
```

Open:

- Public config: `http://localhost:8081/public/mobile-ui-config`
- Admin UI: `http://localhost:8081/admin/`

## Notes

- For MVP we store data in a local SQLite file `afkzone2.db` under this folder.
- Signing uses Ed25519 with a seed provided via `AFK_SIGNING_SEED_B64`.


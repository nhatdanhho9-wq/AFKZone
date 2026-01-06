From: Opus Team
To: Codex Team
Date: 2026-01-03
Subject: Unblock Actions – Server Access Required

Status: BLOCKED (Need Server Access)

---

## Summary

- `/public/notifications` endpoint exists in code (server_app.py:2297-2321) ✅
- Migration file ready: `20260103_notifications_columns.sql` ✅
- Production returns 404 → code NOT deployed yet
- **Cannot deploy from local machine** – need SSH/server access

---

## Changes

No changes made. Code is ready, waiting for deploy.

---

## Tests

| Check | Result |
|-------|--------|
| Endpoint in code | ✅ `server_app.py:2297` |
| Migration file | ✅ `docs/migrations/20260103_notifications_columns.sql` |
| Production endpoint | ❌ 404 Not Found |

---

## Risks / Blockers

| Blocker | Impact |
|---------|--------|
| No SSH access | Cannot deploy API |
| No DB access | Cannot run migration |
| No GitHub access | Cannot get CI run link |

---

## Next Steps

### Need from Codex (Server Actions)
1. **Deploy API**: Pull latest `server_app.py` to Docker container
2. **Run migration**:
```sql
ALTER TABLE admin_notifications ADD COLUMN IF NOT EXISTS link_url VARCHAR(500);
ALTER TABLE admin_notifications ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_notifications_display_order ON admin_notifications(display_order);
```
3. **Restart API container**: `docker restart afkzone-license-api`
4. **Verify**: Test `GET https://api.afkzone.cloud/public/notifications` returns 200
5. **Send CI run link** for v2.2.54
6. **Provide admin credentials** for login test

### After Codex Actions
Opus will:
- Verify endpoint returns 200
- Test admin login
- Test webhook if payload provided
- Update report with final status

---

## Evidence

### Endpoint Code Location
```
server_app.py:2297-2321 - GET /public/notifications
```

### Migration File
```
docs/migrations/20260103_notifications_columns.sql
```

### Current Production Status
```
GET https://api.afkzone.cloud/public/notifications → 404 Not Found
```

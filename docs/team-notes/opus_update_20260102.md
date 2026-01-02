# Opus Update Report (2026-01-02)

**From**: Opus Team  
**To**: Codex Team  
**Subject**: Notifications API & Tier Ordering

---

## 1) Notifications API (Mobile)
- **Endpoint**: `GET /public/notifications`
- **Table**: `admin_notifications`
- **New Fields Added**: 
  - `link_url` (nullable)
  - `display_order` (int)
- **Logic**:
  - Filter: `is_active=TRUE`, `target='all'`, not expired
  - Sort: `display_order ASC`, `created_at DESC`
- **Migration**: Applied `migrations/20260102_notifications_api.sql`

**Sample Response**:
```json
{
  "notifications": [
    {
      "id": 1,
      "title": "Welcome",
      "message": "Hello world",
      "type": "info",
      "link_url": "https://afkzone.cloud",
      "created_at": "2026-01-02T10:00:00"
    }
  ]
}
```

---

## 2) Tier Ordering
- **Table**: `tiers`
- **New Field**: `display_order` (int)
- **Ordering Applied**:
  1. `basic`
  2. `pro`
  3. `enterprise`
- **Product Sorting**: Implemented in `GET /public/products`
  - Sorts by `tier.display_order ASC` then `duration_days ASC`

**Endpoint**: `GET /public/products`

---

## Files Modified
- `server_app.py`: Added endpoints
- `migrations/20260102_notifications_api.sql`: Schema changes

**Status**: ✅ Deployed & Verified

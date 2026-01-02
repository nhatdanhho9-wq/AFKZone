# Phase 4 Plan - Admin Dashboard Rebuild + Future Phases

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)
Decision: Replace old admin dashboard with a new build. Old file stays only as reference until new UI is accepted, then remove or archive.

---

## 1) Goals and Scope (Phase 4)

### Goals
- New admin dashboard that gives full control over licenses, orders, products, tiers, devices, trials, notifications, analytics.
- UX: fast, readable, low error rate, works on mobile.
- Auth: JWT-only for admin (admin_key deprecated).
- Clear statuses + audit-friendly UI.

### Non-goals
- No new backend services unless listed in "Required Backend Changes".
- No redesign of client app.

---

## 2) Information Architecture (IA)

Left navigation (order matters):
1) Overview
2) Licenses
3) Orders (Bank + ZaloPay)
4) Products
5) Tiers
6) Devices
7) Trials
8) Connections
9) Notifications
10) Analytics
11) System Health
12) Settings (config + auth info)

Top bar:
- Search box (global for license_key, device_id, trans_code)
- Environment badge (staging/prod)
- User menu (logout)

---

## 3) Endpoint Mapping (current server)

### Auth
- POST `/admin/login` -> JWT token (store in localStorage)

### Overview
- GET `/admin/dashboard/stats`
- GET `/admin/analytics/revenue`
- GET `/health`

### Licenses
- GET `/admin/licenses/all`
- PUT `/admin/licenses/{license_key}/extend`
- POST `/admin/licenses/{license_key}/revoke`
- POST `/admin/licenses/{license_key}/unrevoke`
- DELETE `/admin/licenses/{license_key}`
- POST `/admin/licenses/generate`
- POST `/admin/licenses/bulk-create`
- POST `/admin/licenses/airdrop`

### Orders
- GET `/admin/orders`
- POST `/admin/orders/{trans_code}/complete`
- GET `/payment/bank/status?trans_code=...`

### Products
- GET `/products` (use for read)
- POST `/admin/products`
- PUT `/admin/products/{id}`
- DELETE `/admin/products/{id}`
- DELETE `/admin/products/{id}/permanent`
- POST `/admin/products/{id}/enable`
- POST `/admin/products/{id}/disable`

### Tiers
- GET `/admin/tiers`
- POST `/admin/tiers`
- PUT `/admin/tiers/{id}`
- DELETE `/admin/tiers/{id}`

### Devices
- GET `/admin/devices/detailed`
- GET `/admin/users` (extra device details)
- DELETE `/admin/devices/{device_id}`

### Trials
- GET `/admin/trial-devices`
- DELETE `/admin/trial-devices/{id}`
- DELETE `/admin/trial-devices`

### Connections
- GET `/admin/connections`

### Notifications
- GET `/admin/notifications`
- POST `/admin/notifications`
- DELETE `/admin/notifications/{id}`

---

## 4) UI Design Direction (new dashboard)

### Visual concept: "Sunlit Control Room"
- Bright, clean, warm background with subtle pattern.
- Strong contrast for tables and badges.
- Zero purple. No dark mode bias.

### Typography
- Headings: "Space Grotesk" (600/700)
- Body: "IBM Plex Sans" (400/500)
- Monospace: "JetBrains Mono" for keys and IDs

### Colors (CSS variables)
```
--bg-0: #F7F3ED;
--bg-1: #FFF9F0;
--panel: #FFFFFF;
--ink-900: #1E1B16;
--ink-700: #3F3A33;
--ink-500: #6D655B;
--accent-1: #E07A5F;  /* warm orange */
--accent-2: #3D7A6B;  /* deep teal */
--accent-3: #F2CC8F;  /* sand */
--success: #2E7D32;
--warn: #F4A261;
--danger: #C44536;
--border: #E6DED3;
```

### Layout
- Desktop: 12-column grid, left nav (260px), content (fluid).
- Mobile: nav collapses into drawer, tables become stacked cards.

### Motion
- Page load: staggered card fade + slide (120ms per card).
- Tab switch: quick fade (150ms).
- Loading: skeleton shimmer only for tables.

---

## 5) Component Spec

### KPIs (Overview)
- Cards: total licenses, active, expired, revenue (30d), pending orders.
- Each card shows delta percentage (if data available).

### Tables
Common features across tables:
- Search, filter, sort (client-side).
- Badges for status.
- Inline action menu (three-dot).
- Bulk actions only where supported (licenses, trial devices).

### Modals
Standard modal types:
- Create product/tier
- Extend license
- Airdrop licenses
- Create notification

### Forms
Always:
- Validate required fields.
- Show API error from `detail` and `message`.

---

## 6) Interaction Flows (key)

### Login
1) POST `/admin/login`
2) Save `access_token` in localStorage
3) Set `Authorization: Bearer <token>` for all admin calls
4) On 401: force logout + show toast

### License Actions
- Revoke: POST `/admin/licenses/{key}/revoke`
- Unrevoke: POST `/admin/licenses/{key}/unrevoke`
- Extend: PUT `/admin/licenses/{key}/extend?additional_days=N`
- Delete: DELETE `/admin/licenses/{key}`
- Create bulk: POST `/admin/licenses/bulk-create`
- Airdrop: POST `/admin/licenses/airdrop`

### Orders
- Filter by status (pending/success/failed)
- Manual complete: POST `/admin/orders/{trans_code}/complete`

### Notifications
Create:
- POST `/admin/notifications` with title, message, type, target, expires_at
List + delete

---

## 7) Implementation Blueprint (for Opus)

### File Structure
```
admin/
  index.html
  assets/
    css/app.css
    js/app.js
    js/api.js
    js/ui.js
    js/pages/*.js
```

### JS Modules
- api.js: `apiFetch(url, opts)` -> auto inject JWT, handle 401
- ui.js: modal/toast/skeleton helpers
- pages/*.js: one file per tab (licenses.js, products.js, etc.)

### Example: apiFetch (pseudo)
```
async function apiFetch(path, options={}) {
  const token = localStorage.getItem('jwt');
  const headers = {...(options.headers||{})};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {...options, headers});
  if (res.status === 401) { logout(); throw new Error('Unauthorized'); }
  return res.json();
}
```

### Serving the dashboard
- Option A: API route `/admin` serves `admin/index.html`
- Option B: Nginx serves static dashboard at `/admin/`
Decision: choose one and remove old `admin_dashboard_current.html`.

---

## 8) Phase 4 Plan (detailed)

### Phase 4.1 - Stabilization + Admin Dashboard Rebuild
Deliverables:
- New dashboard UI (replace old)
- JWT-only admin auth everywhere
- Webhook QR content parsing fix (strip punctuation)
- Monitoring: add `/health` panel with status + last 5 errors (optional)

Tasks:
1) Design system + UI layout (tokens, fonts, grid)
2) Build skeleton pages + routing
3) Implement API layer + auth handling
4) Implement each tab with API mapping
5) QA: manual tests per tab + smoke tests
6) Remove/Archive old dashboard

Acceptance:
- All admin tabs functional with existing endpoints
- Works on mobile + desktop
- No 401 loops; clear logout
- KPI counts accurate

---

## 9) Phase 5-7 Plans (overview)

### Phase 5 - Cleanup + Refactor
- Remove dead scripts and duplicate docs
- Consolidate config and endpoints doc
- Remove admin_key usage from code/docs
- Align OpenAPI admin paths and add security tags
- Add linting + formatting rules

### Phase 6 - Automation / CI
- Add smoke test script to CI
- Pre-commit hooks for lint + schema validation
- Automated deploy pipeline (staging -> prod)
- Nightly health checks + webhook test

### Phase 7 - Performance + Security
- Load testing: connection logs, orders, webhook
- DB index review (licenses.created_at, bank_orders.trans_code)
- Security audit: JWT expiry, webhook signature
- Dependency scanning + SAST

---

## 10) Required Backend Changes (if needed)

1) `/admin` route to serve new UI OR static hosting config.
2) Webhook trans_code normalization:
   - Extract `AFK[A-Z0-9]+` from description
   - Strip punctuation (`.` `:` `,`) before lookup
3) Optional: add endpoints for metrics if dashboard needs more data.

---

## 11) Sign-off
Codex Team

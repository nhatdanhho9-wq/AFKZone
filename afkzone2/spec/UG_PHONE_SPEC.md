# UG Phone Spec Pack (AFK Zone vNext)

This document is the **single source of truth** for the UG-phone mobile UX and the server-driven configuration that controls it.

## Goals

- **UG parity**: Mobile UI matches UG-phone IA 1:1.
- **Admin-driven UI**: Most UI changes ship via **admin dashboard**, not by rebuilding APK/IPA.
- **No RustDesk dependency**: New app, new protocol, new services, new branding.

## Information architecture

### Bottom tabs (fixed set; server controls order + visibility)

1. **Device**
2. **Discover**
3. **Purchase**
4. **Me**

**Rule**: bottom tabs are always rendered from server config; the client only supports a known set of `route_type` values.

## App states

### Global state machine (simplified)

States are derived from **auth** (logged in/out), **entitlement** (licensed/unlicensed), and **device trust** (paired/unpaired).

- **S0: Anonymous**
  - Not logged in.
  - Can see: Discover (optional), Purchase (read-only pricing), Me (login entry), Device (controller UX allowed).
- **S1: Authenticated**
  - Logged in (has session).
  - Can see: Purchase (buy/restore), Me (account), Device (controller).
- **S2: Entitled**
  - Logged in + active entitlement (subscription/license).
  - Can see: all enabled actions, including premium actions defined by server flags.
- **S3: Paired/Trusted Device**
  - Device has a long-lived device key and is trusted for unattended access.
  - Enables: unattended access flows (host-side policies may still apply).

**Rule**: UI config can declare `requires_auth` / `requires_entitlement` / `requires_trust` per action; the client must enforce it locally and also rely on server authorization.

## Tabs and screens

### 1) Device tab

Purpose: remote control entry point (similar to “Connection”), plus quick actions row (replacing RustDesk’s extra tabs).

#### Primary widgets

- **Remote ID input** (or “Device code”/“Host ID” depending on your naming)
- **Connect CTA**
- **Quick actions row** (server-driven list)

#### Quick actions (examples)

From UG intent and product requirements, the Device tab must support at minimum:

- `open_recent`
- `open_favorites`
- `open_contacts`
- `share_screen_start` (start hosting / start service)
- `oauth_google_login` (if enabled)
- `scan_qr` (optional)

**Rule**: quick actions are *not* bottom tabs; they are **small functions** inside Device, driven by UI config.

### 2) Discover tab

Purpose: news/feed surface.

#### Content model

- Sections (e.g. “News”, “Play”) and cards
- Cards link to:
  - internal routes: `open_webview`, `open_article`, `open_purchase`
  - external URLs

**Rule**: Discover is fully server-driven (content + ordering).

### 3) Purchase tab

Purpose: pricing + purchase + region selection (UG parity).

#### Required UI

- Tier tabs (e.g. `UVIP`, `GVIP`, `KVIP`, `MVIP`) — labels are server-provided
- Supported games row (optional; server-driven)
- Server selection (regions with latency badges)
- Plan list (duration + price + discount labels)
- “Buy” CTA

#### Required backend data

- Regions list + recommended region + latency probe targets
- Plans grouped by tier + pricing
- Promotions/discount ribbons

### 4) Me tab

Purpose: account hub and “admin-controlled menu surface”.

#### Required UI

Top area:
- Account ID + copy button
- Wallet / currency (diamonds/coins) (if applicable)

Menu grid/list examples:
- Orders
- Redeem code
- Net check
- User Guide
- Support links (Discord/YouTube/Working hours)

**Rule**: Me menu items are fully server-driven. Each item maps to an `action_key` or URL.

## Action registry (contract between config and client)

The admin dashboard config references actions by `action_key`. Clients implement a fixed registry.

### Core action keys

- **Navigation**
  - `navigate_tab` (params: `{tab_id}`)
  - `open_route` (params: `{route_type, route_params}`)
  - `open_webview` (params: `{url, title?}`)
- **Auth**
  - `auth_login`
  - `auth_logout`
  - `oauth_google_login`
- **Device**
  - `connect_to_remote` (params: `{remote_id}`)
  - `share_screen_start`
  - `share_screen_stop`
  - `open_recent`
  - `open_favorites`
  - `open_contacts`
  - `scan_qr`
  - `net_check`
- **Purchase**
  - `open_purchase`
  - `select_region` (params: `{region_code}`)
  - `buy_plan` (params: `{plan_id}`)
  - `redeem_code` (params: `{code?}`)
- **Account**
  - `open_orders`
  - `copy_text` (params: `{text}`)

### Gating rules

Each action can declare requirements:

- `requires_auth`: boolean
- `requires_entitlement`: boolean
- `requires_trust`: boolean

Client behavior:

- If requirements not met: show login / purchase / trust flow entry.
- Never “pretend success”; always reflect server state.

## Routes supported by the client (route_type)

Clients must only accept these route types from server config:

- `tab_device`
- `tab_discover`
- `tab_purchase`
- `tab_me`
- `screen_orders`
- `screen_redeem`
- `screen_net_check`
- `screen_user_guide`
- `screen_webview`

Adding a new `route_type` requires a client release.

## Non-goals / constraints

- iOS host (being controlled) is likely limited by OS policies; controller-first is acceptable.
- Remote desktop protocol details are defined in separate documents; this spec focuses on **UG UI + admin-driven configurability**.


# Codex Review - Sonnet Milestone 1 (Admin Dashboard)

Date: 2026-01-02
Reviewer: Codex Team
Scope: `admin/` UI scaffold + Overview/Licenses/Orders
Decision: Approved to proceed to Phase 2 with required fixes listed below.

## Findings (ordered by severity)

### Medium
1) Garbled icons/text in navigation and placeholders
   - Sidebar icon glyphs render as corrupted characters (for example: `dY"S`, `dY"`).
   - File: `admin/index.html` (around lines 54-100).

2) Date formatter drops time
   - `formatDate()` uses `toLocaleDateString` with hour/minute options, but those are ignored.
   - File: `admin/assets/js/ui.js` (around `formatDate`).

3) Potential HTML injection in tables
   - License/order data is interpolated directly into `innerHTML` without escaping.
   - Latent XSS risk if any server values become untrusted.
   - Files:
     - `admin/assets/js/pages/licenses.js` (rows in `renderLicensesTable`)
     - `admin/assets/js/pages/orders.js` (rows in `renderOrdersTable`)

### Low
4) Action menu uses `prompt()` + full page reload
   - Usability issue; OK for milestone, but should be replaced by dropdown + local state update later.
   - File: `admin/assets/js/pages/licenses.js`

## What's Good
- Layout + design system matches spec (Sunlit Control Room).
- Auth + JWT storage + 401 handling implemented.
- Overview, Licenses, Orders wired to real APIs.
- Cross-team rules respected (admin-only changes).

## Required Fixes (before Phase 2 is considered done)
1) Replace garbled nav icons with proper icons (SVG/font/emoji).
2) Fix `formatDate()` to include time (use `toLocaleString`).
3) Sanitize/escape table cell values before injecting into `innerHTML`.

## Go-Ahead
Sonnet is approved to proceed to Phase 2 while fixing the above in parallel.

## Sign-off
Codex Team - 2026-01-02

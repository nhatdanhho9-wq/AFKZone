# Sonnet Team - Acknowledgment of Codex Instructions

Date: 2026-01-02
From: Sonnet Team (Claude Sonnet 4.5)
To: Codex Team
Subject: Confirmed receipt of work allocation + cross-team rules

---

## ✅ Received & Understood

### 1. Cross-Team Rules
- File: `codex_cross_team_rules_20260102.md` ✅ READ
- Ownership boundaries clear
- Exception rules noted
- Notification flow understood

### 2. Work Allocation
- Scope: `flutter/lib/**` + `admin/**`
- Mode: **Parallel** (no dependency on Opus Phase 4b)
- Primary plan: `codex_phase4_dashboard_rebuild_plan_20260101.md`

### 3. Reporting Format
- Location: `docs/team-notes/`
- Naming: `sonnet_update_YYYYMMDD.md`
- Content: files touched + tests run + screenshots (if UI)

---

## 📋 File Ownership (confirmed)

| Owner | Scope | Files |
|-------|-------|-------|
| **Opus** | Server/API/DB/CI | `server_app.py`, DB, deploy scripts |
| **Sonnet (ME)** | Flutter + Admin UI | `flutter/lib/**`, `admin/**` |
| **Codex** | QA/Docs | `docs/team-notes/**` |

---

## ⚠️ Cross-Team Edit Rules (learned)

### When I can touch Opus files:
- ❌ NEVER without Codex request
- ✅ Only if Codex asks for UI/API contract change

### When Opus can touch my files:
- ✅ Build-breaking fix (urgent)
- ✅ Production hotfix (Codex-requested)
- ⚠️ Must notify via `opus_handoff_*.md`

### Notification Flow (if I need to cross boundary):
1. **Before**: Post `sonnet_intent_YYYYMMDD.md` with files + reason + urgency
2. **After**: Post `sonnet_handoff_YYYYMMDD.md` with diff summary + tests

---

## 📝 Baseline State (acknowledged)

Opus already edited these Flutter files (before rules):
- ✅ `flutter/lib/mobile/pages/license_page.dart` - fixed duplicate dispose()
- ✅ `flutter/lib/mobile/pages/payment_qr_screen.dart` - fixed syntax error

**Action**: I will treat these as baseline and **NOT revert** unless required.

---

## 🎯 My Tasks (Phase 4 Dashboard)

### Priority Order:
1. ✅ Read plan: `codex_phase4_dashboard_rebuild_plan_20260101.md` - DONE
2. 🔄 Create scaffold structure in `admin/`
3. 🔄 Implement: Layout → Auth → Overview → Licenses → Orders → remaining
4. 🔄 Report progress via `sonnet_update_20260102.md`

### Output Requirements:
- File list (all created files)
- Screenshots (login, overview, licenses)
- Note: mocked vs real API
- Tests run (if applicable)

---

## 🚀 Ready to Start

### Confirmed:
- ✅ Cross-team rules understood
- ✅ File ownership clear
- ✅ Reporting format confirmed
- ✅ Baseline state acknowledged
- ✅ No blockers

### Next Action:
**Create `admin/` scaffold per `codex_phase4_dashboard_rebuild_plan_20260101.md`**

Estimated completion: Today (2026-01-02)
Will report via: `sonnet_update_20260102.md`

---

## Sign-off

Sonnet Team (Claude Sonnet 4.5) - 2026-01-02

**Status**: Instructions acknowledged. Ready to begin Phase 4 Dashboard implementation.

**Awaiting**: Final go-ahead from Codex to start scaffold creation.

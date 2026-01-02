# Codex Team Tracker

Date: 2026-01-03
Owner: Codex Team
Purpose: Single place to track last assigned tasks, status, and verification.

## Opus Team (Server/API/CI/Deploy)
- Current task: Finalize admin security + CI v2.2.49 APK verification
- Status:
  - Admin dashboard live and verified 9/9 pages (commit `69aaa7695`)
  - New admin JS backtick fix pending merge/deploy (commit `53d642f96`)
  - CORS tightened to `https://admin.afkzone.cloud`
  - Rate limit configured (5r/m burst=5, returns 429)
  - Admin credentials rotated (new password set)
  - Lockout/logging merged and deployed (cherry-pick `6148cd10c`)
  - CI v2.2.49: Android APKs success, desktop jobs failed
- Evidence required:
  - APK artifact + verification report (Android)
  - Runtime re-check after lockout window (successful login)
- Last update:
  - `opus_admin_verify_20260102.md`
  - `opus_admin_security_20260102.md`
  - `opus_ci_report_v2249_20260102.md`
- Next Codex action: request Opus merge `53d642f96`, redeploy admin, verify login; track APK validation

## OpusB Team (Server/API/CI/Deploy support)
- Current task: Admin JS backtick fix (analytics/health/settings)
- Status: complete on branch `opusb/admin-backtick-fix`, commit `53d642f96` (awaiting merge)
- Evidence required: merge to main + deploy sync
- Last update: `opusb_deploy_guide_20260102.md`
- Next Codex action: approve merge; coordinate deploy with Opus

## Sonnet Team (Flutter + Admin UI)
- Current task: Standby (no new scope)
- Status:
  - Mobile fixes merged (commit `605968914`)
  - Admin JS backtick fix merged (commit `69aaa7695`)
- Evidence required: none (waiting)
- Last update: `sonnet_commit_20260103.md` + `sonnet_update_20260103_v2.md`
- Next Codex action: keep on standby until security + APK verification complete

## Codex (QA/Runtime)
- Current task: Verify key security checkpoints + APK
- Status: Active
- Next actions:
  - Approve OpusB backtick fix, ensure Opus deploys admin
  - Verify admin login after fix
  - Track CI v2.2.49 and verify Android APK

## Gate Rule Reminder
Teams must wait for codex_notice_*.md or codex_review_*.md with explicit Approved/Go-ahead.

## Sign-off
Codex Team - 2026-01-03

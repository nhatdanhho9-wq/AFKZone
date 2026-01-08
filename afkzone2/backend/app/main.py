from __future__ import annotations

import base64
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import nacl.signing
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Import signaling router for WebRTC sessions
from app.signaling import router as signaling_router

# Import remote router for Remote MVP v0.1
from app.remote import router as remote_router

APP_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = APP_ROOT / "afkzone2.db"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(obj: Any) -> str:
    # Deterministic encoding for signing: sorted keys, no whitespace.
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


@dataclass(frozen=True)
class AdminCreds:
    user: str
    password: str


def _get_admin_creds() -> AdminCreds:
    return AdminCreds(
        user=os.getenv("AFK_ADMIN_USER", "admin"),
        password=_require_env("AFK_ADMIN_PASS"),
    )


def _basic_auth_guard(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="AFK Admin"'},
        )
    try:
        raw = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
        user, pw = raw.split(":", 1)
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
    creds = _get_admin_creds()
    if user != creds.user or pw != creds.password:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="AFK Admin"'},
        )


def _get_signing_key() -> Tuple[str, nacl.signing.SigningKey]:
    """
    Returns (key_id, signing_key) for Ed25519 signing.
    Seed is a 32-byte value encoded as base64.
    """
    seed_b64 = _require_env("AFK_SIGNING_SEED_B64")
    try:
        seed = base64.b64decode(seed_b64)
        if len(seed) != 32:
            raise ValueError("Seed must be 32 bytes")
    except Exception as e:
        raise RuntimeError(f"Invalid AFK_SIGNING_SEED_B64: {e}")
    key_id = os.getenv("AFK_SIGNING_KEY_ID", "dev-key")
    return key_id, nacl.signing.SigningKey(seed)


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _db_init() -> None:
    conn = _db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ui_config (
          revision INTEGER PRIMARY KEY,
          payload_json TEXT NOT NULL,
          signature_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          created_by TEXT NOT NULL,
          comment TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT NOT NULL,
          actor TEXT NOT NULL,
          action TEXT NOT NULL,
          entity_type TEXT NOT NULL,
          entity_id TEXT NOT NULL,
          detail_json TEXT
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS region (
          code TEXT PRIMARY KEY,
          label TEXT NOT NULL,
          probe_host TEXT NOT NULL,
          is_default INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS plan (
          plan_id TEXT PRIMARY KEY,
          tier_id TEXT NOT NULL,
          duration_days INTEGER NOT NULL,
          price_cents INTEGER NOT NULL,
          currency TEXT NOT NULL,
          discount_pct INTEGER NOT NULL DEFAULT 0,
          is_active INTEGER NOT NULL DEFAULT 1
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notification (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          message TEXT NOT NULL,
          link_url TEXT,
          created_at TEXT NOT NULL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS discover_section (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS discover_card (
          id TEXT PRIMARY KEY,
          section_id TEXT NOT NULL,
          title TEXT NOT NULL,
          subtitle TEXT,
          image_url TEXT NOT NULL,
          action_id TEXT NOT NULL,
          FOREIGN KEY(section_id) REFERENCES discover_section(id)
        );
        """
    )
    conn.commit()
    conn.close()


class UiConfigPayload(BaseModel):
    schema_version: int = Field(ge=1)
    revision: int = Field(ge=1)
    issued_at: str
    ttl_seconds: int = Field(ge=30, le=86400)
    kill_switch: bool = False
    tabs: List[Dict[str, Any]]
    routes: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    content: Dict[str, Any] = {}


class UiConfigEnvelope(BaseModel):
    payload: UiConfigPayload
    signature: Dict[str, Any]


class UiConfigCreateRequest(BaseModel):
    payload: Dict[str, Any]
    comment: Optional[str] = None


class RegionUpsert(BaseModel):
    code: str = Field(min_length=2, max_length=16)
    label: str = Field(min_length=1, max_length=64)
    probe_host: str = Field(min_length=1, max_length=255)
    is_default: bool = False


class PlanUpsert(BaseModel):
    plan_id: str = Field(min_length=1, max_length=64)
    tier_id: str = Field(min_length=1, max_length=32)
    duration_days: int = Field(ge=1, le=3650)
    price_cents: int = Field(ge=0, le=10_000_000_00)
    currency: str = Field(min_length=1, max_length=8)
    discount_pct: int = Field(ge=0, le=100, default=0)
    is_active: bool = True


class NotificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    link_url: Optional[str] = None


class DiscoverSectionUpsert(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=64)


class DiscoverCardUpsert(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    section_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=128)
    subtitle: Optional[str] = None
    image_url: str = Field(min_length=1, max_length=2048)
    action_id: str = Field(min_length=1, max_length=64)


app = FastAPI(title="AFKZone vNext Backend (MVP)")

# Mount signaling router for WebRTC session management
app.include_router(signaling_router)

# Mount remote router for Remote MVP v0.1 (devices, trusted, share, remote)
app.include_router(remote_router)


@app.on_event("startup")
def _on_startup() -> None:
    _db_init()


admin_static_dir = APP_ROOT.parent / "admin" / "public"
app.mount("/admin/static", StaticFiles(directory=str(admin_static_dir)), name="admin-static")


@app.get("/admin/", response_class=HTMLResponse)
def admin_index(request: Request) -> Response:
    _basic_auth_guard(request)
    return FileResponse(str(admin_static_dir / "index.html"))


def _audit(actor: str, action: str, entity_type: str, entity_id: str, detail: Optional[Dict[str, Any]] = None) -> None:
    conn = _db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audit_log (ts, actor, action, entity_type, entity_id, detail_json) VALUES (?,?,?,?,?,?)",
        (_utc_now_iso(), actor, action, entity_type, entity_id, json.dumps(detail or {}, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def _get_actor(request: Request) -> str:
    # For MVP: derive actor from basic auth username.
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Basic "):
        try:
            raw = base64.b64decode(auth.split(" ", 1)[1]).decode("utf-8")
            user, _pw = raw.split(":", 1)
            return user
        except Exception:
            pass
    return "unknown"


def _get_latest_revision(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    row = cur.execute("SELECT MAX(revision) AS max_rev FROM ui_config").fetchone()
    return int(row["max_rev"] or 0)


def _sign_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    key_id, sk = _get_signing_key()
    canonical = _canonical_json(payload).encode("utf-8")
    sig = sk.sign(canonical).signature
    return {
        "alg": "ed25519",
        "key_id": key_id,
        "sig": base64.b64encode(sig).decode("ascii"),
    }


def _ensure_seed_config(conn: sqlite3.Connection) -> None:
    if _get_latest_revision(conn) != 0:
        return
    # Seed minimal UG config on first run.
    payload = {
        "schema_version": 1,
        "revision": 1,
        "issued_at": _utc_now_iso(),
        "ttl_seconds": 300,
        "kill_switch": False,
        "tabs": [
            {"id": "device", "label": "Device", "icon": "tab_device", "visible": True, "route_type": "tab_device"},
            {
                "id": "discover",
                "label": "Discover",
                "icon": "tab_discover",
                "visible": True,
                "route_type": "tab_discover",
            },
            {
                "id": "purchase",
                "label": "Purchase",
                "icon": "tab_purchase",
                "visible": True,
                "route_type": "tab_purchase",
            },
            {"id": "me", "label": "Me", "icon": "tab_me", "visible": True, "route_type": "tab_me"},
        ],
        "routes": [],
        "actions": [],
        "content": {"device": {"quick_action_ids": []}, "discover": {"sections": []}, "purchase": {}, "me": {}},
    }
    sig = _sign_payload(payload)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ui_config (revision, payload_json, signature_json, created_at, created_by, comment) VALUES (?,?,?,?,?,?)",
        (1, json.dumps(payload, ensure_ascii=False), json.dumps(sig), _utc_now_iso(), "system", "seed"),
    )
    conn.commit()


def _ensure_seed_catalog(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Regions
    n_regions = cur.execute("SELECT COUNT(*) AS c FROM region").fetchone()["c"]
    if int(n_regions) == 0:
        cur.execute(
            "INSERT INTO region (code,label,probe_host,is_default) VALUES (?,?,?,?)",
            ("sg", "Singapore", "ping-sg.example.com", 1),
        )
        cur.execute(
            "INSERT INTO region (code,label,probe_host,is_default) VALUES (?,?,?,?)",
            ("th", "Thailand", "ping-th.example.com", 0),
        )
    # Plans (placeholders)
    n_plans = cur.execute("SELECT COUNT(*) AS c FROM plan").fetchone()["c"]
    if int(n_plans) == 0:
        cur.execute(
            "INSERT INTO plan (plan_id,tier_id,duration_days,price_cents,currency,discount_pct,is_active) VALUES (?,?,?,?,?,?,?)",
            ("uvip_1d", "uvip", 1, 119, "USD", 25, 1),
        )
        cur.execute(
            "INSERT INTO plan (plan_id,tier_id,duration_days,price_cents,currency,discount_pct,is_active) VALUES (?,?,?,?,?,?,?)",
            ("uvip_7d", "uvip", 7, 269, "USD", 25, 1),
        )
    # Discover
    n_sections = cur.execute("SELECT COUNT(*) AS c FROM discover_section").fetchone()["c"]
    if int(n_sections) == 0:
        cur.execute("INSERT INTO discover_section (id,title) VALUES (?,?)", ("news", "News"))
    conn.commit()


@app.get("/public/mobile-ui-config")
def public_mobile_ui_config() -> JSONResponse:
    conn = _db()
    _ensure_seed_config(conn)
    _ensure_seed_catalog(conn)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT revision, payload_json, signature_json FROM ui_config ORDER BY revision DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=500, detail="UI config missing")
    return JSONResponse(
        {
            "payload": json.loads(row["payload_json"]),
            "signature": json.loads(row["signature_json"]),
        }
    )


@app.get("/public/regions")
def public_regions() -> JSONResponse:
    conn = _db()
    _ensure_seed_catalog(conn)
    cur = conn.cursor()
    rows = cur.execute("SELECT code,label,probe_host,is_default FROM region ORDER BY is_default DESC, code ASC").fetchall()
    conn.close()
    return JSONResponse({"regions": [dict(r) for r in rows]})


@app.get("/public/plans")
def public_plans(tier_id: Optional[str] = None) -> JSONResponse:
    conn = _db()
    _ensure_seed_catalog(conn)
    cur = conn.cursor()
    if tier_id:
        rows = cur.execute(
            "SELECT plan_id,tier_id,duration_days,price_cents,currency,discount_pct,is_active FROM plan WHERE tier_id=? AND is_active=1 ORDER BY duration_days ASC",
            (tier_id,),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT plan_id,tier_id,duration_days,price_cents,currency,discount_pct,is_active FROM plan WHERE is_active=1 ORDER BY tier_id ASC, duration_days ASC"
        ).fetchall()
    conn.close()
    return JSONResponse({"plans": [dict(r) for r in rows]})


@app.get("/public/notifications")
def public_notifications() -> JSONResponse:
    conn = _db()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id,title,message,link_url,created_at FROM notification ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return JSONResponse({"notifications": [dict(r) for r in rows]})


@app.get("/public/discover")
def public_discover() -> JSONResponse:
    conn = _db()
    _ensure_seed_catalog(conn)
    cur = conn.cursor()
    sections = cur.execute("SELECT id,title FROM discover_section ORDER BY id ASC").fetchall()
    out_sections = []
    for s in sections:
        cards = cur.execute(
            "SELECT id,title,subtitle,image_url,action_id FROM discover_card WHERE section_id=? ORDER BY id ASC",
            (s["id"],),
        ).fetchall()
        out_sections.append({"id": s["id"], "title": s["title"], "cards": [dict(c) for c in cards]})
    conn.close()
    return JSONResponse({"sections": out_sections})


@app.get("/admin/api/ui-configs")
def admin_list_ui_configs(request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    conn = _db()
    _ensure_seed_config(conn)
    _ensure_seed_catalog(conn)
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT revision, created_at, created_by, comment FROM ui_config ORDER BY revision DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return JSONResponse({"items": [dict(r) for r in rows]})


@app.get("/admin/api/regions")
def admin_regions(request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    conn = _db()
    _ensure_seed_catalog(conn)
    cur = conn.cursor()
    rows = cur.execute("SELECT code,label,probe_host,is_default FROM region ORDER BY is_default DESC, code ASC").fetchall()
    conn.close()
    return JSONResponse({"regions": [dict(r) for r in rows]})


@app.post("/admin/api/regions")
def admin_upsert_region(req: RegionUpsert, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    if req.is_default:
        cur.execute("UPDATE region SET is_default=0")
    cur.execute(
        "INSERT INTO region (code,label,probe_host,is_default) VALUES (?,?,?,?) "
        "ON CONFLICT(code) DO UPDATE SET label=excluded.label, probe_host=excluded.probe_host, is_default=excluded.is_default",
        (req.code, req.label, req.probe_host, 1 if req.is_default else 0),
    )
    conn.commit()
    conn.close()
    _audit(actor=actor, action="upsert", entity_type="region", entity_id=req.code)
    return JSONResponse({"ok": True})


@app.delete("/admin/api/regions/{code}")
def admin_delete_region(code: str, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    cur.execute("DELETE FROM region WHERE code=?", (code,))
    conn.commit()
    conn.close()
    _audit(actor=actor, action="delete", entity_type="region", entity_id=code)
    return JSONResponse({"ok": True})


@app.get("/admin/api/plans")
def admin_plans(request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    conn = _db()
    _ensure_seed_catalog(conn)
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT plan_id,tier_id,duration_days,price_cents,currency,discount_pct,is_active FROM plan ORDER BY tier_id ASC, duration_days ASC"
    ).fetchall()
    conn.close()
    return JSONResponse({"plans": [dict(r) for r in rows]})


@app.post("/admin/api/plans")
def admin_upsert_plan(req: PlanUpsert, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO plan (plan_id,tier_id,duration_days,price_cents,currency,discount_pct,is_active) VALUES (?,?,?,?,?,?,?) "
        "ON CONFLICT(plan_id) DO UPDATE SET tier_id=excluded.tier_id, duration_days=excluded.duration_days, price_cents=excluded.price_cents, currency=excluded.currency, discount_pct=excluded.discount_pct, is_active=excluded.is_active",
        (
            req.plan_id,
            req.tier_id,
            req.duration_days,
            req.price_cents,
            req.currency,
            req.discount_pct,
            1 if req.is_active else 0,
        ),
    )
    conn.commit()
    conn.close()
    _audit(actor=actor, action="upsert", entity_type="plan", entity_id=req.plan_id)
    return JSONResponse({"ok": True})


@app.delete("/admin/api/plans/{plan_id}")
def admin_delete_plan(plan_id: str, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    cur.execute("DELETE FROM plan WHERE plan_id=?", (plan_id,))
    conn.commit()
    conn.close()
    _audit(actor=actor, action="delete", entity_type="plan", entity_id=plan_id)
    return JSONResponse({"ok": True})


@app.post("/admin/api/notifications")
def admin_create_notification(req: NotificationCreate, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notification (title,message,link_url,created_at) VALUES (?,?,?,?)",
        (req.title, req.message, req.link_url, _utc_now_iso()),
    )
    nid = cur.lastrowid
    conn.commit()
    conn.close()
    _audit(actor=actor, action="create", entity_type="notification", entity_id=str(nid))
    return JSONResponse({"ok": True, "id": nid})


@app.delete("/admin/api/notifications/{nid}")
def admin_delete_notification(nid: int, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    cur.execute("DELETE FROM notification WHERE id=?", (nid,))
    conn.commit()
    conn.close()
    _audit(actor=actor, action="delete", entity_type="notification", entity_id=str(nid))
    return JSONResponse({"ok": True})


@app.post("/admin/api/discover/sections")
def admin_upsert_discover_section(req: DiscoverSectionUpsert, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO discover_section (id,title) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title",
        (req.id, req.title),
    )
    conn.commit()
    conn.close()
    _audit(actor=actor, action="upsert", entity_type="discover_section", entity_id=req.id)
    return JSONResponse({"ok": True})


@app.post("/admin/api/discover/cards")
def admin_upsert_discover_card(req: DiscoverCardUpsert, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO discover_card (id,section_id,title,subtitle,image_url,action_id) VALUES (?,?,?,?,?,?) "
        "ON CONFLICT(id) DO UPDATE SET section_id=excluded.section_id, title=excluded.title, subtitle=excluded.subtitle, image_url=excluded.image_url, action_id=excluded.action_id",
        (req.id, req.section_id, req.title, req.subtitle, req.image_url, req.action_id),
    )
    conn.commit()
    conn.close()
    _audit(actor=actor, action="upsert", entity_type="discover_card", entity_id=req.id)
    return JSONResponse({"ok": True})


@app.delete("/admin/api/discover/cards/{card_id}")
def admin_delete_discover_card(card_id: str, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)
    conn = _db()
    cur = conn.cursor()
    cur.execute("DELETE FROM discover_card WHERE id=?", (card_id,))
    conn.commit()
    conn.close()
    _audit(actor=actor, action="delete", entity_type="discover_card", entity_id=card_id)
    return JSONResponse({"ok": True})


@app.get("/admin/api/ui-configs/{revision}")
def admin_get_ui_config(revision: int, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    conn = _db()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT revision, payload_json, signature_json, created_at, created_by, comment FROM ui_config WHERE revision=?",
        (revision,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse({**dict(row), "payload": json.loads(row["payload_json"]), "signature": json.loads(row["signature_json"])})


@app.post("/admin/api/ui-configs")
def admin_create_ui_config(req: UiConfigCreateRequest, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)

    payload = dict(req.payload)
    payload.setdefault("schema_version", 1)
    payload.setdefault("issued_at", _utc_now_iso())
    payload.setdefault("ttl_seconds", 300)
    payload.setdefault("kill_switch", False)
    payload.setdefault("routes", [])
    payload.setdefault("actions", [])
    payload.setdefault("content", {})

    conn = _db()
    _ensure_seed_config(conn)
    latest = _get_latest_revision(conn)
    new_rev = latest + 1
    payload["revision"] = new_rev

    signature = _sign_payload(payload)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ui_config (revision, payload_json, signature_json, created_at, created_by, comment) VALUES (?,?,?,?,?,?)",
        (new_rev, json.dumps(payload, ensure_ascii=False), json.dumps(signature), _utc_now_iso(), actor, req.comment),
    )
    conn.commit()
    conn.close()
    _audit(actor=actor, action="create", entity_type="ui_config", entity_id=str(new_rev), detail={"comment": req.comment})
    return JSONResponse({"ok": True, "revision": new_rev})


@app.post("/admin/api/ui-configs/{revision}/rollback")
def admin_rollback_ui_config(revision: int, request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    actor = _get_actor(request)

    conn = _db()
    _ensure_seed_config(conn)
    cur = conn.cursor()
    row = cur.execute("SELECT payload_json FROM ui_config WHERE revision=?", (revision,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")
    payload = json.loads(row["payload_json"])
    latest = _get_latest_revision(conn)
    new_rev = latest + 1
    payload["revision"] = new_rev
    payload["issued_at"] = _utc_now_iso()
    signature = _sign_payload(payload)
    cur.execute(
        "INSERT INTO ui_config (revision, payload_json, signature_json, created_at, created_by, comment) VALUES (?,?,?,?,?,?)",
        (new_rev, json.dumps(payload, ensure_ascii=False), json.dumps(signature), _utc_now_iso(), actor, f"rollback_to:{revision}"),
    )
    conn.commit()
    conn.close()
    _audit(actor=actor, action="rollback", entity_type="ui_config", entity_id=str(new_rev), detail={"from_revision": revision})
    return JSONResponse({"ok": True, "revision": new_rev, "rolled_back_to": revision})


@app.get("/admin/api/audit")
def admin_audit(request: Request) -> JSONResponse:
    _basic_auth_guard(request)
    conn = _db()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, ts, actor, action, entity_type, entity_id, detail_json FROM audit_log ORDER BY id DESC LIMIT 200"
    ).fetchall()
    conn.close()
    items = []
    for r in rows:
        d = dict(r)
        try:
            d["detail"] = json.loads(d.pop("detail_json") or "{}")
        except Exception:
            d["detail"] = {}
        items.append(d)
    return JSONResponse({"items": items})


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "ts": _utc_now_iso()}


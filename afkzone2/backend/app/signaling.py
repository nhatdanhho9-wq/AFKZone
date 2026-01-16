"""
AFKZone vNext - Realtime Core Signaling Service
WebRTC-first signaling for session creation, SDP/ICE exchange, and TURN credentials.

Spec reference: afkzone2/spec/REALTIME_TRANSPORT.md
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ==================== MODELS ====================

class SessionStartRequest(BaseModel):
    """Controller initiates a session to connect to a target device."""
    target_device_id: str = Field(min_length=1, max_length=128)
    features_requested: List[str] = []
    region: Optional[str] = None


class SessionHostAttachRequest(BaseModel):
    """Host attaches to a pending session."""
    host_device_id: str = Field(min_length=1, max_length=128)


class SessionResponse(BaseModel):
    """Response for session start/attach."""
    session_id: str
    token: str  # controller_token or host_token
    signaling_ws_url: str


class TurnCredentials(BaseModel):
    """TURN credentials for relay fallback."""
    urls: List[str]
    username: str
    credential: str
    ttl: int


# ==================== SIGNALING MESSAGE TYPES ====================

class SignalingMessage(BaseModel):
    """WebSocket signaling message envelope."""
    type: str = Field(..., pattern="^(sdp_offer|sdp_answer|ice_candidate|control_ready|error)$")
    session_id: str
    role: str = Field(..., pattern="^(host|controller)$")
    ts: str
    payload: Dict[str, Any] = {}


# ==================== SESSION STORE (IN-MEMORY FOR MVP) ====================

class Session:
    """Session state for signaling."""
    def __init__(
        self,
        session_id: str,
        target_device_id: str,
        controller_token: str,
        region: Optional[str] = None,
        features_requested: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ):
        self.session_id = session_id
        self.target_device_id = target_device_id
        self.controller_token = controller_token
        self.host_token: Optional[str] = None
        self.host_device_id: Optional[str] = None
        self.status = "pending"  # pending, active, closed, failed
        self.region = region or "default"
        self.features_requested = features_requested or []
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.closed_at: Optional[str] = None
        self.close_reason: Optional[str] = None
        self.request_id = request_id  # Link to remote_request
        self.host_ready = False  # Host has screen capture ready
        self.screen_capture_enabled = False
        
        # WebSocket connections
        self.controller_ws: Optional[WebSocket] = None
        self.host_ws: Optional[WebSocket] = None


class SessionStore:
    """In-memory session store for MVP."""
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._by_device: Dict[str, str] = {}  # device_id -> session_id (pending)
        self._by_request: Dict[str, str] = {}  # request_id -> session_id
        self._audit_log: List[Dict[str, Any]] = []
        self._rate_limiter: Dict[str, List[float]] = {}  # IP -> timestamps
    
    def create_session(
        self,
        target_device_id: str,
        region: Optional[str] = None,
        features_requested: Optional[List[str]] = None,
        request_id: Optional[str] = None,
    ) -> Session:
        session_id = secrets.token_urlsafe(16)
        controller_token = secrets.token_urlsafe(32)
        
        session = Session(
            session_id=session_id,
            target_device_id=target_device_id,
            controller_token=controller_token,
            region=region,
            features_requested=features_requested,
            request_id=request_id,
        )
        
        self._sessions[session_id] = session
        self._by_device[target_device_id] = session_id
        if request_id:
            self._by_request[request_id] = session_id
        
        self._audit("start", session_id, "controller", {
            "target_device_id": target_device_id,
            "region": region,
            "features": features_requested,
            "request_id": request_id,
        })
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)
    
    def get_pending_for_device(self, device_id: str) -> Optional[Session]:
        session_id = self._by_device.get(device_id)
        if session_id:
            session = self._sessions.get(session_id)
            if session and session.status == "pending":
                return session
        return None
    
    def attach_host(self, session_id: str, host_device_id: str) -> Optional[str]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        if session.status != "pending":
            return None
        if session.target_device_id != host_device_id:
            return None
        
        host_token = secrets.token_urlsafe(32)
        session.host_token = host_token
        session.host_device_id = host_device_id
        session.status = "active"
        
        self._audit("host_attach", session_id, "host", {
            "host_device_id": host_device_id,
        })
        
        return host_token
    
    def close_session(self, session_id: str, reason: str = "normal"):
        session = self._sessions.get(session_id)
        if session:
            session.status = "closed"
            session.closed_at = datetime.now(timezone.utc).isoformat()
            session.close_reason = reason
            
            # Cleanup device mapping
            if session.target_device_id in self._by_device:
                if self._by_device[session.target_device_id] == session_id:
                    del self._by_device[session.target_device_id]
            
            self._audit("close", session_id, "system", {"reason": reason})
    
    def _audit(self, event: str, session_id: str, actor: str, detail: Optional[Dict] = None):
        self._audit_log.append({
            "session_id": session_id,
            "event": event,
            "actor": actor,
            "detail": detail,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
    
    def get_audit_log(self, session_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        logs = self._audit_log
        if session_id:
            logs = [l for l in logs if l["session_id"] == session_id]
        return logs[-limit:]
    
    def check_rate_limit(self, ip: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """Returns True if rate limit exceeded."""
        now = time.time()
        
        if ip not in self._rate_limiter:
            self._rate_limiter[ip] = []
        
        # Clean old entries
        self._rate_limiter[ip] = [
            ts for ts in self._rate_limiter[ip] 
            if now - ts < window_seconds
        ]
        
        if len(self._rate_limiter[ip]) >= max_requests:
            return True
        
        self._rate_limiter[ip].append(now)
        return False
    
    def get_session_by_request_id(self, request_id: str) -> Optional[Session]:
        """Get session by request_id. Returns None if not found or expired."""
        session_id = self._by_request.get(request_id)
        if not session_id:
            return None
        session = self._sessions.get(session_id)
        if not session:
            return None
        # Check if session expired (5 min timeout)
        if session.status == "closed":
            return None
        return session
    
    async def set_host_ready(self, session_id: str, screen_capture: bool = False) -> bool:
        """
        Mark session as host ready and notify controller via WebSocket.
        Returns True if successful.
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.host_ready = True
        session.screen_capture_enabled = screen_capture
        
        self._audit("host_ready", session_id, "host", {
            "screen_capture": screen_capture,
        })
        
        # Notify controller via WebSocket if connected
        if session.controller_ws:
            try:
                await session.controller_ws.send_json({
                    "type": "host_ready",
                    "session_id": session_id,
                    "role": "system",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "payload": {"session_id": session_id},
                })
            except Exception:
                pass  # Controller may have disconnected
        
        return True


# Global session store
session_store = SessionStore()


# ==================== TURN CREDENTIALS ====================

# TURN config for MVP
# NOTE: For clean VPS deployments, set AFK_TURN_PUBLIC_HOST or AFK_TURN_URLS so clients
# don't depend on any pre-existing DNS like turn.afkzone.cloud.
TURN_SECRET = os.getenv("AFK_TURN_SECRET", "mock-for-dev")  # TODO: must be set in production

# Optional: explicit comma-separated TURN URLs (highest priority), e.g.
#   AFK_TURN_URLS="turn:171.253.168.44:3478,turn:171.253.168.44:3478?transport=tcp"
TURN_URLS_ENV = os.getenv("AFK_TURN_URLS", "").strip()

# Optional: public host/ip for TURN, used to construct default URLs.
TURN_PUBLIC_HOST = os.getenv("AFK_TURN_PUBLIC_HOST", "").strip()

# Fallback (legacy) mapping if neither env var is set.
TURN_SERVERS = {
    "default": "turn.afkzone.cloud",
    "vn": "turn-vn.afkzone.cloud",
    "sg": "turn-sg.afkzone.cloud",
}

# ==================== STARTUP LOGGING ====================
# Log TURN config at startup to prevent environment confusion

def _get_turn_config_summary() -> str:
    """Return a summary of which TURN config is active."""
    secret_preview = TURN_SECRET[:8] + "..." if len(TURN_SECRET) > 8 else TURN_SECRET
    if TURN_URLS_ENV:
        return f"TURN_URLS={TURN_URLS_ENV[:50]}... SECRET={secret_preview}"
    elif TURN_PUBLIC_HOST:
        return f"TURN_PUBLIC_HOST={TURN_PUBLIC_HOST} SECRET={secret_preview}"
    else:
        return f"TURN_FALLBACK=turn.afkzone.cloud SECRET={secret_preview}"

# Log at module load
print(f"TURN_CONFIG_STARTUP {_get_turn_config_summary()}")


def mint_turn_credentials(session_id: str, region: str = "default") -> TurnCredentials:
    """Generate short-lived TURN credentials (TURN REST API format)."""
    ttl = 3600  # 1 hour
    expires = int(time.time()) + ttl
    username = f"{expires}:{session_id}"
    password = hmac.new(
        TURN_SECRET.encode(), 
        username.encode(), 
        hashlib.sha1
    ).digest()
    
    # Resolve TURN URLs in priority order:
    #  1) AFK_TURN_URLS (explicit)
    #  2) AFK_TURN_PUBLIC_HOST (construct)
    #  3) TURN_SERVERS mapping (fallback)
    if TURN_URLS_ENV:
        urls = [u.strip() for u in TURN_URLS_ENV.split(",") if u.strip()]
    elif TURN_PUBLIC_HOST:
        urls = [f"turn:{TURN_PUBLIC_HOST}:3478", f"turn:{TURN_PUBLIC_HOST}:3478?transport=tcp"]
    else:
        turn_server = TURN_SERVERS.get(region, TURN_SERVERS["default"])
        urls = [f"turn:{turn_server}:3478", f"turn:{turn_server}:3478?transport=tcp"]

    return TurnCredentials(
        urls=urls,
        username=username,
        credential=base64.b64encode(password).decode(),
        ttl=ttl,
    )


# ==================== AUTHZ STUBS ====================

async def verify_jwt_stub(token: str) -> Dict[str, Any]:
    """Stub: returns mock user claims. Replace with real JWT verification."""
    return {
        "user_id": "stub-user",
        "tier": "pro",
        "features": ["file_transfer", "audio"],
    }


async def check_entitlement_stub(user_id: str, feature: str) -> bool:
    """Stub: always returns True for MVP."""
    return True


async def check_quota_stub(user_id: str) -> Dict[str, Any]:
    """Stub: returns mock quota."""
    return {
        "max_sessions": 5,
        "active_sessions": 0,
        "allowed": True,
    }


# ==================== ROUTER ====================

router = APIRouter(prefix="/sessions", tags=["signaling"])


@router.post("/start", response_model=SessionResponse)
async def session_start(req: SessionStartRequest, request: Request):
    """
    Controller initiates a session to connect to a target device.
    
    Returns session_id and signaling WebSocket URL.
    """
    # Rate limiting based on client IP
    client_ip = request.client.host if request.client else "unknown"
    if session_store.check_rate_limit(client_ip, max_requests=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 10 requests per minute.")
    
    # TODO: Verify JWT and check entitlements
    # user = await verify_jwt_stub(auth_header)
    # if not await check_entitlement_stub(user["user_id"], "remote_access"):
    #     raise HTTPException(status_code=403, detail="Not entitled to remote access")
    
    session = session_store.create_session(
        target_device_id=req.target_device_id,
        region=req.region,
        features_requested=req.features_requested,
    )
    
    return SessionResponse(
        session_id=session.session_id,
        token=session.controller_token,
        signaling_ws_url=f"/sessions/{session.session_id}/ws",
    )


@router.post("/host/attach", response_model=SessionResponse)
async def session_host_attach(req: SessionHostAttachRequest):
    """
    DEPRECATED: Use /remote/host-ready instead.
    
    This endpoint is deprecated and will return 410 Gone.
    Clients should migrate to the new /remote/host-ready/{request_id} flow.
    """
    return JSONResponse(
        status_code=410,
        content={
            "detail": "This endpoint is deprecated. Use /remote/host-ready/{request_id} instead.",
            "error_code": "HOST_ATTACH_DEPRECATED",
        },
        headers={"X-Error-Code": "HOST_ATTACH_DEPRECATED"},
    )


@router.get("/{session_id}/turn-credentials", response_model=TurnCredentials)
async def get_turn_credentials(session_id: str):
    """
    Get TURN credentials for relay fallback.
    
    Returns short-lived credentials (1 hour TTL).
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return mint_turn_credentials(session_id, session.region)


@router.get("/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session status."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "status": session.status,
        "target_device_id": session.target_device_id,
        "host_device_id": session.host_device_id,
        "region": session.region,
        "features_requested": session.features_requested,
        "started_at": session.started_at,
        "closed_at": session.closed_at,
    }


@router.get("/audit")
async def get_audit_log(session_id: Optional[str] = None, limit: int = 100):
    """Get session audit log."""
    return {"audit": session_store.get_audit_log(session_id, limit)}


# ==================== WEBSOCKET SIGNALING ====================

@router.websocket("/{session_id}/ws")
async def signaling_websocket(websocket: WebSocket, session_id: str, token: str):
    """
    WebSocket signaling channel for SDP/ICE exchange.
    
    Query params:
    - token: controller_token or host_token
    
    Message types:
    - sdp_offer: {type, sdp}
    - sdp_answer: {type, sdp}
    - ice_candidate: {candidate, sdpMid, sdpMLineIndex}
    - control_ready: {}
    - error: {code, message}
    """
    session = session_store.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    # Determine role from token
    role: Optional[str] = None
    if token == session.controller_token:
        role = "controller"
    elif token == session.host_token:
        role = "host"
    else:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await websocket.accept()
    
    # Store WebSocket connection
    if role == "controller":
        session.controller_ws = websocket
    else:
        session.host_ws = websocket
    
    session_store._audit("ws_connect", session_id, role, {})
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "session_id": session_id,
                    "role": "system",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "payload": {"code": 400, "message": "Invalid JSON"},
                })
                continue
            
            msg_type = msg.get("type")
            payload = msg.get("payload", {})
            
            # Forward message to the other peer
            target_ws: Optional[WebSocket] = None
            if role == "controller":
                target_ws = session.host_ws
            else:
                target_ws = session.controller_ws
            
            if target_ws:
                await target_ws.send_json({
                    "type": msg_type,
                    "session_id": session_id,
                    "role": role,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "payload": payload,
                })
                
                session_store._audit(f"ws_{msg_type}", session_id, role, {
                    "forwarded": True,
                })
            else:
                # Peer not connected yet
                await websocket.send_json({
                    "type": "error",
                    "session_id": session_id,
                    "role": "system",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "payload": {"code": 503, "message": "Peer not connected"},
                })
    
    except WebSocketDisconnect:
        session_store._audit("ws_disconnect", session_id, role, {})
        
        # Clear WebSocket reference
        if role == "controller":
            session.controller_ws = None
        else:
            session.host_ws = None
        
        # If both disconnected, close session
        if session.controller_ws is None and session.host_ws is None:
            session_store.close_session(session_id, "both_disconnected")

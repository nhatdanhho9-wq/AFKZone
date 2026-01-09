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
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

# Configure logging for session tracking
logger = logging.getLogger("signaling")
logger.setLevel(logging.INFO)

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
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
        controller_device_id: Optional[str] = None,
    ):
        self.session_id = session_id
        self.target_device_id = target_device_id
        self.controller_token = controller_token
        self.host_token: Optional[str] = None
        self.host_device_id: Optional[str] = None
        self.status = "pending"  # pending, active, connected, closed, failed
        self.region = region or "default"
        self.features_requested = features_requested or []
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.closed_at: Optional[str] = None
        self.close_reason: Optional[str] = None
        
        # Request tracking
        self.request_id = request_id
        self.controller_device_id = controller_device_id
        
        # WebSocket connections
        self.controller_ws: Optional[WebSocket] = None
        self.host_ws: Optional[WebSocket] = None
        
        # Lifecycle tracking
        self.lifecycle = {
            "host_session_ready_sent": False,
            "host_ws_connected": False,
            "host_ready": False,  # Host has enabled screen capture
            "host_screen_capture_ready": False,
            "controller_ws_connected": False,
            "controller_waiting_for_host": False,
            "sdp_offer_received": False,
            "sdp_offer_forwarded": False,
            "sdp_answer_received": False,
            "sdp_answer_forwarded": False,
            "ice_candidates_host": 0,
            "ice_candidates_controller": 0,
            "control_ready_received": False,
            "ice_state": None,  # checking, connected, failed, etc.
            "turn_relay_used": None,
            "video_track_reported": False,
            "audio_track_reported": False,
            "media_timeout_at": None,
        }
        
        # Timestamps
        self.timestamps = {
            "created": time.time(),
            "host_connected": None,
            "controller_connected": None,
            "sdp_offer": None,
            "sdp_answer": None,
            "ice_connected": None,
            "media_received": None,
        }
        
        # Detailed lifecycle log
        self.lifecycle_log: List[Dict[str, Any]] = []
        self.add_lifecycle_event("created", {"target_device_id": target_device_id, "region": region})

    def add_lifecycle_event(self, event: str, details: Optional[Dict[str, Any]] = None):
        """Record a timestamped lifecycle event."""
        self.lifecycle_log.append({
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event": event,
            "details": details or {}
        })
    
    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """Get a summary of session lifecycle for logging/debugging."""
        return {
            "session_id": self.session_id,
            "request_id": self.request_id,
            "host_device_id": self.host_device_id,
            "controller_device_id": self.controller_device_id,
            "status": self.status,
            "lifecycle": self.lifecycle,
            "timestamps": self.timestamps,
        }


class SessionStore:
    """In-memory session store for MVP."""
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._by_device: Dict[str, str] = {}  # device_id -> session_id (pending)
        self._audit_log: List[Dict[str, Any]] = []
        self._rate_limiter: Dict[str, List[float]] = {}  # IP -> timestamps
    
    def create_session(
        self,
        target_device_id: str,
        region: Optional[str] = None,
        features_requested: Optional[List[str]] = None,
    ) -> Session:
        session_id = secrets.token_urlsafe(16)
        controller_token = secrets.token_urlsafe(32)
        
        session = Session(
            session_id=session_id,
            target_device_id=target_device_id,
            controller_token=controller_token,
            region=region,
            features_requested=features_requested,
        )
        
        self._sessions[session_id] = session
        self._by_device[target_device_id] = session_id
        
        # P0: Full session tracking for debugging remote failures
        print(f"SESSION_CREATED session_id={session_id} request_id={session.request_id} controller={session.controller_device_id} host={target_device_id}")
        
        self._audit("start", session_id, "controller", {
            "target_device_id": target_device_id,
            "region": region,
            "features": features_requested,
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
    Host attaches to a pending session for its device_id.
    
    Returns session_id and signaling WebSocket URL.
    """
    # Find pending session for this device
    session = session_store.get_pending_for_device(req.host_device_id)
    if not session:
        raise HTTPException(
            status_code=404, 
            detail="No pending session for this device"
        )
    
    host_token = session_store.attach_host(session.session_id, req.host_device_id)
    if not host_token:
        raise HTTPException(
            status_code=409, 
            detail="Session already has a host attached"
        )
    
    return SessionResponse(
        session_id=session.session_id,
        token=host_token,
        signaling_ws_url=f"/sessions/{session.session_id}/ws",
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
async def get_session_status(session_id: str, include_lifecycle: bool = False):
    """
    Get session status and optionally full lifecycle data.
    
    Query params:
    - include_lifecycle: if true, returns detailed lifecycle tracking
    
    Use this to debug "Connected but black screen" issues.
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = {
        "session_id": session.session_id,
        "request_id": session.request_id,
        "status": session.status,
        "target_device_id": session.target_device_id,
        "host_device_id": session.host_device_id,
        "controller_device_id": session.controller_device_id,
        "region": session.region,
        "features_requested": session.features_requested,
        "started_at": session.started_at,
        "closed_at": session.closed_at,
    }
    
    # Quick diagnostics
    lc = session.lifecycle
    response["diagnostics"] = {
        "host_connected": lc["host_ws_connected"],
        "host_capture_ready": lc["host_ready"],  # Explicit host ready state
        "controller_connected": lc["controller_ws_connected"],
        "sdp_exchanged": lc["sdp_offer_forwarded"] and lc["sdp_answer_forwarded"],
        "ice_state": lc["ice_state"],
        "turn_relay_used": lc["turn_relay_used"],
        "video_track_ok": lc["video_track_reported"],
    }
    
    # Detect issues
    issues = []
    if not lc["host_ws_connected"]:
        issues.append("host_not_connected")
    if not lc["sdp_offer_received"]:
        issues.append("no_sdp_offer")
    if not lc["sdp_answer_received"]:
        issues.append("no_sdp_answer")
    if lc["ice_state"] == "failed":
        issues.append("ice_failed")
    if session.status == "connected" and not lc["video_track_reported"]:
        issues.append("connected_but_no_video")
    
    if issues:
        response["issues"] = issues
    
    if include_lifecycle:
        response["lifecycle"] = session.lifecycle
        response["timestamps"] = session.timestamps
        response["lifecycle_log"] = session.lifecycle_log
    
    return response


@router.post("/{session_id}/disconnect")
async def disconnect_session(session_id: str, reason: str = "user_disconnect"):
    """
    Disconnect a session and notify the peer.
    
    Called by controller to end session - sends remote_cancelled to host.
    Called by host to end session - sends session_ended to controller.
    
    Errors:
    - 404: Session not found
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_store._audit("http_disconnect", session_id, "api", {
        "reason": reason,
        "lifecycle": session.get_lifecycle_summary()
    })
    
    # Notify host
    if session.host_ws:
        try:
            await session.host_ws.send_json({
                "type": "remote_cancelled",
                "session_id": session_id,
                "role": "system",
                "ts": datetime.now(timezone.utc).isoformat(),
                "payload": {"reason": reason},
            })
        except Exception:
            pass
    
    # Notify controller
    if session.controller_ws:
        try:
            await session.controller_ws.send_json({
                "type": "session_ended",
                "session_id": session_id,
                "role": "system",
                "ts": datetime.now(timezone.utc).isoformat(),
                "payload": {"reason": reason},
            })
        except Exception:
            pass
    
    session_store.close_session(session_id, reason)
    
    return {"status": "disconnected", "session_id": session_id, "reason": reason}


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
    
    # Store WebSocket connection and update lifecycle
    if role == "controller":
        session.controller_ws = websocket
        session.lifecycle["controller_ws_connected"] = True
        session.timestamps["controller_connected"] = time.time()
        session.add_lifecycle_event("controller_connected", {"remote_address": websocket.client.host if websocket.client else None})
    else:
        session.host_ws = websocket
        session.lifecycle["host_ws_connected"] = True
        session.timestamps["host_connected"] = time.time()
        session.add_lifecycle_event("host_connected", {"remote_address": websocket.client.host if websocket.client else None})
    
    session_store._audit("ws_connect", session_id, role, {
        "lifecycle": session.get_lifecycle_summary()
    })
    
    # Set media timeout (30 seconds from controller connect)
    media_timeout_seconds = 30
    
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
            
            # Track lifecycle events
            if msg_type in ("sdp_offer", "sdp_answer", "control_ready", "ice_state", "host_ready", "controller_join", "media_track", "error"):
                 session.add_lifecycle_event(f"msg_{msg_type}", {"role": role})

            # Track lifecycle events logic (existing)
            if msg_type == "sdp_offer":
                session.lifecycle["sdp_offer_received"] = True
                session.timestamps["sdp_offer"] = time.time()
                # Set media timeout from offer time
                session.lifecycle["media_timeout_at"] = time.time() + media_timeout_seconds
                
            elif msg_type == "sdp_answer":
                session.lifecycle["sdp_answer_received"] = True
                session.timestamps["sdp_answer"] = time.time()
                
            elif msg_type == "ice_candidate":
                if role == "host":
                    session.lifecycle["ice_candidates_host"] += 1
                else:
                    session.lifecycle["ice_candidates_controller"] += 1
                # Check for relay candidate
                candidate_str = payload.get("candidate", "")
                if "relay" in candidate_str.lower() or "typ relay" in candidate_str.lower():
                    session.lifecycle["turn_relay_used"] = True
                    
            elif msg_type == "control_ready":
                session.lifecycle["control_ready_received"] = True
                session.status = "connected"
                
            elif msg_type == "host_ready":
                # Host reports it's ready with screen capture enabled
                session.lifecycle["host_ready"] = True
                session.lifecycle["host_screen_capture_ready"] = payload.get("screen_capture", False)
                session_store._audit("host_ready", session_id, role, {
                    "screen_capture": payload.get("screen_capture", False),
                })
                # Notify waiting controller
                if session.controller_ws and session.lifecycle["controller_waiting_for_host"]:
                    await session.controller_ws.send_json({
                        "type": "host_ready",
                        "session_id": session_id,
                        "role": "system",
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "payload": {"screen_capture": payload.get("screen_capture", False)},
                    })
                    session.lifecycle["controller_waiting_for_host"] = False
                    
            elif msg_type == "controller_join":
                # Controller wants to join - check if host is ready
                if not session.lifecycle["host_ready"]:
                    session.lifecycle["controller_waiting_for_host"] = True
                    session.add_lifecycle_event("error", {
                        "code": 503,
                        "error": "HOST_NOT_READY",
                        "message": "Controller joined but host not ready (waiting)"
                    })
                    await websocket.send_json({
                        "type": "error",
                        "session_id": session_id,
                        "role": "system",
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "payload": {
                            "code": 503,
                            "error": "HOST_NOT_READY",
                            "message": "Host has not enabled screen capture yet. Please wait.",
                        },
                    })
                else:
                    # Host is ready, proceed
                    await websocket.send_json({
                        "type": "host_ready",
                        "session_id": session_id,
                        "role": "system",
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "payload": {"screen_capture": session.lifecycle["host_screen_capture_ready"]},
                    })
                    
            elif msg_type == "controller_disconnect":
                # Controller wants to disconnect - notify host and close session
                session_store._audit("controller_disconnect", session_id, role, {
                    "lifecycle": session.get_lifecycle_summary()
                })
                # Notify host to stop capture
                if session.host_ws:
                    await session.host_ws.send_json({
                        "type": "remote_cancelled",
                        "session_id": session_id,
                        "role": "controller",
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "payload": {"reason": "controller_disconnected"},
                    })
                # Close session
                session_store.close_session(session_id, "controller_disconnected")
                await websocket.close(code=1000, reason="Session ended")
                
            elif msg_type == "ice_state":
                # Client reports ICE connection state
                ice_state = payload.get("state")
                session.lifecycle["ice_state"] = ice_state
                if ice_state == "connected" or ice_state == "completed":
                    session.timestamps["ice_connected"] = time.time()
                elif ice_state == "failed":
                    session.status = "failed"
                    session_store._audit("ice_failed", session_id, role, {
                        "lifecycle": session.get_lifecycle_summary()
                    })
                    
            elif msg_type == "media_track":
                # Client reports media track availability
                track_kind = payload.get("kind")  # "video" or "audio"
                if track_kind == "video":
                    session.lifecycle["video_track_reported"] = True
                    session.timestamps["media_received"] = time.time()
                elif track_kind == "audio":
                    session.lifecycle["audio_track_reported"] = True
                    
            elif msg_type == "no_video_track":
                # Host reports no video track available
                session_store._audit("no_video_track", session_id, role, {
                    "reason": payload.get("reason", "unknown"),
                    "lifecycle": session.get_lifecycle_summary()
                })
                # Notify controller about the error
                if session.controller_ws:
                    await session.controller_ws.send_json({
                        "type": "error",
                        "session_id": session_id,
                        "role": "system",
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "payload": {
                            "code": 503,
                            "error": "no_video_track",
                            "message": "Host has no video track available. Screen capture may have failed.",
                        },
                    })
            
            # Check media timeout
            if session.lifecycle["media_timeout_at"]:
                if time.time() > session.lifecycle["media_timeout_at"]:
                    if not session.lifecycle["video_track_reported"]:
                        # Timeout, no video received
                        session_store._audit("media_timeout", session_id, "system", {
                            "lifecycle": session.get_lifecycle_summary()
                        })
                        await websocket.send_json({
                            "type": "error",
                            "session_id": session_id,
                            "role": "system",
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "payload": {
                                "code": 504,
                                "error": "media_timeout",
                                "message": f"No video track received within {media_timeout_seconds}s",
                            },
                        })
                        session.lifecycle["media_timeout_at"] = None  # Only warn once
            
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
                
                # Track forwarding
                if msg_type == "sdp_offer":
                    session.lifecycle["sdp_offer_forwarded"] = True
                elif msg_type == "sdp_answer":
                    session.lifecycle["sdp_answer_forwarded"] = True
                
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
        session_store._audit("ws_disconnect", session_id, role, {
            "lifecycle": session.get_lifecycle_summary()
        })
        
        # Clear WebSocket reference
        if role == "controller":
            session.controller_ws = None
            session.lifecycle["controller_ws_connected"] = False
        else:
            session.host_ws = None
            session.lifecycle["host_ws_connected"] = False
        
        # If both disconnected, close session
        if session.controller_ws is None and session.host_ws is None:
            session_store.close_session(session_id, "both_disconnected")


# ==================== FAN-OUT NOTIFICATION SYSTEM ====================

class RemoteRequest(BaseModel):
    """Request to initiate remote access to a shared device."""
    share_creator_device_id: str = Field(min_length=1, max_length=128)
    requester_device_id: str = Field(min_length=1, max_length=128)
    requester_name: Optional[str] = None
    features_requested: List[str] = []


class RemoteRequestResponse(BaseModel):
    """Response for remote request creation."""
    request_id: str
    status: str  # pending, accepted, rejected, expired
    expires_at: str


class PendingRemoteRequest:
    """In-memory pending remote request."""
    def __init__(
        self,
        request_id: str,
        share_creator_device_id: str,
        requester_device_id: str,
        requester_name: Optional[str],
        features_requested: List[str],
        owner_user_id: str,
    ):
        self.request_id = request_id
        self.share_creator_device_id = share_creator_device_id
        self.requester_device_id = requester_device_id
        self.requester_name = requester_name
        self.features_requested = features_requested
        self.owner_user_id = owner_user_id
        self.status = "pending"  # pending, host_ready, accepted, rejected, expired, cancelled
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at.timestamp() + 120  # 120 second TTL (longer for host ready wait)
        
        # Host ready tracking
        self.host_ready = False
        self.host_screen_capture_ready = False
        self.session_id: Optional[str] = None
        self.controller_token: Optional[str] = None
        self.host_token: Optional[str] = None


class DeviceRegistry:
    """
    Manages device presence via WebSocket connections.
    Enables fan-out notifications to all devices of a user.
    """
    def __init__(self):
        # {user_id: {device_id: WebSocket}}
        self._ws_by_user: Dict[str, Dict[str, WebSocket]] = {}
        # {device_id: user_id}
        self._device_to_user: Dict[str, str] = {}
        # Pending remote requests: {request_id: PendingRemoteRequest}
        self._pending_requests: Dict[str, PendingRemoteRequest] = {}
        # Device to owner mapping (mock for MVP)
        self._device_owners: Dict[str, str] = {}
    
    async def register(self, user_id: str, device_id: str, ws: WebSocket):
        """Register a device WebSocket connection."""
        if user_id not in self._ws_by_user:
            self._ws_by_user[user_id] = {}
        self._ws_by_user[user_id][device_id] = ws
        self._device_to_user[device_id] = user_id
        self._device_owners[device_id] = user_id
    
    async def unregister(self, device_id: str):
        """Unregister a device WebSocket connection."""
        user_id = self._device_to_user.pop(device_id, None)
        if user_id and user_id in self._ws_by_user:
            self._ws_by_user[user_id].pop(device_id, None)
            if not self._ws_by_user[user_id]:
                del self._ws_by_user[user_id]
    
    def get_owner(self, device_id: str) -> Optional[str]:
        """Get owner user_id for a device."""
        return self._device_owners.get(device_id)
    
    def set_device_owner(self, device_id: str, user_id: str):
        """Set owner for a device (used when device registers)."""
        self._device_owners[device_id] = user_id
    
    async def notify_user_devices(self, user_id: str, message: dict) -> int:
        """
        Fan-out notification to all online devices of a user.
        Returns number of devices notified.
        """
        count = 0
        for device_id, ws in list(self._ws_by_user.get(user_id, {}).items()):
            try:
                await ws.send_json(message)
                count += 1
            except Exception:
                # Connection likely dead, will be cleaned on next heartbeat
                pass
        return count
    
    def create_pending_request(
        self,
        share_creator_device_id: str,
        requester_device_id: str,
        requester_name: Optional[str],
        features_requested: List[str],
    ) -> Optional[PendingRemoteRequest]:
        """Create a pending remote request."""
        owner_user_id = self.get_owner(share_creator_device_id)
        if not owner_user_id:
            return None
        
        request_id = secrets.token_urlsafe(16)
        request = PendingRemoteRequest(
            request_id=request_id,
            share_creator_device_id=share_creator_device_id,
            requester_device_id=requester_device_id,
            requester_name=requester_name,
            features_requested=features_requested,
            owner_user_id=owner_user_id,
        )
        self._pending_requests[request_id] = request
        return request
    
    def get_pending_request(self, request_id: str) -> Optional[PendingRemoteRequest]:
        """Get a pending request by ID."""
        req = self._pending_requests.get(request_id)
        if req and time.time() > req.expires_at:
            req.status = "expired"
        return req
    
    def get_pending_for_user(self, user_id: str) -> List[Dict]:
        """Get all pending requests for a user (for polling)."""
        now = time.time()
        result = []
        for req in self._pending_requests.values():
            if req.owner_user_id == user_id and req.status == "pending":
                if now > req.expires_at:
                    req.status = "expired"
                else:
                    result.append({
                        "request_id": req.request_id,
                        "share_creator_device_id": req.share_creator_device_id,
                        "requester_device_id": req.requester_device_id,
                        "requester_name": req.requester_name,
                        "features": req.features_requested,
                        "created_at": req.created_at.isoformat(),
                        "expires_at": datetime.fromtimestamp(req.expires_at, tz=timezone.utc).isoformat(),
                    })
        return result
    
    def update_request_status(self, request_id: str, status: str) -> bool:
        """Update status of a pending request."""
        req = self._pending_requests.get(request_id)
        if req and req.status == "pending":
            req.status = status
            return True
        return False
    
    def is_device_online(self, device_id: str) -> bool:
        """Check if a device is currently online (has WS connection)."""
        user_id = self._device_to_user.get(device_id)
        if not user_id:
            return False
        return device_id in self._ws_by_user.get(user_id, {})
    
    def get_device_ws(self, device_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for a specific device."""
        user_id = self._device_to_user.get(device_id)
        if not user_id:
            return None
        return self._ws_by_user.get(user_id, {}).get(device_id)


# Global device registry
device_registry = DeviceRegistry()


# ==================== REMOTE NOTIFICATION ENDPOINTS ====================

@router.post("/remote/request", response_model=RemoteRequestResponse)
async def create_remote_request(req: RemoteRequest, request: Request):
    """
    Create a remote access request and notify all owner's devices.
    
    This triggers fan-out notification to all online devices of the
    device owner so they can accept/reject the request.
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if session_store.check_rate_limit(client_ip, max_requests=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Create pending request
    pending = device_registry.create_pending_request(
        share_creator_device_id=req.share_creator_device_id,
        requester_device_id=req.requester_device_id,
        requester_name=req.requester_name,
        features_requested=req.features_requested,
    )
    
    if not pending:
        raise HTTPException(
            status_code=404,
            detail="Device not found or owner not registered"
        )
    
    # Fan-out notification to all owner's devices
    notification = {
        "type": "remote_pending",
        "request_id": pending.request_id,
        "share_creator_device_id": pending.share_creator_device_id,
        "requester_device_id": pending.requester_device_id,
        "requester_name": pending.requester_name,
        "features": pending.features_requested,
        "expires_at": datetime.fromtimestamp(pending.expires_at, tz=timezone.utc).isoformat(),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    
    notified_count = await device_registry.notify_user_devices(
        pending.owner_user_id,
        notification
    )
    
    session_store._audit("remote_request", pending.request_id, "requester", {
        "share_creator_device_id": pending.share_creator_device_id,
        "requester_device_id": pending.requester_device_id,
        "notified_devices": notified_count,
    })
    
    return RemoteRequestResponse(
        request_id=pending.request_id,
        status=pending.status,
        expires_at=datetime.fromtimestamp(pending.expires_at, tz=timezone.utc).isoformat(),
    )


@router.get("/remote/pending")
async def get_pending_requests(user_id: str):
    """
    Polling fallback: Get all pending remote requests for a user.
    
    Used when WebSocket is unavailable.
    """
    pending = device_registry.get_pending_for_user(user_id)
    return {"pending": pending}


@router.post("/remote/respond/{request_id}")
async def respond_to_request(request_id: str, accept: bool, responding_device_id: Optional[str] = None):
    """
    Accept or reject a remote request (Step 1: Owner clicks Accept).
    
    If accepted:
    - Sets status to "wait_host_ready"
    - Does NOT create session yet
    - Notifies host to enable screen capture
    - Controller waits for host_ready signal
    
    Host must call /remote/host-ready/{request_id} after enabling screen capture.
    
    Errors:
    - 404: Request not found
    - 409: Request already handled
    - 503: Host device offline
    """
    pending = device_registry.get_pending_request(request_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if pending.status not in ["pending"]:
        raise HTTPException(
            status_code=409,
            detail=f"Request already {pending.status}"
        )
    
    if accept:
        # Check if host device is online
        host_device_id = pending.share_creator_device_id
        if not device_registry.is_device_online(host_device_id):
            raise HTTPException(
                status_code=503,
                detail="Host device is offline. Cannot establish connection."
            )
        
        # Set status to wait_host_ready - session NOT created yet
        device_registry.update_request_status(request_id, "wait_host_ready")
        
        session_store._audit("remote_accept_wait", request_id, "owner", {
            "host_device_id": host_device_id,
            "responding_device_id": responding_device_id,
            "status": "wait_host_ready",
        })
        
        # Notify host device to enable screen capture
        host_ws = device_registry.get_device_ws(host_device_id)
        if host_ws:
            try:
                await host_ws.send_json({
                    "type": "enable_screen_capture",
                    "request_id": request_id,
                    "requester_device_id": pending.requester_device_id,
                    "requester_name": pending.requester_name,
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                pass
        
        # Notify requester that we're waiting for host to enable capture
        await device_registry.notify_user_devices(
            device_registry.get_owner(pending.requester_device_id) or "",
            {
                "type": "wait_host_ready",
                "request_id": request_id,
                "message": "Host is enabling screen capture. Please wait...",
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        return {
            "status": "wait_host_ready",
            "request_id": request_id,
            "message": "Waiting for host to enable screen capture. Session will be created when host is ready.",
        }
    else:
        device_registry.update_request_status(request_id, "rejected")
        
        session_store._audit("remote_rejected", request_id, "owner", {
            "responding_device_id": responding_device_id,
        })
        
        # Notify requester that request was rejected
        await device_registry.notify_user_devices(
            device_registry.get_owner(pending.requester_device_id) or "",
            {
                "type": "remote_rejected",
                "request_id": request_id,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        return {"status": "rejected"}


@router.post("/remote/host-ready/{request_id}")
async def host_ready_signal(request_id: str, screen_capture: bool = True):
    """
    Host signals it's ready (Step 2: Host enabled screen capture).
    
    Called by host after user grants screen capture permission.
    NOW creates the signaling session and notifies controller.
    
    Errors:
    - 404: Request not found
    - 409: Request not in wait_host_ready state
    - 400: Screen capture not enabled
    """
    pending = device_registry.get_pending_request(request_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if pending.status != "wait_host_ready":
        raise HTTPException(
            status_code=409,
            detail=f"Request in wrong state: {pending.status}. Expected: wait_host_ready"
        )
    
    if not screen_capture:
        raise HTTPException(
            status_code=400,
            detail="Screen capture must be enabled to proceed"
        )
    
    host_device_id = pending.share_creator_device_id
    
    # NOW create the signaling session
    session = session_store.create_session(
        target_device_id=host_device_id,
        features_requested=pending.features_requested,
        request_id=request_id,
        controller_device_id=pending.requester_device_id,
    )
    
    # Pre-attach host to session (host joins first)
    host_token = session_store.attach_host(session.session_id, host_device_id)
    
    # Update pending request with session info
    pending.host_ready = True
    pending.host_screen_capture_ready = screen_capture
    pending.session_id = session.session_id
    pending.controller_token = session.controller_token
    pending.host_token = host_token
    device_registry.update_request_status(request_id, "accepted")
    
    session_store._audit("host_ready", request_id, "host", {
        "session_id": session.session_id,
        "host_device_id": host_device_id,
        "screen_capture": screen_capture,
    })
    
    # Notify controller that host is ready - include session details!
    await device_registry.notify_user_devices(
        device_registry.get_owner(pending.requester_device_id) or "",
        {
            "type": "host_ready",
            "request_id": request_id,
            "session_id": session.session_id,
            "controller_token": session.controller_token,
            "signaling_ws_url": f"/sessions/{session.session_id}/ws",
            "host_device_id": host_device_id,
            "screen_capture": screen_capture,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    )
    
    return {
        "status": "accepted",
        "session_id": session.session_id,
        "host_token": host_token,
        "signaling_ws_url": f"/sessions/{session.session_id}/ws",
    }


@router.post("/remote/cancel/{request_id}")
async def cancel_remote_request(request_id: str, canceller_device_id: Optional[str] = None):
    """
    Cancel a pending remote request.
    
    Called by requester (controller) to cancel their own request.
    Sends remote_cancelled notification to all owner devices to close UI dialogs.
    
    Errors:
    - 404: Request not found
    - 409: Request already handled (accepted/rejected/expired)
    """
    pending = device_registry.get_pending_request(request_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if pending.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Request already {pending.status}"
        )
    
    device_registry.update_request_status(request_id, "cancelled")
    
    session_store._audit("remote_cancelled", request_id, "requester", {
        "canceller_device_id": canceller_device_id,
    })
    
    # Notify all owner devices to close pending dialog
    await device_registry.notify_user_devices(
        pending.owner_user_id,
        {
            "type": "remote_cancelled",
            "request_id": request_id,
            "share_creator_device_id": pending.share_creator_device_id,
            "reason": "requester_cancelled",
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    )
    
    return {"status": "cancelled", "request_id": request_id}


@router.get("/remote/status/{request_id}")
async def get_request_status(request_id: str):
    """
    Get status of a remote request.
    
    Used by controller to check if request was accepted/rejected/cancelled.
    Helps prevent infinite "Connecting" state.
    
    Response:
    - status: pending | accepted | rejected | cancelled | expired
    - session_id: (only if accepted)
    - error: (if applicable, e.g. "host_offline")
    """
    pending = device_registry.get_pending_request(request_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Request not found")
    
    response = {
        "request_id": request_id,
        "status": pending.status,
        "share_creator_device_id": pending.share_creator_device_id,
    }
    
    # Check if host is online (for pending requests)
    if pending.status == "pending":
        if not device_registry.is_device_online(pending.share_creator_device_id):
            response["warning"] = "host_offline"
            response["message"] = "Host device is currently offline. Request may timeout."
    
    return response


@router.websocket("/remote/ws")
async def device_presence_ws(websocket: WebSocket, token: str):
    """
    WebSocket for device presence and push notifications.
    
    Query params:
    - token: JWT containing user_id and device_id
    
    Message types received:
    - heartbeat: keep-alive ping
    - register_device: set device owner
    
    Message types sent:
    - remote_pending: new remote access request
    - remote_cancelled: request was cancelled
    - heartbeat_ack: response to heartbeat
    """
    # For MVP, parse token as "user_id:device_id"
    # In production, use proper JWT verification
    try:
        parts = token.split(":")
        if len(parts) != 2:
            await websocket.close(code=4001, reason="Invalid token format")
            return
        user_id, device_id = parts
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await websocket.accept()
    await device_registry.register(user_id, device_id, websocket)
    
    session_store._audit("device_online", device_id, "device", {
        "user_id": user_id,
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "heartbeat":
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
            
            elif msg_type == "register_device":
                # Allow device to register itself with owner
                device_registry.set_device_owner(device_id, user_id)
                await websocket.send_json({
                    "type": "device_registered",
                    "device_id": device_id,
                    "user_id": user_id,
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
    
    except WebSocketDisconnect:
        await device_registry.unregister(device_id)
        session_store._audit("device_offline", device_id, "device", {
            "user_id": user_id,
        })


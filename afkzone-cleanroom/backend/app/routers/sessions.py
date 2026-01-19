"""
Sessions router - session management and WebSocket signaling.
"""
import os
import secrets
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models import SessionStatsRequest, InputControlRequest, DisconnectRequest
from app.utils import api_success, api_error, utc_now_iso

router = APIRouter()


# In-memory session store
class Session:
    def __init__(self, session_id: str, target_device_id: str):
        self.session_id = session_id
        self.target_device_id = target_device_id
        self.status = "active"
        self.created_at = utc_now_iso()
        self.closed_at: Optional[str] = None
        self.host_ready = False
        self.controller_connected = False
        self.host_connected = False
        self.ice_state: Optional[str] = None
        self.ice_path: Optional[str] = None
        self.last_bitrate_kbps: Optional[int] = None
        self.last_fps: Optional[int] = None
        self.stats_updated_at: Optional[str] = None
        self.host_ws: Optional[WebSocket] = None
        self.controller_ws: Optional[WebSocket] = None


class SessionStore:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    def create(self, session_id: str, target_device_id: str) -> Session:
        session = Session(session_id, target_device_id)
        self.sessions[session_id] = session
        return session
    
    def get(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)
    
    def close(self, session_id: str, reason: str = "user_initiated"):
        session = self.get(session_id)
        if session:
            session.status = "closed"
            session.closed_at = utc_now_iso()


session_store = SessionStore()


# TURN credentials config
TURN_SECRET = os.getenv("AFK_TURN_SECRET", "afkzone-turn-secret-2026")
TURN_HOST = os.getenv("AFK_TURN_PUBLIC_HOST", "turn.afkzone.cloud")
TURN_TTL = 86400


def mint_turn_credentials(session_id: str) -> dict:
    """Generate time-limited TURN credentials."""
    timestamp = int(time.time()) + TURN_TTL
    username = f"{timestamp}:{session_id}"
    
    # HMAC-SHA1 credential
    credential = hashlib.sha1(
        f"{TURN_SECRET}{username}".encode()
    ).hexdigest()[:24]
    
    return {
        "ice_servers": [
            {
                "urls": [f"stun:{TURN_HOST}:3478"],
                "username": "",
                "credential": ""
            },
            {
                "urls": [
                    f"turn:{TURN_HOST}:3478?transport=udp",
                    f"turn:{TURN_HOST}:3478?transport=tcp"
                ],
                "username": username,
                "credential": credential
            }
        ],
        "ttl": TURN_TTL
    }


@router.get("/{session_id}/status")
async def session_status(session_id: str) -> JSONResponse:
    """Get session status and stats."""
    session = session_store.get(session_id)
    
    if not session:
        # Create placeholder for testing
        session = session_store.create(session_id, "unknown")
    
    return JSONResponse(api_success({
        "session_id": session.session_id,
        "status": session.status,
        "target_device_id": session.target_device_id,
        "started_at": session.created_at,
        "closed_at": session.closed_at,
        "controller_connected": session.controller_connected,
        "host_connected": session.host_connected,
        "host_ready": session.host_ready,
        "ice_state": session.ice_state,
        "ice_path": session.ice_path,
        "last_bitrate_kbps": session.last_bitrate_kbps,
        "last_fps": session.last_fps,
        "stats_updated_at": session.stats_updated_at,
    }))


@router.post("/{session_id}/stats")
async def session_stats(session_id: str, stats: SessionStatsRequest) -> JSONResponse:
    """Update session stats."""
    session = session_store.get(session_id)
    
    if not session:
        session = session_store.create(session_id, "unknown")
    
    now = utc_now_iso()
    
    if stats.ice_state:
        session.ice_state = stats.ice_state
    if stats.ice_path:
        session.ice_path = stats.ice_path
    if stats.bitrate_kbps is not None:
        session.last_bitrate_kbps = stats.bitrate_kbps
    if stats.fps is not None:
        session.last_fps = stats.fps
    
    session.stats_updated_at = now
    
    # Log performance stats
    if stats.bitrate_kbps is not None or stats.fps is not None:
        print(f"SESSION_STATS session_id={session_id} ice_state={session.ice_state} bitrate_kbps={session.last_bitrate_kbps} fps={session.last_fps}")
    
    return JSONResponse(api_success({"updated_at": now}))


@router.post("/{session_id}/input-control")
async def session_input_control(session_id: str, req: InputControlRequest) -> JSONResponse:
    """Signal input control start/stop."""
    session = session_store.get(session_id)
    
    if not session:
        return api_error("SESSION_NOT_FOUND", "Session not found", 404)
    
    now = utc_now_iso()
    
    if req.action == "start":
        print(f"INPUT_CONTROL_START session_id={session_id} target_device_id={session.target_device_id} controller_device_id={req.controller_device_id}")
        return JSONResponse(api_success({"action": "start", "timestamp": now}))
    elif req.action == "stop":
        print(f"INPUT_CONTROL_STOP session_id={session_id} target_device_id={session.target_device_id} controller_device_id={req.controller_device_id}")
        return JSONResponse(api_success({"action": "stop", "timestamp": now}))
    else:
        return api_error("INVALID_ACTION", "Action must be 'start' or 'stop'", 400)


@router.post("/{session_id}/disconnect")
async def session_disconnect(session_id: str, req: DisconnectRequest = None) -> JSONResponse:
    """Disconnect a session."""
    session = session_store.get(session_id)
    
    if not session:
        return api_error("SESSION_NOT_FOUND", "Session not found", 404)
    
    reason = req.reason if req else "user_initiated"
    now = utc_now_iso()
    
    session.status = "closed"
    session.closed_at = now
    
    print(f"SESSION_DISCONNECT session_id={session_id} target_device_id={session.target_device_id} reason={reason}")
    
    return JSONResponse(api_success({
        "session_id": session_id,
        "status": "closed",
        "reason": reason,
        "timestamp": now,
    }))


@router.get("/{session_id}/turn-credentials")
async def turn_credentials(session_id: str) -> JSONResponse:
    """Get TURN server credentials."""
    session = session_store.get(session_id)
    
    if not session:
        session = session_store.create(session_id, "unknown")
    
    creds = mint_turn_credentials(session_id)
    
    print(f"TURN_CREDENTIALS session_id={session_id} ttl={creds['ttl']}")
    
    return JSONResponse(api_success(creds))


@router.websocket("/{session_id}/ws")
async def signaling_websocket(websocket: WebSocket, session_id: str, token: str = None):
    """WebSocket signaling channel for SDP/ICE exchange."""
    await websocket.accept()
    
    session = session_store.get(session_id)
    if not session:
        session = session_store.create(session_id, "unknown")
    
    # Determine if host or controller based on token
    is_host = token and token.startswith("host_")
    
    if is_host:
        session.host_ws = websocket
        session.host_connected = True
    else:
        session.controller_ws = websocket
        session.controller_connected = True
    
    print(f"WS_CONNECTED session_id={session_id} role={'host' if is_host else 'controller'}")
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "unknown")
            
            print(f"WS_MESSAGE session_id={session_id} type={msg_type}")
            
            # Forward to peer
            peer_ws = session.host_ws if not is_host else session.controller_ws
            if peer_ws:
                try:
                    await peer_ws.send_json(data)
                except Exception:
                    pass
            
            # Handle special messages
            if msg_type == "host_ready":
                session.host_ready = True
                if session.controller_ws:
                    await session.controller_ws.send_json({"type": "host_ready"})
            elif msg_type == "ice_state":
                session.ice_state = data.get("state")
                
    except WebSocketDisconnect:
        print(f"WS_DISCONNECTED session_id={session_id} role={'host' if is_host else 'controller'}")
        if is_host:
            session.host_connected = False
            session.host_ws = None
        else:
            session.controller_connected = False
            session.controller_ws = None

"""
Sessions router - WebSocket signaling for remote sessions.
"""
import secrets
import json
import time
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse

from app.database import get_db
from app.utils import get_current_user, TokenClaims, api_success, api_error, utc_now_iso, mint_turn_credentials

router = APIRouter()


# In-memory session store
class SessionState:
    def __init__(self, session_id: str, host_device_id: str, client_user_id: str):
        self.session_id = session_id
        self.host_device_id = host_device_id
        self.client_user_id = client_user_id
        self.state = "requested"
        self.created_at = utc_now_iso()
        self.host_ws: Optional[WebSocket] = None
        self.client_ws: Optional[WebSocket] = None
        self.host_connected = False
        self.client_connected = False


sessions: Dict[str, SessionState] = {}

# Device control connections (device_id -> WebSocket)
device_control_ws: Dict[str, WebSocket] = {}

# Pending sessions per device (device_id -> list of session_ids)
pending_sessions: Dict[str, list] = {}


def get_session(session_id: str) -> Optional[SessionState]:
    return sessions.get(session_id)


def create_session(session_id: str, host_device_id: str, client_user_id: str) -> SessionState:
    session = SessionState(session_id, host_device_id, client_user_id)
    sessions[session_id] = session
    
    # Add to pending for device
    if host_device_id not in pending_sessions:
        pending_sessions[host_device_id] = []
    pending_sessions[host_device_id].append(session_id)
    
    return session


async def notify_device_new_session(device_id: str, session_id: str):
    """Notify device of new session request via control WS."""
    ws = device_control_ws.get(device_id)
    if ws:
        try:
            await ws.send_json({
                "type": "REMOTE_REQUESTED",
                "session_id": session_id
            })
            print(f"REMOTE_REQUESTED sent to device_id={device_id} session_id={session_id}")
        except Exception as e:
            print(f"REMOTE_REQUESTED failed device_id={device_id} error={e}")


@router.websocket("/{session_id}/ws")
async def signaling_websocket(websocket: WebSocket, session_id: str, token: str = None, role: str = "client"):
    """WebSocket signaling channel for SDP/ICE exchange."""
    await websocket.accept()
    
    session = get_session(session_id)
    if not session:
        # Create session on-the-fly for testing
        session = create_session(session_id, "unknown", "unknown")
    
    is_host = role == "host"
    
    if is_host:
        session.host_ws = websocket
        session.host_connected = True
        session.state = "approved"
    else:
        session.client_ws = websocket
        session.client_connected = True
    
    print(f"WS_CONNECT session_id={session_id} role={role} timestamp={utc_now_iso()}")
    
    # Notify peer of connection
    if is_host and session.client_ws:
        try:
            await session.client_ws.send_json({"type": "SESSION_STATE", "state": "approved"})
        except:
            pass
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "unknown")
            
            print(f"WS_MESSAGE session_id={session_id} role={role} type={msg_type}")
            
            # Forward to peer
            peer_ws = session.client_ws if is_host else session.host_ws
            if peer_ws:
                try:
                    await peer_ws.send_json(data)
                except Exception as e:
                    print(f"WS_FORWARD_ERROR session_id={session_id} error={str(e)}")
            
            # Handle special messages
            if msg_type == "SDP_OFFER":
                session.state = "connecting"
                print(f"SDP_OFFER session_id={session_id}")
            elif msg_type == "SDP_ANSWER":
                print(f"SDP_ANSWER session_id={session_id}")
            elif msg_type == "ICE_CANDIDATE":
                print(f"ICE_CANDIDATE session_id={session_id}")
            elif msg_type == "INPUT_EVENT":
                print(f"INPUT_CONTROL_START session_id={session_id} target_device_id={session.host_device_id}")
            elif msg_type == "SESSION_STATE" and data.get("state") == "connected":
                session.state = "connected"
                print(f"SESSION_STATS session_id={session_id} state=connected")
                
    except WebSocketDisconnect:
        print(f"WS_DISCONNECT session_id={session_id} role={role} timestamp={utc_now_iso()}")
        if is_host:
            session.host_connected = False
            session.host_ws = None
            if session.client_ws:
                try:
                    await session.client_ws.send_json({"type": "SESSION_STATE", "state": "disconnected"})
                except:
                    pass
        else:
            session.client_connected = False
            session.client_ws = None
        
        if not session.host_connected and not session.client_connected:
            session.state = "disconnected"
            print(f"SESSION_DISCONNECT session_id={session_id}")
    except Exception as e:
        print(f"WS_ERROR session_id={session_id} error={str(e)}")


@router.get("/{session_id}/status")
async def session_status(session_id: str) -> JSONResponse:
    """Get session status."""
    session = get_session(session_id)
    
    if not session:
        # Check database
        conn = get_db()
        cur = conn.cursor()
        row = cur.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        conn.close()
        
        if not row:
            return api_error("SESSION_NOT_FOUND", "Session not found", 404)
        
        return JSONResponse(api_success({
            "session": {
                "id": row["id"],
                "state": row["state"],
                "host_device_id": row["host_device_id"],
                "client_user_id": row["client_user_id"],
                "created_at": row["created_at"]
            }
        }))
    
    return JSONResponse(api_success({
        "session": {
            "id": session.session_id,
            "state": session.state,
            "host_device_id": session.host_device_id,
            "client_user_id": session.client_user_id,
            "host_connected": session.host_connected,
            "client_connected": session.client_connected,
            "created_at": session.created_at
        }
    }))


@router.post("/{session_id}/stats")
async def post_stats(session_id: str) -> JSONResponse:
    """Post session stats (from agent)."""
    session = get_session(session_id)
    now = utc_now_iso()
    
    print(f"SESSION_STATS session_id={session_id} timestamp={now}")
    
    # Update database
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE sessions SET last_stats_at = ? WHERE id = ?", (now, session_id))
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({"updated_at": now}))


# ==================== DEVICE CONTROL ====================

@router.websocket("/devices/{device_id}/control")
async def device_control_websocket(websocket: WebSocket, device_id: str, token: str = None):
    """Device control channel - receives REMOTE_REQUESTED notifications."""
    await websocket.accept()
    
    # Register device
    device_control_ws[device_id] = websocket
    print(f"DEVICE_CONTROL_CONNECT device_id={device_id} timestamp={utc_now_iso()}")
    
    # Send any pending session requests
    if device_id in pending_sessions:
        for session_id in pending_sessions[device_id]:
            try:
                await websocket.send_json({
                    "type": "REMOTE_REQUESTED",
                    "session_id": session_id
                })
            except:
                pass
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "unknown")
            print(f"DEVICE_CONTROL_MSG device_id={device_id} type={msg_type}")
            
            if msg_type == "HEARTBEAT":
                await websocket.send_json({"type": "HEARTBEAT_ACK", "server_time": utc_now_iso()})
                
    except WebSocketDisconnect:
        print(f"DEVICE_CONTROL_DISCONNECT device_id={device_id} timestamp={utc_now_iso()}")
        if device_id in device_control_ws:
            del device_control_ws[device_id]
    except Exception as e:
        print(f"DEVICE_CONTROL_ERROR device_id={device_id} error={str(e)}")
        if device_id in device_control_ws:
            del device_control_ws[device_id]


@router.get("/pending")
async def get_pending_sessions(device_id: str = None) -> JSONResponse:
    """Get pending session requests for a device (polling fallback)."""
    if not device_id:
        return api_error("DEVICE_ID_REQUIRED", "device_id query param required", 400)
    
    sessions_list = pending_sessions.get(device_id, [])
    
    return JSONResponse(api_success({
        "requests": [{"id": sid, "session_id": sid} for sid in sessions_list]
    }))

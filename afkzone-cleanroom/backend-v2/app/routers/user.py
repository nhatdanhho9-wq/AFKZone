"""
User router - profile endpoints.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.database import get_db
from app.schemas import ProfileUpdateRequest
from app.utils import get_current_user, TokenClaims, api_success, utc_now_iso

router = APIRouter()


@router.get("/profile")
async def get_profile(user: TokenClaims = Depends(get_current_user)) -> JSONResponse:
    """Get user profile."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM users WHERE id = ?", (user.user_id,)
    ).fetchone()
    
    device_count = cur.execute(
        "SELECT COUNT(*) FROM devices WHERE owner_user_id = ?", (user.user_id,)
    ).fetchone()[0]
    
    conn.close()
    
    if not row:
        return JSONResponse(status_code=404, content={"ok": False, "error_code": "USER_NOT_FOUND", "message": "User not found"})
    
    return JSONResponse(api_success({
        "profile": {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "created_at": row["created_at"],
            "plan": row["plan"] or "free",
            "plan_expires_at": row["plan_expires_at"],
            "active_devices_count": device_count,
            "display_name": row["display_name"],
            "avatar_url": row["avatar_url"]
        }
    }))


@router.patch("/profile")
async def update_profile(
    req: ProfileUpdateRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Update user profile."""
    conn = get_db()
    cur = conn.cursor()
    
    updates = []
    params = []
    
    if req.display_name is not None:
        updates.append("display_name = ?")
        params.append(req.display_name)
    
    if req.avatar_url is not None:
        updates.append("avatar_url = ?")
        params.append(req.avatar_url)
    
    if updates:
        params.append(user.user_id)
        cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    # Return updated profile
    row = cur.execute("SELECT * FROM users WHERE id = ?", (user.user_id,)).fetchone()
    device_count = cur.execute("SELECT COUNT(*) FROM devices WHERE owner_user_id = ?", (user.user_id,)).fetchone()[0]
    conn.close()
    
    return JSONResponse(api_success({
        "profile": {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "created_at": row["created_at"],
            "plan": row["plan"] or "free",
            "plan_expires_at": row["plan_expires_at"],
            "active_devices_count": device_count,
            "display_name": row["display_name"],
            "avatar_url": row["avatar_url"]
        }
    }))

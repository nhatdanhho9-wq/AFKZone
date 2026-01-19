"""
Notifications router - user notifications.
"""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.database import get_db
from app.utils import get_current_user, TokenClaims, api_success, api_error

router = APIRouter()


@router.get("/notifications")
async def list_notifications(user: TokenClaims = Depends(get_current_user)) -> JSONResponse:
    """Get user notifications."""
    conn = get_db()
    cur = conn.cursor()
    
    # Get user-specific and global notifications
    rows = cur.execute(
        """SELECT * FROM notifications 
           WHERE user_id = ? OR user_id IS NULL
           ORDER BY created_at DESC
           LIMIT 50""",
        (user.user_id,)
    ).fetchall()
    conn.close()
    
    notifications = []
    for r in rows:
        data = None
        if r["data"]:
            try:
                data = json.loads(r["data"])
            except:
                pass
        
        notifications.append({
            "id": r["id"],
            "type": r["type"],
            "title": r["title"],
            "body": r["body"],
            "data": data,
            "read": bool(r["read"]),
            "created_at": r["created_at"]
        })
    
    return JSONResponse(api_success({"notifications": notifications}))


@router.post("/notifications/{notification_id}/read")
async def mark_read(
    notification_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Mark notification as read."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(
        "UPDATE notifications SET read = 1 WHERE id = ? AND (user_id = ? OR user_id IS NULL)",
        (notification_id, user.user_id)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success())

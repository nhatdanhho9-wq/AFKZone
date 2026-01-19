"""
Plans router - subscription plans.
"""
import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database import get_db
from app.utils import api_success

router = APIRouter()


@router.get("/plans")
async def list_plans() -> JSONResponse:
    """Get available subscription plans."""
    conn = get_db()
    cur = conn.cursor()
    
    rows = cur.execute("SELECT * FROM plans ORDER BY price_usd").fetchall()
    conn.close()
    
    plans = []
    for r in rows:
        features = []
        if r["features"]:
            try:
                features = json.loads(r["features"])
            except:
                pass
        
        plans.append({
            "code": r["code"],
            "name": r["name"],
            "price_usd": r["price_usd"],
            "billing_period": r["billing_period"] or "month",
            "vcpu": r["vcpu"] or 2,
            "ram_gb": r["ram_gb"] or 4,
            "features": features
        })
    
    return JSONResponse(api_success({"plans": plans}))

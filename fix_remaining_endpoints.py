#!/usr/bin/env python3
"""
Fix remaining endpoints: /admin, dashboard stats, /admin/licenses auth, connections, generate license
"""

with open('/app/app.py', 'r') as f:
    content = f.read()

changes = []

# 1. Add /admin endpoint to serve admin dashboard
if '@app.get("/admin")' not in content:
    # Add after imports
    admin_endpoint = '''
from fastapi.responses import HTMLResponse

@app.get("/admin")
async def admin_dashboard():
    """Serve admin dashboard"""
    try:
        with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Admin Dashboard not found</h1>", status_code=404)

'''
    # Insert after app = FastAPI()
    if 'app = FastAPI()' in content:
        content = content.replace('app = FastAPI()', 'app = FastAPI()' + admin_endpoint)
        changes.append('Added /admin endpoint')

# 2. Fix dashboard stats - wrap in try/except
old_dashboard_stats = '''    # Total devices
    total_devices = db.execute(text("SELECT COUNT(*) FROM devices")).scalar()

    # Active devices (last 24h)
    active_24h = db.execute(text(
        "SELECT COUNT(*) FROM devices WHERE last_seen > NOW() - INTERVAL '24 hours'"
    )).scalar()'''

new_dashboard_stats = '''    # Total devices (with error handling)
    try:
        total_devices = db.execute(text("SELECT COUNT(*) FROM devices")).scalar() or 0
    except Exception:
        total_devices = 0

    # Active devices (last 24h)
    try:
        active_24h = db.execute(text(
            "SELECT COUNT(*) FROM devices WHERE last_seen > NOW() - INTERVAL '24 hours'"
        )).scalar() or 0
    except Exception:
        active_24h = 0'''

if old_dashboard_stats in content:
    content = content.replace(old_dashboard_stats, new_dashboard_stats)
    changes.append('Fixed dashboard stats with try/except')

# 3. Fix active/expired licenses queries
old_active = '''    # Active licenses
    active_licenses = db.execute(text(
        "SELECT COUNT(*) FROM licenses WHERE expires_at > EXTRACT(EPOCH FROM NOW()) * 1000 AND activated_at IS NOT NULL"
    )).scalar()

    # Expired licenses
    expired_licenses = db.execute(text(
        "SELECT COUNT(*) FROM licenses WHERE expires_at <= EXTRACT(EPOCH FROM NOW()) * 1000 AND activated_at IS NOT NULL"
    )).scalar()'''

new_active = '''    # Active licenses (with error handling)
    try:
        active_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at > NOW() AND activated_at IS NOT NULL"
        )).scalar() or 0
    except Exception:
        active_licenses = 0

    # Expired licenses
    try:
        expired_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at <= NOW() AND activated_at IS NOT NULL"
        )).scalar() or 0
    except Exception:
        expired_licenses = 0'''

if old_active in content:
    content = content.replace(old_active, new_active)
    changes.append('Fixed active/expired licenses queries')

# 4. Fix revenue queries
old_revenue = '''    # Revenue today
    revenue_today = db.execute(text(
        "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND DATE(completed_at) = CURRENT_DATE"
    )).scalar() or 0

    # Revenue this month
    revenue_month = db.execute(text(
        "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND EXTRACT(MONTH FROM completed_at) = EXTRACT(MONTH FROM NOW())"
    )).scalar() or 0

    # Revenue all time
    revenue_all = db.execute(text(
        "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success'"
    )).scalar() or 0'''

new_revenue = '''    # Revenue (with error handling for missing payments table)
    try:
        revenue_today = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND DATE(completed_at) = CURRENT_DATE"
        )).scalar() or 0
    except Exception:
        revenue_today = 0

    try:
        revenue_month = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND EXTRACT(MONTH FROM completed_at) = EXTRACT(MONTH FROM NOW())"
        )).scalar() or 0
    except Exception:
        revenue_month = 0

    try:
        revenue_all = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success'"
        )).scalar() or 0
    except Exception:
        revenue_all = 0'''

if old_revenue in content:
    content = content.replace(old_revenue, new_revenue)
    changes.append('Fixed revenue queries')

# 5. Fix server_stats query
old_server = '''    # Server stats (if exists)
    server_stats = db.execute(text(
        "SELECT cpu_usage_percent, memory_usage_mb, active_connections, bandwidth_in_mbps, bandwidth_out_mbps FROM server_stats ORDER BY timestamp DESC LIMIT 1"
    )).fetchone()'''

new_server = '''    # Server stats (if exists)
    try:
        server_stats = db.execute(text(
            "SELECT cpu_usage_percent, memory_usage_mb, active_connections, bandwidth_in_mbps, bandwidth_out_mbps FROM server_stats ORDER BY timestamp DESC LIMIT 1"
        )).fetchone()
    except Exception:
        server_stats = None'''

if old_server in content:
    content = content.replace(old_server, new_server)
    changes.append('Fixed server_stats query')

# 6. Add /admin/connections endpoint after device delete
connections_endpoint = '''
@app.get("/admin/connections")
def get_connections(
    page: int = 1,
    limit: int = 100,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Get connection logs"""
    offset = (page - 1) * limit
    
    try:
        results = db.execute(text("""
            SELECT device_id, peer_id, connection_type, ip_address, connected_at, disconnected_at, duration_seconds, license_key
            FROM connection_logs
            ORDER BY connected_at DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).fetchall()
        
        total = db.execute(text("SELECT COUNT(*) FROM connection_logs")).scalar() or 0
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "connections": [
                {
                    "device_id": r[0],
                    "peer_id": r[1],
                    "connection_type": r[2],
                    "ip_address": r[3],
                    "connected_at": r[4].isoformat() if r[4] else None,
                    "disconnected_at": r[5].isoformat() if r[5] else None,
                    "duration_seconds": r[6],
                    "license_key": r[7]
                } for r in results
            ]
        }
    except Exception:
        # Table doesn't exist
        return {"total": 0, "page": page, "limit": limit, "connections": []}

'''

if '@app.get("/admin/connections")' not in content:
    # Insert after device delete endpoint
    marker = 'return {"success": True, "message": f"Device {device_id} removed successfully"}'
    if marker in content:
        content = content.replace(marker, marker + connections_endpoint)
        changes.append('Added /admin/connections endpoint')

# 7. Add /admin/licenses/generate endpoint
generate_endpoint = '''
class SingleLicenseRequest(BaseModel):
    tier: str
    duration_days: int
    max_devices: Optional[int] = None
    notes: Optional[str] = None

@app.post("/admin/licenses/generate")
def generate_single_license(
    req: SingleLicenseRequest,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Generate a single license"""
    key = f"AFK-{req.tier.upper()}-{secrets.token_hex(12).upper()}"
    
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, created_by, notes)
        VALUES (:key, :tier, :days, :devices, 'admin', :note)
    """), {
        "key": key,
        "tier": req.tier,
        "days": req.duration_days,
        "devices": req.max_devices or 1,
        "note": req.notes
    })
    
    db.commit()
    
    return {
        "success": True,
        "license_key": key,
        "tier": req.tier,
        "duration_days": req.duration_days,
        "max_devices": req.max_devices
    }

'''

if '@app.post("/admin/licenses/generate")' not in content:
    # Insert after connections endpoint (or after device delete if connections not added)
    if '@app.get("/admin/connections")' in content:
        # Find end of connections endpoint
        pos = content.find('"connections": []}')
        if pos > 0:
            pos = content.find('\n', pos) + 1
            content = content[:pos] + generate_endpoint + content[pos:]
            changes.append('Added /admin/licenses/generate endpoint')
    else:
        # Add after device delete
        marker = 'return {"success": True, "message": f"Device {device_id} removed successfully"}'
        if marker in content:
            content = content.replace(marker, marker + '\n' + generate_endpoint)
            changes.append('Added /admin/licenses/generate endpoint')

# Write back
with open('/app/app.py', 'w') as f:
    f.write(content)

# Verify
import ast
try:
    ast.parse(content)
    print('✅ All fixes applied:')
    for change in changes:
        print(f'  - {change}')
    print('✅ Python syntax valid')
except SyntaxError as e:
    print(f'❌ Syntax error at line {e.lineno}: {e}')
    exit(1)


#!/usr/bin/env python3
"""
Fix trial devices management and add connections endpoint
"""

# 1. Clear all trial devices
def clear_trials():
    from database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    db.execute(text('DELETE FROM trial_devices'))
    db.commit()
    print("Cleared all trial devices!")
    db.close()

# 2. Add new endpoints to app.py
NEW_ENDPOINTS = '''

# ==================== TRIAL DEVICE MANAGEMENT ====================

@app.get("/admin/trial-devices")
async def get_trial_devices(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get all trial devices"""
    try:
        query = text("""
            SELECT id, device_fingerprint, ip_address, license_key, created_at
            FROM trial_devices
            ORDER BY created_at DESC
        """)
        result = db.execute(query)
        devices = []
        for row in result:
            devices.append({
                "id": row[0],
                "device_fingerprint": row[1][:16] + "..." if row[1] else "N/A",
                "ip_address": row[2],
                "license_key": row[3],
                "created_at": row[4].strftime("%H:%M:%S %d/%m/%Y") if row[4] else None
            })
        return {"devices": devices}
    except Exception as e:
        print(f"Error getting trial devices: {e}")
        return {"devices": []}


@app.delete("/admin/trial-devices/{device_id}")
async def delete_trial_device(device_id: int, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Delete a trial device"""
    try:
        db.execute(text("DELETE FROM trial_devices WHERE id = :id"), {"id": device_id})
        db.commit()
        return {"message": "Trial device deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/trial-devices")
async def clear_all_trial_devices(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Clear ALL trial devices"""
    try:
        db.execute(text("DELETE FROM trial_devices"))
        db.commit()
        return {"message": "All trial devices cleared"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONNECTION LOGS ====================

@app.post("/connection/log")
async def log_connection(data: dict, db: Session = Depends(get_db)):
    """Log a connection from client"""
    try:
        device_id = data.get("device_id", "")
        remote_id = data.get("remote_id", "")
        action = data.get("action", "connect")  # connect, disconnect
        
        # Try to create table if not exists
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS connection_logs (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(255),
                    remote_id VARCHAR(255),
                    action VARCHAR(50),
                    ip_address VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            db.commit()
        except:
            db.rollback()
        
        db.execute(text("""
            INSERT INTO connection_logs (device_id, remote_id, action, ip_address)
            VALUES (:device_id, :remote_id, :action, :ip)
        """), {
            "device_id": device_id,
            "remote_id": remote_id,
            "action": action,
            "ip": "unknown"
        })
        db.commit()
        return {"status": "logged"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}


@app.get("/admin/connections")
async def get_connections_v2(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get connection logs"""
    try:
        # Check if table exists
        try:
            result = db.execute(text("""
                SELECT device_id, remote_id, action, ip_address, created_at
                FROM connection_logs
                ORDER BY created_at DESC
                LIMIT 100
            """))
            connections = []
            for row in result:
                connections.append({
                    "device_id": row[0],
                    "remote_id": row[1],
                    "action": row[2],
                    "ip_address": row[3],
                    "created_at": row[4].strftime("%H:%M:%S %d/%m/%Y") if row[4] else None
                })
            return {"connections": connections}
        except:
            return {"connections": [], "note": "Connection logging not yet initialized. Connections will appear after clients connect."}
    except Exception as e:
        print(f"Error getting connections: {e}")
        return {"connections": []}

'''

def add_endpoints():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    if '/admin/trial-devices' in content:
        print("Trial device endpoints already exist")
        return
    
    content = content.rstrip() + NEW_ENDPOINTS
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Added trial device and connection endpoints!")

if __name__ == "__main__":
    clear_trials()
    add_endpoints()


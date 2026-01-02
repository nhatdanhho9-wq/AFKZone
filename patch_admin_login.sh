#!/bin/bash
# Patch admin_login to use security_lockout module

APP_FILE="/app/app.py"

# 1. Add import at top of file (after 'import os')
sed -i '1a from security_lockout import check_lockout, record_failed_login, clear_failed_logins, log_successful_login, get_lockout_remaining' $APP_FILE

# 2. Find and replace the admin_login function
# Create new function
cat > /tmp/new_admin_login.py << 'EOF'
@app.post("/admin/login")
def admin_login(req: AdminLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Admin login - returns JWT token with lockout protection"""
    ip = request.client.host if request.client else "unknown"
    
    # Check lockout
    if check_lockout(ip):
        remaining = get_lockout_remaining(ip)
        raise HTTPException(
            status_code=429, 
            detail=f"Too many failed attempts. Try again in {remaining // 60} minutes."
        )
    
    result = db.execute(
        text("SELECT * FROM admin_users WHERE username=:username"),
        {"username": req.username}
    ).fetchone()

    if not result:
        record_failed_login(ip, req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password (bcrypt)
    if not bcrypt.checkpw(req.password.encode(), result[2].encode()):
        record_failed_login(ip, req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Success - clear failed attempts and log
    clear_failed_logins(ip)
    log_successful_login(ip, result[1])
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": result[1], "role": result[3]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": result[1],
        "role": result[3],
        "expires_in": 86400
    }
EOF

echo "Import added and new function ready"
echo "Manual steps needed:"
echo "1. Find line '@app.post(\"/admin/login\")' in $APP_FILE"
echo "2. Replace the admin_login function with content from /tmp/new_admin_login.py"

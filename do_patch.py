#!/usr/bin/env python3
"""Patch admin_login function to use security lockout"""
import re

APP_FILE = "/app/app.py"

with open(APP_FILE, 'r') as f:
    content = f.read()

# New admin_login function with lockout
new_function = '''@app.post("/admin/login")
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
    }'''

# Find and replace the old admin_login function
# Pattern matches from @app.post("/admin/login") to the start of next route or function
pattern = r'@app\.post\("/admin/login"\)\s*def admin_login\([^)]+\):.*?(?=\n@app\.|# ={10,})'

# Replace
new_content = re.sub(pattern, new_function + '\n\n', content, flags=re.DOTALL)

if new_content != content:
    with open(APP_FILE, 'w') as f:
        f.write(new_content)
    print("SUCCESS: admin_login function patched with lockout logic")
else:
    print("WARNING: Pattern not found, no changes made")

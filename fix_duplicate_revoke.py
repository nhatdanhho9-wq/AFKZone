#!/usr/bin/env python3
"""Remove duplicate revoke endpoint"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Find and remove the old revoke endpoint (the one with reason parameter)
    old_endpoint = '''@app.post("/admin/licenses/{license_key}/revoke")
def revoke_license(license_key: str, reason: str, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Revoke a license"""
    db.execute(
        text("UPDATE licenses SET is_revoked=TRUE, revoked_at=NOW(), revoked_reason=:reason WHERE license_key=:key"),
        {"key": license_key, "reason": reason}
    )
    db.commit()
    return {
        "message": "License revoked",
        "license_key": license_key,
        "revoked_at": datetime.now().isoformat()
    }'''
    
    if old_endpoint in content:
        content = content.replace(old_endpoint, '# Old revoke endpoint removed - using v2')
        print("Removed old revoke endpoint")
    else:
        # Try to find and comment out the problematic endpoint
        lines = content.split('\n')
        new_lines = []
        skip_until_next_decorator = False
        skip_count = 0
        
        for i, line in enumerate(lines):
            if '@app.post("/admin/licenses/{license_key}/revoke")' in line:
                # Check if next line has 'reason: str'
                if i + 1 < len(lines) and 'reason: str' in lines[i + 1]:
                    skip_until_next_decorator = True
                    skip_count = 0
                    new_lines.append('# ' + line + ' # DISABLED - old version')
                    continue
            
            if skip_until_next_decorator:
                skip_count += 1
                if line.strip().startswith('@app.') or (skip_count > 15 and line.strip() == ''):
                    skip_until_next_decorator = False
                    new_lines.append(line)
                else:
                    new_lines.append('# ' + line)
                continue
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        print("Commented out old revoke endpoint")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()


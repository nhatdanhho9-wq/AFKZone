#!/usr/bin/env python3
"""
Phase 1 Security: Update server_app.py to use environment variables
"""

def update_server_for_env():
    with open('server_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('server_app.py.bak_phase1', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Add env imports at top
    if 'import os' not in content[:500]:
        content = 'import os\n' + content
    
    if 'from dotenv import load_dotenv' not in content[:500]:
        content = content.replace('import os\n', 'import os\nfrom dotenv import load_dotenv\n\nload_dotenv()\n')
    
    # Replace hardcoded secrets with env vars
    # Note: We'll use get() with fallback for backward compatibility during transition
    
    replacements = [
        # Admin key
        ('ADMIN_KEY = "afkzone-admin-2025"', 'ADMIN_KEY = os.getenv("ADMIN_KEY", "afkzone-admin-2025")'),
        
        # JWT Secret
        ('SECRET_KEY = "your-secret-key-change-in-production"', 'SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")'),
        
        # Casso config (if exists)
        ('"casso_token": "AK_CS.', '"casso_token": os.getenv("CASSO_API_KEY", "AK_CS.'),
    ]
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Replaced: {old[:30]}...")
    
    # Re-enable webhook verification (remove accept-all block)
    # Look for commented signature verification
    if '# if not signature or signature != expected_signature:' in content:
        content = content.replace(
            '# if not signature or signature != expected_signature:',
            'if not signature or signature != expected_signature:'
        )
        content = content.replace(
            '#     raise HTTPException(status_code=401, detail="Invalid signature")',
            '    raise HTTPException(status_code=401, detail="Invalid signature")'
        )
        print("✅ Re-enabled webhook signature verification")
    
    with open('server_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ server_app.py updated for environment variables!")

if __name__ == '__main__':
    update_server_for_env()

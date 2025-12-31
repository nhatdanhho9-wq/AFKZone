#!/usr/bin/env python3
"""
Phase 1 Security: Move secrets to environment variables
and re-enable webhook verification
"""

def create_env_template():
    """Create .env.example template"""
    template = """# AFK Zone License API - Environment Variables
# Copy to .env and fill in actual values

# Database
DATABASE_URL=postgresql://afkzone:YOUR_DB_PASSWORD@afkzone-postgres:5432/afkzone

# Security - CHANGE THESE VALUES
ADMIN_KEY=your-new-admin-key-here
JWT_SECRET=your-new-jwt-secret-here-min-32-chars

# Payment Gateway
CASSO_API_KEY=your-casso-api-key
CASSO_WEBHOOK_SECRET=your-casso-webhook-secret
BANK_ID=970422
BANK_ACCOUNT_NO=your-account-number
BANK_ACCOUNT_NAME=YOUR NAME

# ZaloPay (if used)
ZALOPAY_APP_ID=your-zalopay-app-id
ZALOPAY_KEY1=your-zalopay-key1
ZALOPAY_KEY2=your-zalopay-key2
"""
    
    with open('.env.example', 'w') as f:
        f.write(template)
    
    print("✅ Created .env.example template")

def generate_secrets():
    """Generate new secure secrets"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits + string.punctuation
    
    admin_key = 'afkzone-admin-' + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    jwt_secret = ''.join(secrets.choice(alphabet) for _ in range(64))
    
    print("\n🔐 Generated New Secrets (SAVE THESE SECURELY):")
    print(f"ADMIN_KEY={admin_key}")
    print(f"JWT_SECRET={jwt_secret}")
    print("\n⚠️  Add these to ~/license-api/.env on server")

if __name__ == '__main__':
    create_env_template()
    generate_secrets()

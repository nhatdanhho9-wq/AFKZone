#!/usr/bin/env python3
"""Create admin user with correct password"""
from database import get_db
from sqlalchemy import text
import bcrypt

db = next(get_db())

# Delete existing admin user
db.execute(text('DELETE FROM admin_users WHERE username = :username'), {'username': 'admin'})
db.commit()

# Create new admin user
password = 'admin123'
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

db.execute(text('''
    INSERT INTO admin_users (username, password_hash, role)
    VALUES (:username, :password_hash, 'admin')
'''), {
    'username': 'admin',
    'password_hash': password_hash
})

db.commit()

# Verify
result = db.execute(text('SELECT username, role FROM admin_users WHERE username=:username'), {'username': 'admin'}).fetchone()
if result:
    print(f'✅ Admin user created: {result[0]} ({result[1]})')
    print(f'Password: admin123')
    
    # Test password
    stored = db.execute(text('SELECT password_hash FROM admin_users WHERE username=:username'), {'username': 'admin'}).fetchone()
    if bcrypt.checkpw(b'admin123', stored[0].encode('utf-8')):
        print('✅ Password verification: SUCCESS')
    else:
        print('❌ Password verification: FAILED')
else:
    print('❌ Failed to create admin user')


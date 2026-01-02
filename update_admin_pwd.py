#!/usr/bin/env python3
"""Update admin password in database"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

engine = create_engine(DATABASE_URL)
new_hash = "$2b$12$9DIBgdVqM4UHFkojrmAOyuG3OgXBeFoh8Jcj.7SN.2getjTeuYFly"

with engine.connect() as conn:
    # Update admin user password
    result = conn.execute(
        text("UPDATE admin_users SET password_hash = :hash WHERE username = 'admin'"),
        {"hash": new_hash}
    )
    conn.commit()
    print(f"Updated {result.rowcount} row(s)")
    
    # Verify
    verify = conn.execute(
        text("SELECT username, password_hash FROM admin_users WHERE username = 'admin'")
    ).fetchone()
    if verify:
        print(f"Verified: {verify[0]} has new hash starting with: {verify[1][:20]}...")

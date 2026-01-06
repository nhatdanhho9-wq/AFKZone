#!/usr/bin/env python3
"""Run migration 004 for login_attempts table"""
from database import get_db
from sqlalchemy import text

db = next(get_db())
try:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            ip_address VARCHAR(45),
            attempt_time TIMESTAMP DEFAULT NOW(),
            success BOOLEAN DEFAULT FALSE
        )
    """))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time ON login_attempts(email, attempt_time)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time ON login_attempts(ip_address, attempt_time)"))
    db.commit()
    print("Migration 004 complete: login_attempts table created")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()

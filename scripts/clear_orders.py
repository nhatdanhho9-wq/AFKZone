#!/usr/bin/env python3
"""Clear all orders from database"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM orders"))
    count = result.fetchone()[0]
    print(f"📊 Found {count} orders")
    
    conn.execute(text("DELETE FROM orders"))
    conn.commit()
    print("✅ All orders cleared!")

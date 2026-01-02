#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('/app/data/licenses.db')
c = conn.cursor()

# List all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

# Check connections table
if 'connections' in tables:
    c.execute("SELECT COUNT(*) FROM connections")
    print(f"Connections count: {c.fetchone()[0]}")
    c.execute("SELECT * FROM connections LIMIT 5")
    for r in c.fetchall():
        print(f"  {r}")
else:
    print("❌ No 'connections' table found")

# Check if there's a connection_history table
if 'connection_history' in tables:
    c.execute("SELECT COUNT(*) FROM connection_history")
    print(f"Connection_history count: {c.fetchone()[0]}")
else:
    print("❌ No 'connection_history' table found")

# Check products/pricing tables
if 'products' in tables:
    c.execute("SELECT COUNT(*) FROM products")
    print(f"Products count: {c.fetchone()[0]}")
if 'pricing' in tables:
    c.execute("SELECT * FROM pricing")
    print("Pricing table:")
    for r in c.fetchall():
        print(f"  {r}")

conn.close()

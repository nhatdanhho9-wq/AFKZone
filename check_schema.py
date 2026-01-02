#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host="172.26.31.115",
    database="afkzone_license",
    user="postgres",
    password="your_secure_password"
)

cur = conn.cursor()

print("=== license_devices table schema ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'license_devices'
    ORDER BY ordinal_position
""")

for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== licenses table schema ===")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'licenses'
    ORDER BY ordinal_position
""")

for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.close()
conn.close()


import psycopg2
import os

conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

# Check today's orders (0103)
cur.execute("SELECT id,trans_code,amount,status,tier,license_key,paid_at FROM bank_orders WHERE trans_code LIKE 'AFKBASIC3260103%' ORDER BY id")
rows = cur.fetchall()
print("=== TODAY ORDERS (0103) ===")
for r in rows:
    print(r)

# Check specific order
cur.execute("SELECT * FROM bank_orders WHERE trans_code='AFKBASIC3260103001'")
specific = cur.fetchall()
print("\n=== SPECIFIC ORDER AFKBASIC3260103001 ===")
print(specific if specific else "NOT FOUND")

conn.close()

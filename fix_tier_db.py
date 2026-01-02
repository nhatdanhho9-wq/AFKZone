#!/usr/bin/env python3
"""Fix tier constraint on server"""
import psycopg2

try:
    conn = psycopg2.connect(
        host="afkzone-postgres",
        database="afkzone",
        user="afkzone",
        password="afkzone123"
    )
    cur = conn.cursor()
    
    # Drop old constraint
    cur.execute("ALTER TABLE bank_orders DROP CONSTRAINT IF EXISTS fk_tier;")
    print("✅ Dropped old fk_tier constraint")
    
    # Add new constraint
    cur.execute("""
        ALTER TABLE bank_orders ADD CONSTRAINT fk_tier 
        CHECK (tier IN ('basic', 'pro', 'enterprise', 'ProMax', 'SuperVVIP'));
    """)
    print("✅ Added new fk_tier constraint with ProMax, SuperVVIP")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ Tier constraint updated successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")

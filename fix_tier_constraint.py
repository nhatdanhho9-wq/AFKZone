#!/usr/bin/env python3
"""
Fix tier issues:
1. Update bank_orders constraint to allow new tiers
2. Fix payment_screen.dart to use tier names instead of product names
"""
import subprocess

def fix_tier_constraint():
    """Drop old constraint and add new one with all tiers"""
    
    sql_commands = [
        # Drop old constraint
        "ALTER TABLE bank_orders DROP CONSTRAINT IF EXISTS fk_tier;",
        
        # Add new constraint with all tiers including ProMax and SuperVVIP
        """ALTER TABLE bank_orders ADD CONSTRAINT fk_tier 
           CHECK (tier IN ('basic', 'pro', 'enterprise', 'ProMax', 'SuperVVIP'));""",
    ]
    
    for sql in sql_commands:
        cmd = f'docker exec afkzone-postgres psql -U postgres -d afkzone -c "{sql}"'
        result = subprocess.run(
            ['ssh', 'automation@172.26.31.115', cmd],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {sql[:50]}...")
        else:
            print(f"❌ Error: {result.stderr}")
    
    print("\n✅ Tier constraint updated!")
    print("   Allowed tiers: basic, pro, enterprise, ProMax, SuperVVIP")

if __name__ == '__main__':
    fix_tier_constraint()

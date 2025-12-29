#!/usr/bin/env python3
"""Script to update product price - run on server"""
import subprocess

# Create Python script to run in container
python_script = '''
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())
# Update price
db.execute(text("UPDATE products SET price = 15000 WHERE tier = 'basic' AND duration_days = 7"))
db.commit()

# Verify
result = db.execute(text("SELECT id, name, tier, duration_days, price FROM products WHERE tier='basic' AND duration_days=7")).fetchone()
if result:
    print(f"Updated: ID={result[0]}, Name={result[1]}, Tier={result[2]}, Days={result[3]}, Price={result[4]}")
else:
    print("Product not found!")
'''

# SSH and run script
ssh_cmd = f'ssh ubuntu "docker exec -i afkzone-license-api python3 -c \\"{python_script.replace(chr(10), "; ").replace(chr(34), chr(39))}\\" "'

print("Running update command...")
result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
print("STDOUT:", result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)


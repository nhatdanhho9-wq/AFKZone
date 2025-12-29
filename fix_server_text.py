#!/usr/bin/env python3
"""Fix server app.py - change Vô cực to Không giới hạn thiết bị"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

# This script will be copied to server and run there
with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('max_devices_display = "Vô cực"', 'max_devices_display = "Không giới hạn thiết bị"')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py: Changed 'Vô cực' to 'Không giới hạn thiết bị'")


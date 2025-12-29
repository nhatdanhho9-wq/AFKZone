#!/usr/bin/env python3
"""Update max_devices_display text on server - change 'Vô cực' to 'Không giới hạn thiết bị'"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())

# Update the /products endpoint in app.py to use new text
# This script updates the server code
print("Note: This requires manual update to app.py on server")
print("Change line 521 from:")
print('            max_devices_display = "Vô cực"')
print("to:")
print('            max_devices_display = "Không giới hạn thiết bị"')


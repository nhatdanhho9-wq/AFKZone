#!/usr/bin/env python3
"""
Script to deploy admin endpoints to app.py
"""
import sys

# Read admin endpoints
with open('admin_endpoints.py', 'r', encoding='utf-8') as f:
    endpoints_content = f.read()

# Extract only the endpoint functions (skip imports and comments at top)
lines = endpoints_content.split('\n')
start_idx = 0
for i, line in enumerate(lines):
    if line.startswith('@app.'):
        start_idx = i
        break

endpoints_code = '\n'.join(lines[start_idx:])

# Remove the comment at top
endpoints_code = endpoints_code.replace('# Additional Admin Endpoints for AFK Zone License API\n# Add these to app.py.original\n\n', '')

# Remove duplicate imports
endpoints_code = endpoints_code.replace('from fastapi import HTTPException, Depends\n', '')
endpoints_code = endpoints_code.replace('from sqlalchemy.orm import Session\n', '')
endpoints_code = endpoints_code.replace('from sqlalchemy import text\n', '')
endpoints_code = endpoints_code.replace('from typing import Optional, List\n', '')
endpoints_code = endpoints_code.replace('from datetime import datetime\n', '')
endpoints_code = endpoints_code.replace('from pydantic import BaseModel\n', '')
endpoints_code = endpoints_code.replace('from database import get_db\n', '')

# Fix the generate_license function signature
endpoints_code = endpoints_code.replace(
    'def generate_license(\n    req: GenerateLicenseRequest,',
    'def generate_license(\n    tier: str,\n    duration_days: int,\n    max_devices: Optional[int] = None,\n    notes: Optional[str] = None,'
)

# Remove GenerateLicenseRequest class
endpoints_code = endpoints_code.replace('class GenerateLicenseRequest(BaseModel):\n    tier: str\n    duration_days: int\n    max_devices: Optional[int] = None\n    notes: Optional[str] = None\n\n', '')

# Fix generate_license function body
endpoints_code = endpoints_code.replace('max_devices = req.max_devices\n    if max_devices is None:\n        max_devices = DEVICE_LIMITS.get(req.tier, 2)\n    \n    # Generate license key\n    key = f"AFK-{req.tier.upper()}-{secrets.token_hex(12).upper()}"\n    \n    # Calculate expiry (will be set on activation)\n    expires_timestamp = int((datetime.now() + timedelta(days=req.duration_days)).timestamp() * 1000)\n    \n    # Insert license\n    db.execute(text("""\n        INSERT INTO licenses (license_key, tier, duration_days, expires_at, max_devices, created_by, notes)\n        VALUES (:key, :tier, :days, :exp, :devices, 'admin', :note)\n    """), {\n        "key": key,\n        "tier": req.tier,\n        "days": req.duration_days,\n        "exp": expires_timestamp,\n        "devices": max_devices,\n        "note": req.notes\n    })', 
    'if max_devices is None:\n        max_devices = DEVICE_LIMITS.get(tier, 2)\n    \n    # Generate license key\n    key = f"AFK-{tier.upper()}-{secrets.token_hex(12).upper()}"\n    \n    # Calculate expiry (will be set on activation)\n    expires_timestamp = int((datetime.now() + timedelta(days=duration_days)).timestamp() * 1000)\n    \n    # Insert license\n    db.execute(text("""\n        INSERT INTO licenses (license_key, tier, duration_days, expires_at, max_devices, created_by, notes)\n        VALUES (:key, :tier, :days, :exp, :devices, 'admin', :note)\n    """), {\n        "key": key,\n        "tier": tier,\n        "days": duration_days,\n        "exp": expires_timestamp,\n        "devices": max_devices,\n        "note": notes\n    })')

print(endpoints_code)


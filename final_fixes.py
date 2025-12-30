#!/usr/bin/env python3
"""Final fixes for admin endpoints"""

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix dashboard stats - expires_at is bigint, need to cast properly
content = content.replace(
    'expires_at > (EXTRACT(EPOCH FROM NOW())::bigint * 1000)',
    'expires_at::bigint > (EXTRACT(EPOCH FROM NOW())::bigint * 1000)'
)
content = content.replace(
    'expires_at <= (EXTRACT(EPOCH FROM NOW())::bigint * 1000)',
    'expires_at::bigint <= (EXTRACT(EPOCH FROM NOW())::bigint * 1000)'
)

# 2. Fix /admin/users to query from license_devices
# Find and replace the SELECT query
old_select = 'SELECT * FROM devices'
new_select = '''SELECT DISTINCT 
            ld.device_id,
            COALESCE(d.device_model, 'N/A') as device_model,
            COALESCE(d.app_version, 'N/A') as app_version,
            ld.last_check as last_seen,
            ld.license_key,
            l.tier as license_tier,
            l.expires_at as license_expires_at,
            ld.is_active,
            COALESCE(d.total_sessions, 0) as total_sessions
        FROM license_devices ld
        JOIN licenses l ON ld.license_key = l.license_key
        LEFT JOIN devices d ON ld.device_id = d.device_id
        WHERE ld.is_active=TRUE'''

if 'SELECT * FROM devices' in content and 'def get_users' in content:
    # Find the function and replace
    lines = content.split('\n')
    new_lines = []
    in_get_users = False
    for i, line in enumerate(lines):
        if 'def get_users' in line:
            in_get_users = True
        if in_get_users and 'SELECT * FROM devices' in line:
            # Replace with new query
            new_lines.append(new_select)
            # Skip the old query lines until WHERE
            j = i + 1
            while j < len(lines) and 'WHERE' not in lines[j] and 'ORDER BY' not in lines[j]:
                j += 1
            # Add WHERE clause
            if j < len(lines):
                new_lines.append('        WHERE ld.is_active=TRUE')
                # Skip to ORDER BY
                while j < len(lines) and 'ORDER BY' not in lines[j]:
                    j += 1
                if j < len(lines):
                    new_lines.append(lines[j].replace('last_seen', 'ld.last_check'))
                    j += 1
                    while j < len(lines) and 'LIMIT' in lines[j]:
                        new_lines.append(lines[j])
                        j += 1
                    i = j - 1
                    continue
            i = j - 1
            continue
        new_lines.append(line)
    content = '\n'.join(new_lines)

# 3. Fix the mapping in get_users
old_mapping = '"device_id": r[1],'
if old_mapping in content and 'def get_users' in content:
    # Replace mapping
    content = content.replace(
        '"device_id": r[1],',
        '"device_id": r[0] if len(r) > 0 else None,'
    )
    content = content.replace(
        '"device_fingerprint": r[2],',
        '"device_model": r[1] if len(r) > 1 else None,'
    )
    content = content.replace(
        '"device_model": r[3],',
        '"app_version": r[2] if len(r) > 2 else None,'
    )
    content = content.replace(
        '"os_version": r[4],',
        '"last_seen": r[3].isoformat() if len(r) > 3 and r[3] else None,'
    )
    content = content.replace(
        '"app_version": r[5],',
        '"license_key": r[4] if len(r) > 4 else None,'
    )
    content = content.replace(
        '"first_seen": r[6].isoformat() if r[6] else None,',
        '"license_tier": r[5] if len(r) > 5 else None,'
    )
    content = content.replace(
        '"last_seen": r[7].isoformat() if r[7] else None,',
        '"license_expires_at": r[6] if len(r) > 6 else None,'
    )
    content = content.replace(
        '"last_ip": r[8],',
        '"is_active": r[7] if len(r) > 7 else None,'
    )
    content = content.replace(
        '"license_key": r[9],',
        '"total_sessions": r[8] if len(r) > 8 else 0'
    )
    # Remove old fields
    content = content.replace('"license_status": r[10],', '')
    content = content.replace('"license_tier": r[11],', '')
    content = content.replace('"license_expires_at": r[12],', '')
    content = content.replace('"is_active": r[13],', '')
    content = content.replace('"total_sessions": r[14]', '')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Applied all fixes')


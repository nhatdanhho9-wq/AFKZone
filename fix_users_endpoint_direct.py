#!/usr/bin/env python3
"""Direct fix for /admin/users endpoint"""

with open('/app/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
in_get_users = False
skip_until_return = False

while i < len(lines):
    line = lines[i]
    
    # Find get_users function
    if '@app.get("/admin/users")' in line:
        in_get_users = True
        new_lines.append(line)
        i += 1
        # Copy function signature and docstring
        while i < len(lines) and ('def get_users' not in lines[i] or '"""' in lines[i]):
            new_lines.append(lines[i])
            i += 1
        # Copy def line
        if i < len(lines):
            new_lines.append(lines[i])
            i += 1
        # Skip until we find the query
        while i < len(lines) and 'SELECT' not in lines[i] and 'FROM devices' not in lines[i] and 'FROM license_devices' not in lines[i]:
            if 'where_clauses' in lines[i] or 'where_sql' in lines[i] or 'params =' in lines[i]:
                # Keep these lines but adjust
                if 'license_status=:status' in lines[i]:
                    # Remove status filter (not in license_devices)
                    i += 1
                    continue
                if 'license_tier=:tier' in lines[i]:
                    lines[i] = lines[i].replace('license_tier=:tier', 'l.tier=:tier')
                if 'device_id ILIKE' in lines[i]:
                    lines[i] = lines[i].replace('device_id ILIKE', 'ld.device_id ILIKE')
                new_lines.append(lines[i])
            else:
                new_lines.append(lines[i])
            i += 1
        
        # Replace query section
        new_lines.append('    # Query from license_devices\n')
        new_lines.append('    results = db.execute(text("""\n')
        new_lines.append('        SELECT DISTINCT\n')
        new_lines.append('            ld.device_id,\n')
        new_lines.append('            COALESCE(d.device_model, \'N/A\') as device_model,\n')
        new_lines.append('            COALESCE(d.app_version, \'N/A\') as app_version,\n')
        new_lines.append('            ld.last_check as last_seen,\n')
        new_lines.append('            ld.license_key,\n')
        new_lines.append('            l.tier as license_tier,\n')
        new_lines.append('            l.expires_at as license_expires_at,\n')
        new_lines.append('            ld.is_active,\n')
        new_lines.append('            COALESCE(d.total_sessions, 0) as total_sessions\n')
        new_lines.append('        FROM license_devices ld\n')
        new_lines.append('        JOIN licenses l ON ld.license_key = l.license_key\n')
        new_lines.append('        LEFT JOIN devices d ON ld.device_id = d.device_id\n')
        new_lines.append('        WHERE ld.is_active=TRUE')
        
        # Add where conditions if any
        if 'where_sql' in '\n'.join(new_lines[-50:]):
            new_lines.append(' AND ({where_sql})'.format(where_sql='{where_sql}'))
        
        new_lines.append('\n')
        new_lines.append('        ORDER BY ld.last_check DESC\n')
        new_lines.append('        LIMIT :limit OFFSET :offset\n')
        new_lines.append('    """).format(where_sql=where_sql) if where_clauses else text("""\n')
        new_lines.append('        SELECT DISTINCT\n')
        new_lines.append('            ld.device_id,\n')
        new_lines.append('            COALESCE(d.device_model, \'N/A\') as device_model,\n')
        new_lines.append('            COALESCE(d.app_version, \'N/A\') as app_version,\n')
        new_lines.append('            ld.last_check as last_seen,\n')
        new_lines.append('            ld.license_key,\n')
        new_lines.append('            l.tier as license_tier,\n')
        new_lines.append('            l.expires_at as license_expires_at,\n')
        new_lines.append('            ld.is_active,\n')
        new_lines.append('            COALESCE(d.total_sessions, 0) as total_sessions\n')
        new_lines.append('        FROM license_devices ld\n')
        new_lines.append('        JOIN licenses l ON ld.license_key = l.license_key\n')
        new_lines.append('        LEFT JOIN devices d ON ld.device_id = d.device_id\n')
        new_lines.append('        WHERE ld.is_active=TRUE\n')
        new_lines.append('        ORDER BY ld.last_check DESC\n')
        new_lines.append('        LIMIT :limit OFFSET :offset\n')
        new_lines.append('    """), params).fetchall()\n')
        
        # Skip old query
        while i < len(lines) and ('SELECT' in lines[i] or 'FROM' in lines[i] or 'WHERE' in lines[i] or 'ORDER BY' in lines[i] or 'LIMIT' in lines[i] or 'OFFSET' in lines[i]):
            i += 1
        
        # Add total count
        new_lines.append('\n    # Get total count\n')
        new_lines.append('    total = db.execute(text("""\n')
        new_lines.append('        SELECT COUNT(DISTINCT ld.device_id)\n')
        new_lines.append('        FROM license_devices ld\n')
        new_lines.append('        JOIN licenses l ON ld.license_key = l.license_key\n')
        new_lines.append('        WHERE ld.is_active=TRUE')
        if 'where_sql' in '\n'.join(new_lines[-50:]):
            new_lines.append(' AND ({where_sql})'.format(where_sql='{where_sql}'))
        new_lines.append('\n    """).format(where_sql=where_sql) if where_clauses else text("""\n')
        new_lines.append('        SELECT COUNT(DISTINCT ld.device_id)\n')
        new_lines.append('        FROM license_devices ld\n')
        new_lines.append('        JOIN licenses l ON ld.license_key = l.license_key\n')
        new_lines.append('        WHERE ld.is_active=TRUE\n')
        new_lines.append('    """), params).scalar()\n')
        
        # Skip old total query
        while i < len(lines) and ('total =' in lines[i] or 'SELECT COUNT' in lines[i]):
            i += 1
        
        # Add return statement
        new_lines.append('\n    return {\n')
        new_lines.append('        "total": total or 0,\n')
        new_lines.append('        "page": page,\n')
        new_lines.append('        "limit": limit,\n')
        new_lines.append('        "users": [\n')
        new_lines.append('            {\n')
        new_lines.append('                "device_id": r[0] if len(r) > 0 else None,\n')
        new_lines.append('                "device_model": r[1] if len(r) > 1 else None,\n')
        new_lines.append('                "app_version": r[2] if len(r) > 2 else None,\n')
        new_lines.append('                "last_seen": r[3].isoformat() if len(r) > 3 and r[3] else None,\n')
        new_lines.append('                "license_key": r[4] if len(r) > 4 else None,\n')
        new_lines.append('                "license_tier": r[5] if len(r) > 5 else None,\n')
        new_lines.append('                "license_expires_at": r[6] if len(r) > 6 else None,\n')
        new_lines.append('                "is_active": r[7] if len(r) > 7 else None,\n')
        new_lines.append('                "total_sessions": r[8] if len(r) > 8 else 0\n')
        new_lines.append('            } for r in results\n')
        new_lines.append('        ]\n')
        new_lines.append('    }\n')
        
        # Skip old return
        while i < len(lines) and ('return {' in lines[i] or '"device_id": r[1]' in lines[i] or '}' in lines[i]):
            if '}' in lines[i] and 'return' in '\n'.join(new_lines[-5:]):
                break
            i += 1
        continue
    
    new_lines.append(line)
    i += 1

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✅ Fixed /admin/users endpoint')


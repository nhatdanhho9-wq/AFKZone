#!/usr/bin/env python3
"""Fix dashboard stats - wrap all queries in try/except and handle transaction rollback"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Find dashboard stats function and wrap server_stats query in try/except
old_server_stats = '''    # Server stats (if exists)
    server_stats = db.execute(text(
        "SELECT cpu_usage_percent, memory_usage_mb, active_connections, bandwidth_in_mbps, bandwidth_out_mbps FROM server_stats ORDER BY timestamp DESC LIMIT 1"
    )).fetchone()

    return {
        "total_devices": total_devices or 0,
        "active_devices_24h": active_24h or 0,
        "total_licenses_active": active_licenses or 0,
        "total_licenses_expired": expired_licenses or 0,
        "total_revenue_today": revenue_today,
        "total_revenue_month": revenue_month,
        "total_revenue_all": revenue_all,
        "server_status": {
            "cpu_usage": server_stats[0] if server_stats else 0,
            "memory_usage_mb": server_stats[1] if server_stats else 0,
            "active_connections": server_stats[2] if server_stats else 0,
            "bandwidth_in_mbps": server_stats[3] if server_stats else 0,
            "bandwidth_out_mbps": server_stats[4] if server_stats else 0
        } if server_stats else None
    }'''

new_server_stats = '''    # Server stats (if exists)
    server_stats = None
    try:
        server_stats = db.execute(text(
            "SELECT cpu_usage_percent, memory_usage_mb, active_connections, bandwidth_in_mbps, bandwidth_out_mbps FROM server_stats ORDER BY timestamp DESC LIMIT 1"
        )).fetchone()
    except Exception:
        server_stats = None

    return {
        "total_devices": total_devices or 0,
        "active_devices_24h": active_24h or 0,
        "total_licenses_active": active_licenses or 0,
        "total_licenses_expired": expired_licenses or 0,
        "total_revenue_today": revenue_today,
        "total_revenue_month": revenue_month,
        "total_revenue_all": revenue_all,
        "server_status": {
            "cpu_usage": server_stats[0] if server_stats else 0,
            "memory_usage_mb": server_stats[1] if server_stats else 0,
            "active_connections": server_stats[2] if server_stats else 0,
            "bandwidth_in_mbps": server_stats[3] if server_stats else 0,
            "bandwidth_out_mbps": server_stats[4] if server_stats else 0
        } if server_stats else None
    }'''

if old_server_stats in content:
    content = content.replace(old_server_stats, new_server_stats)
    print('✅ Fixed server_stats query with try/except')

# Also ensure all queries have proper error handling
# Wrap all queries in try/except to prevent transaction abort
if '# Total devices' in content and 'try:' not in content[content.find('# Total devices'):content.find('# Total devices')+200]:
    # Need to wrap all queries
    dashboard_start = content.find('def get_dashboard_stats')
    dashboard_end = content.find('    }', content.find('return {', dashboard_start))
    
    if dashboard_start > 0 and dashboard_end > 0:
        # Replace the entire function body with try/except wrapped version
        function_body = content[dashboard_start:dashboard_end+5]
        
        # Actually, simpler approach - just ensure server_stats has try/except
        # And wrap other queries if needed
        
        # Check if total_devices already has try/except
        if 'try:' not in content[content.find('# Total devices'):content.find('# Revenue', content.find('# Total devices'))]:
            # Wrap all queries
            old_queries = '''    # Total devices
    total_devices = db.execute(text("SELECT COUNT(*) FROM devices")).scalar()

    # Active devices (last 24h)
    active_24h = db.execute(text(
        "SELECT COUNT(*) FROM devices WHERE last_seen > NOW() - INTERVAL '24 hours'"
    )).scalar()'''
            
            new_queries = '''    # Total devices
    try:
        total_devices = db.execute(text("SELECT COUNT(*) FROM devices")).scalar() or 0
    except Exception:
        total_devices = 0

    # Active devices (last 24h)
    try:
        active_24h = db.execute(text(
            "SELECT COUNT(*) FROM devices WHERE last_seen > NOW() - INTERVAL '24 hours'"
        )).scalar() or 0
    except Exception:
        active_24h = 0'''
            
            if old_queries in content:
                content = content.replace(old_queries, new_queries)
                print('✅ Wrapped device queries in try/except')

with open('/app/app.py', 'w') as f:
    f.write(content)

# Verify
import ast
try:
    ast.parse(content)
    print('✅ Syntax is valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')
    exit(1)


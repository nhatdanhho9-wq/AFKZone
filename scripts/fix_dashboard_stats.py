#!/usr/bin/env python3
"""Fix dashboard stats to handle missing payments table"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Fix dashboard stats - wrap payments queries in try/except
old_revenue = '''    # Revenue today
    revenue_today = db.execute(text(
        "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND DATE(completed_at) = CURRENT_DATE"
    )).scalar() or 0

    # Revenue this month
    revenue_month = db.execute(text(
        "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND EXTRACT(MONTH FROM completed_at) = EXTRACT(MONTH FROM NOW())"
    )).scalar() or 0

    # Revenue all time
    revenue_all = db.execute(text(
        "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success'"
    )).scalar() or 0'''

new_revenue = '''    # Revenue (handle missing payments table)
    try:
        revenue_today = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND DATE(completed_at) = CURRENT_DATE"
        )).scalar() or 0
    except Exception:
        revenue_today = 0

    try:
        revenue_month = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND EXTRACT(MONTH FROM completed_at) = EXTRACT(MONTH FROM NOW())"
        )).scalar() or 0
    except Exception:
        revenue_month = 0

    try:
        revenue_all = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success'"
        )).scalar() or 0
    except Exception:
        revenue_all = 0'''

if old_revenue in content:
    content = content.replace(old_revenue, new_revenue)
    print('✅ Fixed dashboard stats revenue queries')

# Also fix expires_at comparison with try/except
old_active_licenses = '''    # Active licenses (expires_at is timestamp)
    try:
        active_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at > NOW() AND activated_at IS NOT NULL"
        )).scalar()
    except:
        # Fallback: try bigint comparison
        active_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at::bigint > (EXTRACT(EPOCH FROM NOW())::bigint * 1000) AND activated_at IS NOT NULL"
        )).scalar()

    # Expired licenses
    try:
        expired_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at <= NOW() AND activated_at IS NOT NULL"
        )).scalar()
    except:
        # Fallback: try bigint comparison
        expired_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at::bigint <= (EXTRACT(EPOCH FROM NOW())::bigint * 1000) AND activated_at IS NOT NULL"
        )).scalar()'''

# Actually, let's use simpler version
if '# Active licenses (expires_at is timestamp)' in content:
    # Check if it already has try/except
    if 'try:' in content[content.find('# Active licenses'):content.find('# Active licenses')+500]:
        print('✅ Active/expired licenses already have try/except')
    else:
        # Replace with simpler version
        simple_version = '''    # Active licenses
    try:
        active_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at > NOW() AND activated_at IS NOT NULL"
        )).scalar() or 0
    except Exception:
        active_licenses = 0

    # Expired licenses
    try:
        expired_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at <= NOW() AND activated_at IS NOT NULL"
        )).scalar() or 0
    except Exception:
        expired_licenses = 0'''
        
        # Find and replace
        start_pos = content.find('# Active licenses')
        if start_pos > 0:
            end_pos = content.find('# Revenue', start_pos)
            if end_pos > 0:
                content = content[:start_pos] + simple_version + '\n\n' + content[end_pos:]
                print('✅ Fixed active/expired licenses queries')

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


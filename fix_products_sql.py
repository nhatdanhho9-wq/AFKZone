#!/usr/bin/env python3
"""Fix the products endpoint SQL syntax error"""
import re

with open('/app/app.py', 'r') as f:
    content = f.read()

# The issue is the f-string with {{where_clause}} - it needs to be fixed
# Find the broken products endpoint and replace with working version

WORKING_PRODUCTS = '''@app.get("/products")
def get_products(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all products with color_hex from tiers, sorted by tier.display_order then duration"""
    if active_only:
        query = """
            SELECT p.id, p.name, p.tier, p.duration_days, p.price, p.max_devices,
                   p.is_active, p.display_order, p.description,
                   COALESCE(t.color_hex, '#808080') as color_hex,
                   COALESCE(t.display_order, 999) as tier_order
            FROM products p
            LEFT JOIN tiers t ON LOWER(p.tier) = LOWER(t.tier_key) OR LOWER(p.tier) = LOWER(t.tier_name)
            WHERE p.is_active = TRUE
            ORDER BY COALESCE(t.display_order, 999), p.duration_days, p.id
        """
    else:
        query = """
            SELECT p.id, p.name, p.tier, p.duration_days, p.price, p.max_devices,
                   p.is_active, p.display_order, p.description,
                   COALESCE(t.color_hex, '#808080') as color_hex,
                   COALESCE(t.display_order, 999) as tier_order
            FROM products p
            LEFT JOIN tiers t ON LOWER(p.tier) = LOWER(t.tier_key) OR LOWER(p.tier) = LOWER(t.tier_name)
            ORDER BY COALESCE(t.display_order, 999), p.duration_days, p.id
        """
    results = db.execute(text(query)).fetchall()
    products = []
    for r in results:
        price, max_dev = r[4], r[5]
        products.append({
            "id": r[0], "name": r[1], "tier": r[2], "duration_days": r[3], "price": price,
            "display_price": f"{price:,.0f}d".replace(",", "."), "max_devices": max_dev,
            "max_devices_display": "Vo cuc" if max_dev == -1 else f"{max_dev} thiet bi",
            "is_active": r[6], "display_order": r[7], "description": r[8], "color_hex": r[9]
        })
    return {"products": products}'''

# Find and replace the broken products endpoint
old_pattern = r'@app\.get\("/products"\)\ndef get_products\(active_only: bool = True, db: Session = Depends\(get_db\)\):.*?return \{"products": products\}'

if re.search(old_pattern, content, re.DOTALL):
    content = re.sub(old_pattern, WORKING_PRODUCTS, content, flags=re.DOTALL)
    with open('/app/app.py', 'w') as f:
        f.write(content)
    print("SUCCESS: Fixed products endpoint SQL syntax")
else:
    print("ERROR: Products endpoint pattern not found")

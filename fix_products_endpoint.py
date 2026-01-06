#!/usr/bin/env python3
"""
Fix products endpoint to include color_hex from tiers table
and sort by tier.display_order, product.display_order
"""

# New /products endpoint implementation
NEW_PRODUCTS_ENDPOINT = '''@app.get("/products")
def get_products(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all products with color_hex from tiers, sorted by tier.display_order then product.display_order"""
    query = """
        SELECT p.id, p.name, p.tier, p.duration_days, p.price, p.max_devices, 
               p.is_active, p.display_order, p.description,
               COALESCE(t.color_hex, '#808080') as color_hex,
               COALESCE(t.display_order, 999) as tier_order
        FROM products p
        LEFT JOIN tiers t ON LOWER(p.tier) = LOWER(t.name)
        {where_clause}
        ORDER BY COALESCE(t.display_order, 999), p.display_order, p.id
    """.format(where_clause="WHERE p.is_active=TRUE" if active_only else "")
    
    results = db.execute(text(query)).fetchall()
    products = []
    for r in results:
        price, max_dev = r[4], r[5]
        products.append({
            "id": r[0],
            "name": r[1],
            "tier": r[2],
            "duration_days": r[3],
            "price": price,
            "display_price": f"{price:,.0f}đ".replace(",", "."),
            "max_devices": max_dev,
            "max_devices_display": "Vô cực" if max_dev == -1 else f"{max_dev} thiết bị",
            "is_active": r[6],
            "display_order": r[7],
            "description": r[8],
            "color_hex": r[9]
        })
    return {"products": products}'''

# Read current app.py
with open('/app/app.py', 'r') as f:
    content = f.read()

# Find and replace the old products endpoint
import re

# Pattern for old endpoint - match from @app.get("/products") to return {"products": products}
old_pattern = r'@app\.get\("/products"\)\ndef get_products\(active_only: bool = True, db: Session = Depends\(get_db\)\):.*?return \{"products": products\}'

if re.search(old_pattern, content, re.DOTALL):
    new_content = re.sub(old_pattern, NEW_PRODUCTS_ENDPOINT, content, flags=re.DOTALL)
    with open('/app/app.py', 'w') as f:
        f.write(new_content)
    print("SUCCESS: Products endpoint patched with color_hex and tier sorting")
else:
    print("ERROR: Old products endpoint pattern not found")
    print("Trying alternative approach...")
    
    # Alternative: Just find the specific function start
    if '@app.get("/products")' in content:
        print("Found products endpoint, needs manual patch")
    else:
        print("Products endpoint not found at all")

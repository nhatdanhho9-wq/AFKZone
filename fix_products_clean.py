#!/usr/bin/env python3
"""
Complete fix for products endpoint - replace entire function
"""

# Read current app.py
with open('/app/app.py', 'r') as f:
    lines = f.readlines()

# Find the products endpoint and replace the entire function
start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if '@app.get("/products")' in line:
        start_line = i
    elif start_line >= 0 and line.startswith('@app.') and i > start_line:
        end_line = i
        break

if start_line >= 0 and end_line > 0:
    # New clean products endpoint
    new_code = '''@app.get("/products")
def get_products(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all products with color_hex from tiers, sorted by tier.display_order then product.display_order"""
    where_clause = "WHERE p.is_active=TRUE" if active_only else ""
    query = f"""
        SELECT p.id, p.name, p.tier, p.duration_days, p.price, p.max_devices,
               p.is_active, p.display_order, p.description,
               COALESCE(t.color_hex, '#808080') as color_hex,
               COALESCE(t.display_order, 999) as tier_order
        FROM products p
        LEFT JOIN tiers t ON LOWER(p.tier) = LOWER(t.name)
        {where_clause}
        ORDER BY COALESCE(t.display_order, 999), p.display_order, p.id
    """
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
    return {"products": products}

'''
    # Replace the function
    new_lines = lines[:start_line] + [new_code] + lines[end_line:]
    
    with open('/app/app.py', 'w') as f:
        f.writelines(new_lines)
    
    print(f"SUCCESS: Replaced lines {start_line+1} to {end_line}")
else:
    print(f"ERROR: start_line={start_line}, end_line={end_line}")

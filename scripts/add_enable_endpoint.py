#!/usr/bin/env python3
"""Add enable product endpoint to app.py"""

def add_enable_endpoint():
    with open('/app/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already exists
    if '/admin/products/{product_id}/enable' in content:
        print("⚠️ Enable endpoint already exists!")
        return
    
    # Add endpoint after delete_product_permanent
    endpoint_code = '''

# ==================== ENABLE PRODUCT ====================
@app.post("/admin/products/{product_id}/enable")
def enable_product(product_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Enable product (set is_active=TRUE)"""
    # Check if product exists
    product = db.execute(text("SELECT * FROM products WHERE id=:id"), {"id": product_id}).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.execute(text("UPDATE products SET is_active=TRUE WHERE id=:id"), {"id": product_id})
    db.commit()
    return {"success": True, "message": "Product enabled successfully"}

# ==================== DISABLE PRODUCT ====================
@app.post("/admin/products/{product_id}/disable")
def disable_product(product_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Disable product (set is_active=FALSE)"""
    product = db.execute(text("SELECT * FROM products WHERE id=:id"), {"id": product_id}).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.execute(text("UPDATE products SET is_active=FALSE WHERE id=:id"), {"id": product_id})
    db.commit()
    return {"success": True, "message": "Product disabled successfully"}
'''
    
    # Find where to insert - after delete_product_permanent
    marker = '# ==================== DASHBOARD STATS ===================='
    if marker in content:
        content = content.replace(marker, endpoint_code + '\n' + marker)
    else:
        # Append at end
        content += endpoint_code
    
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Added enable_product and disable_product endpoints!")

if __name__ == '__main__':
    add_enable_endpoint()

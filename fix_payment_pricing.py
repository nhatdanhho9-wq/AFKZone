#!/usr/bin/env python3
"""
Fix payment pricing - read from products table instead of pricing table
Also add delete product endpoint and improve license revocation
"""

with open('/app/app.py', 'r') as f:
    content = f.read()

changes = []

# 1. Fix /payment/bank/create to read from products table first
old_payment = '''@app.post("/payment/bank/create")
def bank_transfer_create(req: BankTransferRequest, db: Session = Depends(get_db)):
    price_result = db.execute(text("SELECT price FROM pricing WHERE tier=:tier AND duration_days=:days"), {"tier": req.tier, "days": req.duration_days}).fetchone()
    if not price_result:
        raise HTTPException(status_code=400, detail="Invalid tier or duration")'''

new_payment = '''@app.post("/payment/bank/create")
def bank_transfer_create(req: BankTransferRequest, db: Session = Depends(get_db)):
    # First try products table (for admin-created products)
    price_result = db.execute(text("SELECT price FROM products WHERE tier=:tier AND duration_days=:days AND is_active=TRUE"), {"tier": req.tier, "days": req.duration_days}).fetchone()
    
    # Fallback to pricing table
    if not price_result:
        price_result = db.execute(text("SELECT price FROM pricing WHERE tier=:tier AND duration_days=:days"), {"tier": req.tier, "days": req.duration_days}).fetchone()
    
    if not price_result:
        raise HTTPException(status_code=400, detail="Invalid tier or duration")'''

if old_payment in content:
    content = content.replace(old_payment, new_payment)
    changes.append('Fixed payment to read from products table first')

# 2. Add permanent delete endpoint for products
delete_product_endpoint = '''
@app.delete("/admin/products/{product_id}/permanent")
def delete_product_permanent(
    product_id: int,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Permanently delete a product"""
    # Check if product exists
    product = db.execute(text("SELECT * FROM products WHERE id=:id"), {"id": product_id}).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete from pricing table
    db.execute(text("DELETE FROM pricing WHERE tier=:tier AND duration_days=:days"), 
               {"tier": product[2], "days": product[3]})
    
    # Delete product
    db.execute(text("DELETE FROM products WHERE id=:id"), {"id": product_id})
    db.commit()
    
    return {"success": True, "message": "Product permanently deleted"}

'''

if '@app.delete("/admin/products/{product_id}/permanent")' not in content:
    # Insert after soft delete endpoint
    marker = 'return {"success": True, "message": "Product deleted successfully"}'
    if marker in content:
        pos = content.find(marker)
        end_pos = content.find('\n', pos)
        content = content[:end_pos+1] + delete_product_endpoint + content[end_pos+1:]
        changes.append('Added permanent delete product endpoint')

# 3. Add license revocation check to /check endpoint
# Find the check endpoint and enhance it
old_check_return = '''    return {
        "status": "active",
        "tier": r[2],'''

new_check_return = '''    # Check if license is revoked
    if len(r) > 9 and r[9]:  # is_revoked
        return {"status": "revoked", "message": "License has been revoked"}
    
    return {
        "status": "active",
        "tier": r[2],'''

if old_check_return in content and 'is_revoked' not in content[content.find('def check_license'):content.find('def check_license')+2000]:
    content = content.replace(old_check_return, new_check_return)
    changes.append('Added revocation check to /check endpoint')

with open('/app/app.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('✅ All fixes applied:')
    for c in changes:
        print(f'  - {c}')
    print('✅ Syntax valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')


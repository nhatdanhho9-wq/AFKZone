#!/usr/bin/env python3
"""
Patch to update DELETE /admin/products/{product_id} endpoint
with smart hard/soft delete logic based on order existence.
"""

NEW_DELETE_ENDPOINT = '''
@app.delete("/admin/products/{product_id}")
def delete_product(product_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """
    Admin: Delete product with smart logic:
    - If product has NO orders -> hard delete (remove from DB)
    - If product has orders -> soft delete (set is_active=FALSE)
    """
    # Get product info first
    product = db.execute(text("SELECT id, name, tier, duration_days FROM products WHERE id=:id"), {"id": product_id}).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    tier = product[2]
    duration_days = product[3]
    
    # Check if any orders exist for this product (by tier + duration_days)
    order_count = db.execute(text("""
        SELECT COUNT(*) FROM bank_orders 
        WHERE tier = :tier AND duration_days = :days
    """), {"tier": tier, "days": duration_days}).scalar() or 0
    
    if order_count == 0:
        # No orders - HARD DELETE
        # Also clean up pricing table
        db.execute(text("DELETE FROM pricing WHERE tier=:tier AND duration_days=:days"),
                   {"tier": tier, "days": duration_days})
        db.execute(text("DELETE FROM products WHERE id=:id"), {"id": product_id})
        db.commit()
        return {
            "success": True,
            "action": "hard_deleted",
            "message": f"Product '{product[1]}' permanently deleted (no orders found)"
        }
    else:
        # Has orders - SOFT DELETE
        db.execute(text("UPDATE products SET is_active=FALSE WHERE id=:id"), {"id": product_id})
        db.commit()
        return {
            "success": True,
            "action": "soft_disabled",
            "reason": f"Product has {order_count} associated order(s)",
            "message": f"Product '{product[1]}' disabled (has {order_count} orders)"
        }
'''

print(NEW_DELETE_ENDPOINT)

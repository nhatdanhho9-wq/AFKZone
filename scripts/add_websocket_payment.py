#!/usr/bin/env python3
"""
Add WebSocket Payment Notification to FastAPI backend
"""

def add_websocket_payment():
    with open('/app/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/app.py.bak_ws', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Check if already exists
    if '/ws/payment/' in content:
        print("⚠️ WebSocket endpoint already exists!")
        return
    
    # Add WebSocket imports if not exists
    if 'from fastapi import WebSocket' not in content:
        content = content.replace(
            'from fastapi import FastAPI',
            'from fastapi import FastAPI, WebSocket, WebSocketDisconnect'
        )
        print("✅ Added WebSocket import")
    
    # Add WebSocket manager and endpoint
    websocket_code = '''

# ==================== WEBSOCKET PAYMENT NOTIFICATION ====================
import asyncio
from typing import Dict, Set

# Store active WebSocket connections by order_id
payment_connections: Dict[str, Set[WebSocket]] = {}

class PaymentConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, order_id: str, websocket: WebSocket):
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = set()
        self.active_connections[order_id].add(websocket)
        print(f"📡 WebSocket connected for order {order_id}")
    
    def disconnect(self, order_id: str, websocket: WebSocket):
        if order_id in self.active_connections:
            self.active_connections[order_id].discard(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]
        print(f"📡 WebSocket disconnected for order {order_id}")
    
    async def notify_payment_complete(self, order_id: str, license_key: str, expires_at: int):
        """Notify all connected clients that payment is complete"""
        if order_id in self.active_connections:
            message = {
                "type": "payment_complete",
                "order_id": order_id,
                "license_key": license_key,
                "expires_at": expires_at,
                "message": "Thanh toán thành công! License của bạn đã được kích hoạt."
            }
            disconnected = []
            for websocket in self.active_connections[order_id]:
                try:
                    await websocket.send_json(message)
                    print(f"✅ Sent license notification to order {order_id}")
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected
            for ws in disconnected:
                self.active_connections[order_id].discard(ws)

payment_manager = PaymentConnectionManager()

@app.websocket("/ws/payment/{order_id}")
async def websocket_payment_endpoint(websocket: WebSocket, order_id: str):
    """WebSocket endpoint for payment notifications"""
    await payment_manager.connect(order_id, websocket)
    try:
        # Check if order already completed
        from database import get_db
        db = next(get_db())
        order = db.execute(text(
            "SELECT payment_status, license_key FROM orders WHERE order_id=:oid"
        ), {"oid": order_id}).fetchone()
        
        if order and order[0] == 'success' and order[1]:
            # Already paid, send license immediately
            await websocket.send_json({
                "type": "payment_complete",
                "order_id": order_id,
                "license_key": order[1],
                "message": "Đơn hàng đã được thanh toán!"
            })
        
        # Keep connection alive and wait for payment
        while True:
            try:
                # Receive heartbeat or close
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "keepalive"})
    except WebSocketDisconnect:
        payment_manager.disconnect(order_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        payment_manager.disconnect(order_id, websocket)

# Endpoint to check order status (fallback if WebSocket fails)
@app.get("/payment/status/{order_id}")
def check_payment_status(order_id: str, db: Session = Depends(get_db)):
    """Check payment status for an order"""
    order = db.execute(text(
        "SELECT payment_status, license_key, tier, duration_days FROM orders WHERE order_id=:oid"
    ), {"oid": order_id}).fetchone()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "order_id": order_id,
        "status": order[0],
        "license_key": order[1],
        "tier": order[2],
        "duration_days": order[3]
    }
'''
    
    # Add websocket code before the last lines
    content += websocket_code
    print("✅ Added WebSocket endpoint")
    
    # Update Casso webhook to notify WebSocket clients
    old_webhook_success = '''logging.info(f"License created: {license_key} for order {order_id}")
            
            results.append({
                "success": True,
                "order_id": order_id,
                "license_key": license_key,
                "expires_at": expires_at
            })'''
    
    new_webhook_success = '''logging.info(f"License created: {license_key} for order {order_id}")
            
            # Notify WebSocket clients
            try:
                import asyncio
                asyncio.create_task(payment_manager.notify_payment_complete(order_id, license_key, expires_at))
            except Exception as ws_err:
                logging.warning(f"Could not notify WebSocket: {ws_err}")
            
            results.append({
                "success": True,
                "order_id": order_id,
                "license_key": license_key,
                "expires_at": expires_at
            })'''
    
    if old_webhook_success in content:
        content = content.replace(old_webhook_success, new_webhook_success)
        print("✅ Updated Casso webhook to notify WebSocket")
    else:
        print("⚠️ Could not find webhook success block to update")
    
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ DONE! Restart container to apply changes.")

if __name__ == '__main__':
    add_websocket_payment()

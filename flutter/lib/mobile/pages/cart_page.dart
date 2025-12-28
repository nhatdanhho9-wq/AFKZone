import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_hbb/services/cart_service.dart';
import 'package:flutter_hbb/models/cart_model.dart';
import 'payment_qr_screen.dart';

class CartPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Gio hang'),
        backgroundColor: Colors.deepPurple,
      ),
      body: Consumer<CartService>(
        builder: (context, cart, child) {
          if (cart.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.shopping_cart_outlined, size: 100, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('Gio hang trong', style: TextStyle(fontSize: 18, color: Colors.grey)),
                  SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => Navigator.pop(context),
                    child: Text('Tiep tuc mua hang'),
                  ),
                ],
              ),
            );
          }

          return Column(
            children: [
              Expanded(
                child: ListView.builder(
                  itemCount: cart.items.length,
                  padding: EdgeInsets.all(16),
                  itemBuilder: (context, index) {
                    final item = cart.items[index];
                    return _buildCartItem(context, cart, item);
                  },
                ),
              ),
              _buildCheckoutSection(context, cart),
            ],
          );
        },
      ),
    );
  }

  Widget _buildCartItem(BuildContext context, CartService cart, CartItem item) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: EdgeInsets.all(12),
        child: Row(
          children: [
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: _getTierColor(item.product.tier).withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(Icons.card_membership, color: _getTierColor(item.product.tier), size: 32),
            ),
            SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.product.name, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  SizedBox(height: 4),
                  Text('${item.product.tierDisplayName} - ${item.product.durationDays} ngay', 
                    style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                  SizedBox(height: 4),
                  Text(item.product.formattedPrice, 
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: _getTierColor(item.product.tier))),
                ],
              ),
            ),
            Column(
              children: [
                Row(
                  children: [
                    IconButton(
                      icon: Icon(Icons.remove_circle_outline),
                      onPressed: () => cart.updateQuantity(item.product.id, item.quantity - 1),
                      padding: EdgeInsets.zero,
                      constraints: BoxConstraints(),
                    ),
                    Container(
                      width: 40,
                      alignment: Alignment.center,
                      child: Text('${item.quantity}', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    ),
                    IconButton(
                      icon: Icon(Icons.add_circle_outline),
                      onPressed: () => cart.updateQuantity(item.product.id, item.quantity + 1),
                      padding: EdgeInsets.zero,
                      constraints: BoxConstraints(),
                    ),
                  ],
                ),
                TextButton.icon(
                  icon: Icon(Icons.delete, size: 16),
                  label: Text('Xoa', style: TextStyle(fontSize: 12)),
                  onPressed: () => cart.removeFromCart(item.product.id),
                  style: TextButton.styleFrom(foregroundColor: Colors.red),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCheckoutSection(BuildContext context, CartService cart) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, -2))],
      ),
      child: SafeArea(
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Tong cong (${cart.itemCount} san pham):', style: TextStyle(fontSize: 16)),
                Text(cart.formattedTotalPrice, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.deepPurple)),
              ],
            ),
            SizedBox(height: 12),
            ElevatedButton(
              onPressed: () => _showCheckoutDialog(context, cart),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                minimumSize: Size(double.infinity, 50),
              ),
              child: Text('Thanh toan', style: TextStyle(fontSize: 18, color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  void _showCheckoutDialog(BuildContext context, CartService cart) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Xac nhan thanh toan'),
        content: Text('Ban muon thanh toan ${cart.itemCount} san pham voi tong gia ${cart.formattedTotalPrice}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Huy'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              // For now, just checkout the first item
              // In production, you'd handle multiple items
              final firstItem = cart.items.first;
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (c) => PaymentQRScreen(
                    tier: firstItem.product.tier,
                    durationDays: firstItem.product.durationDays,
                  ),
                ),
              ).then((_) {
                // Clear cart after successful payment
                cart.clearCart();
              });
            },
            child: Text('Thanh toan'),
          ),
        ],
      ),
    );
  }

  Color _getTierColor(String tier) {
    switch (tier) {
      case 'basic':
        return Colors.blue;
      case 'pro':
        return Colors.purple;
      case 'enterprise':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}


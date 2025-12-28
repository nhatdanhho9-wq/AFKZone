import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/product_service.dart';
import '../services/cart_service.dart';
import '../../models/product_model.dart';
import 'payment_qr_screen.dart';
import 'cart_page.dart';

class PaymentScreen extends StatefulWidget {
  @override
  _PaymentScreenState createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  bool _isLoading = true;
  String? _error;
  Map<String, List<Product>> _productsByTier = {};

  @override
  void initState() {
    super.initState();
    _loadProducts();
  }

  Future<void> _loadProducts() async {
    try {
      final products = await ProductService.fetchProductsByTier();
      setState(() {
        _productsByTier = products;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Khong the tai danh sach goi';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Mua License AFK Zone'),
        backgroundColor: Colors.deepPurple,
        actions: [
          Consumer<CartService>(
            builder: (context, cart, child) {
              return Stack(
                children: [
                  IconButton(
                    icon: Icon(Icons.shopping_cart),
                    onPressed: () {
                      Navigator.push(context, MaterialPageRoute(builder: (c) => CartPage()));
                    },
                  ),
                  if (cart.itemCount > 0)
                    Positioned(
                      right: 8,
                      top: 8,
                      child: Container(
                        padding: EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          shape: BoxShape.circle,
                        ),
                        constraints: BoxConstraints(minWidth: 18, minHeight: 18),
                        child: Text(
                          '${cart.itemCount}',
                          style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ],
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 64, color: Colors.red),
                      SizedBox(height: 16),
                      Text(_error!, textAlign: TextAlign.center),
                      SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadProducts,
                        child: Text('Thu lai'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadProducts,
                  child: ListView(
                    padding: EdgeInsets.all(16),
                    children: [
                      Text('Chon goi license', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
                      SizedBox(height: 8),
                      Text('Keo xuong de lam moi gia', style: TextStyle(fontSize: 12, color: Colors.grey), textAlign: TextAlign.center),
                      SizedBox(height: 24),
                      if (_productsByTier['basic']?.isNotEmpty ?? false)
                        _buildTierSection('Basic', Colors.blue, _productsByTier['basic']!),
                      SizedBox(height: 16),
                      if (_productsByTier['pro']?.isNotEmpty ?? false)
                        _buildTierSection('Pro', Colors.purple, _productsByTier['pro']!),
                      SizedBox(height: 16),
                      if (_productsByTier['enterprise']?.isNotEmpty ?? false)
                        _buildTierSection('Enterprise', Colors.orange, _productsByTier['enterprise']!),
                    ],
                  ),
                ),
    );
  }

  Widget _buildTierSection(String name, Color color, List<Product> products) {
    return Card(
      elevation: 4,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.star, color: color),
                SizedBox(width: 8),
                Text(name, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
                Spacer(),
                Text('${products.first.maxDevices} thiet bi', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
              ],
            ),
            if (products.first.description != null) ...[
              SizedBox(height: 8),
              Text(products.first.description!, style: TextStyle(fontSize: 12, color: Colors.grey[700])),
            ],
            SizedBox(height: 12),
            ...products.map((product) => _buildProductButton(product, color)).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildProductButton(Product product, Color color) {
    return Consumer<CartService>(
      builder: (context, cart, child) {
        final inCart = cart.hasProduct(product.id);
        return Padding(
          padding: EdgeInsets.only(bottom: 8),
          child: Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (c) => PaymentQRScreen(tier: product.tier, durationDays: product.durationDays),
                      ),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: color,
                    minimumSize: Size(0, 56),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('${product.durationDays} ngay', style: TextStyle(fontSize: 18, color: Colors.white)),
                      Text(product.formattedPrice, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                    ],
                  ),
                ),
              ),
              SizedBox(width: 8),
              IconButton(
                icon: Icon(inCart ? Icons.shopping_cart : Icons.add_shopping_cart),
                color: inCart ? Colors.green : color,
                onPressed: () {
                  cart.addToCart(product);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Da them vao gio hang'), duration: Duration(seconds: 1)),
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

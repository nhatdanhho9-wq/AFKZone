import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/services/cart_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import 'package:flutter_hbb/common/license_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
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
                Text(products.first.maxDevicesDisplay, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
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
        final isFree = product.price == 0;
        final is7DaysFree = isFree && product.durationDays == 7;
        
        return Padding(
          padding: EdgeInsets.only(bottom: 8),
          child: Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () async {
                    // Handle free 7-day license (same as trial)
                    if (is7DaysFree) {
                      await _handleFree7DaysLicense(product);
                    } else {
                      // Paid products - go to payment screen
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (c) => PaymentQRScreen(tier: product.tier, durationDays: product.durationDays),
                        ),
                      );
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isFree ? Colors.green : color,
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
              if (!isFree) // Don't show cart for free products
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

  Future<void> _handleFree7DaysLicense(Product product) async {
    // Show loading dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => Center(child: CircularProgressIndicator()),
    );

    try {
      // Check if user has already used trial
      final trialStatus = await LicenseService.checkTrial();
      final hasTrialed = trialStatus['has_trialed'] ?? false;

      Navigator.pop(context); // Close loading dialog

      if (hasTrialed) {
        // Already used trial - show message
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: Row(
              children: [
                Icon(Icons.info_outline, color: Colors.orange),
                SizedBox(width: 8),
                Expanded(child: Text('Thông báo')),
              ],
            ),
            content: Text(
              'Bạn đã sử dụng dùng thử 7 ngày.\n\nVui lòng liên hệ admin để tiếp tục trải nghiệm miễn phí.',
              style: TextStyle(fontSize: 16),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text('Đã hiểu'),
              ),
            ],
          ),
        );
        return;
      }

      // Generate and activate free license (same as trial)
      final result = await LicenseService.generateTrial();
      if (result != null && result['license_key'] != null) {
        final deviceId = await LicenseService.getDeviceFingerprint();
        final activationResult = await LicenseService.activateLicense(
          result['license_key'],
          deviceId,
        );

        if (activationResult != null) {
          // Save license info
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('license_key', result['license_key']);
          await prefs.setString('device_id', deviceId);
          await prefs.setBool('afk_license_active', true);
          
          // Add license_key to result for callback
          activationResult['license_key'] = result['license_key'];
          
          // Show success dialog
          showDialog(
            context: context,
            barrierDismissible: false,
            builder: (context) => AlertDialog(
              title: Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.green, size: 32),
                  SizedBox(width: 12),
                  Expanded(child: Text('Kích hoạt thành công!')),
                ],
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('🎉 Bạn đã được kích hoạt license 7 ngày miễn phí!', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  SizedBox(height: 12),
                  Container(
                    padding: EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.grey[100],
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: SelectableText(
                      result['license_key'],
                      style: TextStyle(fontFamily: 'monospace', fontSize: 12),
                    ),
                  ),
                  SizedBox(height: 8),
                  Text('License đã được tự động kích hoạt trên thiết bị này.', style: TextStyle(fontSize: 14)),
                ],
              ),
              actions: [
                ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context); // Close dialog
                    Navigator.pop(context); // Go back to previous screen
                  },
                  child: Text('Hoàn tất'),
                ),
              ],
            ),
          );
        }
      }
    } catch (e) {
      Navigator.pop(context); // Close loading dialog if still open
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Lỗi'),
          content: Text(e.toString().replaceAll('Exception: ', '').replaceAll('Error: ', '')),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Đóng'),
            ),
          ],
        ),
      );
    }
  }
}

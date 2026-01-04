import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/services/cart_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import 'package:flutter_hbb/common/license_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'payment_qr_screen.dart';
import 'cart_page.dart';
import 'license_wrapper.dart' as license_wrapper;

class PaymentScreen extends StatefulWidget {
  final String? preSelectedTier;
  final String? renewLicenseKey;
  
  const PaymentScreen({
    Key? key,
    this.preSelectedTier,
    this.renewLicenseKey,
  }) : super(key: key);
  
  @override
  _PaymentScreenState createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  bool _isLoading = true;
  String? _error;
  Map<String, List<Product>> _productsByTier = {};
  Map<String, String> _tierNames = {}; // tier key -> tier display name
  String? _selectedTier;

  @override
  void initState() {
    super.initState();
    _selectedTier = widget.preSelectedTier;
    _loadProducts();
  }

  Future<void> _loadProducts({bool showLoading = true}) async {
    if (showLoading) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    }
    
    try {
      print('🔄 PaymentScreen: Loading products and tiers from API...');
      
      // Load products
      final products = await ProductService.fetchProductsByTier();
      print('✅ PaymentScreen: Loaded ${products.length} tiers');
      
      // Load tier names from /tiers API
      final tierNames = await ProductService.fetchTierNames();
      print('✅ PaymentScreen: Loaded tier names: $tierNames');
      
      setState(() {
        _productsByTier = products;
        _tierNames = tierNames;
        _isLoading = false;
        _error = null;
      });
    } catch (e) {
      print('❌ PaymentScreen: Error loading products: $e');
      setState(() {
        _error = 'Không thể tải danh sách gói. Vui lòng thử lại.';
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
          // Refresh button
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: () => _loadProducts(),
            tooltip: 'Làm mới giá',
          ),
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
                  onRefresh: () => _loadProducts(showLoading: false),
                  child: ListView(
                    padding: EdgeInsets.all(16),
                    children: [
                      Text('Chọn gói license', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
                      SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.info_outline, size: 14, color: Colors.grey),
                          SizedBox(width: 4),
                          Text('Kéo xuống hoặc nhấn nút refresh để làm mới giá', style: TextStyle(fontSize: 12, color: Colors.grey)),
                        ],
                      ),
                      SizedBox(height: 24),
                      // Dynamically render all tiers from API
                      ..._productsByTier.entries.map((entry) {
                        final tierKey = entry.key;
                        final products = entry.value;
                        if (products.isEmpty) return SizedBox.shrink();
                        
                        // Get tier name from API, fallback to tier key (NOT product name)
                        final tierName = _tierNames[tierKey] ?? tierKey.toUpperCase();
                        
                        // Choose color based on tier key
                        Color color;
                        switch (tierKey.toLowerCase()) {
                          case 'basic': color = Colors.purple; break;
                          case 'pro': color = Colors.orange; break;
                          case 'enterprise': color = Colors.red; break;
                          case 'promax': color = Colors.blue; break;
                          case 'supervvip': color = Colors.amber; break;
                          default: color = Colors.blueGrey;
                        }
                        
                        return Padding(
                          padding: EdgeInsets.only(bottom: 16),
                          child: _buildTierSection(tierName, color, products),
                        );
                      }).toList(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildTierSection(String tierName, Color color, List<Product> products) {
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
                Expanded(
                  child: Text(tierName, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
                ),
              ],
            ),
            if (products.first.description != null && products.first.description!.isNotEmpty) ...[
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
                    print('🔍 Product clicked: ${product.tier} ${product.durationDays} ngày, price=${product.price}, isFree=$isFree, is7DaysFree=$is7DaysFree');
                    try {
                      // Handle free 7-day license (same as trial) - only if price is 0
                      if (is7DaysFree) {
                        print('✅ Handling as FREE 7-day trial');
                        await _handleFree7DaysLicense(product);
                      } else {
                        // All paid products (including 7-day with price > 0) - go to payment screen
                        print('✅ Navigating to PaymentQRScreen for paid product: ${product.tier} ${product.durationDays} days');
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (c) => PaymentQRScreen(tier: product.tier, durationDays: product.durationDays),
                          ),
                        );
                      }
                    } catch (e) {
                      print('❌ Error in product button: $e');
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Lỗi: ${e.toString()}'), duration: Duration(seconds: 3)),
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
                      Expanded(
                        child: Text(
                          '${product.durationDays} ngày - ${product.maxDevices == -1 ? "Không giới hạn thiết bị" : "${product.maxDevices} thiết bị"}',
                          style: TextStyle(fontSize: 16, color: Colors.white),
                        ),
                      ),
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
          // Add license_key to result for callback
          activationResult['license_key'] = result['license_key'];
          
          // Call LicenseWrapper callback to save license properly
          final licenseWrapperState = context.findAncestorStateOfType<license_wrapper.LicenseWrapperState>();
          if (licenseWrapperState != null) {
            await licenseWrapperState.onLicenseActivated(activationResult);
          } else {
            // Fallback: save manually if wrapper not found
            final prefs = await SharedPreferences.getInstance();
            await prefs.setString('license_key', result['license_key']);
            await prefs.setString('device_id', deviceId);
            await prefs.setBool('afk_license_active', true);
            if (activationResult['expires_at'] != null) {
              try {
                int expiresAt;
                if (activationResult['expires_at'] is String) {
                  final dateTime = DateTime.parse(activationResult['expires_at']);
                  expiresAt = dateTime.millisecondsSinceEpoch;
                } else {
                  expiresAt = activationResult['expires_at'] as int;
                }
                await prefs.setInt('afk_license_expires_at', expiresAt);
              } catch (e) {
                print('Error parsing expires_at: $e');
              }
            }
          }
          
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

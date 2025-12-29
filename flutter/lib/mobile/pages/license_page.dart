import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_hbb/common/license_service.dart';
import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import 'payment_screen.dart';
import 'dart:io';

class LicensePage extends StatefulWidget {
  final Future<void> Function(Map<String, dynamic>) onLicenseActivated;

  const LicensePage({Key? key, required this.onLicenseActivated}) : super(key: key);

  @override
  _LicensePageState createState() => _LicensePageState();
}

class _LicensePageState extends State<LicensePage> {
  final TextEditingController _licenseKeyController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;
  bool _hasTrialed = false;
  bool _trialLoading = true;
  List<Product> _products = [];
  bool _productsLoading = true;

  @override
  void initState() {
    super.initState();
    _checkTrial();
    _loadProducts();
  }

  Future<void> _loadProducts() async {
    try {
      final products = await ProductService.fetchProducts();
      setState(() {
        _products = products;
        _productsLoading = false;
      });
    } catch (e) {
      print('Error loading products for pricing: $e');
      setState(() {
        _productsLoading = false;
      });
    }
  }

  Future<void> _checkTrial() async {
    setState(() => _trialLoading = true);
    try {
      final result = await LicenseService.checkTrial();
      setState(() {
        _hasTrialed = result['has_trialed'] ?? false;
        _trialLoading = false;
      });
    } catch (e) {
      setState(() => _trialLoading = false);
    }
  }

  Future<void> _activateTrial() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      print('🔄 Step 1: Generating trial...');
      final result = await LicenseService.generateTrial();
      print('✅ Step 1 result: $result');
      
      if (result != null && result['license_key'] != null) {
        // Auto-activate with returned license key
        final deviceId = await _getDeviceId();
        final licenseKey = result['license_key'];
        print('🔄 Step 2: Activating license $licenseKey with device $deviceId...');
        
        final activationResult = await LicenseService.activateLicense(
          licenseKey,
          deviceId,
        );
        print('✅ Step 2 result: $activationResult');

        if (activationResult != null && (activationResult['status'] == 'activated' || activationResult['status'] == 'active')) {
          // Add license_key to result so callback can save it
          activationResult['license_key'] = licenseKey;
          print('✅ Step 3: Calling onLicenseActivated callback...');
          setState(() => _isLoading = false);
          try {
            await widget.onLicenseActivated(activationResult);
            print('✅ Step 3: Callback completed successfully');
          } catch (e, stackTrace) {
            print('❌ Step 3: Callback error: $e');
            print('Stack trace: $stackTrace');
            setState(() {
              _errorMessage = 'Lỗi khi lưu license: ${e.toString()}';
            });
          }
        } else {
          print('❌ Step 2 failed: activationResult=${activationResult != null ? activationResult['status'] : 'null'}');
          setState(() {
            _isLoading = false;
            _errorMessage = 'Kích hoạt dùng thử thất bại. Vui lòng thử lại.';
          });
        }
      } else {
        print('❌ Step 1 failed: result is null or no license_key');
        setState(() {
          _isLoading = false;
          _errorMessage = 'Không thể tạo license dùng thử. Vui lòng thử lại.';
        });
      }
    } catch (e, stackTrace) {
      print('❌ Error in _activateTrial: $e');
      print('Stack trace: $stackTrace');
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '').replaceAll('Error: ', '');
        _isLoading = false;
      });
    }
  }

  Future<void> _activateLicenseKey() async {
    if (_licenseKeyController.text.trim().isEmpty) {
      setState(() => _errorMessage = 'Vui lòng nhập license key');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final deviceId = await _getDeviceId();
      final licenseKey = _licenseKeyController.text.trim();
      final result = await LicenseService.activateLicense(
        licenseKey,
        deviceId,
      );

      if (result != null) {
        // Add license_key to result so callback can save it
        result['license_key'] = licenseKey;
        setState(() => _isLoading = false);
        widget.onLicenseActivated(result);
      } else {
        setState(() {
          _isLoading = false;
          _errorMessage = 'Kích hoạt thất bại. Vui lòng thử lại.';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '').replaceAll('Error: ', '');
        _isLoading = false;
      });
    }
  }

  Future<String> _getDeviceId() async {
    return await LicenseService.getDeviceFingerprint();
  }

  void _openZalo() {
    // Open Zalo chat or copy number
    Clipboard.setData(ClipboardData(text: '0823333374'));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Đã copy số Zalo: 0823333374')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0D47A1),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(height: 40),

              // Logo
              Image.asset(
                'assets/logo.png',
                height: 120,
                errorBuilder: (context, error, stackTrace) =>
                  Icon(Icons.desktop_windows, size: 120, color: Colors.white),
              ),

              SizedBox(height: 16),

              // App Name
              Text(
                'AFK Zone',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),

              SizedBox(height: 8),

              Text(
                'Remote Desktop',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 18,
                  color: Colors.white70,
                ),
              ),

              SizedBox(height: 40),

              // License Key Input Card
              Card(
                elevation: 4,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Kích hoạt License',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      SizedBox(height: 16),

                      TextField(
                        controller: _licenseKeyController,
                        decoration: InputDecoration(
                          labelText: 'License Key',
                          hintText: 'AFK-XXXXXXXXXXXXXXXX',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.vpn_key),
                        ),
                        textCapitalization: TextCapitalization.characters,
                        enabled: !_isLoading,
                      ),

                      SizedBox(height: 16),

                      ElevatedButton(
                        onPressed: _isLoading ? null : _activateLicenseKey,
                        style: ElevatedButton.styleFrom(
                          padding: EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        child: _isLoading
                            ? SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : Text(
                                'KÍCH HOẠT',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                              ),
                      ),

                      SizedBox(height: 12),

                      OutlinedButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => PaymentScreen(),
                            ),
                          );
                        },
                        style: OutlinedButton.styleFrom(
                          padding: EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          side: BorderSide(color: Colors.blue, width: 2),
                        ),
                        child: Text(
                          'MUA LICENSE',
                          style: TextStyle(
                            fontSize: 16, 
                            fontWeight: FontWeight.bold,
                            color: Colors.blue,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              SizedBox(height: 24),

              // Trial Button
              if (!_hasTrialed && !_trialLoading)
                Card(
                  color: Color(0xFF4CAF50),
                  elevation: 4,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: InkWell(
                    onTap: _isLoading ? null : _activateTrial,
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: EdgeInsets.all(20),
                      child: Column(
                        children: [
                          Icon(Icons.star, size: 48, color: Colors.white),
                          SizedBox(height: 8),
                          Text(
                            'DÙNG THỬ 7 NGÀY MIỄN PHÍ',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          SizedBox(height: 4),
                          Text(
                            _getTrialDisplayText(),
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.white70,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

              if (_hasTrialed)
                Card(
                  color: Colors.grey[300],
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Padding(
                    padding: EdgeInsets.all(20),
                    child: Row(
                      children: [
                        Icon(Icons.info_outline, color: Colors.grey[600]),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Bạn đã sử dụng dùng thử',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[700],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

              SizedBox(height: 24),

              // Contact Card
              Card(
                color: Color(0xFFFF6B6B),
                elevation: 4,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: InkWell(
                  onTap: _openZalo,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: EdgeInsets.all(20),
                    child: Column(
                      children: [
                        Icon(Icons.shopping_cart, size: 48, color: Colors.white),
                        SizedBox(height: 12),
                        Text(
                          'Mua License',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Zalo: 0823333374',
                          style: TextStyle(
                            fontSize: 18,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Nhấn để copy số Zalo',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.white70,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              SizedBox(height: 16),

              // Pricing Info - Load from API
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Bảng giá',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 12),
                      if (_productsLoading)
                        Center(child: CircularProgressIndicator())
                      else if (_products.isEmpty)
                        Text('Không có thông tin giá', style: TextStyle(color: Colors.grey))
                      else
                        ..._buildPricingRowsFromAPI(),
                    ],
                  ),
                ),
              ),

              if (_errorMessage != null)
                Padding(
                  padding: EdgeInsets.only(top: 16),
                  child: Card(
                    color: Colors.red[100],
                    child: Padding(
                      padding: EdgeInsets.all(12),
                      child: Row(
                        children: [
                          Icon(Icons.error_outline, color: Colors.red[900]),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _errorMessage!,
                              style: TextStyle(color: Colors.red[900]),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

              SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  String _getTrialDisplayText() {
    // Try to get trial product info from API
    if (_products.isNotEmpty) {
      final trialProduct = _products.firstWhere(
        (p) => p.price == 0 && p.durationDays == 7 && p.tier == 'basic',
        orElse: () => _products.firstWhere(
          (p) => p.tier == 'basic',
          orElse: () => _products.first,
        ),
      );
      final tierName = trialProduct.name.isNotEmpty ? trialProduct.name : 'Basic';
      return '$tierName - ${trialProduct.maxDevicesDisplay}';
    }
    return 'Basic - Tối đa 1 thiết bị'; // Fallback
  }

  List<Widget> _buildPricingRowsFromAPI() {
    // Group products by tier and show one product per tier (prefer 30 days)
    // IMPORTANT: Filter out 7-day paid products - only show 7-day free (price=0)
    final Map<String, Product> tierProducts = {};
    
    for (var product in _products) {
      // Skip 7-day paid products (only show free 7-day in trial section)
      if (product.durationDays == 7 && product.price > 0) {
        continue;
      }
      
      if (!tierProducts.containsKey(product.tier)) {
        tierProducts[product.tier] = product;
      } else {
        // Prefer 30 days, then any other duration
        final current = tierProducts[product.tier]!;
        if (current.durationDays != 30 && product.durationDays == 30) {
          tierProducts[product.tier] = product;
        }
      }
    }

    return tierProducts.values.map((product) {
      final tierName = product.name.isNotEmpty ? product.name : product.tierDisplayName;
      final tierLabel = '$tierName (${product.maxDevicesDisplay})';
      final priceLabel = '${product.durationDays} ngày: ${product.displayPrice}';
      return _buildPricingRow(tierLabel, priceLabel);
    }).toList();
  }

  Widget _buildPricingRow(String tier, String price) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(child: Text(tier, style: TextStyle(fontSize: 14))),
          Text(
            price,
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _licenseKeyController.dispose();
    super.dispose();
  }
}

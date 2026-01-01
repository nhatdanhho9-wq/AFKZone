import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_hbb/common/license_service.dart';
import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'payment_screen.dart';
import 'dart:io';

class LicensePage extends StatefulWidget {
  final Future<void> Function(Map<String, dynamic>) onLicenseActivated;

  const LicensePage({Key? key, required this.onLicenseActivated}) : super(key: key);

  @override
  _LicensePageState createState() => _LicensePageState();
}

class _LicensePageState extends State<LicensePage> with WidgetsBindingObserver {
  final TextEditingController _licenseKeyController = TextEditingController();
  final TextEditingController _transCodeController = TextEditingController();
  bool _isLoading = false;
  bool _isRecovering = false;
  String? _errorMessage;
  bool _hasTrialed = false;
  bool _trialLoading = true;
  List<Product> _products = [];
  bool _productsLoading = true;
  List<Map<String, dynamic>> _purchaseHistory = [];
  Map<String, dynamic>? _activeLicense; // Local active license
  List<Map<String, dynamic>> _paidHistory = [];
  List<Map<String, dynamic>> _trialHistory = [];
  bool _showTrials = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _checkTrial();
    _loadProducts();
    _loadActiveLicense(); // Load local active state
    _loadPurchaseHistory();
    _checkDirtyFlag();  // Check on init too
    _checkDirtyFlag();  // Check on init too
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _checkDirtyFlag();
    }
  }

  Future<void> _checkDirtyFlag() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool('license_history_dirty') == true) {
      await prefs.setBool('license_history_dirty', false);
      _loadPurchaseHistory();
      _loadActiveLicense(); // Also reload active license
    }
  }

  Future<void> _loadActiveLicense() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool('afk_license_active') == true) {
      setState(() {
        _activeLicense = {
          'license_key': prefs.getString('afk_license_key') ?? 'Unknown',
          'tier': prefs.getString('afk_license_tier') ?? 'basic',
          'expires_at': _formatDate(prefs.getInt('afk_license_expires_at')),
          'status': 'active',
          'is_local': true,
        };
      });
    } else {
      setState(() => _activeLicense = null);
    }
  }

  String _formatDate(int? millis) {
    if (millis == null) return '';
    return DateTime.fromMillisecondsSinceEpoch(millis).toIso8601String().split('T')[0];
  }

  Future<void> _loadPurchaseHistory() async {
    try {
      final deviceId = await _getDeviceId();
      // Fetch ALL history including trials and expired
      final history = await LicenseService.getPurchaseHistory(
        deviceId, 
        includeTrial: true, 
        includeExpired: true
      );
      
      if (mounted) {
        setState(() {
          _purchaseHistory = history;
          // Split into Paid vs Trial/Expired
          _paidHistory = history.where((l) => 
            l['tier'] != 'trial' && l['source'] != 'trial'
          ).toList();
          
          _trialHistory = history.where((l) => 
            l['tier'] == 'trial' || l['source'] == 'trial'
          ).toList();
        });
      }
    } catch (e) {
      print('Error loading purchase history: $e');
    }
  }

  Future<void> _recoverLicense() async {
    final transCode = _transCodeController.text.trim();
    if (transCode.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Vui lòng nhập mã giao dịch')),
      );
      return;
    }

    setState(() => _isRecovering = true);
    try {
      final result = await LicenseService.recoverLicense(transCode);
      if (result != null && result['license_key'] != null) {
        // Copy license key to clipboard
        await Clipboard.setData(ClipboardData(text: result['license_key']));
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ Đã tìm thấy license! Key đã được copy.'),
              backgroundColor: Colors.green,
              duration: Duration(seconds: 3),
            ),
          );
          // Auto-fill license key
          _licenseKeyController.text = result['license_key'];
          _loadPurchaseHistory(); // Refresh history
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ ${e.toString().replaceAll('Exception: ', '')}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isRecovering = false);
      }
    }
  }

  Widget _buildLicenseHistoryItem(Map<String, dynamic> license, {bool isHighlight = false}) {
    final licenseKey = license['license_key'] ?? '';
    final tier = license['tier'] ?? 'unknown';
    final expiresAt = license['expires_at'] ?? '';
    final status = license['status'] ?? 'unknown';
    
    // ... rest of method
    
    Color statusColor = Colors.grey;
    String statusText = status;
    if (status == 'active') {
      statusColor = Colors.green;
      statusText = 'Hoạt động';
    } else if (status == 'expired') {
      statusColor = Colors.red;
      statusText = 'Hết hạn';
    }

    return Container(
      margin: EdgeInsets.only(bottom: 8),
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isHighlight ? Colors.green.shade50 : Colors.grey[100],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isHighlight ? Colors.green.shade200 : Colors.grey[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: _getTierColor(tier),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  tier.toUpperCase(),
                  style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ),
              SizedBox(width: 8),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  statusText,
                  style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ),
              Spacer(),
              IconButton(
                icon: Icon(Icons.copy, size: 18),
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: licenseKey));
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Đã copy license key')),
                  );
                },
                padding: EdgeInsets.zero,
                constraints: BoxConstraints(),
              ),
            ],
          ),
          SizedBox(height: 6),
          Text(
            licenseKey,
            style: TextStyle(fontSize: 12, fontFamily: 'monospace', color: Colors.grey[700]),
          ),
          if (expiresAt.isNotEmpty)
            Padding(
              padding: EdgeInsets.only(top: 4),
              child: Text(
                'Hết hạn: $expiresAt',
                style: TextStyle(fontSize: 11, color: Colors.grey[600]),
              ),
            ),
          SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () {
                _licenseKeyController.text = licenseKey;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Đã điền license key, bấm KÍCH HOẠT để sử dụng')),
                );
              },
              icon: Icon(Icons.login, size: 16),
              label: Text('Kích hoạt trên thiết bị này'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(vertical: 8),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getTierColor(String tier) {
    switch (tier.toLowerCase()) {
      case 'pro':
        return Colors.purple;
      case 'enterprise':
        return Colors.orange;
      case 'basic':
      default:
        return Colors.blue;
    }
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
        print('✅ Step 2 - Checking status: ${activationResult?['status']}, keys: ${activationResult?.keys}');

        if (activationResult != null) {
          final status = activationResult['status'];
          print('✅ Step 2 - Status check: status=$status, isActivated=${status == 'activated'}, isActive=${status == 'active'}');
          
          if (status == 'activated' || status == 'active') {
            // Add license_key to result so callback can save it
            activationResult['license_key'] = licenseKey;
            print('✅ Step 3: Calling onLicenseActivated callback with: ${activationResult.keys}');
            try {
              await widget.onLicenseActivated(activationResult);
              print('✅ Step 3: Callback completed successfully');
              // Only set loading to false after successful callback
              if (mounted) {
                setState(() => _isLoading = false);
              }
            } catch (e, stackTrace) {
              print('❌ Step 3: Callback error: $e');
              print('Stack trace: $stackTrace');
              if (mounted) {
                setState(() {
                  _isLoading = false;
                  _errorMessage = 'Lỗi khi lưu license: ${e.toString()}';
                });
              }
            }
          } else {
            print('❌ Step 2 failed: Unexpected status=$status (expected "activated" or "active")');
            if (mounted) {
              setState(() {
                _isLoading = false;
                _errorMessage = 'Kích hoạt dùng thử thất bại. Status: $status';
              });
            }
          }
        } else {
          print('❌ Step 2 failed: activationResult is null');
          if (mounted) {
            setState(() {
              _isLoading = false;
              _errorMessage = 'Kích hoạt dùng thử thất bại. Không nhận được response từ server.';
            });
          }
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

              SizedBox(height: 16),

              // Purchase History & License Recovery Card
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.history, color: Colors.blue),
                          SizedBox(width: 8),
                          Text(
                            'Lịch sử & Khôi phục License',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 12),
                      Text(
                        'Nếu bạn đã mua license trước đó, nhập mã giao dịch để khôi phục:',
                        style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                      ),
                      SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _transCodeController,
                              decoration: InputDecoration(
                                labelText: 'Mã giao dịch',
                                hintText: 'AFKPRO90251230003',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.receipt_long),
                                isDense: true,
                              ),
                              style: TextStyle(fontSize: 14),
                            ),
                          ),
                          SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: _isRecovering ? null : _recoverLicense,
                            style: ElevatedButton.styleFrom(
                              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                              backgroundColor: Colors.orange,
                            ),
                            child: _isRecovering
                                ? SizedBox(
                                    height: 18,
                                    width: 18,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                  )
                                : Text('Khôi phục', style: TextStyle(color: Colors.white)),
                          ),
                        ],
                      ),
                      // 1. Active License (Local)
                      if (_activeLicense != null) ...[
                        SizedBox(height: 16),
                        Divider(thickness: 1),
                        SizedBox(height: 8),
                         Row(
                          children: [
                            Icon(Icons.check_circle, color: Colors.green, size: 16),
                            SizedBox(width: 8),
                            Text(
                              'License đang kích hoạt:',
                              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green[800]),
                            ),
                          ],
                        ),
                        SizedBox(height: 8),
                        _buildLicenseHistoryItem(_activeLicense!, isHighlight: true),
                      ],

                      // 2. Paid History (Server)
                      if (_paidHistory.isNotEmpty) ...[
                        SizedBox(height: 16),
                        Divider(),
                        SizedBox(height: 8),
                        Text(
                          'Lịch sử mua hàng:',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        SizedBox(height: 8),
                        ..._paidHistory.map((license) => _buildLicenseHistoryItem(license)).toList(),
                      ],

                      // 3. Trials (Collapsed)
                      if (_purchaseHistory.isNotEmpty || _trialHistory.isNotEmpty) ...[
                         SizedBox(height: 8),
                         TextButton.icon(
                           onPressed: () => setState(() => _showTrials = !_showTrials),
                           icon: Icon(_showTrials ? Icons.expand_less : Icons.expand_more, size: 16),
                           label: Text(_showTrials ? 'Ẩn lịch sử dùng thử' : 'Xem lịch sử dùng thử (${_trialHistory.length})'),
                           style: TextButton.styleFrom(
                             foregroundColor: Colors.grey,
                             padding: EdgeInsets.zero,
                             tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                           ),
                         ),
                         if (_showTrials)
                           ..._trialHistory.map((license) => _buildLicenseHistoryItem(license)).toList(),
                      ],
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
    // Show all products grouped by tier (sorted by duration)
    // Format: "Tier Name (X thiết bị)" - "Y ngày: Z đồng"
    
    final List<Widget> rows = [];
    String currentTier = '';
    
    // Sort products by tier, then by duration
    final sortedProducts = List<Product>.from(_products)
      ..sort((a, b) {
        final tierCompare = a.tier.compareTo(b.tier);
        if (tierCompare != 0) return tierCompare;
        return a.durationDays.compareTo(b.durationDays);
      });
    
    for (var product in sortedProducts) {
      // Skip 7-day free trial products (already shown in trial section)
      if (product.durationDays == 7 && product.price == 0) {
        continue;
      }
      
      // Build tier label: "Product Name (X thiết bị)"
      final tierLabel = '${product.name.isNotEmpty ? product.name : product.tierDisplayName} (${product.maxDevicesDisplay})';
      
      // Build price label: "Y ngày: Z đồng"
      final priceLabel = '${product.durationDays} ngày: ${product.displayPrice}';
      
      rows.add(_buildPricingRow(tierLabel, priceLabel));
    }
    
    return rows;
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

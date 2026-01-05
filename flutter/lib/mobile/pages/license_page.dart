import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_hbb/common/license_service.dart';
import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'payment_screen.dart';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';

class LicensePage extends StatefulWidget {
  final Future<void> Function(Map<String, dynamic>)? onLicenseActivated;

  const LicensePage({Key? key, this.onLicenseActivated}) : super(key: key);

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
  bool _showPurchaseHistory = true; // Default expanded
  bool _showActivationHistory = true; // Default expanded
  List<Map<String, dynamic>> _notifications = [];
  bool _notificationsLoading = true;
  List<Map<String, dynamic>> _activationHistory = []; // Activation history for this device
  bool _activationHistoryLoading = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _checkTrial();
    _loadProducts();
    _loadActiveLicense(); // Load local active state
    _loadPurchaseHistory();
    _loadActivationHistory(); // Load activation history for this device
    _loadNotifications();
    _checkDirtyFlag();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _licenseKeyController.dispose();
    _transCodeController.dispose();
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
      // Fallback chain: afk_license_key -> license_key -> latest paid history
      String? licenseKey = prefs.getString('afk_license_key');
      if (licenseKey == null || licenseKey.isEmpty) {
        licenseKey = prefs.getString('license_key');
      }
      if (licenseKey == null || licenseKey.isEmpty) {
        // Fallback to latest paid history (if available)
        if (_purchaseHistory.isNotEmpty) {
          final latestPaid = _purchaseHistory.firstWhere(
            (h) => h['status'] == 'paid' || h['status'] == 'completed',
            orElse: () => {},
          );
          licenseKey = latestPaid['license_key'];
        }
      }

      setState(() {
        _activeLicense = {
          'license_key': licenseKey ?? 'Unknown',
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
    final devicesUsed = license['devices_used'] ?? 0;
    final devicesMax = license['devices_max'] ?? license['max_devices'] ?? 1;
    
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
              SizedBox(width: 8),
              // Devices used/max badge
              Container(
                padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.devices, size: 12, color: Colors.blue),
                    SizedBox(width: 4),
                    Text(
                      '$devicesUsed/$devicesMax',
                      style: TextStyle(color: Colors.blue, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ],
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
          SizedBox(height: 12),
          // PROMINENT CTA: "Kích hoạt máy này" - ALWAYS ENABLED
          Container(
            width: double.infinity,
            height: 48,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF4CAF50), Color(0xFF2E7D32)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Color(0xFF4CAF50).withOpacity(0.4),
                  blurRadius: 8,
                  offset: Offset(0, 4),
                ),
              ],
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: () async {
                  // Call real activate API (A3 fix)
                  try {
                    final deviceId = await LicenseService.getDeviceFingerprint();
                    final result = await LicenseService.activateLicense(licenseKey, deviceId);
                    if (result != null) {
                      final prefs = await SharedPreferences.getInstance();
                      await prefs.setString('afk_license_key', licenseKey);
                      await prefs.setBool('afk_license_active', true);
                      await prefs.setString('device_id', deviceId);
                      if (result['tier'] != null) {
                        await prefs.setString('afk_license_tier', result['tier']);
                      }
                      if (result['max_devices'] != null) {
                        await prefs.setInt('afk_max_devices', result['max_devices']);
                      }
                      await prefs.setBool('license_history_dirty', true);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('✅ Kích hoạt thành công!'), backgroundColor: Colors.green),
                      );
                      // Reload history
                      _loadPurchaseHistory();
                      _loadActivationHistory();
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('❌ Kích hoạt thất bại'), backgroundColor: Colors.red),
                      );
                    }
                  } catch (e) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('❌ Lỗi: $e'), backgroundColor: Colors.red),
                    );
                  }
                },
                borderRadius: BorderRadius.circular(12),
                child: Center(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.rocket_launch,
                        color: Colors.white,
                        size: 22,
                      ),
                      SizedBox(width: 10),
                      Text(
                        'KÍCH HOẠT MÁY NÀY',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // G16: Support color_hex from API, fallback to hardcoded defaults
  Color _getTierColor(String tier, {String? colorHex}) {
    // If color_hex provided from API, use it
    if (colorHex != null && colorHex.isNotEmpty) {
      try {
        final hex = colorHex.replaceFirst('#', '');
        return Color(int.parse('FF$hex', radix: 16));
      } catch (e) {
        // Fall through to default colors
      }
    }
    // Fallback to hardcoded colors
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

  Widget _buildActivationHistoryItem(Map<String, dynamic> activation) {
    final activatedAt = activation['activated_at'] ?? activation['created_at'] ?? '';
    final licenseKey = activation['license_key'] ?? '';
    final tier = activation['tier'] ?? 'unknown';
    final status = activation['status'] ?? 'unknown';
    
    return Container(
      margin: EdgeInsets.only(bottom: 8),
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.purple.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.purple.shade200),
      ),
      child: Row(
        children: [
          Icon(Icons.check_circle, color: Colors.purple, size: 20),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tier.toString().toUpperCase(),
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.purple.shade800),
                ),
                if (activatedAt.isNotEmpty)
                  Text('Kích hoạt: $activatedAt', style: TextStyle(fontSize: 11, color: Colors.grey[600])),
                if (licenseKey.isNotEmpty)
                  Text('Key: ${licenseKey.length > 16 ? licenseKey.substring(0, 16) + '...' : licenseKey}',
                       style: TextStyle(fontSize: 10, fontFamily: 'monospace', color: Colors.grey[500])),
              ],
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: status == 'active' ? Colors.green.shade100 : Colors.grey.shade100,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              status == 'active' ? 'Đang hoạt động' : status.toString(),
              style: TextStyle(fontSize: 11, color: status == 'active' ? Colors.green.shade800 : Colors.grey.shade700),
            ),
          ),
        ],
      ),
    );
  }

  void _showAllActivationHistory() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.9,
        minChildSize: 0.5,
        builder: (context, scrollController) => Container(
          padding: EdgeInsets.all(16),
          child: ListView(
            controller: scrollController,
            children: [
              Text('Lịch sử kích hoạt (${_activationHistory.length})', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              SizedBox(height: 16),
              ..._activationHistory.map((h) => _buildActivationHistoryItem(h)).toList(),
            ],
          ),
        ),
      ),
    );
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

  Future<void> _loadNotifications() async {
    setState(() => _notificationsLoading = true);
    try {
      final response = await http.get(
        Uri.parse('https://api.afkzone.cloud/public/notifications'),
        headers: {'Cache-Control': 'no-cache'},
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> notifsJson = data['notifications'] ?? [];
        setState(() {
          _notifications = notifsJson.map((n) => {
            'id': n['id'],
            'title': n['title'] ?? '',
            'message': n['message'] ?? '',
            'type': n['type'] ?? 'info',
            'link_url': n['link_url'],
            'created_at': n['created_at'],
          }).toList();
          _notificationsLoading = false;
        });
      } else {
        setState(() => _notificationsLoading = false);
      }
    } catch (e) {
      print('Error loading notifications: $e');
      setState(() => _notificationsLoading = false);
    }
  }

  Future<void> _loadActivationHistory() async {
    setState(() => _activationHistoryLoading = true);
    try {
      final deviceId = await LicenseService.getDeviceFingerprint();
      final response = await http.get(
        Uri.parse('https://api.afkzone.cloud/api/devices/activation-history?device_id=$deviceId'),
        headers: {'Cache-Control': 'no-cache'},
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> historyJson = data['activations'] ?? data['history'] ?? [];
        setState(() {
          _activationHistory = historyJson.map<Map<String, dynamic>>((h) => Map<String, dynamic>.from(h)).toList();
          _activationHistoryLoading = false;
        });
      } else {
        setState(() => _activationHistoryLoading = false);
      }
    } catch (e) {
      print('Error loading activation history: $e');
      setState(() => _activationHistoryLoading = false);
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
              final handler = widget.onLicenseActivated;
              if (handler != null) {
                await handler(activationResult);
              }
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
        if (widget.onLicenseActivated != null) {
          widget.onLicenseActivated!(result);
        }
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
                      // NOTE: Removed 'License đang kích hoạt' section per Codex v2.2.59 requirement
                      // All licenses now shown in Purchase History with CTA button

                      // 2. Paid History (Collapsible - show 3 by default)
                      if (_paidHistory.isNotEmpty) ...[
                        SizedBox(height: 16),
                        Divider(),
                        SizedBox(height: 8),
                        InkWell(
                          onTap: () => setState(() => _showPurchaseHistory = !_showPurchaseHistory),
                          child: Row(
                            children: [
                              Icon(Icons.shopping_cart, color: Colors.blue, size: 18),
                              SizedBox(width: 8),
                              Text(
                                'Lịch sử mua hàng (${_paidHistory.length})',
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                              ),
                              Spacer(),
                              Icon(_showPurchaseHistory ? Icons.expand_less : Icons.expand_more, color: Colors.grey),
                            ],
                          ),
                        ),
                        if (_showPurchaseHistory) ...[
                          SizedBox(height: 8),
                          ...(_paidHistory.take(3).map((license) => _buildLicenseHistoryItem(license)).toList()),
                          if (_paidHistory.length > 3)
                            TextButton(
                              onPressed: () {
                                showModalBottomSheet(
                                  context: context,
                                  isScrollControlled: true,
                                  builder: (context) => DraggableScrollableSheet(
                                    initialChildSize: 0.7,
                                    maxChildSize: 0.9,
                                    minChildSize: 0.5,
                                    builder: (context, scrollController) => Container(
                                      padding: EdgeInsets.all(16),
                                      child: ListView(
                                        controller: scrollController,
                                        children: [
                                          Text('Tất cả đơn hàng (${_paidHistory.length})', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                                          SizedBox(height: 16),
                                          ..._paidHistory.map((l) => _buildLicenseHistoryItem(l)).toList(),
                                        ],
                                      ),
                                    ),
                                  ),
                                );
                              },
                              child: Text('Xem thêm ${_paidHistory.length - 3} đơn hàng...'),
                            ),
                        ],
                      ],

                      // 3. Activation History for this device (Collapsible)
                      SizedBox(height: 16),
                      Divider(),
                      SizedBox(height: 8),
                      InkWell(
                        onTap: () => setState(() => _showActivationHistory = !_showActivationHistory),
                        child: Row(
                          children: [
                            Icon(Icons.history, color: Colors.purple, size: 18),
                            SizedBox(width: 8),
                            Text(
                              'Lịch sử kích hoạt (${_activationHistory.length})',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                            ),
                            Spacer(),
                            Icon(_showActivationHistory ? Icons.expand_less : Icons.expand_more, color: Colors.grey),
                          ],
                        ),
                      ),
                      if (_showActivationHistory) ...[
                        SizedBox(height: 8),
                        if (_activationHistoryLoading)
                          Center(child: CircularProgressIndicator())
                        else if (_activationHistory.isEmpty)
                          Container(
                            padding: EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Colors.grey[100],
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Column(
                              children: [
                                Icon(Icons.history_toggle_off, size: 40, color: Colors.grey[400]),
                                SizedBox(height: 8),
                                Text('Chưa có lịch sử kích hoạt', style: TextStyle(color: Colors.grey[600])),
                                Text('Kích hoạt license để bắt đầu', style: TextStyle(fontSize: 12, color: Colors.grey[500])),
                              ],
                            ),
                          )
                        else ...[
                          ...(_activationHistory.take(3).map((h) => _buildActivationHistoryItem(h)).toList()),
                          if (_activationHistory.length > 3)
                            TextButton(
                              onPressed: () => _showAllActivationHistory(),
                              child: Text('Xem thêm ${_activationHistory.length - 3} lần kích hoạt...'),
                            ),
                        ],
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

              // Notifications - Load from /public/notifications
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
                      Row(
                        children: [
                          Icon(Icons.info_outline, color: Colors.blue, size: 20),
                          SizedBox(width: 8),
                          Text(
                            'Thông tin & Thông báo',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 12),
                      if (_notificationsLoading)
                        Center(child: CircularProgressIndicator())
                      else if (_notifications.isEmpty)
                        Text('Không có thông báo mới', style: TextStyle(color: Colors.grey[600]))
                      else
                        ..._buildNotificationsList(),
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

  List<Widget> _buildNotificationsList() {
    return _notifications.map((n) {
      Color typeColor = _getNotificationColor(n['type']);
      IconData typeIcon = _getNotificationIcon(n['type']);

      return Container(
        margin: EdgeInsets.only(bottom: 12),
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: typeColor.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: typeColor.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(typeIcon, color: typeColor, size: 18),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    n['title'],
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: typeColor,
                    ),
                  ),
                ),
              ],
            ),
            if (n['message'].toString().isNotEmpty) ...[
              SizedBox(height: 6),
              Text(
                n['message'],
                style: TextStyle(fontSize: 13, color: Colors.grey[800]),
              ),
            ],
            if (n['link_url'] != null && n['link_url'].toString().isNotEmpty) ...[
              SizedBox(height: 8),
              InkWell(
                onTap: () {
                  // Copy link to clipboard
                  Clipboard.setData(ClipboardData(text: n['link_url']));
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Đã copy link')),
                  );
                },
                child: Text(
                  'Link: ${n['link_url']}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.blue,
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ],
          ],
        ),
      );
    }).toList();
  }

  Color _getNotificationColor(String type) {
    switch (type.toLowerCase()) {
      case 'warning':
        return Colors.orange;
      case 'success':
        return Colors.green;
      case 'error':
        return Colors.red;
      case 'info':
      default:
        return Colors.blue;
    }
  }

  IconData _getNotificationIcon(String type) {
    switch (type.toLowerCase()) {
      case 'warning':
        return Icons.warning_amber;
      case 'success':
        return Icons.check_circle;
      case 'error':
        return Icons.error;
      case 'info':
      default:
        return Icons.info;
    }
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
}

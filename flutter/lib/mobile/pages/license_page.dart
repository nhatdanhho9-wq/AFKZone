import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'license_service.dart';
import 'payment_screen.dart';
import 'dart:io';

class LicensePage extends StatefulWidget {
  final Function(Map<String, dynamic>) onLicenseActivated;

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

  @override
  void initState() {
    super.initState();
    _checkTrial();
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
      final result = await LicenseService.generateTrial();
      if (result != null) {
        // Auto-activate with returned license key
        final deviceId = await _getDeviceId();
        final activationResult = await LicenseService.activateLicense(
          result['license_key'],
          deviceId,
        );

        if (activationResult != null) {
          widget.onLicenseActivated(activationResult);
        }
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  Future<void> _activateLicenseKey() async {
    if (_licenseKeyController.text.isEmpty) {
      setState(() => _errorMessage = 'Vui lòng nhập license key');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final deviceId = await _getDeviceId();
      final result = await LicenseService.activateLicense(
        _licenseKeyController.text.trim(),
        deviceId,
      );

      if (result != null) {
        widget.onLicenseActivated(result);
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '');
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
                            'Basic - Tối đa 1 thiết bị',
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

              // Pricing Info
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
                      _buildPricingRow('Basic (2 thiết bị)', '30 ngày: 50.000đ'),
                      _buildPricingRow('Pro (5 thiết bị)', '30 ngày: 100.000đ'),
                      _buildPricingRow('Enterprise (∞)', '30 ngày: 200.000đ'),
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

  Widget _buildPricingRow(String tier, String price) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(tier),
          Text(
            price,
            style: TextStyle(fontWeight: FontWeight.bold),
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

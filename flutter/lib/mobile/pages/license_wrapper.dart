import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_hbb/common/license_service.dart';
import 'license_page.dart' as afk;
import 'dart:async';

class LicenseWrapper extends StatefulWidget {
  final Widget child;

  const LicenseWrapper({Key? key, required this.child}) : super(key: key);

  @override
  LicenseWrapperState createState() => LicenseWrapperState();
}

class LicenseWrapperState extends State<LicenseWrapper> {
  bool _isChecking = true;
  bool _hasValidLicense = false;
  String? _licenseKey;
  String? _deviceId;
  Map<String, dynamic>? _serverConfigs;
  Timer? _backgroundCheckTimer;

  @override
  void initState() {
    super.initState();
    _checkLicense();
    _startBackgroundCheck();
  }

  @override
  void dispose() {
    _backgroundCheckTimer?.cancel();
    super.dispose();
  }

  Future<void> _checkLicense() async {
    setState(() => _isChecking = true);

    try {
      final prefs = await SharedPreferences.getInstance();
      _licenseKey = prefs.getString('license_key');
      _deviceId = prefs.getString('device_id');

      if (_licenseKey == null || _deviceId == null) {
        setState(() {
          _hasValidLicense = false;
          _isChecking = false;
        });
        return;
      }

      // Validate license with backend
      final result = await LicenseService.checkLicense(_licenseKey!, _deviceId!);

      if (result != null && result['status'] == 'active') {
        setState(() {
          _hasValidLicense = true;
          _serverConfigs = result;
          _isChecking = false;
        });

        // Update server configs if needed
        await _updateServerConfigs(result);
      } else {
        // License invalid or expired
        setState(() {
          _hasValidLicense = false;
          _isChecking = false;
        });
        await prefs.remove('license_key');
        await prefs.remove('device_id');
      }
    } catch (e) {
      print('License check error: $e');
      setState(() {
        _hasValidLicense = false;
        _isChecking = false;
      });
    }
  }

  void _startBackgroundCheck() {
    // Check license every 24 hours
    _backgroundCheckTimer = Timer.periodic(Duration(hours: 24), (timer) {
      _checkLicense();
    });
  }

  Future<void> _updateServerConfigs(Map<String, dynamic> config) async {
    final prefs = await SharedPreferences.getInstance();

    // Store server configs
    await prefs.setString('id_server', config['id_server'] ?? '');
    await prefs.setString('relay_server', config['relay_server'] ?? '');
    await prefs.setString('public_key', config['public_key'] ?? '');
    await prefs.setString('api_server', config['api_server'] ?? '');
  }

  Future<void> onLicenseActivated(Map<String, dynamic> result) async {
    print('🔄 onLicenseActivated called with keys: ${result.keys}');
    final prefs = await SharedPreferences.getInstance();

    // Extract license_key from result (added by license_page.dart)
    String? licenseKey = result['license_key'];
    print('🔄 onLicenseActivated - licenseKey from result: $licenseKey');
    
    if (licenseKey == null && result['message'] != null) {
      // From trial response
      licenseKey = result['message'].toString().split('License key: ').last;
      print('🔄 onLicenseActivated - licenseKey from message: $licenseKey');
    }

    if (licenseKey != null) {
      final deviceId = await LicenseService.getDeviceFingerprint();
      print('🔄 onLicenseActivated - Saving license: $licenseKey, deviceId: $deviceId');
      
      await prefs.setString('license_key', licenseKey);
      await prefs.setString('device_id', deviceId);
      await prefs.setBool('afk_license_active', true);
      
      // Save expiration if available
      if (result['expires_at'] != null) {
        try {
          // expires_at might be ISO string or timestamp
          int expiresAt;
          if (result['expires_at'] is String) {
            final dateTime = DateTime.parse(result['expires_at']);
            expiresAt = dateTime.millisecondsSinceEpoch;
          } else {
            expiresAt = result['expires_at'] as int;
          }
          await prefs.setInt('afk_license_expires_at', expiresAt);
          print('🔄 onLicenseActivated - Saved expires_at: $expiresAt');
        } catch (e) {
          print('❌ Error parsing expires_at: $e');
        }
      }

      print('🔄 onLicenseActivated - Updating state...');
      setState(() {
        _licenseKey = licenseKey;
        _deviceId = deviceId;
        _hasValidLicense = true;
        _serverConfigs = result;
      });

      print('🔄 onLicenseActivated - Updating server configs...');
      await _updateServerConfigs(result);
      print('✅ onLicenseActivated - Completed successfully');
    } else {
      print('❌ Warning: license_key not found in activation result. Keys: ${result.keys}');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isChecking) {
      return Scaffold(
        backgroundColor: Color(0xFF0D47A1),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Image.asset(
                'assets/logo.png',
                height: 120,
                errorBuilder: (context, error, stackTrace) =>
                  Icon(Icons.desktop_windows, size: 120, color: Colors.white),
              ),
              SizedBox(height: 24),
              CircularProgressIndicator(color: Colors.white),
              SizedBox(height: 16),
              Text(
                'Đang kiểm tra license...',
                style: TextStyle(color: Colors.white, fontSize: 16),
              ),
            ],
          ),
        ),
      );
    }

    if (!_hasValidLicense) {
      return afk.LicensePage(onLicenseActivated: onLicenseActivated);
    }

    return widget.child;
  }
}

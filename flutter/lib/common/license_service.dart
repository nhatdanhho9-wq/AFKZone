import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:device_info_plus/device_info_plus.dart';
import 'package:crypto/crypto.dart';
import 'dart:io';

class LicenseService {
  static const String API_URL = 'https://api.afkzone.cloud';

  // Get device fingerprint for trial abuse prevention
  static Future<String> getDeviceFingerprint() async {
    final deviceInfo = DeviceInfoPlugin();
    String fingerprint = '';

    try {
      if (Platform.isAndroid) {
        final androidInfo = await deviceInfo.androidInfo;
        final data = '${androidInfo.id}_${androidInfo.model}_${androidInfo.device}';
        fingerprint = sha256.convert(utf8.encode(data)).toString();
      } else if (Platform.isIOS) {
        final iosInfo = await deviceInfo.iosInfo;
        final data = '${iosInfo.identifierForVendor}_${iosInfo.model}';
        fingerprint = sha256.convert(utf8.encode(data)).toString();
      }
    } catch (e) {
      print('Error getting device fingerprint: $e');
      fingerprint = 'unknown_device';
    }

    return fingerprint;
  }

  // Check if device has already used trial
  static Future<Map<String, dynamic>> checkTrial() async {
    try {
      final fingerprint = await getDeviceFingerprint();
      final response = await http.post(
        Uri.parse('$API_URL/trial/check'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'device_fingerprint': fingerprint}),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return {'has_trialed': false};
    } catch (e) {
      print('Error checking trial: $e');
      return {'has_trialed': false};
    }
  }

  // Generate trial license
  static Future<Map<String, dynamic>?> generateTrial() async {
    try {
      final fingerprint = await getDeviceFingerprint();
      print('🔄 generateTrial: deviceFingerprint=$fingerprint');
      final response = await http.post(
        Uri.parse('$API_URL/trial/generate'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'device_fingerprint': fingerprint}),
      ).timeout(Duration(seconds: 10));

      print('🔄 generateTrial: statusCode=${response.statusCode}, body=${response.body}');

      if (response.statusCode == 200) {
        final result = json.decode(response.body);
        print('✅ Generate trial API response: $result');
        print('✅ Generate trial - license_key: ${result['license_key']}');
        return result;
      } else {
        final error = json.decode(response.body);
        print('❌ Generate trial API error: status=${response.statusCode}, detail=${error['detail']}');
        throw Exception(error['detail'] ?? 'Failed to generate trial');
      }
    } catch (e) {
      print('❌ Error generating trial: $e');
      rethrow;
    }
  }

  // Activate license key
  static Future<Map<String, dynamic>?> activateLicense(String licenseKey, String deviceId) async {
    try {
      print('🔄 activateLicense: licenseKey=$licenseKey, deviceId=$deviceId');
      final response = await http.post(
        Uri.parse('$API_URL/activate'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'license_key': licenseKey,
          'device_id': deviceId,
        }),
      ).timeout(Duration(seconds: 10));

      print('🔄 activateLicense: statusCode=${response.statusCode}, body=${response.body}');

      if (response.statusCode == 200) {
        final result = json.decode(response.body);
        print('✅ Activate API response: $result');
        print('✅ Activate API - status: ${result['status']}, tier: ${result['tier']}, expires_at: ${result['expires_at']}');
        return result;
      } else {
        final error = json.decode(response.body);
        print('❌ Activate API error: status=${response.statusCode}, detail=${error['detail']}');
        throw Exception(error['detail'] ?? 'Activation failed');
      }
    } catch (e) {
      print('❌ Error activating license: $e');
      rethrow;
    }
  }

  // Check license validity
  static Future<Map<String, dynamic>?> checkLicense(String licenseKey, String deviceId) async {
    try {
      final response = await http.post(
        Uri.parse('$API_URL/check'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'license_key': licenseKey,
          'device_id': deviceId,
        }),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        return null;
      }
    } catch (e) {
      print('Error checking license: $e');
      return null;
    }
  }

  // Check for app updates
  static Future<Map<String, dynamic>?> checkVersion(String currentVersion) async {
    try {
      final response = await http.get(
        Uri.parse('$API_URL/version/check?current=$currentVersion'),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print('Error checking version: $e');
      return null;
    }
  }

  // Create ZaloPay payment order
  static Future<Map<String, dynamic>?> createPayment({
    required String tier,
    required int durationDays,
    required String deviceId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$API_URL/payment/create'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'tier': tier,
          'duration_days': durationDays,
          'device_id': deviceId,
        }),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Payment creation failed');
      }
    } catch (e) {
      print('Error creating payment: $e');
      rethrow;
    }
  }

  // Logout - remove device from license
  static Future<bool> logoutDevice(String licenseKey, String deviceId) async {
    try {
      print('🔄 logoutDevice: licenseKey=$licenseKey, deviceId=$deviceId');
      final response = await http.post(
        Uri.parse('$API_URL/license/logout'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'license_key': licenseKey,
          'device_id': deviceId,
        }),
      ).timeout(Duration(seconds: 10));

      print('🔄 logoutDevice: statusCode=${response.statusCode}, body=${response.body}');

      if (response.statusCode == 200) {
        print('✅ Device logged out successfully');
        return true;
      } else {
        print('❌ Logout failed: ${response.body}');
        return false;
      }
    } catch (e) {
      print('❌ Error logging out device: $e');
      return false;
    }
  }

  // Get license info including device count
  static Future<Map<String, dynamic>?> getLicenseInfo(String licenseKey) async {
    try {
      final response = await http.get(
        Uri.parse('$API_URL/license/info?license_key=$licenseKey'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        return null;
      }
    } catch (e) {
      print('Error getting license info: $e');
      return null;
    }
  }

  // Get purchase history for a device
  static Future<List<Map<String, dynamic>>> getPurchaseHistory(String deviceId) async {
    try {
      final fingerprint = await getDeviceFingerprint();
      final response = await http.get(
        Uri.parse('$API_URL/user/history?device_id=$deviceId&fingerprint=$fingerprint'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['licenses'] != null) {
          return List<Map<String, dynamic>>.from(data['licenses']);
        }
      }
      return [];
    } catch (e) {
      print('Error getting purchase history: $e');
      return [];
    }
  }

  // Recover license by transaction code
  static Future<Map<String, dynamic>?> recoverLicense(String transCode) async {
    try {
      final response = await http.post(
        Uri.parse('$API_URL/license/recover'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'trans_code': transCode}),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Recovery failed');
      }
    } catch (e) {
      print('Error recovering license: $e');
      rethrow;
    }
  }

  // Log connection to backend for tracking
  static Future<void> logConnection({
    required String deviceId,
    required String remoteId,
    required String action, // 'connect' or 'disconnect'
    String? licenseKey,
    String? ipAddress,
  }) async {
    try {
      print('🔄 logConnection: deviceId=$deviceId, remoteId=$remoteId, action=$action');
      final response = await http.post(
        Uri.parse('$API_URL/connection/log'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'device_id': deviceId,
          'remote_id': remoteId,
          'action': action,
          'license_key': licenseKey ?? '',
          'ip_address': ipAddress ?? '',
        }),
      ).timeout(Duration(seconds: 5));

      if (response.statusCode == 200) {
        print('✅ Connection logged successfully');
      } else {
        print('⚠️ Connection log failed: ${response.statusCode}');
      }
    } catch (e) {
      // Don't throw - connection logging is non-critical
      print('⚠️ Error logging connection (non-critical): $e');
    }
  }
}

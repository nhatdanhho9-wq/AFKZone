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
      final response = await http.post(
        Uri.parse('$API_URL/trial/generate'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'device_fingerprint': fingerprint}),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final result = json.decode(response.body);
        print('✅ Generate trial API response: $result');
        return result;
      } else {
        final error = json.decode(response.body);
        print('❌ Generate trial API error: ${error['detail']}');
        throw Exception(error['detail'] ?? 'Failed to generate trial');
      }
    } catch (e) {
      print('Error generating trial: $e');
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
}

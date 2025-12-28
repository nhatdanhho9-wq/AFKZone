import 'dart:convert';
import 'package:http/http.dart' as http;

class PaymentService {
  static const String API_URL = 'https://api.afkzone.cloud';

  /// Create bank transfer order
  /// Returns: {trans_code, amount, qr_url, bank_info, message, expires_in}
  static Future<Map<String, dynamic>> createBankOrder({
    required String tier,
    required int durationDays,
    required String deviceId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${API_URL}/payment/bank/create'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'tier': tier,
          'duration_days': durationDays,
          'device_id': deviceId,
        }),
      ).timeout(Duration(seconds: 15));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to create order');
      }
    } catch (e) {
      print('Error creating bank order: $e');
      rethrow;
    }
  }

  /// Check payment status by transaction code
  /// Returns: {trans_code, status, amount, tier, duration_days, license_key, ...}
  static Future<Map<String, dynamic>> checkPaymentStatus(String transCode) async {
    try {
      final response = await http.get(
        Uri.parse('${API_URL}/payment/bank/status?trans_code=$transCode'),
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else if (response.statusCode == 404) {
        throw Exception('Order not found');
      } else {
        throw Exception('Failed to check payment status');
      }
    } catch (e) {
      print('Error checking payment status: $e');
      rethrow;
    }
  }
}

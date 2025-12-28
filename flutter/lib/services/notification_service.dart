import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/notification_model.dart';
import '../../common/license_service.dart';

class NotificationService {
  static const String API_URL = 'https://api.afkzone.cloud';

  static Future<List<AppNotification>> fetchNotifications() async {
    try {
      final deviceId = await LicenseService.getDeviceFingerprint();
      final response = await http.get(
        Uri.parse('$API_URL/notifications?device_id=$deviceId')
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> notifs = data['notifications'] ?? [];
        return notifs.map((json) => AppNotification.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('Error fetching notifications: $e');
      return [];
    }
  }

  static Future<int> getUnreadCount() async {
    try {
      final notifications = await fetchNotifications();
      return notifications.where((n) => !n.isRead && !n.isExpired).length;
    } catch (e) {
      return 0;
    }
  }
}


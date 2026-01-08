import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'auth_service.dart';

/// Device Service for Remote Preview v0.1
/// Handles: register, list, heartbeat
class DeviceService {
  static String? _deviceId;
  static Timer? _heartbeatTimer;

  /// Register device with server
  static Future<DeviceResult> registerDevice({
    required String deviceName,
    String? platform,
  }) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/devices/register'),
        headers: headers,
        body: json.encode({
          'device_name': deviceName,
          'platform': platform ?? 'android',
        }),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        _deviceId = data['device_id'];
        print('[DeviceService] Registered: $_deviceId');
        return DeviceResult(success: true, deviceId: _deviceId);
      } else {
        return DeviceResult(success: false, error: data['detail'] ?? 'Registration failed');
      }
    } catch (e) {
      return DeviceResult(success: false, error: e.toString());
    }
  }

  /// Get list of devices
  static Future<List<Device>> getDevices() async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/devices'),
        headers: headers,
      ).timeout(Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final devices = (data['devices'] as List?)
            ?.map((d) => Device.fromJson(d))
            .toList() ?? [];
        return devices;
      }
      return [];
    } catch (e) {
      print('[DeviceService] getDevices error: $e');
      return [];
    }
  }

  /// Send heartbeat for device presence
  static Future<bool> heartbeat() async {
    if (_deviceId == null) return false;
    
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/devices/$_deviceId/heartbeat'),
        headers: headers,
      ).timeout(Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      print('[DeviceService] heartbeat error: $e');
      return false;
    }
  }

  /// Start heartbeat timer (every 30 seconds)
  static void startHeartbeat() {
    stopHeartbeat();
    _heartbeatTimer = Timer.periodic(Duration(seconds: 30), (_) {
      heartbeat();
    });
    // Send first heartbeat immediately
    heartbeat();
    print('[DeviceService] Heartbeat started');
  }

  /// Stop heartbeat timer
  static void stopHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
  }

  /// Get current device ID
  static String? get deviceId => _deviceId;
}

/// Device model
class Device {
  final String id;
  final String name;
  final String platform;
  final bool online;
  final String? lastSeen;

  Device({
    required this.id,
    required this.name,
    required this.platform,
    required this.online,
    this.lastSeen,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['device_id'] ?? json['id'] ?? '',
      name: json['device_name'] ?? json['name'] ?? '',
      platform: json['platform'] ?? 'unknown',
      online: json['online'] ?? false,
      lastSeen: json['last_seen'],
    );
  }
}

/// Device operation result
class DeviceResult {
  final bool success;
  final String? deviceId;
  final String? error;

  DeviceResult({required this.success, this.deviceId, this.error});
}

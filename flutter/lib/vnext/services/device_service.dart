import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';
import 'auth_service.dart';

/// Device Service for Remote Preview v0.1
/// Handles: register, list, heartbeat
class DeviceService {
  static const String _deviceIdKey = 'device_id';
  static String? _deviceId;
  static Timer? _heartbeatTimer;

  static Future<String> _getOrCreateDeviceId() async {
    if (_deviceId != null) return _deviceId!;
    final prefs = await SharedPreferences.getInstance();
    final existing = prefs.getString(_deviceIdKey);
    if (existing != null && existing.isNotEmpty) {
      _deviceId = existing;
      return existing;
    }
    // No device id yet (first login). Let server assign on /devices/register.
    return '';
  }

  /// Ensure we have a stable device_id (even before login).
  static Future<String> ensureDeviceId() async {
    final id = await _getOrCreateDeviceId();
    if (id.isNotEmpty) return id;
    // Not registered yet (guest / pre-login). Use a temporary id for request attribution.
    final rnd = Random.secure();
    final bytes = List<int>.generate(16, (_) => rnd.nextInt(256));
    return base64Url.encode(bytes).replaceAll('=', '');
  }

  /// Register device with server
  static Future<DeviceResult> registerDevice({
    required String deviceName,
    String? platform,
  }) async {
    try {
      final deviceId = await _getOrCreateDeviceId();
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/devices/register'),
        headers: headers,
        body: json.encode({
          if (deviceId.isNotEmpty) 'device_id': deviceId,
          'device_name': deviceName,
          'device_type': platform ?? 'android',
        }),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        final newId = (data['device_id'] ?? '').toString();
        if (newId.isNotEmpty) {
          _deviceId = newId;
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(_deviceIdKey, newId);
        }
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

  /// Clear device cache (for account switch)
  static Future<void> clearDeviceCache() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_deviceIdKey);
    _deviceId = null;
    print('[DeviceService] Device cache cleared');
  }

  // Host auto-attach polling
  static Timer? _hostAttachTimer;
  static Function(String sessionId, String hostToken)? onHostSessionReady;

  /// Start polling for host attach (for 3-device flow)
  /// When owner approves from another device, this device gets the session
  static void startHostAttachPolling({
    required Function(String sessionId, String hostToken) onSessionReady,
    Duration interval = const Duration(seconds: 3),
  }) {
    stopHostAttachPolling();
    onHostSessionReady = onSessionReady;
    
    _hostAttachTimer = Timer.periodic(interval, (_) async {
      await _checkHostAttach();
    });
    // Check immediately
    _checkHostAttach();
    print('[DeviceService] Host attach polling started');
  }

  /// Stop host attach polling
  static void stopHostAttachPolling() {
    _hostAttachTimer?.cancel();
    _hostAttachTimer = null;
    onHostSessionReady = null;
  }

  /// Check if there's a session waiting for this device to attach as host
  static Future<void> _checkHostAttach() async {
    if (_deviceId == null) return;
    
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/sessions/host/attach'),
        headers: headers,
        body: json.encode({'host_device_id': _deviceId}),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final sessionId = data['session_id']?.toString();
        final hostToken = data['token']?.toString();
        
        if (sessionId != null && sessionId.isNotEmpty && 
            hostToken != null && hostToken.isNotEmpty) {
          print('[DeviceService] Host session ready: $sessionId');
          stopHostAttachPolling();
          onHostSessionReady?.call(sessionId, hostToken);
        }
      }
      // 404 = no pending session, keep polling
    } catch (e) {
      print('[DeviceService] Host attach check error: $e');
    }
  }
  /// Update device settings via PATCH /devices/{id}
  static Future<bool> updateDevice(
    String deviceId, {
    String? name,
    bool? isFavorite,
    bool? alwaysRelay,
  }) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final body = <String, dynamic>{};
      if (name != null) body['device_name'] = name;
      if (isFavorite != null) body['is_favorite'] = isFavorite;
      if (alwaysRelay != null) body['always_relay'] = alwaysRelay;
      
      if (body.isEmpty) return true;
      
      final response = await http.patch(
        Uri.parse('${ApiConfig.baseUrl}/devices/$deviceId'),
        headers: headers,
        body: json.encode(body),
      ).timeout(const Duration(seconds: 15));
      
      print('[DeviceService] updateDevice $deviceId: ${response.statusCode}');
      return response.statusCode == 200;
    } catch (e) {
      print('[DeviceService] updateDevice error: $e');
      return false;
    }
  }

  /// Delete/deactivate device via DELETE /devices/{id}
  static Future<bool> deleteDevice(String deviceId) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.delete(
        Uri.parse('${ApiConfig.baseUrl}/devices/$deviceId'),
        headers: headers,
      ).timeout(const Duration(seconds: 15));

      print('[DeviceService] deleteDevice $deviceId: ${response.statusCode}');
      return response.statusCode == 200 || response.statusCode == 204;
    } catch (e) {
      print('[DeviceService] deleteDevice error: $e');
      return false;
    }
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
  final bool isFavorite;
  final bool alwaysRelay;

  Device({
    required this.id,
    required this.name,
    required this.platform,
    required this.online,
    this.lastSeen,
    this.isFavorite = false,
    this.alwaysRelay = false,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      id: json['device_id'] ?? json['id'] ?? '',
      name: json['device_name'] ?? json['name'] ?? '',
      platform: json['device_type'] ?? json['platform'] ?? 'unknown',
      online: json['online'] ?? false,
      lastSeen: json['last_seen'],
      isFavorite: json['is_favorite'] ?? json['favorite'] ?? false,
      alwaysRelay: json['always_relay'] ?? json['relay'] ?? false,
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

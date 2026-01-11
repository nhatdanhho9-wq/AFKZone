import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'auth_service.dart';
import 'device_service.dart';

/// Remote Service for Remote Preview v0.1
/// Handles: share tokens, remote requests, pending, approve/reject, TURN creds
class RemoteService {
  static String _asString(dynamic v) {
    if (v == null) return '';
    if (v is String) return v;
    // FastAPI validation errors: {"detail":[{...},{...}]}
    if (v is List) {
      try {
        if (v.isNotEmpty && v.first is Map && (v.first as Map).containsKey('msg')) {
          return (v.first as Map)['msg']?.toString() ?? v.toString();
        }
      } catch (_) {}
      return v.toString();
    }
    if (v is Map) {
      if (v.containsKey('detail')) return _asString(v['detail']);
      if (v.containsKey('msg')) return _asString(v['msg']);
      return v.toString();
    }
    return v.toString();
  }

  /// Create a share token for remote access
  static Future<ShareResult> createShareToken({int? validSeconds}) async {
    try {
      final deviceId = DeviceService.deviceId;
      if (deviceId == null) {
        return ShareResult(success: false, error: 'Device not registered. Please login again.');
      }

      // Backend accepts expires_hours (min 1). Keep MVP simple.
      final int expiresHours = validSeconds == null
          ? 24
          : ((validSeconds / 3600).ceil()).clamp(1, 168) as int;
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/share/create'),
        headers: headers,
        body: json.encode({
          'device_id': deviceId,
          'expires_hours': expiresHours,
          'max_uses': 1,
        }),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return ShareResult(success: true, token: _asString(data['token']));
      } else {
        return ShareResult(success: false, error: _asString(data['detail']).isNotEmpty ? _asString(data['detail']) : 'Failed to create share token');
      }
    } catch (e) {
      return ShareResult(success: false, error: e.toString());
    }
  }

  /// Create a share token for a specific device (owner only).
  static Future<ShareResult> createShareTokenForDevice({
    required String deviceId,
    int expiresHours = 24,
    int maxUses = 1,
  }) async {
    try {
      final creatorDeviceId = DeviceService.deviceId ?? await DeviceService.ensureDeviceId();
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/share/create'),
        headers: headers,
        body: json.encode({
          'device_id': deviceId,
          'expires_hours': expiresHours.clamp(1, 168),
          'max_uses': maxUses.clamp(1, 100),
          'created_by_device_id': creatorDeviceId,
        }),
      ).timeout(const Duration(seconds: 15));

      final data = json.decode(response.body);
      if (response.statusCode == 200 || response.statusCode == 201) {
        return ShareResult(success: true, token: _asString(data['token']));
      }
      return ShareResult(success: false, error: _asString(data['detail']).isNotEmpty ? _asString(data['detail']) : 'Failed to create token');
    } catch (e) {
      return ShareResult(success: false, error: e.toString());
    }
  }

  /// Request remote access via share token
  static Future<RemoteRequestResult> requestByToken(String shareToken) async {
    try {
      final requesterDeviceId = await DeviceService.ensureDeviceId();
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/request'),
        headers: headers,
        body: json.encode({'share_token': shareToken, 'requester_device_id': requesterDeviceId}),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return RemoteRequestResult(
          success: true,
          requestId: data['request_id'],
          status: data['status'] ?? 'pending',
          claimToken: data['claim_token'],
          sessionId: data['session_id'],
        );
      } else {
        return RemoteRequestResult(success: false, error: _asString(data['detail']).isNotEmpty ? _asString(data['detail']) : 'Request failed');
      }
    } catch (e) {
      return RemoteRequestResult(success: false, error: e.toString());
    }
  }

  /// Request remote access via target device ID (trusted flow)
  static Future<RemoteRequestResult> requestByDevice(String targetDeviceId) async {
    try {
      final requesterDeviceId = await DeviceService.ensureDeviceId();
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/request'),
        headers: headers,
        body: json.encode({'target_device_id': targetDeviceId, 'requester_device_id': requesterDeviceId}),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return RemoteRequestResult(
          success: true,
          requestId: data['request_id'],
          status: data['status'] ?? 'pending',
          claimToken: data['claim_token'],
          sessionId: data['session_id'],
        );
      } else {
        return RemoteRequestResult(success: false, error: _asString(data['detail']).isNotEmpty ? _asString(data['detail']) : 'Request failed');
      }
    } catch (e) {
      return RemoteRequestResult(success: false, error: e.toString());
    }
  }

  /// Get pending remote requests (for owner to approve/reject)
  static Future<List<PendingRequest>> getPending() async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/remote/pending'),
        headers: headers,
      ).timeout(Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final requests = (data['requests'] as List?)
            ?.map((r) => PendingRequest.fromJson(r))
            .toList() ?? [];
        return requests;
      }
      return [];
    } catch (e) {
      print('[RemoteService] getPending error: $e');
      return [];
    }
  }

  /// Approve a remote request
  static Future<ApproveResult> approve(String requestId) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      print('[RemoteService] approve: calling /remote/approve for request=$requestId');
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/approve'),
        headers: headers,
        body: json.encode({'request_id': requestId}),
      ).timeout(Duration(seconds: 15));

      print('[RemoteService] approve: status=${response.statusCode}, body=${response.body}');
      final data = json.decode(response.body);
      
      if (response.statusCode == 200) {
        // Try multiple field names for host token
        final hostToken = data['host_token'] ?? data['ws_token'] ?? data['token'];
        final sessionId = data['session_id'] ?? data['sessionId'];
        final controllerToken = data['controller_token'] ?? data['controllerToken'];
        
        print('[RemoteService] approve parsed: session=$sessionId, hostToken=${hostToken != null ? 'present (${hostToken.toString().length} chars)' : 'NULL'}, controllerToken=${controllerToken != null ? 'present' : 'NULL'}');
        print('[RemoteService] approve raw keys: ${data.keys.toList()}');
        
        if (hostToken == null) {
          print('[RemoteService] WARNING: host_token is NULL in approve response!');
        }
        
        return ApproveResult(
          success: true,
          sessionId: sessionId,
          controllerToken: controllerToken,
          hostToken: hostToken,
        );
      } else {
        print('[RemoteService] approve failed: ${response.body}');
        return ApproveResult(success: false, error: _asString(data['detail']).isNotEmpty ? _asString(data['detail']) : 'Approve failed');
      }
    } catch (e) {
      print('[RemoteService] approve exception: $e');
      return ApproveResult(success: false, error: e.toString());
    }
  }

  /// Reject a remote request
  static Future<bool> reject(String requestId) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/reject'),
        headers: headers,
        body: json.encode({'request_id': requestId}),
      ).timeout(Duration(seconds: 15));

      return response.statusCode == 200;
    } catch (e) {
      print('[RemoteService] reject error: $e');
      return false;
    }
  }

  /// Cancel a remote request (requester side)
  static Future<bool> cancelRequest(String requestId) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/cancel'),
        headers: headers,
        body: json.encode({'request_id': requestId}),
      ).timeout(Duration(seconds: 15));

      print('[RemoteService] cancelRequest $requestId: ${response.statusCode}');
      return response.statusCode == 200;
    } catch (e) {
      print('[RemoteService] cancelRequest error: $e');
      return false;
    }
  }

  /// Host signals ready after MediaProjection enabled (2-step flow)
  /// Returns HostReadyResult with host_token and signaling_ws_url
  static Future<HostReadyResult> hostReady(String requestId, {bool screenCapture = true}) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final url = '${ApiConfig.baseUrl}/remote/host-ready/$requestId?screen_capture=$screenCapture';
      print('[RemoteService] hostReady: calling $url');
      final response = await http.post(
        Uri.parse(url),
        headers: headers,
      ).timeout(Duration(seconds: 15));

      // Log RAW response BEFORE any parsing
      print('[RemoteService] hostReady RAW response:');
      print('  status: ${response.statusCode}');
      print('  content-type: ${response.headers['content-type']}');
      print('  body length: ${response.body.length}');
      print('  body preview: ${response.body.length > 200 ? response.body.substring(0, 200) : response.body}');
      
      // Check content-type before parsing
      final contentType = response.headers['content-type'] ?? '';
      if (!contentType.contains('application/json')) {
        print('[RemoteService] hostReady ERROR: Response is not JSON! content-type=$contentType');
        return HostReadyResult(
          success: false, 
          error: 'Server returned non-JSON response (${response.statusCode}): ${response.body.length > 100 ? response.body.substring(0, 100) : response.body}'
        );
      }
      
      // Safe JSON parse
      dynamic data;
      try {
        data = json.decode(response.body);
      } catch (parseError) {
        print('[RemoteService] hostReady JSON parse error: $parseError');
        return HostReadyResult(success: false, error: 'Invalid JSON: ${response.body.length > 100 ? response.body.substring(0, 100) : response.body}');
      }
      
      if (response.statusCode == 200) {
        // Try multiple field names for host_token
        final hostToken = data['host_token'] ?? data['ws_token'] ?? data['token'];
        final sessionId = data['session_id'] ?? data['sessionId'];
        final signalingWsUrl = data['signaling_ws_url'] ?? data['ws_url'];
        
        print('[RemoteService] hostReady parsed: sessionId=$sessionId, hostToken=${hostToken != null ? 'present (${hostToken.length} chars)' : 'NULL'}, wsUrl=${signalingWsUrl ?? 'NULL'}');
        print('[RemoteService] hostReady raw keys: ${data.keys.toList()}');
        
        if (hostToken == null) {
          print('[RemoteService] WARNING: host_token is NULL in hostReady response!');
        }
        
        return HostReadyResult(
          success: true,
          sessionId: sessionId,
          hostToken: hostToken,
          signalingWsUrl: signalingWsUrl,
        );
      } else {
        return HostReadyResult(success: false, error: data['detail']?.toString() ?? 'Host ready failed (${response.statusCode})');
      }
    } catch (e) {
      print('[RemoteService] hostReady exception: $e');
      return HostReadyResult(success: false, error: e.toString());
    }
  }

  /// Report ICE state to server for diagnostics
  /// POST /sessions/{id}/ice-state
  static Future<void> reportIceState(String sessionId, String iceState) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final url = '${ApiConfig.baseUrl}/sessions/$sessionId/ice-state';
      print('[RemoteService] reportIceState: $url, state=$iceState');
      
      final response = await http.post(
        Uri.parse(url),
        headers: headers,
        body: json.encode({'ice_state': iceState}),
      ).timeout(Duration(seconds: 5));
      
      print('[RemoteService] reportIceState: status=${response.statusCode}');
    } catch (e) {
      print('[RemoteService] reportIceState error: $e');
    }
  }

  /// Get TURN credentials for a session
  /// Throws SessionExpiredException if session is expired (404)
  static Future<TurnCredentials?> getTurnCredentials(String sessionId) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/sessions/$sessionId/turn-credentials'),
        headers: headers,
      ).timeout(Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return TurnCredentials.fromJson(data);
      } else if (response.statusCode == 404) {
        // Session expired or not found - need to re-approve
        print('[RemoteService] getTurnCredentials 404: session expired or not found');
        throw SessionExpiredException('Session expired. Please re-approve the connection.');
      } else {
        print('[RemoteService] getTurnCredentials failed: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      if (e is SessionExpiredException) rethrow;
      print('[RemoteService] getTurnCredentials error: $e');
      return null;
    }
  }

  /// Claim session details after approval using request_id + claim_token
  static Future<ClaimResult> claim({required String requestId, required String claimToken}) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/claim'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'request_id': requestId, 'claim_token': claimToken}),
      ).timeout(const Duration(seconds: 15));

      final data = json.decode(response.body);
      if (response.statusCode == 200) {
        return ClaimResult(
          ok: data['ok'] == true,
          status: data['status'] ?? 'pending',
          sessionId: data['session_id'],
          controllerToken: data['controller_token'],
        );
      }
      return ClaimResult(ok: false, status: 'error', error: _asString(data['detail']).isNotEmpty ? _asString(data['detail']) : 'Claim failed');
    } catch (e) {
      return ClaimResult(ok: false, status: 'error', error: e.toString());
    }
  }

  /// Host attaches to pending session for its device_id and receives host_token
  static Future<HostAttachResult> hostAttach({required String hostDeviceId}) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/sessions/host/attach'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'host_device_id': hostDeviceId}),
      ).timeout(const Duration(seconds: 15));

      final data = json.decode(response.body);
      if (response.statusCode == 200) {
        return HostAttachResult(
          success: true,
          sessionId: data['session_id'],
          hostToken: data['token'],
        );
      }
      return HostAttachResult(success: false, error: _asString(data['detail']).isNotEmpty ? _asString(data['detail']) : 'Host attach failed');
    } catch (e) {
      return HostAttachResult(success: false, error: e.toString());
    }
  }

  /// Build WebSocket URL for signaling using the correct WS token
  static String signalingUrl({required String sessionId, required String wsToken}) {
    final baseUrl = ApiConfig.baseUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');
    return '$baseUrl/sessions/$sessionId/ws?token=$wsToken';
  }
}

/// Share token result
class ShareResult {
  final bool success;
  final String? token;
  final String? error;

  ShareResult({required this.success, this.token, this.error});
}

/// Remote request result
class RemoteRequestResult {
  final bool success;
  final String? requestId;
  final String? status;
  final String? claimToken;
  final String? sessionId;
  final String? error;

  RemoteRequestResult({required this.success, this.requestId, this.status, this.claimToken, this.sessionId, this.error});
}

/// Pending request model
class PendingRequest {
  final String requestId;
  final String? requesterAccountId;
  final String? requesterDeviceId;
  final String? requesterName;
  final String? targetDeviceId; // share_creator_device_id - the device that created the share token
  final String status;
  final String createdAt;

  PendingRequest({
    required this.requestId,
    this.requesterAccountId,
    this.requesterDeviceId,
    this.requesterName,
    this.targetDeviceId,
    required this.status,
    required this.createdAt,
  });

  factory PendingRequest.fromJson(Map<String, dynamic> json) {
    return PendingRequest(
      requestId: json['request_id'] ?? '',
      requesterAccountId: json['requester_account_id'],
      requesterDeviceId: json['requester_device_id'],
      requesterName: json['requester_name'],
      targetDeviceId: json['target_device_id'] ?? json['share_creator_device_id'],
      status: json['status'] ?? 'pending',
      createdAt: json['created_at'] ?? '',
    );
  }
}

/// Approve result
class ApproveResult {
  final bool success;
  final String? sessionId;
  final String? controllerToken;
  final String? hostToken;
  final String? error;

  ApproveResult({required this.success, this.sessionId, this.controllerToken, this.hostToken, this.error});
}

/// Host ready result (from POST /remote/host-ready)
class HostReadyResult {
  final bool success;
  final String? sessionId;
  final String? hostToken;
  final String? signalingWsUrl;
  final String? error;

  HostReadyResult({required this.success, this.sessionId, this.hostToken, this.signalingWsUrl, this.error});
}

/// TURN credentials
class TurnCredentials {
  final List<String> urls;
  final String username;
  final String credential;

  TurnCredentials({
    required this.urls,
    required this.username,
    required this.credential,
  });

  factory TurnCredentials.fromJson(Map<String, dynamic> json) {
    // Safely convert urls to List<String> - handles List<dynamic> from JSON
    final dynamic rawUrls = json['urls'];
    final List<String> urlsList = rawUrls is List
        ? rawUrls.map((e) => e?.toString() ?? '').where((s) => s.isNotEmpty).toList()
        : <String>[];
    return TurnCredentials(
      urls: urlsList,
      username: json['username']?.toString() ?? '',
      credential: json['credential']?.toString() ?? '',
    );
  }
}

class ClaimResult {
  final bool ok;
  final String status;
  final String? sessionId;
  final String? controllerToken;
  final String? error;
  ClaimResult({required this.ok, required this.status, this.sessionId, this.controllerToken, this.error});
}

class HostAttachResult {
  final bool success;
  final String? sessionId;
  final String? hostToken;
  final String? error;
  HostAttachResult({required this.success, this.sessionId, this.hostToken, this.error});
}

/// Exception thrown when a session has expired (e.g., server restart, 404 on turn-credentials)
class SessionExpiredException implements Exception {
  final String message;
  SessionExpiredException(this.message);
  
  @override
  String toString() => 'SessionExpiredException: $message';
}

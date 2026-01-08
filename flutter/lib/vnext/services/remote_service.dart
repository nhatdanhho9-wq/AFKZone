import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'auth_service.dart';

/// Remote Service for Remote Preview v0.1
/// Handles: share tokens, remote requests, pending, approve/reject, TURN creds
class RemoteService {
  /// Create a share token for remote access
  static Future<ShareResult> createShareToken({int? validSeconds}) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/share/create'),
        headers: headers,
        body: json.encode({
          if (validSeconds != null) 'valid_seconds': validSeconds,
        }),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return ShareResult(success: true, token: data['token']);
      } else {
        return ShareResult(success: false, error: data['detail'] ?? 'Failed to create share token');
      }
    } catch (e) {
      return ShareResult(success: false, error: e.toString());
    }
  }

  /// Request remote access via share token
  static Future<RemoteRequestResult> requestByToken(String shareToken) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/request'),
        headers: headers,
        body: json.encode({'share_token': shareToken}),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return RemoteRequestResult(
          success: true,
          requestId: data['request_id'],
          status: data['status'] ?? 'pending',
        );
      } else {
        return RemoteRequestResult(success: false, error: data['detail'] ?? 'Request failed');
      }
    } catch (e) {
      return RemoteRequestResult(success: false, error: e.toString());
    }
  }

  /// Request remote access via target device ID (trusted flow)
  static Future<RemoteRequestResult> requestByDevice(String targetDeviceId) async {
    try {
      final headers = await AuthService.getAuthHeaders();
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/request'),
        headers: headers,
        body: json.encode({'target_device_id': targetDeviceId}),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return RemoteRequestResult(
          success: true,
          requestId: data['request_id'],
          status: data['status'] ?? 'pending',
        );
      } else {
        return RemoteRequestResult(success: false, error: data['detail'] ?? 'Request failed');
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
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/remote/approve'),
        headers: headers,
        body: json.encode({'request_id': requestId}),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200) {
        return ApproveResult(
          success: true,
          sessionId: data['session_id'],
        );
      } else {
        return ApproveResult(success: false, error: data['detail'] ?? 'Approve failed');
      }
    } catch (e) {
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

  /// Get TURN credentials for a session
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
      }
      return null;
    } catch (e) {
      print('[RemoteService] getTurnCredentials error: $e');
      return null;
    }
  }

  /// Get WebSocket URL for signaling
  static Future<String?> getSignalingUrl(String sessionId) async {
    final token = await AuthService.getToken();
    if (token == null) return null;
    
    final baseUrl = ApiConfig.baseUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');
    return '$baseUrl/sessions/$sessionId/ws?token=$token';
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
  final String? error;

  RemoteRequestResult({required this.success, this.requestId, this.status, this.error});
}

/// Pending request model
class PendingRequest {
  final String requestId;
  final String requesterId;
  final String? requesterName;
  final String status;
  final String createdAt;

  PendingRequest({
    required this.requestId,
    required this.requesterId,
    this.requesterName,
    required this.status,
    required this.createdAt,
  });

  factory PendingRequest.fromJson(Map<String, dynamic> json) {
    return PendingRequest(
      requestId: json['request_id'] ?? '',
      requesterId: json['requester_id'] ?? '',
      requesterName: json['requester_name'],
      status: json['status'] ?? 'pending',
      createdAt: json['created_at'] ?? '',
    );
  }
}

/// Approve result
class ApproveResult {
  final bool success;
  final String? sessionId;
  final String? error;

  ApproveResult({required this.success, this.sessionId, this.error});
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
    return TurnCredentials(
      urls: List<String>.from(json['urls'] ?? []),
      username: json['username'] ?? '',
      credential: json['credential'] ?? '',
    );
  }
}

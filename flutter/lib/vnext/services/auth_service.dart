import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

/// Auth Service for Remote Preview v0.1
/// Handles: register, login, logout, JWT storage
class AuthService {
  static const String _tokenKey = 'auth_token';
  static const String _accountIdKey = 'account_id';
  static const String _usernameKey = 'username';

  static String? _cachedToken;
  static String? _cachedAccountId;

  /// Register new account
  static Future<AuthResult> register(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'username': username, 'password': password}),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return AuthResult(success: true, accountId: data['account_id']);
      } else {
        return AuthResult(success: false, error: data['detail'] ?? 'Registration failed');
      }
    } catch (e) {
      return AuthResult(success: false, error: e.toString());
    }
  }

  /// Login and store JWT token
  static Future<AuthResult> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'username': username, 'password': password}),
      ).timeout(Duration(seconds: 15));

      final data = json.decode(response.body);
      
      if (response.statusCode == 200) {
        final token = data['access_token'];
        final accountId = data['account_id'];
        
        // Store token
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_tokenKey, token);
        await prefs.setString(_accountIdKey, accountId);
        await prefs.setString(_usernameKey, username);
        
        _cachedToken = token;
        _cachedAccountId = accountId;
        
        print('[AuthService] Login success: account=$accountId');
        return AuthResult(success: true, token: token, accountId: accountId);
      } else {
        return AuthResult(success: false, error: data['detail'] ?? 'Login failed');
      }
    } catch (e) {
      return AuthResult(success: false, error: e.toString());
    }
  }

  /// Logout and clear stored token
  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_accountIdKey);
    await prefs.remove(_usernameKey);
    _cachedToken = null;
    _cachedAccountId = null;
    print('[AuthService] Logged out');
  }

  /// Get stored JWT token
  static Future<String?> getToken() async {
    if (_cachedToken != null) return _cachedToken;
    final prefs = await SharedPreferences.getInstance();
    _cachedToken = prefs.getString(_tokenKey);
    return _cachedToken;
  }

  /// Get stored account ID
  static Future<String?> getAccountId() async {
    if (_cachedAccountId != null) return _cachedAccountId;
    final prefs = await SharedPreferences.getInstance();
    _cachedAccountId = prefs.getString(_accountIdKey);
    return _cachedAccountId;
  }

  /// Check if logged in
  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  /// Get auth headers for API calls
  static Future<Map<String, String>> getAuthHeaders() async {
    final token = await getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }
}

/// Auth operation result
class AuthResult {
  final bool success;
  final String? token;
  final String? accountId;
  final String? error;

  AuthResult({required this.success, this.token, this.accountId, this.error});
}

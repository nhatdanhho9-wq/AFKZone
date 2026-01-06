import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// AuthService for account-based licensing (v2.2.62+)
/// Handles JWT authentication with /auth/* endpoints
class AuthService {
  static const String _baseUrl = 'https://api.afkzone.cloud';
  static const String _tokenKey = 'afk_auth_token';
  static const String _userIdKey = 'afk_user_id';
  static const String _userEmailKey = 'afk_user_email';
  static const String _userNameKey = 'afk_user_name';

  /// Register new user
  /// Returns user data with token on success, throws on error
  static Future<Map<String, dynamic>> register(String email, String password, {String? name}) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'email': email,
        'password': password,
        if (name != null) 'name': name,
      }),
    ).timeout(Duration(seconds: 15));

    final data = json.decode(utf8.decode(response.bodyBytes));
    
    if (response.statusCode == 200 && data['success'] == true) {
      // Save token and user info
      await _saveAuthData(data);
      return data;
    } else if (response.statusCode == 400) {
      throw Exception(data['detail'] ?? 'Email đã được đăng ký');
    } else {
      throw Exception(data['detail'] ?? 'Lỗi đăng ký');
    }
  }

  /// Login with email/password
  /// Returns user data with token on success
  /// Throws with specific message for 429 (throttle) and 401 (invalid)
  static Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'email': email,
        'password': password,
      }),
    ).timeout(Duration(seconds: 15));

    final data = json.decode(utf8.decode(response.bodyBytes));
    
    if (response.statusCode == 200 && data['success'] == true) {
      await _saveAuthData(data);
      return data;
    } else if (response.statusCode == 429) {
      // Login throttle: 5 wrong attempts / 15 min
      throw Exception('Quá nhiều lần thử. Vui lòng đợi 15 phút.');
    } else if (response.statusCode == 401) {
      throw Exception('Email hoặc mật khẩu không đúng');
    } else {
      throw Exception(data['detail'] ?? 'Lỗi đăng nhập');
    }
  }

  /// Get current user info (requires token)
  static Future<Map<String, dynamic>> getMe() async {
    final token = await getToken();
    if (token == null) throw Exception('Chưa đăng nhập');

    final response = await http.get(
      Uri.parse('$_baseUrl/auth/me'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    ).timeout(Duration(seconds: 10));

    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes));
    } else if (response.statusCode == 401) {
      // Token expired or invalid
      await logout();
      throw Exception('Phiên đăng nhập hết hạn');
    } else {
      throw Exception('Lỗi lấy thông tin user');
    }
  }

  /// Logout - clear all auth data
  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userIdKey);
    await prefs.remove(_userEmailKey);
    await prefs.remove(_userNameKey);
  }

  /// Check if user is logged in
  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  /// Get stored JWT token
  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  /// Get stored user email
  static Future<String?> getUserEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_userEmailKey);
  }

  /// Get stored user name
  static Future<String?> getUserName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_userNameKey);
  }

  /// Save auth data to SharedPreferences
  static Future<void> _saveAuthData(Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    if (data['token'] != null) {
      await prefs.setString(_tokenKey, data['token']);
    }
    if (data['user_id'] != null) {
      await prefs.setInt(_userIdKey, data['user_id']);
    }
    if (data['email'] != null) {
      await prefs.setString(_userEmailKey, data['email']);
    }
    if (data['name'] != null) {
      await prefs.setString(_userNameKey, data['name']);
    }
  }

  /// Make authenticated GET request
  static Future<http.Response> authGet(String endpoint) async {
    final token = await getToken();
    return http.get(
      Uri.parse('$_baseUrl$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      },
    ).timeout(Duration(seconds: 15));
  }

  /// Make authenticated POST request
  static Future<http.Response> authPost(String endpoint, Map<String, dynamic> body) async {
    final token = await getToken();
    return http.post(
      Uri.parse('$_baseUrl$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      },
      body: json.encode(body),
    ).timeout(Duration(seconds: 15));
  }

  /// Make authenticated PATCH request
  static Future<http.Response> authPatch(String endpoint, Map<String, dynamic> body) async {
    final token = await getToken();
    return http.patch(
      Uri.parse('$_baseUrl$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      },
      body: json.encode(body),
    ).timeout(Duration(seconds: 15));
  }

  /// Make authenticated DELETE request
  static Future<http.Response> authDelete(String endpoint) async {
    final token = await getToken();
    return http.delete(
      Uri.parse('$_baseUrl$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      },
    ).timeout(Duration(seconds: 15));
  }
}

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/ui_config.dart';

/// Config Service for server-driven UI
/// Handles: fetch, cache, signature verify, LKG fallback, TTL refresh
class ConfigService {
  static const String _baseUrl = 'https://api.afkzone.cloud';
  static const String _configEndpoint = '/public/mobile-ui-config';
  static const String _lkgKey = 'mobile_ui_config:lkg';
  static const String _revisionKey = 'mobile_ui_config:revision';

  /// Load config with verification and caching
  static Future<UiConfig> loadConfig() async {
    try {
      // Try to fetch from server
      final response = await http.get(
        Uri.parse('$_baseUrl$_configEndpoint'),
        headers: {'Cache-Control': 'no-cache'},
      ).timeout(Duration(seconds: 15));

      if (response.statusCode == 200) {
        final envelope = json.decode(utf8.decode(response.bodyBytes));
        return await _processEnvelope(envelope);
      }
    } catch (e) {
      print('[ConfigService] Fetch error: $e');
    }

    // Fallback to LKG
    return await _loadLkg();
  }

  /// Process signed envelope
  static Future<UiConfig> _processEnvelope(Map<String, dynamic> envelope) async {
    final payload = envelope['payload'];
    final signature = envelope['signature'];

    if (payload == null) {
      throw Exception('Missing payload');
    }

    // 1. Verify signature (TODO: implement Ed25519)
    if (signature != null) {
      final isValid = await _verifySignature(payload, signature);
      if (!isValid) {
        print('[ConfigService] Invalid signature - using LKG');
        return await _loadLkg();
      }
    }

    final config = UiConfig.fromJson(payload);

    // 2. Check kill_switch
    if (config.killSwitch) {
      print('[ConfigService] Kill switch active - using defaults');
      return UiConfig.defaults();
    }

    // 3. Enforce monotonic revision
    final prefs = await SharedPreferences.getInstance();
    final cachedRevision = prefs.getInt(_revisionKey) ?? 0;
    if (config.revision < cachedRevision) {
      print('[ConfigService] Revision rollback detected - using LKG');
      return await _loadLkg();
    }

    // 4. Save as LKG
    await _saveLkg(payload, config.revision);

    return config;
  }

  /// Verify Ed25519 signature
  static Future<bool> _verifySignature(Map<String, dynamic> payload, Map<String, dynamic> signature) async {
    // TODO: Implement Ed25519 verification
    // For now, accept all signatures (mock mode)
    final alg = signature['alg'];
    final keyId = signature['key_id'];
    final sig = signature['sig'];

    if (alg != 'ed25519') {
      print('[ConfigService] Unknown signature algorithm: $alg');
      return false;
    }

    // In production: verify sig over canonical JSON of payload
    // For now: trust dev signatures
    print('[ConfigService] Signature verification (mock): key_id=$keyId');
    return true;
  }

  /// Save config to LKG cache
  static Future<void> _saveLkg(Map<String, dynamic> payload, int revision) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_lkgKey, json.encode(payload));
    await prefs.setInt(_revisionKey, revision);
    print('[ConfigService] Saved LKG revision $revision');
  }

  /// Load from LKG cache or use defaults
  static Future<UiConfig> _loadLkg() async {
    final prefs = await SharedPreferences.getInstance();
    final lkgJson = prefs.getString(_lkgKey);

    if (lkgJson != null) {
      try {
        final payload = json.decode(lkgJson);
        print('[ConfigService] Loaded LKG revision ${payload['revision']}');
        return UiConfig.fromJson(payload);
      } catch (e) {
        print('[ConfigService] LKG parse error: $e');
      }
    }

    print('[ConfigService] Using baked-in defaults');
    return UiConfig.defaults();
  }

  /// Clear LKG cache (for testing)
  static Future<void> clearCache() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_lkgKey);
    await prefs.remove(_revisionKey);
  }
}

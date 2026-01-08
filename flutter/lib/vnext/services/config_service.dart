import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/ui_config.dart';
import '../config/api_config.dart';
import '../crypto/ed25519_verifier.dart';

/// Config Service for server-driven UI
/// Handles: fetch, cache, signature verify, LKG fallback, TTL refresh
class ConfigService {
  static const String _lkgKey = 'mobile_ui_config:lkg';
  static const String _revisionKey = 'mobile_ui_config:revision';
  static const String _lastFetchKey = 'mobile_ui_config:last_fetch';

  /// Load config with verification and caching
  static Future<UiConfig> loadConfig() async {
    final timestamp = DateTime.now().toIso8601String();
    print('[ConfigService] [$timestamp] Loading config from ${ApiConfig.configEndpoint}');

    try {
      // Try to fetch from server
      final response = await http.get(
        Uri.parse(ApiConfig.configEndpoint),
        headers: {'Cache-Control': 'no-cache'},
      ).timeout(Duration(seconds: 15));

      print('[ConfigService] Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final envelope = json.decode(utf8.decode(response.bodyBytes));
        return await _processEnvelope(envelope);
      } else {
        print('[ConfigService] Non-200 response: ${response.statusCode}');
      }
    } catch (e) {
      print('[ConfigService] Fetch error: $e');
    }

    // Fallback to LKG
    print('[ConfigService] Falling back to LKG');
    return await _loadLkg();
  }

  /// Process signed envelope
  static Future<UiConfig> _processEnvelope(Map<String, dynamic> envelope) async {
    final payload = envelope['payload'];
    final signature = envelope['signature'];
    final timestamp = DateTime.now().toIso8601String();

    if (payload == null) {
      print('[ConfigService] [$timestamp] Missing payload in envelope');
      throw Exception('Missing payload');
    }

    // 1. Verify signature using Ed25519
    if (signature != null) {
      print('[ConfigService] [$timestamp] Verifying signature...');
      final isValid = await Ed25519Verifier.verify(
        payload: payload,
        signature: signature,
      );
      
      if (!isValid) {
        print('[ConfigService] [$timestamp] INVALID SIGNATURE - rejecting update, using LKG');
        return await _loadLkg();
      }
      print('[ConfigService] [$timestamp] Signature VALID');
    } else {
      print('[ConfigService] [$timestamp] WARNING: No signature present');
    }

    final config = UiConfig.fromJson(payload);

    // 2. Check kill_switch
    if (config.killSwitch) {
      print('[ConfigService] [$timestamp] Kill switch ACTIVE - using baked-in defaults');
      return UiConfig.defaults();
    }

    // 3. Verify issued_at not in far future (allow ±5 min clock skew)
    try {
      final issuedAt = DateTime.parse(config.issuedAt);
      final now = DateTime.now();
      final maxFuture = now.add(Duration(minutes: 5));
      if (issuedAt.isAfter(maxFuture)) {
        print('[ConfigService] [$timestamp] issued_at too far in future: ${config.issuedAt}');
        return await _loadLkg();
      }
    } catch (e) {
      print('[ConfigService] [$timestamp] Invalid issued_at format: ${config.issuedAt}');
    }

    // 4. Enforce monotonic revision
    final prefs = await SharedPreferences.getInstance();
    final cachedRevision = prefs.getInt(_revisionKey) ?? 0;
    if (config.revision < cachedRevision) {
      print('[ConfigService] [$timestamp] Revision ROLLBACK detected: ${config.revision} < $cachedRevision');
      return await _loadLkg();
    }
    print('[ConfigService] [$timestamp] Revision check OK: ${config.revision} >= $cachedRevision');

    // 5. Check TTL (for refresh scheduling)
    print('[ConfigService] [$timestamp] TTL: ${config.ttlSeconds} seconds');

    // 6. Save as LKG
    await _saveLkg(payload, config.revision);

    print('[ConfigService] [$timestamp] Config loaded successfully: revision=${config.revision}, tabs=${config.tabs.length}');
    return config;
  }

  /// Save config to LKG cache
  static Future<void> _saveLkg(Map<String, dynamic> payload, int revision) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_lkgKey, json.encode(payload));
    await prefs.setInt(_revisionKey, revision);
    await prefs.setString(_lastFetchKey, DateTime.now().toIso8601String());
    print('[ConfigService] Saved LKG revision $revision');
  }

  /// Load from LKG cache or use defaults
  static Future<UiConfig> _loadLkg() async {
    final prefs = await SharedPreferences.getInstance();
    final lkgJson = prefs.getString(_lkgKey);
    final timestamp = DateTime.now().toIso8601String();

    if (lkgJson != null) {
      try {
        final payload = json.decode(lkgJson);
        print('[ConfigService] [$timestamp] Loaded LKG revision ${payload['revision']}');
        return UiConfig.fromJson(payload);
      } catch (e) {
        print('[ConfigService] [$timestamp] LKG parse error: $e');
      }
    }

    print('[ConfigService] [$timestamp] Using baked-in defaults (no LKG available)');
    return UiConfig.defaults();
  }

  /// Clear LKG cache (for testing)
  static Future<void> clearCache() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_lkgKey);
    await prefs.remove(_revisionKey);
    await prefs.remove(_lastFetchKey);
    print('[ConfigService] Cache cleared');
  }

  /// Get cached revision number
  static Future<int> getCachedRevision() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_revisionKey) ?? 0;
  }

  /// Get last fetch timestamp
  static Future<String?> getLastFetchTime() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_lastFetchKey);
  }
}

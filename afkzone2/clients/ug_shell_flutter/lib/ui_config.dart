import 'dart:convert';

import 'package:cryptography/cryptography.dart';

class UiConfigEnvelope {
  final Map<String, dynamic> payload;
  final Map<String, dynamic> signature;

  UiConfigEnvelope({required this.payload, required this.signature});

  static UiConfigEnvelope fromJson(Map<String, dynamic> json) {
    return UiConfigEnvelope(
      payload: Map<String, dynamic>.from(json['payload'] ?? const {}),
      signature: Map<String, dynamic>.from(json['signature'] ?? const {}),
    );
  }

  int get revision => (payload['revision'] as num?)?.toInt() ?? 0;
  int get ttlSeconds => (payload['ttl_seconds'] as num?)?.toInt() ?? 300;
  bool get killSwitch => payload['kill_switch'] == true;
}

class UiConfigVerifier {
  /// Build-time overrides for dev.
  /// Example:
  ///   flutter run --dart-define=AFK_UI_KEY_ID=dev-key --dart-define=AFK_UI_PUBKEY_B64=...
  static const String envKeyId = String.fromEnvironment('AFK_UI_KEY_ID', defaultValue: '');
  static const String envPubKeyB64 = String.fromEnvironment('AFK_UI_PUBKEY_B64', defaultValue: '');

  // Pin public keys by key_id for production (replace with real keys).
  static const Map<String, String> pinnedPublicKeysB64 = {
    // Intentionally empty for MVP; use dart-define in development.
  };

  static Future<bool> verify(UiConfigEnvelope env) async {
    final alg = env.signature['alg'];
    final keyId = env.signature['key_id'];
    final sigB64 = env.signature['sig'];
    if (alg != 'ed25519' || keyId is! String || sigB64 is! String) return false;

    final pkB64 = _resolvePublicKeyB64(keyId);
    if (pkB64 == null) return false;

    final pkBytes = base64Decode(pkB64);
    final sigBytes = base64Decode(sigB64);

    final canonical = canonicalJson(env.payload);
    final message = utf8.encode(canonical);

    final algorithm = Ed25519();
    final publicKey = SimplePublicKey(pkBytes, type: KeyPairType.ed25519);
    final signature = Signature(sigBytes, publicKey: publicKey);
    try {
      return await algorithm.verify(message, signature: signature);
    } catch (_) {
      return false;
    }
  }

  static String? _resolvePublicKeyB64(String keyId) {
    if (envKeyId.isNotEmpty && envPubKeyB64.isNotEmpty && keyId == envKeyId) {
      return envPubKeyB64;
    }
    return pinnedPublicKeysB64[keyId];
  }

  static String canonicalJson(Object? obj) {
    final normalized = _normalize(obj);
    return jsonEncode(normalized);
  }

  static Object? _normalize(Object? obj) {
    if (obj is Map) {
      final keys = obj.keys.map((k) => k.toString()).toList()..sort();
      final out = <String, Object?>{};
      for (final k in keys) {
        out[k] = _normalize(obj[k]);
      }
      return out;
    }
    if (obj is List) {
      return obj.map(_normalize).toList();
    }
    return obj;
  }
}

UiConfigEnvelope bakedDefaultConfig() {
  return UiConfigEnvelope(
    payload: {
      'schema_version': 1,
      'revision': 0,
      'issued_at': '1970-01-01T00:00:00Z',
      'ttl_seconds': 300,
      'kill_switch': false,
      'tabs': [
        {'id': 'device', 'label': 'Device', 'icon': 'tab_device', 'visible': true, 'route_type': 'tab_device'},
        {'id': 'discover', 'label': 'Discover', 'icon': 'tab_discover', 'visible': true, 'route_type': 'tab_discover'},
        {'id': 'purchase', 'label': 'Purchase', 'icon': 'tab_purchase', 'visible': true, 'route_type': 'tab_purchase'},
        {'id': 'me', 'label': 'Me', 'icon': 'tab_me', 'visible': true, 'route_type': 'tab_me'},
      ],
      'routes': [],
      'actions': [],
      'content': {
        'device': {'quick_action_ids': []},
        'discover': {'sections': []},
        'purchase': {},
        'me': {'menu_action_ids': []},
      }
    },
    signature: const {'alg': 'ed25519', 'key_id': 'baked', 'sig': ''},
  );
}


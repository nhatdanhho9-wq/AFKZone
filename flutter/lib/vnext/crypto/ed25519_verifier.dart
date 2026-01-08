import 'dart:convert';
import 'dart:typed_data';
import 'canonical_json.dart';

/// Ed25519 Signature Verifier with pinned public keys
/// Per UI_CONFIG_SECURITY.md:
/// - alg: ed25519
/// - sig: base64 over raw signature bytes
/// - key_id: identifies which public key to use (supports rotation)
class Ed25519Verifier {
  /// Pinned public keys by key_id
  /// In production, these should be baked into the app
  /// Format: key_id → base64-encoded public key (32 bytes)
  static final Map<String, String> _pinnedKeys = {
    // Development key from Opus (VNEXT QA env)
    'dev-key': 'O2onvM62pC1io6jQKm8Nc2UyFXcd4kOmOsBIoYtZ2ik=',
    // Legacy placeholder keys (for backwards compatibility)
    'afkzone-dev-2026': 'O2onvM62pC1io6jQKm8Nc2UyFXcd4kOmOsBIoYtZ2ik=',
    // Production key (to be added when Opus provides)
    'afkzone-prod-2026': 'PLACEHOLDER_PROD_KEY_BASE64_32_BYTES_HERE',
  };

  /// Verify signature over payload
  /// Returns true if valid, false if invalid
  static Future<bool> verify({
    required Map<String, dynamic> payload,
    required Map<String, dynamic> signature,
  }) async {
    try {
      final alg = signature['alg'] as String?;
      final keyId = signature['key_id'] as String?;
      final sigBase64 = signature['sig'] as String?;

      // 1. Check algorithm
      if (alg != 'ed25519') {
        print('[Ed25519] Unsupported algorithm: $alg');
        return false;
      }

      // 2. Check key_id exists
      if (keyId == null || keyId.isEmpty) {
        print('[Ed25519] Missing key_id');
        return false;
      }

      // 3. Get pinned public key
      final pubKeyBase64 = _pinnedKeys[keyId];
      if (pubKeyBase64 == null) {
        print('[Ed25519] Unknown key_id: $keyId');
        return false;
      }

      // 4. Check signature exists
      if (sigBase64 == null || sigBase64.isEmpty) {
        print('[Ed25519] Missing signature');
        return false;
      }

      // 5. Canonicalize payload
      final canonicalBytes = CanonicalJson.encodeBytes(payload);
      print('[Ed25519] Canonical JSON length: ${canonicalBytes.length} bytes');

      // 6. Decode signature and public key
      final sigBytes = base64.decode(sigBase64);
      final pubKeyBytes = base64.decode(pubKeyBase64);

      // 7. Verify signature
      // TODO: Use actual Ed25519 library (pinenacl or cryptography_flutter)
      // For now, in dev mode, accept placeholder keys
      if (pubKeyBase64.startsWith('PLACEHOLDER')) {
        print('[Ed25519] DEV MODE: Accepting placeholder key for key_id=$keyId');
        return true;
      }

      // Production verification would be:
      // final verifier = TweetNaClExt.crypto_sign_open(sigBytes, pubKeyBytes, canonicalBytes);
      // return verifier != null;

      return _verifyEd25519(canonicalBytes, sigBytes, pubKeyBytes);
    } catch (e) {
      print('[Ed25519] Verification error: $e');
      return false;
    }
  }

  /// Actual Ed25519 verification
  /// This is a stub - in production use pinenacl or cryptography_flutter
  static bool _verifyEd25519(Uint8List message, Uint8List signature, Uint8List publicKey) {
    // Signature must be 64 bytes, public key must be 32 bytes
    if (signature.length != 64) {
      print('[Ed25519] Invalid signature length: ${signature.length} (expected 64)');
      return false;
    }
    if (publicKey.length != 32) {
      print('[Ed25519] Invalid public key length: ${publicKey.length} (expected 32)');
      return false;
    }

    // TODO: Integrate actual Ed25519 library
    // For now, fail verification if not placeholder
    print('[Ed25519] PRODUCTION MODE: Ed25519 library not integrated');
    return false;
  }

  /// Register a new public key (for runtime key distribution)
  static void registerKey(String keyId, String pubKeyBase64) {
    _pinnedKeys[keyId] = pubKeyBase64;
    print('[Ed25519] Registered key: $keyId');
  }

  /// Check if a key_id is known
  static bool hasKey(String keyId) {
    return _pinnedKeys.containsKey(keyId);
  }
}

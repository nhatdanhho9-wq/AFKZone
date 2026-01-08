import 'dart:convert';
import 'dart:typed_data';

/// Canonical JSON encoder for signature verification
/// Per UI_CONFIG_SECURITY.md:
/// - UTF-8
/// - Object keys sorted lexicographically at every level
/// - No insignificant whitespace
/// - Arrays preserve order
class CanonicalJson {
  /// Encode any JSON value to canonical JSON string
  static String encode(dynamic value) {
    return _encodeValue(value);
  }

  /// Encode to UTF-8 bytes for signing
  static Uint8List encodeBytes(dynamic value) {
    return Uint8List.fromList(utf8.encode(encode(value)));
  }

  static String _encodeValue(dynamic value) {
    if (value == null) {
      return 'null';
    } else if (value is bool) {
      return value ? 'true' : 'false';
    } else if (value is num) {
      // Handle integers and doubles
      if (value is int) {
        return value.toString();
      } else {
        // Ensure no trailing zeros for whole numbers
        final d = value as double;
        if (d == d.truncateToDouble()) {
          return d.toInt().toString();
        }
        return value.toString();
      }
    } else if (value is String) {
      return _encodeString(value);
    } else if (value is List) {
      return _encodeArray(value);
    } else if (value is Map) {
      return _encodeObject(value as Map<String, dynamic>);
    } else {
      throw ArgumentError('Cannot encode type: ${value.runtimeType}');
    }
  }

  static String _encodeString(String s) {
    final buffer = StringBuffer('"');
    for (final char in s.runes) {
      if (char == 0x22) { // "
        buffer.write(r'\"');
      } else if (char == 0x5C) { // \
        buffer.write(r'\\');
      } else if (char == 0x08) { // backspace
        buffer.write(r'\b');
      } else if (char == 0x0C) { // form feed
        buffer.write(r'\f');
      } else if (char == 0x0A) { // newline
        buffer.write(r'\n');
      } else if (char == 0x0D) { // carriage return
        buffer.write(r'\r');
      } else if (char == 0x09) { // tab
        buffer.write(r'\t');
      } else if (char < 0x20) {
        // Other control characters
        buffer.write('\\u${char.toRadixString(16).padLeft(4, '0')}');
      } else {
        buffer.writeCharCode(char);
      }
    }
    buffer.write('"');
    return buffer.toString();
  }

  static String _encodeArray(List list) {
    if (list.isEmpty) return '[]';
    final items = list.map(_encodeValue).join(',');
    return '[$items]';
  }

  static String _encodeObject(Map<String, dynamic> map) {
    if (map.isEmpty) return '{}';
    
    // Sort keys lexicographically
    final sortedKeys = map.keys.toList()..sort();
    
    final pairs = sortedKeys.map((key) {
      final encodedKey = _encodeString(key);
      final encodedValue = _encodeValue(map[key]);
      return '$encodedKey:$encodedValue';
    }).join(',');
    
    return '{$pairs}';
  }
}

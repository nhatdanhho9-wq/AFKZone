/// Date parsing utilities for AFK Zone
/// Handles both ISO 8601 strings and legacy epoch milliseconds

class AfkDateUtils {
  /// Parse expires_at from API which can be ISO string or int (epoch ms)
  /// Returns epoch milliseconds for storage
  static int? parseExpiresAt(dynamic value) {
    if (value == null) return null;
    
    if (value is String) {
      // ISO 8601 string from server (e.g., "2026-02-01T00:00:00")
      try {
        final dt = DateTime.parse(value);
        return dt.millisecondsSinceEpoch;
      } catch (e) {
        print('❌ Error parsing ISO date: $e');
        return null;
      }
    } else if (value is int) {
      // Legacy epoch milliseconds
      return value;
    } else if (value is double) {
      // Sometimes JSON parses numbers as double
      return value.toInt();
    }
    
    return null;
  }
  
  /// Format epoch ms to display string
  static String formatDate(int? epochMs) {
    if (epochMs == null) return 'N/A';
    final date = DateTime.fromMillisecondsSinceEpoch(epochMs);
    return '${date.day}/${date.month}/${date.year}';
  }
  
  /// Format ISO string or epoch to display string
  static String formatExpiresAt(dynamic value) {
    final epochMs = parseExpiresAt(value);
    return formatDate(epochMs);
  }
}

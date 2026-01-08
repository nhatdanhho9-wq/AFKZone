/// API Configuration for vNext
/// Supports runtime base URL switch via environment/build-define
class ApiConfig {
  /// Default production base URL
  static const String _defaultBaseUrl = 'https://api.afkzone.cloud';

  /// Staging base URL
  static const String _stagingBaseUrl = 'https://staging-api.afkzone.cloud';

  /// QA base URL (from Opus VNEXT_API_BASE)
  static const String _qaBaseUrl = const String.fromEnvironment(
    'VNEXT_API_BASE',
    defaultValue: 'http://172.26.31.115:21121',
  );

  /// Local development base URL
  static const String _localBaseUrl = 'http://localhost:8000';

  /// Current environment (can be set via build-define)
  /// Options: 'production', 'staging', 'qa', 'local'
  static String _environment = const String.fromEnvironment(
    'API_ENV',
    defaultValue: 'production',
  );

  /// Override base URL (for runtime switching)
  static String? _overrideBaseUrl;

  /// Get current base URL
  static String get baseUrl {
    // Priority: override > environment-based > default
    if (_overrideBaseUrl != null) {
      return _overrideBaseUrl!;
    }

    switch (_environment) {
      case 'staging':
        return _stagingBaseUrl;
      case 'qa':
        return _qaBaseUrl;
      case 'local':
        return _localBaseUrl;
      case 'production':
      default:
        return _defaultBaseUrl;
    }
  }

  /// Get current environment name
  static String get environment => _environment;

  /// Set environment at runtime
  static void setEnvironment(String env) {
    _environment = env;
    print('[ApiConfig] Environment set to: $env → ${baseUrl}');
  }

  /// Override base URL directly
  static void setBaseUrl(String url) {
    _overrideBaseUrl = url;
    print('[ApiConfig] Base URL override: $url');
  }

  /// Clear base URL override
  static void clearOverride() {
    _overrideBaseUrl = null;
    print('[ApiConfig] Base URL override cleared');
  }

  /// Check if using production
  static bool get isProduction => _environment == 'production' && _overrideBaseUrl == null;

  /// Check if using staging
  static bool get isStaging => _environment == 'staging';

  /// Check if using local
  static bool get isLocal => _environment == 'local';

  /// Get config endpoint URL
  static String get configEndpoint => '$baseUrl/public/mobile-ui-config';

  /// Get regions endpoint URL
  static String get regionsEndpoint => '$baseUrl/public/regions';

  /// Get plans endpoint URL
  static String plansEndpoint(String? tierId) {
    final base = '$baseUrl/public/plans';
    return tierId != null ? '$base?tier_id=$tierId' : base;
  }

  /// Get discover endpoint URL
  static String get discoverEndpoint => '$baseUrl/public/discover';

  /// Get notifications endpoint URL
  static String get notificationsEndpoint => '$baseUrl/public/notifications';
}

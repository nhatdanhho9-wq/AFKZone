import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/ui_config.dart';

/// Action Dispatcher - Handles all action_key dispatch with gating
class VNextActionDispatcher {
  /// Dispatch an action by action_key
  static void dispatch(
    BuildContext context,
    String actionKey, {
    Map<String, dynamic>? params,
    GateConfig? gate,
  }) {
    // TODO: Gate enforcement
    // if (gate?.requiresAuth == true && !isLoggedIn) { showLoginPrompt(); return; }
    // if (gate?.requiresEntitlement == true && !hasEntitlement) { showPurchasePrompt(); return; }

    print('[VNextActionDispatcher] $actionKey params=$params');

    switch (actionKey) {
      // Device actions
      case 'connect_to_remote':
        _handleConnectToRemote(context, params);
        break;
      case 'open_recent':
        _handleOpenRecent(context);
        break;
      case 'open_favorites':
        _handleOpenFavorites(context);
        break;
      case 'open_contacts':
        _handleOpenContacts(context);
        break;
      case 'share_screen_start':
        _handleShareScreenStart(context);
        break;
      case 'scan_qr':
        _handleScanQr(context);
        break;

      // Auth actions
      case 'auth_login':
        _handleAuthLogin(context);
        break;
      case 'auth_logout':
        _handleAuthLogout(context);
        break;
      case 'oauth_google_login':
        _handleOAuthGoogle(context);
        break;

      // Purchase actions
      case 'select_region':
        _handleSelectRegion(context, params);
        break;
      case 'buy_plan':
        _handleBuyPlan(context, params);
        break;
      case 'redeem_code':
        _handleRedeemCode(context, params);
        break;

      // Account actions
      case 'open_orders':
        _handleOpenOrders(context);
        break;
      case 'net_check':
        _handleNetCheck(context);
        break;
      case 'open_webview':
        _handleOpenWebview(context, params);
        break;
      case 'open_route':
        _handleOpenRoute(context, params);
        break;
      case 'copy_text':
        _handleCopyText(context, params);
        break;

      default:
        _showSnackBar(context, 'Unknown action: $actionKey');
    }
  }

  // ============= Device Handlers =============

  static void _handleConnectToRemote(BuildContext context, Map<String, dynamic>? params) {
    final remoteId = params?['remote_id'] ?? '';
    if (remoteId.isEmpty) {
      _showSnackBar(context, 'Please enter a device ID');
      return;
    }
    // TODO: Navigate to remote connection screen
    _showSnackBar(context, 'Connecting to $remoteId...');
  }

  static void _handleOpenRecent(BuildContext context) {
    // TODO: Navigate to recent connections
    _showSnackBar(context, 'Opening recent connections...');
  }

  static void _handleOpenFavorites(BuildContext context) {
    // TODO: Navigate to favorites
    _showSnackBar(context, 'Opening favorites...');
  }

  static void _handleOpenContacts(BuildContext context) {
    // TODO: Navigate to contacts
    _showSnackBar(context, 'Opening contacts...');
  }

  static void _handleShareScreenStart(BuildContext context) {
    // TODO: Start screen share service
    _showSnackBar(context, 'Starting screen share...');
  }

  static void _handleScanQr(BuildContext context) {
    // TODO: Open QR scanner
    _showSnackBar(context, 'Opening QR scanner...');
  }

  // ============= Auth Handlers =============

  static void _handleAuthLogin(BuildContext context) {
    // TODO: Navigate to login page
    _showSnackBar(context, 'Opening login...');
  }

  static void _handleAuthLogout(BuildContext context) {
    // TODO: Logout and clear session
    _showSnackBar(context, 'Logging out...');
  }

  static void _handleOAuthGoogle(BuildContext context) {
    // TODO: Google OAuth flow
    _showSnackBar(context, 'Google login...');
  }

  // ============= Purchase Handlers =============

  static void _handleSelectRegion(BuildContext context, Map<String, dynamic>? params) {
    final regionCode = params?['region_code'] ?? '';
    _showSnackBar(context, 'Selected region: $regionCode');
  }

  static void _handleBuyPlan(BuildContext context, Map<String, dynamic>? params) {
    final planId = params?['plan_id'] ?? '';
    final region = params?['region'] ?? '';
    // TODO: Navigate to payment screen
    _showSnackBar(context, 'Buying plan $planId in region $region');
  }

  static void _handleRedeemCode(BuildContext context, Map<String, dynamic>? params) {
    final code = params?['code'] ?? '';
    // TODO: Navigate to redeem screen
    _showSnackBar(context, 'Redeeming code: $code');
  }

  // ============= Account Handlers =============

  static void _handleOpenOrders(BuildContext context) {
    // TODO: Navigate to orders screen
    _showSnackBar(context, 'Opening orders...');
  }

  static void _handleNetCheck(BuildContext context) {
    // TODO: Navigate to network check screen
    _showSnackBar(context, 'Opening network check...');
  }

  static void _handleOpenWebview(BuildContext context, Map<String, dynamic>? params) {
    final url = params?['url'] ?? '';
    final title = params?['title'] ?? 'Web';
    // TODO: Navigate to webview screen
    _showSnackBar(context, 'Opening $title: $url');
  }

  static void _handleOpenRoute(BuildContext context, Map<String, dynamic>? params) {
    final routeId = params?['route_id'] ?? '';
    // TODO: Resolve route from config and navigate
    _showSnackBar(context, 'Opening route: $routeId');
  }

  static void _handleCopyText(BuildContext context, Map<String, dynamic>? params) {
    final text = params?['text'] ?? '';
    Clipboard.setData(ClipboardData(text: text));
    _showSnackBar(context, 'Copied to clipboard');
  }

  // ============= Helpers =============

  static void _showSnackBar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 2)),
    );
  }
}

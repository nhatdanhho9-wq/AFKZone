import 'package:flutter/material.dart';

class ActionDef {
  final String id;
  final String label;
  final String icon;
  final String actionKey;
  final Map<String, dynamic> params;
  final Map<String, dynamic> gate;

  ActionDef({
    required this.id,
    required this.label,
    required this.icon,
    required this.actionKey,
    required this.params,
    required this.gate,
  });

  static ActionDef? fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    final label = json['label'];
    final icon = json['icon'];
    final actionKey = json['action_key'];
    if (id is! String || label is! String || icon is! String || actionKey is! String) return null;
    return ActionDef(
      id: id,
      label: label,
      icon: icon,
      actionKey: actionKey,
      params: Map<String, dynamic>.from(json['params'] ?? const {}),
      gate: Map<String, dynamic>.from(json['gate'] ?? const {}),
    );
  }
}

IconData iconFromKey(String key) {
  switch (key) {
    case 'tab_device':
      return Icons.devices;
    case 'tab_discover':
      return Icons.explore;
    case 'tab_purchase':
      return Icons.shopping_bag;
    case 'tab_me':
      return Icons.person;
    case 'recent':
      return Icons.history;
    case 'favorite':
      return Icons.star;
    case 'contacts':
      return Icons.people;
    case 'share_screen':
      return Icons.cast;
    case 'orders':
      return Icons.receipt_long;
    case 'redeem':
      return Icons.redeem;
    case 'net_check':
      return Icons.speed;
    case 'user_guide':
      return Icons.menu_book;
    default:
      return Icons.circle;
  }
}

/// MVP registry: dispatch actions to app-local behavior.
/// In production this should:
/// - enforce gate rules locally
/// - call backend for privileged actions
/// - navigate using strongly-typed routes
Future<void> dispatchAction({
  required BuildContext context,
  required ActionDef action,
}) async {
  final msg = 'action=${action.actionKey} params=${action.params}';
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
}


import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/ui_config.dart';
import '../actions/action_dispatcher.dart';
import '../services/auth_service.dart';
import '../config/api_config.dart';

/// Me Tab - Account hub with server-driven menu
class MeTab extends StatelessWidget {
  final UiConfig? config;
  final bool isLoggedIn;
  final VoidCallback onShowLogin;
  final VoidCallback? onLogout;

  const MeTab({
    Key? key,
    this.config,
    required this.isLoggedIn,
    required this.onShowLogin,
    this.onLogout,
  }) : super(key: key);

  List<ActionConfig> get _menuActions {
    final cfg = config;
    if (cfg?.content?.me == null) return [];
    
    return cfg!.content!.me!.menuActionIds
        .map((id) => cfg.getActionById(id))
        .where((a) => a != null)
        .cast<ActionConfig>()
        .toList();
  }

  IconData _getMenuIcon(String iconKey) {
    switch (iconKey) {
      case 'orders': return Icons.receipt_long;
      case 'redeem': return Icons.card_giftcard;
      case 'net_check': return Icons.network_check;
      case 'user_guide': return Icons.help_outline;
      case 'support': return Icons.headset_mic;
      case 'settings': return Icons.settings;
      default: return Icons.circle;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Me'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Account header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.green.shade400, Colors.green.shade600],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              child: Column(
                children: [
                  const CircleAvatar(
                    radius: 40,
                    backgroundColor: Colors.white,
                    child: Icon(Icons.person, size: 48, color: Colors.green),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    isLoggedIn ? 'Logged In' : 'Guest',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  FutureBuilder<String?>(
                    future: AuthService.getAccountId(),
                    builder: (context, snap) {
                      final accountId = snap.data;
                      final label = isLoggedIn && accountId != null ? accountId : 'Not logged in';
                      return Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            'Account: $label',
                            style: const TextStyle(color: Colors.white70, fontSize: 14),
                          ),
                          const SizedBox(width: 8),
                          GestureDetector(
                            onTap: () {
                              Clipboard.setData(ClipboardData(text: label));
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Copied!')),
                              );
                            },
                            child: const Icon(Icons.copy, color: Colors.white70, size: 16),
                          ),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 10),
                  Text(
                    'API: ${ApiConfig.baseUrl}',
                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: onShowLogin,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.green,
                    ),
                    child: Text(isLoggedIn ? 'Switch Account' : 'Login / Register'),
                  ),
                ],
              ),
            ),

            // Menu items from config
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: _menuActions.map((action) => _buildMenuItem(action, context)).toList(),
              ),
            ),

            // Static items
            const Divider(),
            if (onLogout != null)
              ListTile(
                leading: const Icon(Icons.logout, color: Colors.red),
                title: const Text('Logout', style: TextStyle(color: Colors.red)),
                onTap: onLogout,
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItem(ActionConfig action, BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(_getMenuIcon(action.icon), color: Colors.green),
        title: Text(action.label),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => VNextActionDispatcher.dispatch(context, action.actionKey, params: action.params),
      ),
    );
  }
}

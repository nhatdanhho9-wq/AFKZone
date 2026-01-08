import 'package:flutter/material.dart';
import '../models/ui_config.dart';
import '../actions/action_dispatcher.dart';

/// Device Tab - Remote control entry point with quick actions
class DeviceTab extends StatefulWidget {
  final UiConfig? config;

  const DeviceTab({Key? key, this.config}) : super(key: key);

  @override
  State<DeviceTab> createState() => _DeviceTabState();
}

class _DeviceTabState extends State<DeviceTab> {
  final _remoteIdController = TextEditingController();

  List<ActionConfig> get _quickActions {
    final config = widget.config;
    if (config?.content?.device == null) return [];
    
    return config!.content!.device!.quickActionIds
        .map((id) => config.getActionById(id))
        .where((a) => a != null)
        .cast<ActionConfig>()
        .toList();
  }

  IconData _getActionIcon(String iconKey) {
    switch (iconKey) {
      case 'recent': return Icons.history;
      case 'favorite': return Icons.star;
      case 'share_screen': return Icons.screen_share;
      case 'contacts': return Icons.contacts;
      case 'scan_qr': return Icons.qr_code_scanner;
      default: return Icons.circle;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AFK Zone'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Remote ID input
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    const Icon(Icons.devices_other, size: 48, color: Colors.green),
                    const SizedBox(height: 16),
                    const Text(
                      'Remote Connection',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _remoteIdController,
                      decoration: InputDecoration(
                        labelText: 'Device ID',
                        hintText: 'Enter remote device ID',
                        prefixIcon: const Icon(Icons.computer),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      keyboardType: TextInputType.text,
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () {
                          final remoteId = _remoteIdController.text.trim();
                          if (remoteId.isNotEmpty) {
                            VNextActionDispatcher.dispatch(
                              context,
                              'connect_to_remote',
                              params: {'remote_id': remoteId},
                            );
                          }
                        },
                        icon: const Icon(Icons.play_arrow),
                        label: const Text('Connect'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Quick Actions Row
            if (_quickActions.isNotEmpty) ...[
              const Text(
                'Quick Actions',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: _quickActions.map((action) => _buildQuickAction(action)).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildQuickAction(ActionConfig action) {
    return InkWell(
      onTap: () => VNextActionDispatcher.dispatch(context, action.actionKey, params: action.params),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(_getActionIcon(action.icon), color: Colors.green, size: 28),
            ),
            const SizedBox(height: 8),
            Text(action.label, style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }
}

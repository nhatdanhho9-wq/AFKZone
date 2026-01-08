import 'package:flutter/material.dart';
import '../models/ui_config.dart';
import '../actions/action_dispatcher.dart';
import '../services/remote_service.dart';
import 'remote_session.dart';
import 'pending_requests.dart';

/// Device Tab - Remote control entry point with connect flow
class DeviceTab extends StatefulWidget {
  final UiConfig? config;

  const DeviceTab({Key? key, this.config}) : super(key: key);

  @override
  State<DeviceTab> createState() => _DeviceTabState();
}

class _DeviceTabState extends State<DeviceTab> {
  final _remoteIdController = TextEditingController();
  bool _isConnecting = false;
  String? _pendingRequestId;

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
      case 'pending': return Icons.pending_actions;
      default: return Icons.circle;
    }
  }

  /// Detect if input is share token (6 chars, uppercase) or device ID
  bool _isShareToken(String input) {
    return input.length == 6 && input == input.toUpperCase();
  }

  /// Handle connect button press
  Future<void> _handleConnect() async {
    final input = _remoteIdController.text.trim();
    if (input.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter device ID or share token')),
      );
      return;
    }

    setState(() => _isConnecting = true);

    RemoteRequestResult result;
    
    if (_isShareToken(input)) {
      // Share token flow
      result = await RemoteService.requestByToken(input);
    } else {
      // Device ID flow
      result = await RemoteService.requestByDevice(input);
    }

    if (result.success) {
      _pendingRequestId = result.requestId;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Request sent! Waiting for approval...')),
      );
      
      // Start polling for approval (in production use WebSocket)
      _pollForApproval();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Request failed: ${result.error}')),
      );
      setState(() => _isConnecting = false);
    }
  }

  /// Poll for approval status
  Future<void> _pollForApproval() async {
    // Simple polling - in production this would be via WebSocket
    for (int i = 0; i < 60; i++) {
      await Future.delayed(const Duration(seconds: 2));
      
      if (!mounted) return;
      
      // Check if session was approved (simplified - real impl would check status)
      // For now, just show pending dialog
      if (i == 0) {
        _showPendingDialog();
      }
    }
    
    if (mounted) {
      setState(() {
        _isConnecting = false;
        _pendingRequestId = null;
      });
    }
  }

  void _showPendingDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Waiting for Approval'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: Colors.green),
            const SizedBox(height: 16),
            Text('Request: ${_pendingRequestId?.substring(0, 8) ?? ''}...'),
            const SizedBox(height: 8),
            const Text('Waiting for device owner to approve...'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              setState(() {
                _isConnecting = false;
                _pendingRequestId = null;
              });
            },
            child: const Text('Cancel'),
          ),
          // Simulate approval for testing
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              _navigateToSession('test-session-id');
            },
            child: const Text('(Test) Simulate Approve'),
          ),
        ],
      ),
    );
  }

  void _navigateToSession(String sessionId) {
    setState(() {
      _isConnecting = false;
      _pendingRequestId = null;
    });
    
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => RemoteSessionScreen(sessionId: sessionId),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AFK Zone'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        centerTitle: true,
        actions: [
          // Pending requests button
          IconButton(
            icon: const Icon(Icons.pending_actions),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const PendingRequestsScreen()),
            ),
            tooltip: 'Pending Requests',
          ),
        ],
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
                      enabled: !_isConnecting,
                      decoration: InputDecoration(
                        labelText: 'Device ID or Share Token',
                        hintText: 'e.g., UF4PCE or device-id',
                        prefixIcon: const Icon(Icons.computer),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        helperText: 'Enter 6-char token for share, or device ID for trusted',
                      ),
                      keyboardType: TextInputType.text,
                      textCapitalization: TextCapitalization.characters,
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _isConnecting ? null : _handleConnect,
                        icon: _isConnecting 
                            ? const SizedBox(
                                width: 16, 
                                height: 16, 
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Icon(Icons.play_arrow),
                        label: Text(_isConnecting ? 'Connecting...' : 'Connect'),
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
            
            const SizedBox(height: 24),
            
            // Share Token section
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Allow Remote Access',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Generate a share token to let others connect to this device.',
                      style: TextStyle(color: Colors.grey),
                    ),
                    const SizedBox(height: 12),
                    ElevatedButton.icon(
                      onPressed: _createShareToken,
                      icon: const Icon(Icons.share),
                      label: const Text('Generate Share Token'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _createShareToken() async {
    final result = await RemoteService.createShareToken(validSeconds: 300);
    if (result.success && result.token != null) {
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Share Token'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Share this token with others:'),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  result.token!,
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 4,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Text('Valid for 5 minutes', style: TextStyle(color: Colors.grey)),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to create token: ${result.error}')),
      );
    }
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

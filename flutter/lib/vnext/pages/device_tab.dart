import 'package:flutter/material.dart';
import '../models/ui_config.dart';
import '../actions/action_dispatcher.dart';
import '../services/remote_service.dart';
import '../services/device_service.dart';
import '../services/auth_service.dart';
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
  String? _claimToken;
  bool _devicesLoading = false;
  bool _isLoggedIn = false;
  List<Device> _devices = [];

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

  @override
  void initState() {
    super.initState();
    _refreshDevices();
  }

  Future<void> _refreshDevices() async {
    final loggedIn = await AuthService.isLoggedIn();
    if (!loggedIn) {
      setState(() {
        _devices = [];
        _devicesLoading = false;
        _isLoggedIn = false;
      });
      return;
    }
    setState(() {
      _devicesLoading = true;
      _isLoggedIn = true;
    });
    final list = await DeviceService.getDevices();
    if (!mounted) return;
    setState(() {
      _devices = list;
      _devicesLoading = false;
    });
  }

  /// Detect if input is share token (6 chars, uppercase) or device ID
  bool _isShareToken(String input) {
    final v = input.trim().toUpperCase();
    if (v.length < 6 || v.length > 8) return false;
    final re = RegExp(r'^[A-Z0-9]{6,8}$');
    return re.hasMatch(v);
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
      _claimToken = result.claimToken;

      // If auto-approved, navigate immediately (trusted flow)
      if ((result.status ?? '') == 'approved' && result.sessionId != null) {
        // For auto-approved sessions, we still need controller_token (not returned here).
        // Use claim API to fetch it.
        await _pollForApproval(showDialogFirst: false);
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Request sent! Waiting for approval...')),
      );
      
      // Start polling for approval (in production use WebSocket)
      _pollForApproval(showDialogFirst: true);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Request failed: ${result.error}')),
      );
      setState(() => _isConnecting = false);
    }
  }

  /// Poll for approval status
  Future<void> _pollForApproval({required bool showDialogFirst}) async {
    // Simple polling - in production this would be via WebSocket
    for (int i = 0; i < 60; i++) {
      await Future.delayed(const Duration(seconds: 2));
      
      if (!mounted) return;
      
      if (i == 0 && showDialogFirst) {
        _showPendingDialog();
      }

      final requestId = _pendingRequestId;
      final claimToken = _claimToken;
      if (requestId == null || claimToken == null) continue;

      final claim = await RemoteService.claim(requestId: requestId, claimToken: claimToken);
      if (claim.ok && claim.status == 'approved' && claim.sessionId != null && claim.controllerToken != null) {
        if (mounted) {
          Navigator.of(context, rootNavigator: true).maybePop();
          _navigateToSession(claim.sessionId!, wsToken: claim.controllerToken!);
        }
        return;
      }
    }
    
    if (mounted) {
      setState(() {
        _isConnecting = false;
        _pendingRequestId = null;
        _claimToken = null;
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
            onPressed: () async {
              // Call POST /remote/cancel + close dialog immediately
              final requestId = _pendingRequestId;
              Navigator.of(context).pop();
              setState(() {
                _isConnecting = false;
                _pendingRequestId = null;
              });
              if (requestId != null) {
                await RemoteService.cancelRequest(requestId);
                print('[DeviceTab] Cancelled request: $requestId');
              }
            },
            child: const Text('Cancel', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  void _navigateToSession(String sessionId, {required String wsToken}) {
    setState(() {
      _isConnecting = false;
      _pendingRequestId = null;
      _claimToken = null;
    });
    
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => RemoteSessionScreen(sessionId: sessionId, wsToken: wsToken),
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

            // My Devices section (same-account devices)
            _buildMyDevices(),
          ],
        ),
      ),
    );
  }

  Widget _buildMyDevices() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'My Devices',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                IconButton(
                  onPressed: _devicesLoading ? null : _refreshDevices,
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Refresh',
                ),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Login to see all devices under your account. Tap a device to remote; use ⋮ to Share client.',
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 12),

            if (_devicesLoading)
              const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()))
            else if (_devices.isEmpty)
              Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  children: [
                    Icon(
                      _isLoggedIn ? Icons.devices : Icons.login,
                      size: 40,
                      color: Colors.grey.shade400,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _isLoggedIn
                          ? 'No devices registered yet.\nThis device will appear after sync.'
                          : 'Login required to view your devices.',
                      style: TextStyle(color: Colors.grey.shade600),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              )
            else
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.6,
                ),
                itemCount: _devices.length,
                itemBuilder: (context, idx) => _buildDeviceTile(_devices[idx]),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDeviceTile(Device d) {
    final isThis = (DeviceService.deviceId != null && d.id == DeviceService.deviceId);
    return InkWell(
      onTap: () {
        if (isThis) {
          // Block self-remote with dialog
          showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              title: const Text('Cannot Connect'),
              content: const Text('Cannot connect to this device - you are already on it.'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(ctx).pop(),
                  child: const Text('OK'),
                ),
              ],
            ),
          );
          return;
        }
        _remoteIdController.text = d.id;
        _handleConnect();
      },
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isThis ? Colors.green : Colors.grey.shade200,
            width: isThis ? 2 : 1,
          ),
          color: isThis ? Colors.green.shade50 : Colors.white,
        ),
        child: Row(
          children: [
            Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: d.online ? Colors.green : Colors.grey,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    d.name.isNotEmpty ? d.name : 'Device',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    isThis ? 'This device' : (d.online ? 'Online' : 'Offline'),
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                  ),
                ],
              ),
            ),
            // RustDesk-style 3-dots menu
            PopupMenuButton<String>(
              icon: const Icon(Icons.more_vert, size: 20),
              onSelected: (v) => _handleDeviceMenuAction(v, d, isThis),
              itemBuilder: (ctx) => [
                PopupMenuItem(
                  value: 'connect',
                  enabled: !isThis,
                  child: Row(
                    children: [
                      Icon(Icons.play_arrow, size: 18, color: isThis ? Colors.grey : Colors.green),
                      const SizedBox(width: 8),
                      Text('Connect', style: TextStyle(color: isThis ? Colors.grey : null)),
                    ],
                  ),
                ),
                const PopupMenuDivider(),
                const PopupMenuItem(
                  value: 'rename',
                  child: Row(
                    children: [Icon(Icons.edit, size: 18), SizedBox(width: 8), Text('Rename')],
                  ),
                ),
                PopupMenuItem(
                  value: 'favorite',
                  child: Row(
                    children: [
                      Icon(d.isFavorite ? Icons.star : Icons.star_border, size: 18, color: Colors.amber),
                      const SizedBox(width: 8),
                      Text(d.isFavorite ? 'Remove Favorite' : 'Add to Favorites'),
                    ],
                  ),
                ),
                PopupMenuItem(
                  value: 'relay',
                  child: Row(
                    children: [
                      Icon(d.alwaysRelay ? Icons.check_box : Icons.check_box_outline_blank, size: 18),
                      const SizedBox(width: 8),
                      const Text('Always connect via relay'),
                    ],
                  ),
                ),
                const PopupMenuDivider(),
                const PopupMenuItem(
                  value: 'share_client',
                  child: Row(
                    children: [Icon(Icons.share, size: 18), SizedBox(width: 8), Text('Share client')],
                  ),
                ),
                const PopupMenuItem(
                  value: 'copy_id',
                  child: Row(
                    children: [Icon(Icons.copy, size: 18), SizedBox(width: 8), Text('Copy device ID')],
                  ),
                ),
                const PopupMenuDivider(),
                PopupMenuItem(
                  value: 'delete',
                  enabled: !isThis,
                  child: Row(
                    children: [
                      Icon(Icons.delete_outline, size: 18, color: isThis ? Colors.grey : Colors.red),
                      const SizedBox(width: 8),
                      Text('Clear client', style: TextStyle(color: isThis ? Colors.grey : Colors.red)),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleDeviceMenuAction(String action, Device d, bool isThis) async {
    switch (action) {
      case 'connect':
        if (isThis) {
          showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              title: const Text('Cannot Connect'),
              content: const Text('Cannot connect to this device - you are already on it.'),
              actions: [TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('OK'))],
            ),
          );
        } else {
          _remoteIdController.text = d.id;
          _handleConnect();
        }
        break;
      case 'rename':
        _showRenameDialog(d);
        break;
      case 'favorite':
        await _toggleFavorite(d);
        break;
      case 'relay':
        await _toggleAlwaysRelay(d);
        break;
      case 'share_client':
        await _shareClient(d);
        break;
      case 'copy_id':
        _remoteIdController.text = d.id;
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Device ID copied to input')));
        break;
      case 'delete':
        if (!isThis) {
          await _deleteDevice(d);
        }
        break;
    }
  }

  void _showRenameDialog(Device d) {
    final controller = TextEditingController(text: d.name);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Rename Device'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(labelText: 'Device Name', border: OutlineInputBorder()),
          autofocus: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('CANCEL')),
          ElevatedButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              final newName = controller.text.trim();
              if (newName.isNotEmpty && newName != d.name) {
                final success = await DeviceService.updateDevice(d.id, name: newName);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(success ? 'Device renamed' : 'Failed to rename')),
                  );
                  if (success) _refreshDevices();
                }
              }
            },
            child: const Text('SAVE'),
          ),
        ],
      ),
    );
  }

  Future<void> _toggleFavorite(Device d) async {
    final success = await DeviceService.updateDevice(d.id, isFavorite: !d.isFavorite);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(success ? (d.isFavorite ? 'Removed from favorites' : 'Added to favorites') : 'Failed')),
      );
      if (success) _refreshDevices();
    }
  }

  Future<void> _toggleAlwaysRelay(Device d) async {
    final success = await DeviceService.updateDevice(d.id, alwaysRelay: !d.alwaysRelay);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(success ? 'Relay setting updated' : 'Failed')),
      );
      if (success) _refreshDevices();
    }
  }

  Future<void> _deleteDevice(Device d) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clear Client'),
        content: Text('Are you sure you want to remove "${d.name.isNotEmpty ? d.name : d.id}" from your devices?'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('CANCEL')),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('DELETE', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      final success = await DeviceService.deleteDevice(d.id);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(success ? 'Device removed' : 'Failed to remove device')),
        );
        if (success) _refreshDevices();
      }
    }
  }

  Future<void> _shareClient(Device d) async {
    // For now share = generate guest token for this device (as requested: per-device, not “this device” only).
    final result = await RemoteService.createShareTokenForDevice(deviceId: d.id, expiresHours: 24, maxUses: 1);
    if (!mounted) return;
    if (result.success && result.token != null && result.token!.isNotEmpty) {
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Share Client Token'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Device: ${d.name}'),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  result.token!,
                  style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: 3),
                ),
              ),
              const SizedBox(height: 8),
              const Text('Share this token to request access (owner must approve).', style: TextStyle(color: Colors.grey)),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Close')),
          ],
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Share client failed: ${result.error ?? 'unknown'}')),
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

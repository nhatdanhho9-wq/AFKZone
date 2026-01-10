import 'package:flutter/material.dart';
import 'pages/device_tab.dart';
import 'pages/discover_tab.dart';
import 'pages/purchase_tab.dart';
import 'pages/me_tab.dart';
import 'pages/login_screen.dart';
import 'pages/remote_session.dart';
import 'pages/pending_requests.dart';
import 'models/ui_config.dart';
import 'services/config_service.dart';
import 'services/auth_service.dart';
import 'services/device_service.dart';
import 'services/remote_service.dart';

/// vNext App - Server-driven mobile UI with auth flow
/// Tabs rendered from /public/mobile-ui-config
class VNextApp extends StatefulWidget {
  const VNextApp({Key? key}) : super(key: key);

  @override
  State<VNextApp> createState() => _VNextAppState();
}

class _VNextAppState extends State<VNextApp> {
  int _currentIndex = 0;
  UiConfig? _config;
  bool _isLoading = true;
  bool _isLoggedIn = false;
  String? _error;
  // Owner/host background polling (MVP): show popup + attach to sessions when approved.
  bool _pendingWatcherStarted = false;
  bool _pendingDialogOpen = false;

  @override
  void initState() {
    super.initState();
    _loadApp();
  }

  Future<void> _loadApp() async {
    setState(() => _isLoading = true);
    try {
      final config = await ConfigService.loadConfig();
      final loggedIn = await AuthService.isLoggedIn();

      setState(() {
        _config = config;
        _isLoggedIn = loggedIn;
        _isLoading = false;
      });

      // Only register device + heartbeat when logged in (needs JWT).
      if (loggedIn) {
        await _initializeAfterLogin();
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
        _config = UiConfig.defaults();
      });
    }
  }

  Future<void> _initializeAfterLogin() async {
    // Register device and start heartbeat
    await DeviceService.registerDevice(deviceName: 'vNext-Mobile', platform: 'android');
    DeviceService.startHeartbeat();
    _startPendingWatcher();
    
    // Start host attach polling (for 3-device flow)
    DeviceService.startHostAttachPolling(
      onSessionReady: _onHostSessionReady,
    );
  }

  /// Called when this device needs to act as host (approved by owner on another device)
  void _onHostSessionReady(String sessionId, String hostToken) {
    print('[VNextApp] Host session ready: $sessionId');
    // Navigate to host session screen
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => RemoteSessionScreen(
          sessionId: sessionId,
          wsToken: hostToken,
          isHost: true,
        ),
      ),
    );
  }

  Future<void> _showLogin() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => LoginScreen(
          onLoginSuccess: () async {
            // Pop login screen first, then init.
            Navigator.of(context).pop();
            await _onLoginSuccess();
          },
        ),
      ),
    );
  }

  Future<void> _onLoginSuccess() async {
    setState(() => _isLoggedIn = true);
    await _initializeAfterLogin();
  }

  void _onLogout() async {
    // Stop all background services
    DeviceService.stopHeartbeat();
    DeviceService.stopHostAttachPolling();
    
    // Clear auth and caches
    await AuthService.logout();
    
    // Clear device cache (for account switch)
    await DeviceService.clearDeviceCache();
    
    setState(() {
      _isLoggedIn = false;
    });
    _pendingWatcherStarted = false;
    _pendingDialogOpen = false;
    print('[VNextApp] Logged out and cleared all caches');
  }

  // Track shown pending notifications to avoid duplicates
  final Set<String> _shownPendingNotifications = {};

  void _startPendingWatcher() {
    if (_pendingWatcherStarted) return;
    _pendingWatcherStarted = true;

    // Lightweight loop: checks for pending requests and attaches to approved sessions (host).
    Future<void>(() async {
      while (mounted && _isLoggedIn) {
        try {
          // 1) Check for pending requests for this account and show notification
          final pending = await RemoteService.getPending();
          final myDeviceId = DeviceService.deviceId;
          for (final req in pending) {
            if (!_shownPendingNotifications.contains(req.requestId)) {
              _shownPendingNotifications.add(req.requestId);
              if (mounted) {
                // If this device is the share creator (targetDeviceId) → popup approve dialog
                // Else → just show badge notification
                final isShareCreator = myDeviceId != null && 
                    req.targetDeviceId != null && 
                    req.targetDeviceId == myDeviceId;
                if (isShareCreator) {
                  _showApproveDialog(req);
                } else {
                  _showPendingBadge(req);
                }
              }
            }
          }

          // 2) Host attach loop: try to attach if a session is pending for this device.
          if (myDeviceId != null) {
            final attach = await RemoteService.hostAttach(hostDeviceId: myDeviceId);
            if (attach.success && attach.sessionId != null && attach.hostToken != null) {
              if (!_pendingDialogOpen) {
                _pendingDialogOpen = true;
                if (mounted) {
                  // Auto-open host session screen to trigger system screen-share prompt.
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => RemoteSessionScreen(
                        sessionId: attach.sessionId!,
                        isHost: true,
                        wsToken: attach.hostToken!,
                      ),
                    ),
                  ).then((_) => _pendingDialogOpen = false);
                }
              }
            }
          }

          await Future.delayed(const Duration(seconds: 3));
        } catch (_) {
          await Future.delayed(const Duration(seconds: 5));
        }
      }
    });
  }

  /// Popup approve dialog for share creator device
  void _showApproveDialog(PendingRequest req) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.person_add, color: Colors.green),
            const SizedBox(width: 12),
            const Text('Remote Access Request'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Device "${req.requesterDeviceId?.substring(0, 8) ?? "unknown"}..." is requesting access.',
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              'Created: ${req.createdAt}',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              final success = await RemoteService.reject(req.requestId);
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(success ? 'Request rejected' : 'Failed to reject')),
                );
              }
            },
            child: const Text('REJECT', style: TextStyle(color: Colors.red)),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              final result = await RemoteService.approve(req.requestId);
              if (mounted) {
                if (result.success) {
                  // NEW CONTRACT: approve does NOT return host_token
                  // Host will get host_token from POST /remote/host-ready AFTER enable_screen_capture
                  print('[VNextApp] Approve success (new contract): session=${result.sessionId}, requestId=${req.requestId}');
                  print('[VNextApp] NOTE: host_token will come from /remote/host-ready, NOT from approve');
                  
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Request approved - waiting for screen capture...'), backgroundColor: Colors.green),
                  );
                  // Navigate to RemoteSessionScreen WITHOUT token
                  // Host will connect WS, receive enable_screen_capture, call host-ready, THEN get token
                  print('[VNextApp] Navigating to RemoteSessionScreen as HOST for session=${result.sessionId}, requestId=${req.requestId}');
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => RemoteSessionScreen(
                        sessionId: result.sessionId ?? req.requestId,
                        isHost: true,
                        wsToken: null, // Token comes from host-ready, not approve
                        requestId: req.requestId, // Pass requestId for host-ready call
                      ),
                    ),
                  );
                } else if (result.error?.contains('password') == true) {
                  // Server requires password → show password dialog
                  _showPasswordDialog(req);
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Failed: ${result.error}')),
                  );
                }
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            child: const Text('APPROVE', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  /// Badge-only notification for non-share-creator devices
  void _showPendingBadge(PendingRequest req) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.info_outline, color: Colors.white),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'New remote request pending (approve on device that created the share token)',
                style: const TextStyle(fontSize: 12),
              ),
            ),
          ],
        ),
        backgroundColor: Colors.blue.shade700,
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 4),
      ),
    );
  }

  /// Password dialog for dt2 when server requires password
  void _showPasswordDialog(PendingRequest req) {
    final passwordController = TextEditingController();
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('Password Required'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Enter the connection password to approve this request.'),
            const SizedBox(height: 16),
            TextField(
              controller: passwordController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('CANCEL'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              final password = passwordController.text.trim();
              if (password.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Password cannot be empty')),
                );
                return;
              }
              // TODO: Call approve with password when backend supports it
              // For now, show pending
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Password submitted (backend integration pending)')),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            child: const Text('SUBMIT', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  List<TabConfig> get _visibleTabs {
    if (_config == null) return [];
    return _config!.tabs.where((t) => t.visible).toList();
  }

  Widget _buildTabPage(String tabId) {
    switch (tabId) {
      case 'device':
        return DeviceTab(config: _config);
      case 'discover':
        return DiscoverTab(config: _config);
      case 'purchase':
        return PurchaseTab(config: _config);
      case 'me':
        return MeTab(
          config: _config,
          isLoggedIn: _isLoggedIn,
          onShowLogin: _showLogin,
          onLogout: _isLoggedIn ? _onLogout : null,
        );
      default:
        return Center(child: Text('Unknown tab: $tabId'));
    }
  }

  IconData _getTabIcon(String iconKey) {
    switch (iconKey) {
      case 'tab_device':
        return Icons.devices;
      case 'tab_discover':
        return Icons.explore;
      case 'tab_purchase':
        return Icons.shopping_cart;
      case 'tab_me':
        return Icons.person;
      default:
        return Icons.circle;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(color: Colors.green),
              SizedBox(height: 16),
              Text('Loading...'),
            ],
          ),
        ),
      );
    }

    final tabs = _visibleTabs;
    if (tabs.isEmpty) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Config Error: ${_error ?? "No tabs configured"}'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loadApp,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: tabs.map((t) => _buildTabPage(t.id)).toList(),
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        selectedItemColor: Colors.green,
        unselectedItemColor: Colors.grey,
        items: tabs.map((tab) => BottomNavigationBarItem(
          icon: Icon(_getTabIcon(tab.icon)),
          label: tab.label,
        )).toList(),
      ),
    );
  }

  @override
  void dispose() {
    DeviceService.stopHeartbeat();
    super.dispose();
  }
}

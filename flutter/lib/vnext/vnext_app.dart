import 'package:flutter/material.dart';
import 'pages/device_tab.dart';
import 'pages/discover_tab.dart';
import 'pages/purchase_tab.dart';
import 'pages/me_tab.dart';
import 'pages/login_screen.dart';
import 'pages/remote_session.dart';
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
    DeviceService.stopHeartbeat();
    await AuthService.logout();
    setState(() {
      _isLoggedIn = false;
    });
    _pendingWatcherStarted = false;
  }

  void _startPendingWatcher() {
    if (_pendingWatcherStarted) return;
    _pendingWatcherStarted = true;

    // Lightweight loop: checks for pending requests and attaches to approved sessions (host).
    Future<void>(() async {
      while (mounted && _isLoggedIn) {
        try {
          // 1) If there is a pending request for this account, show a popup on the device that is the TARGET.
          final pending = await RemoteService.getPending();
          final myDeviceId = DeviceService.deviceId;
          final forThisDevice = myDeviceId == null
              ? null
              : pending.where((r) => r.requesterDeviceId != null).toList();

          // NOTE: Backend pending list doesn't include target_device_id per item in our client model.
          // Keep MVP: rely on user opening Pending screen for approvals.
          // Future: extend model + filter only requests targeting this device.

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

import 'package:flutter/material.dart';
import 'pages/device_tab.dart';
import 'pages/discover_tab.dart';
import 'pages/purchase_tab.dart';
import 'pages/me_tab.dart';
import 'models/ui_config.dart';
import 'services/config_service.dart';

/// vNext App - Server-driven mobile UI
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
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    setState(() => _isLoading = true);
    try {
      final config = await ConfigService.loadConfig();
      setState(() {
        _config = config;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
        // Use baked-in defaults on error
        _config = UiConfig.defaults();
      });
    }
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
        return MeTab(config: _config);
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
        body: Center(child: CircularProgressIndicator()),
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
                onPressed: _loadConfig,
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
}

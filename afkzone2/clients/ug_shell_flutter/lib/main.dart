import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'actions.dart';
import 'ui_config.dart';

const _defaultBaseUrl = String.fromEnvironment('AFK_API_BASE', defaultValue: 'http://localhost:8081');

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const AfkZoneApp());
}

class AfkZoneApp extends StatefulWidget {
  const AfkZoneApp({super.key});

  @override
  State<AfkZoneApp> createState() => _AfkZoneAppState();
}

class _AfkZoneAppState extends State<AfkZoneApp> {
  UiConfigEnvelope _config = bakedDefaultConfig();
  bool _loading = true;
  int _selectedIndex = 0;
  Timer? _refreshTimer;

  final Map<String, ActionDef> _actionsById = {};

  @override
  void initState() {
    super.initState();
    _boot();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _boot() async {
    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getString('ui_config_lkg');
    if (cached != null) {
      try {
        final jsonMap = jsonDecode(cached) as Map<String, dynamic>;
        final env = UiConfigEnvelope.fromJson(jsonMap);
        if (!env.killSwitch) {
          setState(() => _config = env);
        }
      } catch (_) {
        // ignore
      }
    }
    await _refreshConfig();
    setState(() => _loading = false);
    _scheduleRefresh();
  }

  Future<void> _refreshConfig() async {
    try {
      final res = await http
          .get(Uri.parse('$_defaultBaseUrl/public/mobile-ui-config'), headers: {'Cache-Control': 'no-cache'})
          .timeout(const Duration(seconds: 8));
      if (res.statusCode != 200) return;
      final jsonMap = jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      final env = UiConfigEnvelope.fromJson(jsonMap);
      if (env.killSwitch) return;

      // Verify signature; if fails, ignore update.
      final ok = await UiConfigVerifier.verify(env);
      if (!ok) return;

      // Accept only monotonic revision.
      if (env.revision < _config.revision) return;

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('ui_config_lkg', jsonEncode(jsonMap));

      setState(() => _config = env);
      _rebuildActionIndex();
      _scheduleRefresh();
    } catch (_) {
      // keep LKG/baked
    }
  }

  void _scheduleRefresh() {
    _refreshTimer?.cancel();
    final ttl = _config.ttlSeconds;
    final seconds = (ttl / 2).clamp(30, 3600).toInt();
    _refreshTimer = Timer.periodic(Duration(seconds: seconds), (_) => _refreshConfig());
  }

  void _rebuildActionIndex() {
    _actionsById.clear();
    final actions = (_config.payload['actions'] as List?) ?? const [];
    for (final a in actions) {
      if (a is Map<String, dynamic>) {
        final def = ActionDef.fromJson(a);
        if (def != null) _actionsById[def.id] = def;
      } else if (a is Map) {
        final def = ActionDef.fromJson(Map<String, dynamic>.from(a));
        if (def != null) _actionsById[def.id] = def;
      }
    }
  }

  List<Map<String, dynamic>> _visibleTabs() {
    final tabs = (_config.payload['tabs'] as List?) ?? const [];
    final out = <Map<String, dynamic>>[];
    for (final t in tabs) {
      if (t is Map) {
        final m = Map<String, dynamic>.from(t);
        if (m['visible'] == true) out.add(m);
      }
    }
    return out;
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AFK Zone',
      theme: ThemeData.dark(useMaterial3: true),
      home: Scaffold(
        appBar: AppBar(
          title: const Text('AFK Zone'),
          actions: [
            IconButton(
              onPressed: _refreshConfig,
              icon: const Icon(Icons.refresh),
              tooltip: 'Refresh config',
            )
          ],
        ),
        body: _loading ? _buildLoading() : _buildBody(),
        bottomNavigationBar: _loading ? null : _buildBottomBar(),
      ),
    );
  }

  Widget _buildLoading() {
    return const Center(child: CircularProgressIndicator());
  }

  Widget _buildBody() {
    final tabs = _visibleTabs();
    if (tabs.isEmpty) return const Center(child: Text('No tabs'));
    final tab = tabs[_selectedIndex.clamp(0, tabs.length - 1)];
    final routeType = tab['route_type'] as String? ?? '';
    switch (routeType) {
      case 'tab_device':
        return DeviceTab(config: _config, actionsById: _actionsById);
      case 'tab_discover':
        return DiscoverTab(config: _config, actionsById: _actionsById);
      case 'tab_purchase':
        return PurchaseTab(config: _config, actionsById: _actionsById);
      case 'tab_me':
        return MeTab(config: _config, actionsById: _actionsById);
      default:
        return Center(child: Text('Unsupported route_type: $routeType'));
    }
  }

  Widget _buildBottomBar() {
    final tabs = _visibleTabs();
    return NavigationBar(
      selectedIndex: _selectedIndex,
      onDestinationSelected: (i) => setState(() => _selectedIndex = i),
      destinations: [
        for (final t in tabs)
          NavigationDestination(
            icon: Icon(iconFromKey(t['icon']?.toString() ?? 'circle')),
            label: t['label']?.toString() ?? t['id']?.toString() ?? 'tab',
          )
      ],
    );
  }
}

class DeviceTab extends StatelessWidget {
  final UiConfigEnvelope config;
  final Map<String, ActionDef> actionsById;

  const DeviceTab({super.key, required this.config, required this.actionsById});

  @override
  Widget build(BuildContext context) {
    final content = Map<String, dynamic>.from(config.payload['content'] ?? const {});
    final device = Map<String, dynamic>.from(content['device'] ?? const {});
    final ids = (device['quick_action_ids'] as List?)?.map((e) => e.toString()).toList() ?? const <String>[];

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Remote ID', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          TextField(
            decoration: InputDecoration(
              hintText: 'Enter Remote ID',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: () {},
              child: const Text('Connect'),
            ),
          ),
          const SizedBox(height: 18),
          const Text('Quick actions', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              for (final id in ids)
                _ActionChip(
                  action: actionsById[id],
                  onTap: (a) => dispatchAction(context: context, action: a),
                )
            ],
          ),
        ],
      ),
    );
  }
}

class DiscoverTab extends StatelessWidget {
  final UiConfigEnvelope config;
  final Map<String, ActionDef> actionsById;

  const DiscoverTab({super.key, required this.config, required this.actionsById});

  @override
  Widget build(BuildContext context) {
    final content = Map<String, dynamic>.from(config.payload['content'] ?? const {});
    final discover = Map<String, dynamic>.from(content['discover'] ?? const {});
    final sections = (discover['sections'] as List?) ?? const [];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final s in sections)
          if (s is Map)
            _DiscoverSection(
              section: Map<String, dynamic>.from(s),
              actionsById: actionsById,
            ),
        if (sections.isEmpty) const Text('No discover content.'),
      ],
    );
  }
}

class PurchaseTab extends StatelessWidget {
  final UiConfigEnvelope config;
  final Map<String, ActionDef> actionsById;

  const PurchaseTab({super.key, required this.config, required this.actionsById});

  @override
  Widget build(BuildContext context) {
    final content = Map<String, dynamic>.from(config.payload['content'] ?? const {});
    final purchase = Map<String, dynamic>.from(content['purchase'] ?? const {});
    final tiers = (purchase['tiers'] as List?) ?? const [];
    final regions = (purchase['regions'] as List?) ?? const [];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Purchase', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        if (tiers.isNotEmpty) ...[
          const Text('Tiers', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            children: [
              for (final t in tiers)
                if (t is Map) Chip(label: Text(t['label']?.toString() ?? t['id']?.toString() ?? 'tier')),
            ],
          ),
          const SizedBox(height: 18),
        ],
        const Text('Server selection', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        for (final r in regions)
          if (r is Map)
            ListTile(
              title: Text(r['label']?.toString() ?? r['code']?.toString() ?? 'region'),
              subtitle: Text(r['probe_host']?.toString() ?? ''),
              trailing: const Icon(Icons.chevron_right),
            ),
        if (regions.isEmpty) const Text('No regions in config.'),
      ],
    );
  }
}

class MeTab extends StatelessWidget {
  final UiConfigEnvelope config;
  final Map<String, ActionDef> actionsById;

  const MeTab({super.key, required this.config, required this.actionsById});

  @override
  Widget build(BuildContext context) {
    final content = Map<String, dynamic>.from(config.payload['content'] ?? const {});
    final me = Map<String, dynamic>.from(content['me'] ?? const {});
    final ids = (me['menu_action_ids'] as List?)?.map((e) => e.toString()).toList() ?? const <String>[];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Me', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        for (final id in ids)
          _ActionTile(
            action: actionsById[id],
            onTap: (a) => dispatchAction(context: context, action: a),
          ),
        if (ids.isEmpty) const Text('No menu actions.'),
      ],
    );
  }
}

class _ActionChip extends StatelessWidget {
  final ActionDef? action;
  final void Function(ActionDef action) onTap;

  const _ActionChip({required this.action, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final a = action;
    if (a == null) return const Chip(label: Text('Unknown'));
    return ActionChip(
      avatar: Icon(iconFromKey(a.icon), size: 18),
      label: Text(a.label),
      onPressed: () => onTap(a),
    );
  }
}

class _ActionTile extends StatelessWidget {
  final ActionDef? action;
  final void Function(ActionDef action) onTap;

  const _ActionTile({required this.action, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final a = action;
    if (a == null) {
      return const ListTile(title: Text('Unknown action'));
    }
    return ListTile(
      leading: Icon(iconFromKey(a.icon)),
      title: Text(a.label),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => onTap(a),
    );
  }
}

class _DiscoverSection extends StatelessWidget {
  final Map<String, dynamic> section;
  final Map<String, ActionDef> actionsById;

  const _DiscoverSection({required this.section, required this.actionsById});

  @override
  Widget build(BuildContext context) {
    final title = section['title']?.toString() ?? 'Section';
    final cards = (section['cards'] as List?) ?? const [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        for (final c in cards)
          if (c is Map)
            Card(
              child: ListTile(
                title: Text(c['title']?.toString() ?? 'Card'),
                subtitle: Text(c['subtitle']?.toString() ?? ''),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  final actionId = c['action_id']?.toString();
                  final a = actionId == null ? null : actionsById[actionId];
                  if (a != null) {
                    dispatchAction(context: context, action: a);
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('No action for card')));
                  }
                },
              ),
            ),
        const SizedBox(height: 16),
      ],
    );
  }
}


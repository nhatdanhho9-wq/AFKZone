/// UI Config models for server-driven mobile UI
/// Based on mobile_ui_config.schema.json

class UiConfig {
  final int schemaVersion;
  final int revision;
  final String issuedAt;
  final int ttlSeconds;
  final bool killSwitch;
  final List<TabConfig> tabs;
  final List<RouteConfig> routes;
  final List<ActionConfig> actions;
  final ContentConfig? content;

  UiConfig({
    required this.schemaVersion,
    required this.revision,
    required this.issuedAt,
    required this.ttlSeconds,
    this.killSwitch = false,
    required this.tabs,
    required this.routes,
    required this.actions,
    this.content,
  });

  factory UiConfig.fromJson(Map<String, dynamic> json) {
    return UiConfig(
      schemaVersion: json['schema_version'] ?? 1,
      revision: json['revision'] ?? 1,
      issuedAt: json['issued_at'] ?? '',
      ttlSeconds: json['ttl_seconds'] ?? 300,
      killSwitch: json['kill_switch'] ?? false,
      tabs: (json['tabs'] as List?)?.map((t) => TabConfig.fromJson(t)).toList() ?? [],
      routes: (json['routes'] as List?)?.map((r) => RouteConfig.fromJson(r)).toList() ?? [],
      actions: (json['actions'] as List?)?.map((a) => ActionConfig.fromJson(a)).toList() ?? [],
      content: json['content'] != null ? ContentConfig.fromJson(json['content']) : null,
    );
  }

  /// Baked-in default config (fallback)
  factory UiConfig.defaults() {
    return UiConfig(
      schemaVersion: 1,
      revision: 0,
      issuedAt: DateTime.now().toIso8601String(),
      ttlSeconds: 300,
      killSwitch: false,
      tabs: [
        TabConfig(id: 'device', label: 'Device', icon: 'tab_device', visible: true, routeType: 'tab_device'),
        TabConfig(id: 'discover', label: 'Discover', icon: 'tab_discover', visible: true, routeType: 'tab_discover'),
        TabConfig(id: 'purchase', label: 'Purchase', icon: 'tab_purchase', visible: true, routeType: 'tab_purchase'),
        TabConfig(id: 'me', label: 'Me', icon: 'tab_me', visible: true, routeType: 'tab_me'),
      ],
      routes: [],
      actions: [
        ActionConfig(id: 'qa_recent', label: 'Recent', icon: 'recent', actionKey: 'open_recent'),
        ActionConfig(id: 'qa_fav', label: 'Favorites', icon: 'favorite', actionKey: 'open_favorites'),
        ActionConfig(id: 'qa_share', label: 'Share', icon: 'share_screen', actionKey: 'share_screen_start'),
      ],
      content: ContentConfig(
        device: DeviceContent(quickActionIds: ['qa_recent', 'qa_fav', 'qa_share']),
        discover: DiscoverContent(sections: []),
        purchase: PurchaseContent(tiers: [], regions: []),
        me: MeContent(menuActionIds: []),
      ),
    );
  }

  ActionConfig? getActionById(String id) {
    try {
      return actions.firstWhere((a) => a.id == id);
    } catch (_) {
      return null;
    }
  }
}

class TabConfig {
  final String id;
  final String label;
  final String icon;
  final bool visible;
  final String routeType;

  TabConfig({
    required this.id,
    required this.label,
    required this.icon,
    required this.visible,
    required this.routeType,
  });

  factory TabConfig.fromJson(Map<String, dynamic> json) {
    return TabConfig(
      id: json['id'] ?? '',
      label: json['label'] ?? '',
      icon: json['icon'] ?? '',
      visible: json['visible'] ?? true,
      routeType: json['route_type'] ?? '',
    );
  }
}

class RouteConfig {
  final String id;
  final String routeType;
  final Map<String, dynamic>? params;

  RouteConfig({required this.id, required this.routeType, this.params});

  factory RouteConfig.fromJson(Map<String, dynamic> json) {
    return RouteConfig(
      id: json['id'] ?? '',
      routeType: json['route_type'] ?? '',
      params: json['params'],
    );
  }
}

class ActionConfig {
  final String id;
  final String label;
  final String icon;
  final String actionKey;
  final Map<String, dynamic>? params;
  final GateConfig? gate;

  ActionConfig({
    required this.id,
    required this.label,
    required this.icon,
    required this.actionKey,
    this.params,
    this.gate,
  });

  factory ActionConfig.fromJson(Map<String, dynamic> json) {
    return ActionConfig(
      id: json['id'] ?? '',
      label: json['label'] ?? '',
      icon: json['icon'] ?? '',
      actionKey: json['action_key'] ?? '',
      params: json['params'],
      gate: json['gate'] != null ? GateConfig.fromJson(json['gate']) : null,
    );
  }
}

class GateConfig {
  final bool requiresAuth;
  final bool requiresEntitlement;
  final bool requiresTrust;

  GateConfig({
    this.requiresAuth = false,
    this.requiresEntitlement = false,
    this.requiresTrust = false,
  });

  factory GateConfig.fromJson(Map<String, dynamic> json) {
    return GateConfig(
      requiresAuth: json['requires_auth'] ?? false,
      requiresEntitlement: json['requires_entitlement'] ?? false,
      requiresTrust: json['requires_trust'] ?? false,
    );
  }
}

class ContentConfig {
  final DeviceContent? device;
  final DiscoverContent? discover;
  final PurchaseContent? purchase;
  final MeContent? me;

  ContentConfig({this.device, this.discover, this.purchase, this.me});

  factory ContentConfig.fromJson(Map<String, dynamic> json) {
    return ContentConfig(
      device: json['device'] != null ? DeviceContent.fromJson(json['device']) : null,
      discover: json['discover'] != null ? DiscoverContent.fromJson(json['discover']) : null,
      purchase: json['purchase'] != null ? PurchaseContent.fromJson(json['purchase']) : null,
      me: json['me'] != null ? MeContent.fromJson(json['me']) : null,
    );
  }
}

class DeviceContent {
  final List<String> quickActionIds;

  DeviceContent({required this.quickActionIds});

  factory DeviceContent.fromJson(Map<String, dynamic> json) {
    return DeviceContent(
      quickActionIds: List<String>.from(json['quick_action_ids'] ?? []),
    );
  }
}

class DiscoverContent {
  final List<DiscoverSection> sections;

  DiscoverContent({required this.sections});

  factory DiscoverContent.fromJson(Map<String, dynamic> json) {
    return DiscoverContent(
      sections: (json['sections'] as List?)?.map((s) => DiscoverSection.fromJson(s)).toList() ?? [],
    );
  }
}

class DiscoverSection {
  final String id;
  final String title;
  final List<DiscoverCard> cards;

  DiscoverSection({required this.id, required this.title, required this.cards});

  factory DiscoverSection.fromJson(Map<String, dynamic> json) {
    return DiscoverSection(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      cards: (json['cards'] as List?)?.map((c) => DiscoverCard.fromJson(c)).toList() ?? [],
    );
  }
}

class DiscoverCard {
  final String id;
  final String title;
  final String? subtitle;
  final String imageUrl;
  final String actionId;

  DiscoverCard({
    required this.id,
    required this.title,
    this.subtitle,
    required this.imageUrl,
    required this.actionId,
  });

  factory DiscoverCard.fromJson(Map<String, dynamic> json) {
    return DiscoverCard(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      subtitle: json['subtitle'],
      imageUrl: json['image_url'] ?? '',
      actionId: json['action_id'] ?? '',
    );
  }
}

class PurchaseContent {
  final List<TierConfig> tiers;
  final List<RegionConfig> regions;

  PurchaseContent({required this.tiers, required this.regions});

  factory PurchaseContent.fromJson(Map<String, dynamic> json) {
    return PurchaseContent(
      tiers: (json['tiers'] as List?)?.map((t) => TierConfig.fromJson(t)).toList() ?? [],
      regions: (json['regions'] as List?)?.map((r) => RegionConfig.fromJson(r)).toList() ?? [],
    );
  }
}

class TierConfig {
  final String id;
  final String label;

  TierConfig({required this.id, required this.label});

  factory TierConfig.fromJson(Map<String, dynamic> json) {
    return TierConfig(
      id: json['id'] ?? '',
      label: json['label'] ?? '',
    );
  }
}

class RegionConfig {
  final String code;
  final String label;
  final String probeHost;

  RegionConfig({required this.code, required this.label, required this.probeHost});

  factory RegionConfig.fromJson(Map<String, dynamic> json) {
    return RegionConfig(
      code: json['code'] ?? '',
      label: json['label'] ?? '',
      probeHost: json['probe_host'] ?? '',
    );
  }
}

class MeContent {
  final List<String> menuActionIds;

  MeContent({required this.menuActionIds});

  factory MeContent.fromJson(Map<String, dynamic> json) {
    return MeContent(
      menuActionIds: List<String>.from(json['menu_action_ids'] ?? []),
    );
  }
}

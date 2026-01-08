import 'package:flutter/material.dart';
import '../models/ui_config.dart';
import '../actions/action_dispatcher.dart';

/// Purchase Tab - Tiers, regions, plans, buy CTA
class PurchaseTab extends StatefulWidget {
  final UiConfig? config;

  const PurchaseTab({Key? key, this.config}) : super(key: key);

  @override
  State<PurchaseTab> createState() => _PurchaseTabState();
}

class _PurchaseTabState extends State<PurchaseTab> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String? _selectedRegion;

  List<TierConfig> get _tiers {
    return widget.config?.content?.purchase?.tiers ?? [];
  }

  List<RegionConfig> get _regions {
    return widget.config?.content?.purchase?.regions ?? [];
  }

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tiers.length.clamp(1, 10), vsync: this);
    if (_regions.isNotEmpty) {
      _selectedRegion = _regions.first.code;
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Purchase'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        centerTitle: true,
        bottom: _tiers.isNotEmpty
            ? TabBar(
                controller: _tabController,
                isScrollable: true,
                indicatorColor: Colors.white,
                labelColor: Colors.white,
                unselectedLabelColor: Colors.white70,
                tabs: _tiers.map((t) => Tab(text: t.label)).toList(),
              )
            : null,
      ),
      body: Column(
        children: [
          // Region selector
          if (_regions.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Select Region', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: _regions.map((r) => ChoiceChip(
                      label: Text(r.label),
                      selected: _selectedRegion == r.code,
                      onSelected: (selected) {
                        if (selected) {
                          setState(() => _selectedRegion = r.code);
                          VNextActionDispatcher.dispatch(
                            context,
                            'select_region',
                            params: {'region_code': r.code},
                          );
                        }
                      },
                      selectedColor: Colors.green.shade100,
                    )).toList(),
                  ),
                ],
              ),
            ),
            const Divider(),
          ],

          // Plans (stub for now)
          Expanded(
            child: _tiers.isNotEmpty
                ? TabBarView(
                    controller: _tabController,
                    children: _tiers.map((tier) => _buildTierPlans(tier)).toList(),
                  )
                : const Center(
                    child: Text('No plans available', style: TextStyle(color: Colors.grey)),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildTierPlans(TierConfig tier) {
    // Stub plans - will be fetched from /public/plans
    final stubPlans = [
      {'id': '${tier.id}_7', 'duration': '7 days', 'price': '50,000đ'},
      {'id': '${tier.id}_30', 'duration': '30 days', 'price': '150,000đ'},
      {'id': '${tier.id}_90', 'duration': '90 days', 'price': '400,000đ'},
    ];

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: stubPlans.length,
      itemBuilder: (context, index) {
        final plan = stubPlans[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            contentPadding: const EdgeInsets.all(16),
            title: Text(
              '${tier.label} - ${plan['duration']}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text('Region: ${_selectedRegion ?? 'Not selected'}'),
            trailing: ElevatedButton(
              onPressed: () {
                VNextActionDispatcher.dispatch(
                  context,
                  'buy_plan',
                  params: {'plan_id': plan['id'], 'region': _selectedRegion},
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
              ),
              child: Text(plan['price']!),
            ),
          ),
        );
      },
    );
  }
}

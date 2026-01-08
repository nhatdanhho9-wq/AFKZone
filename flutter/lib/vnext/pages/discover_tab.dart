import 'package:flutter/material.dart';
import '../models/ui_config.dart';
import '../actions/action_dispatcher.dart';

/// Discover Tab - News/feed with sections and cards
class DiscoverTab extends StatelessWidget {
  final UiConfig? config;

  const DiscoverTab({Key? key, this.config}) : super(key: key);

  List<DiscoverSection> get _sections {
    return config?.content?.discover?.sections ?? [];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Discover'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        centerTitle: true,
      ),
      body: _sections.isEmpty
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.explore_outlined, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('No content available', style: TextStyle(color: Colors.grey)),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _sections.length,
              itemBuilder: (context, index) => _buildSection(_sections[index], context),
            ),
    );
  }

  Widget _buildSection(DiscoverSection section, BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          section.title,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 160,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            itemCount: section.cards.length,
            itemBuilder: (context, index) => _buildCard(section.cards[index], context),
          ),
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildCard(DiscoverCard card, BuildContext context) {
    return GestureDetector(
      onTap: () {
        final action = config?.getActionById(card.actionId);
        if (action != null) {
          VNextActionDispatcher.dispatch(context, action.actionKey, params: action.params);
        }
      },
      child: Container(
        width: 200,
        margin: const EdgeInsets.only(right: 12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          color: Colors.grey.shade200,
          image: card.imageUrl.isNotEmpty
              ? DecorationImage(
                  image: NetworkImage(card.imageUrl),
                  fit: BoxFit.cover,
                  onError: (_, __) {},
                )
              : null,
        ),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Colors.transparent, Colors.black.withOpacity(0.7)],
            ),
          ),
          padding: const EdgeInsets.all(12),
          alignment: Alignment.bottomLeft,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.end,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                card.title,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
              if (card.subtitle != null)
                Text(
                  card.subtitle!,
                  style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

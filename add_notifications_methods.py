#!/usr/bin/env python3
"""Add notifications methods after _getTrialDisplayText"""

import io

file_path = 'd:/rustdesk-dev/flutter/lib/mobile/pages/license_page.dart'

with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add notifications methods after _getTrialDisplayText method
old_trial_display = """  String _getTrialDisplayText() {
    // Try to get trial product info from API
    if (_products.isNotEmpty) {
      final trialProduct = _products.firstWhere(
        (p) => p.price == 0 && p.durationDays == 7 && p.tier == 'basic',
        orElse: () => _products.firstWhere(
          (p) => p.tier == 'basic',
          orElse: () => _products.first,
        ),
      );
      final tierName = trialProduct.name.isNotEmpty ? trialProduct.name : 'Basic';
      return '$tierName - ${trialProduct.maxDevicesDisplay}';
    }
    return 'Basic - Tối đa 1 thiết bị'; // Fallback
  }"""

new_with_notifications = """  String _getTrialDisplayText() {
    // Try to get trial product info from API
    if (_products.isNotEmpty) {
      final trialProduct = _products.firstWhere(
        (p) => p.price == 0 && p.durationDays == 7 && p.tier == 'basic',
        orElse: () => _products.firstWhere(
          (p) => p.tier == 'basic',
          orElse: () => _products.first,
        ),
      );
      final tierName = trialProduct.name.isNotEmpty ? trialProduct.name : 'Basic';
      return '$tierName - ${trialProduct.maxDevicesDisplay}';
    }
    return 'Basic - Tối đa 1 thiết bị'; // Fallback
  }

  List<Widget> _buildNotificationsList() {
    return _notifications.map((n) {
      Color typeColor = _getNotificationColor(n['type']);
      IconData typeIcon = _getNotificationIcon(n['type']);

      return Container(
        margin: EdgeInsets.only(bottom: 12),
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: typeColor.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: typeColor.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(typeIcon, color: typeColor, size: 18),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    n['title'],
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: typeColor,
                    ),
                  ),
                ),
              ],
            ),
            if (n['message'].toString().isNotEmpty) ...[
              SizedBox(height: 6),
              Text(
                n['message'],
                style: TextStyle(fontSize: 13, color: Colors.grey[800]),
              ),
            ],
            if (n['link_url'] != null && n['link_url'].toString().isNotEmpty) ...[
              SizedBox(height: 8),
              InkWell(
                onTap: () {
                  // Copy link to clipboard
                  Clipboard.setData(ClipboardData(text: n['link_url']));
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Đã copy link')),
                  );
                },
                child: Text(
                  'Link: ${n['link_url']}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.blue,
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ],
          ],
        ),
      );
    }).toList();
  }

  Color _getNotificationColor(String type) {
    switch (type.toLowerCase()) {
      case 'warning':
        return Colors.orange;
      case 'success':
        return Colors.green;
      case 'error':
        return Colors.red;
      case 'info':
      default:
        return Colors.blue;
    }
  }

  IconData _getNotificationIcon(String type) {
    switch (type.toLowerCase()) {
      case 'warning':
        return Icons.warning_amber;
      case 'success':
        return Icons.check_circle;
      case 'error':
        return Icons.error;
      case 'info':
      default:
        return Icons.info;
    }
  }"""

content = content.replace(old_trial_display, new_with_notifications)

with io.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Added notification methods successfully")

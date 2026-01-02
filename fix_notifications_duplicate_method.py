#!/usr/bin/env python3
"""Remove duplicate _loadNotifications method"""

import io

file_path = 'd:/rustdesk-dev/flutter/lib/mobile/pages/license_page.dart'

with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the second duplicate _loadNotifications (keep only the first one)
duplicate_method = """
  Future<void> _loadNotifications() async {
    setState(() => _notificationsLoading = true);
    try {
      final response = await http.get(
        Uri.parse('https://api.afkzone.cloud/public/notifications'),
        headers: {'Cache-Control': 'no-cache'},
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> notifsJson = data['notifications'] ?? [];
        setState(() {
          _notifications = notifsJson.map((n) => {
            'id': n['id'],
            'title': n['title'] ?? '',
            'message': n['message'] ?? '',
            'type': n['type'] ?? 'info',
            'link_url': n['link_url'],
            'created_at': n['created_at'],
          }).toList();
          _notificationsLoading = false;
        });
      } else {
        setState(() => _notificationsLoading = false);
      }
    } catch (e) {
      print('Error loading notifications: $e');
      setState(() => _notificationsLoading = false);
    }
  }"""

# Find the position of the first occurrence
first_pos = content.find(duplicate_method)
# Find the position of the second occurrence (start searching after the first one)
second_pos = content.find(duplicate_method, first_pos + len(duplicate_method))

if second_pos != -1:
    # Remove only the second occurrence
    content = content[:second_pos] + content[second_pos + len(duplicate_method):]
    print("Removed duplicate _loadNotifications method")
else:
    print("No duplicate found (this is OK if already fixed)")

with io.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

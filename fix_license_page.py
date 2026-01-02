#!/usr/bin/env python3
"""Fix license_page.dart - Add fallback logic for afk_license_key"""

file_path = 'd:/rustdesk-dev/flutter/lib/mobile/pages/license_page.dart'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_load_active = """  Future<void> _loadActiveLicense() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool('afk_license_active') == true) {
      setState(() {
        _activeLicense = {
          'license_key': prefs.getString('afk_license_key') ?? 'Unknown',
          'tier': prefs.getString('afk_license_tier') ?? 'basic',
          'expires_at': _formatDate(prefs.getInt('afk_license_expires_at')),
          'status': 'active',
          'is_local': true,
        };
      });
    } else {
      setState(() => _activeLicense = null);
    }"""

new_load_active = """  Future<void> _loadActiveLicense() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool('afk_license_active') == true) {
      // Fallback chain: afk_license_key -> license_key -> latest paid history
      String? licenseKey = prefs.getString('afk_license_key');
      if (licenseKey == null || licenseKey.isEmpty) {
        licenseKey = prefs.getString('license_key');
      }
      if (licenseKey == null || licenseKey.isEmpty) {
        // Fallback to latest paid history (if available)
        if (_paymentHistory.isNotEmpty) {
          final latestPaid = _paymentHistory.firstWhere(
            (h) => h['status'] == 'paid' || h['status'] == 'completed',
            orElse: () => {},
          );
          licenseKey = latestPaid['license_key'];
        }
      }

      setState(() {
        _activeLicense = {
          'license_key': licenseKey ?? 'Unknown',
          'tier': prefs.getString('afk_license_tier') ?? 'basic',
          'expires_at': _formatDate(prefs.getInt('afk_license_expires_at')),
          'status': 'active',
          'is_local': true,
        };
      });
    } else {
      setState(() => _activeLicense = null);
    }"""

content = content.replace(old_load_active, new_load_active)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed license_page.dart successfully")

#!/usr/bin/env python3
"""Fix payment_qr_screen.dart - Final fixes for Codex verification"""

file_path = 'd:/rustdesk-dev/flutter/lib/mobile/pages/payment_qr_screen.dart'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Define activationSuccessful and only set afk_license_active conditionally
old_section = """    // Auto-activate license
    int? expiresAt;
    int? maxDevices;
    try {
      final deviceId = await LicenseService.getDeviceFingerprint();

      // Also save device_id to match LicenseWrapper
      await prefs.setString('device_id', deviceId);

      final result = await LicenseService.activateLicense(licenseKey, deviceId);
      if (result != null) {
        await prefs.setBool('afk_license_active', true);
        if (result['license_key'] != null) {
          await prefs.setString('afk_license_key', result['license_key']);
        }
        if (result['tier'] != null) {
          await prefs.setString('afk_license_tier', result['tier']);
        }"""

new_section = """    // Auto-activate license
    int? expiresAt;
    int? maxDevices;
    bool activationSuccessful = false;
    try {
      final deviceId = await LicenseService.getDeviceFingerprint();

      // Also save device_id to match LicenseWrapper
      await prefs.setString('device_id', deviceId);

      final result = await LicenseService.activateLicense(licenseKey, deviceId);
      if (result != null) {
        final status = result['status']?.toString().toLowerCase();

        // Only set afk_license_active=true if status is active/activated
        if (status == 'active' || status == 'activated') {
          await prefs.setBool('afk_license_active', true);
          activationSuccessful = true;
        }

        if (result['tier'] != null) {
          await prefs.setString('afk_license_tier', result['tier']);
        }"""

content = content.replace(old_section, new_section)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed payment_qr_screen.dart successfully")

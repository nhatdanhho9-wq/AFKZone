#!/usr/bin/env python3
"""Fix payment_qr_screen.dart - Phase 4b user findings"""

import re

file_path = 'd:/rustdesk-dev/flutter/lib/mobile/pages/payment_qr_screen.dart'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Add afk_license_key setter after line with afk_license_purchased_at
content = content.replace(
    "await prefs.setInt('afk_license_purchased_at', DateTime.now().millisecondsSinceEpoch);",
    """await prefs.setInt('afk_license_purchased_at', DateTime.now().millisecondsSinceEpoch);

    // ALWAYS set afk_license_key after payment success
    await prefs.setString('afk_license_key', licenseKey);"""
)

# Fix 2: Add activation tracking variables and conditional afk_license_active
old_activation_section = """    // Auto-activate license
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

new_activation_section = """    // Auto-activate license
    int? expiresAt;
    int? maxDevices;
    bool activationSuccessful = false;
    String? activationStatus;
    try {
      final deviceId = await LicenseService.getDeviceFingerprint();

      // Also save device_id to match LicenseWrapper
      await prefs.setString('device_id', deviceId);

      final result = await LicenseService.activateLicense(licenseKey, deviceId);
      if (result != null) {
        activationStatus = result['status']?.toString().toLowerCase();

        // Only set afk_license_active=true if status is active/activated
        if (activationStatus == 'active' || activationStatus == 'activated') {
          await prefs.setBool('afk_license_active', true);
          activationSuccessful = true;
        }

        if (result['tier'] != null) {
          await prefs.setString('afk_license_tier', result['tier']);
        }"""

content = content.replace(old_activation_section, new_activation_section)

# Fix 3: Update dialog text based on activation success
old_dialog_text = """                    Text(
                      '🎉 Cảm ơn bạn đã chọn dịch vụ AFK Zone!',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),"""

new_dialog_text = """                    Text(
                      activationSuccessful
                        ? '🎉 Cảm ơn bạn đã chọn dịch vụ AFK Zone!'
                        : '⚠️ Thanh toán thành công! Vui lòng kích hoạt license thủ công.',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),"""

content = content.replace(old_dialog_text, new_dialog_text)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed payment_qr_screen.dart successfully")

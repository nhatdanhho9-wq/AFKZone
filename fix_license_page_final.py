#!/usr/bin/env python3
"""Fix license_page.dart - Replace _paymentHistory with _purchaseHistory"""

file_path = 'd:/rustdesk-dev/flutter/lib/mobile/pages/license_page.dart'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: Replace _paymentHistory with _purchaseHistory in fallback logic
content = content.replace('if (_paymentHistory.isNotEmpty)', 'if (_purchaseHistory.isNotEmpty)')
content = content.replace('final latestPaid = _paymentHistory.firstWhere(', 'final latestPaid = _purchaseHistory.firstWhere(')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed license_page.dart successfully")

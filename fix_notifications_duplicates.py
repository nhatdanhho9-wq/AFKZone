#!/usr/bin/env python3
"""Fix duplicate imports and state variables in license_page.dart"""

import io

file_path = 'd:/rustdesk-dev/flutter/lib/mobile/pages/license_page.dart'

with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove duplicate imports
content = content.replace(
    """import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'dart:convert';""",
    """import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';"""
)

# Remove duplicate state variables
content = content.replace(
    """  bool _showTrials = false;
  List<Map<String, dynamic>> _notifications = [];
  bool _notificationsLoading = true;
  List<Map<String, dynamic>> _notifications = [];
  bool _notificationsLoading = true;""",
    """  bool _showTrials = false;
  List<Map<String, dynamic>> _notifications = [];
  bool _notificationsLoading = true;"""
)

with io.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed duplicate imports and state variables")

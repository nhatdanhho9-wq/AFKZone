#!/usr/bin/env python3
"""Replace Zalo banner and pricing with API-driven notifications in license_page.dart"""

import io

file_path = 'd:/rustdesk-dev/flutter/lib/mobile/pages/license_page.dart'

with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Remove Zalo banner section (lines 784-830)
old_zalo_section = """              SizedBox(height: 24),

              // Contact Card
              Card(
                color: Color(0xFFFF6B6B),
                elevation: 4,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: InkWell(
                  onTap: _openZalo,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: EdgeInsets.all(20),
                    child: Column(
                      children: [
                        Icon(Icons.shopping_cart, size: 48, color: Colors.white),
                        SizedBox(height: 12),
                        Text(
                          'Mua License',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Zalo: 0823333374',
                          style: TextStyle(
                            fontSize: 18,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Nhấn để copy số Zalo',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.white70,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              SizedBox(height: 16),"""

new_zalo_section = """              SizedBox(height: 24),"""

# Step 2: Replace pricing section with notifications
old_pricing_section = """              // Pricing Info - Load from API
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Bảng giá',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 12),
                      if (_productsLoading)
                        Center(child: CircularProgressIndicator())
                      else if (_products.isEmpty)
                        Text('Không có thông tin giá', style: TextStyle(color: Colors.grey))
                      else
                        ..._buildPricingRowsFromAPI(),
                    ],
                  ),
                ),
              ),"""

new_notifications_section = """              // Notifications - Load from /public/notifications
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.info_outline, color: Colors.blue, size: 20),
                          SizedBox(width: 8),
                          Text(
                            'Thông tin & Thông báo',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 12),
                      if (_notificationsLoading)
                        Center(child: CircularProgressIndicator())
                      else if (_notifications.isEmpty)
                        Text('Không có thông báo mới', style: TextStyle(color: Colors.grey[600]))
                      else
                        ..._buildNotificationsList(),
                    ],
                  ),
                ),
              ),"""

content = content.replace(old_zalo_section, new_zalo_section)
content = content.replace(old_pricing_section, new_notifications_section)

# Step 3: Add state variables for notifications (after _showTrials declaration around line 33)
old_state_vars = """  List<Map<String, dynamic>> _paidHistory = [];
  List<Map<String, dynamic>> _trialHistory = [];
  bool _showTrials = false;"""

new_state_vars = """  List<Map<String, dynamic>> _paidHistory = [];
  List<Map<String, dynamic>> _trialHistory = [];
  bool _showTrials = false;
  List<Map<String, dynamic>> _notifications = [];
  bool _notificationsLoading = true;"""

content = content.replace(old_state_vars, new_state_vars)

# Step 4: Add notifications loading in initState (after _loadProducts() call around line 40)
old_initstate = """    _checkTrial();
    _loadProducts();
    _loadActiveLicense(); // Load local active state
    _loadPurchaseHistory();
    _checkDirtyFlag();  // Check on init too
    _checkDirtyFlag();  // Check on init too"""

new_initstate = """    _checkTrial();
    _loadProducts();
    _loadActiveLicense(); // Load local active state
    _loadPurchaseHistory();
    _loadNotifications();
    _checkDirtyFlag();  // Check on init too
    _checkDirtyFlag();  // Check on init too"""

content = content.replace(old_initstate, new_initstate)

# Step 5: Add _loadNotifications method (after _loadProducts method around line 312)
old_loadproducts_end = """  Future<void> _loadProducts() async {
    try {
      final products = await ProductService.fetchProducts();
      setState(() {
        _products = products;
        _productsLoading = false;
      });
    } catch (e) {
      print('Error loading products for pricing: $e');
      setState(() {
        _productsLoading = false;
      });
    }
  }"""

new_loadproducts_with_notifications = """  Future<void> _loadProducts() async {
    try {
      final products = await ProductService.fetchProducts();
      setState(() {
        _products = products;
        _productsLoading = false;
      });
    } catch (e) {
      print('Error loading products for pricing: $e');
      setState(() {
        _productsLoading = false;
      });
    }
  }

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

content = content.replace(old_loadproducts_end, new_loadproducts_with_notifications)

# Step 6: Add _buildNotificationsList method (replace _buildPricingRowsFromAPI and _buildPricingRow)
old_pricing_methods = """  List<Widget> _buildPricingRowsFromAPI() {
    // Show all products grouped by tier (sorted by duration)
    // Format: "Tier Name (X thiết bị)" - "Y ngày: Z đồng"

    final List<Widget> rows = [];
    String currentTier = '';

    // Sort products by tier, then by duration
    final sortedProducts = List<Product>.from(_products)
      ..sort((a, b) {
        final tierCompare = a.tier.compareTo(b.tier);
        if (tierCompare != 0) return tierCompare;
        return a.durationDays.compareTo(b.durationDays);
      });

    for (var product in sortedProducts) {
      // Skip 7-day free trial products (already shown in trial section)
      if (product.durationDays == 7 && product.price == 0) {
        continue;
      }

      // Build tier label: "Product Name (X thiết bị)"
      final tierLabel = '${product.name.isNotEmpty ? product.name : product.tierDisplayName} (${product.maxDevicesDisplay})';

      // Build price label: "Y ngày: Z đồng"
      final priceLabel = '${product.durationDays} ngày: ${product.displayPrice}';

      rows.add(_buildPricingRow(tierLabel, priceLabel));
    }

    return rows;
  }

  Widget _buildPricingRow(String tier, String price) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(child: Text(tier, style: TextStyle(fontSize: 14))),
          Text(
            price,
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
        ],
      ),
    );
  }"""

new_notifications_methods = """  List<Widget> _buildNotificationsList() {
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
            if (n['message'].isNotEmpty) ...[
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

content = content.replace(old_pricing_methods, new_notifications_methods)

# Step 7: Add http and convert imports (after existing imports around line 8)
old_imports = """import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'payment_screen.dart';
import 'dart:io';"""

new_imports = """import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'payment_screen.dart';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';"""

content = content.replace(old_imports, new_imports)

# Step 8: Remove _openZalo method since we removed the Zalo card (around line 457)
old_openzalo_method = """  void _openZalo() {
    // Open Zalo chat or copy number
    Clipboard.setData(ClipboardData(text: '0823333374'));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Đã copy số Zalo: 0823333374')),
    );
  }

  @override"""

new_openzalo_removed = """  @override"""

content = content.replace(old_openzalo_method, new_openzalo_removed)

with io.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Replaced Zalo banner and pricing with notifications successfully")
print("Changes:")
print("  1. Removed Zalo banner section (Contact Card)")
print("  2. Replaced 'Bang gia' with 'Thong tin & Thong bao'")
print("  3. Added notifications state variables")
print("  4. Added _loadNotifications() method to fetch from /public/notifications")
print("  5. Added _buildNotificationsList() with type-based colors and icons")
print("  6. Added http and convert imports")
print("  7. Removed _openZalo() method")

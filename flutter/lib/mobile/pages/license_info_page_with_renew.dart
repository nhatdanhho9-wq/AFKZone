import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:intl/intl.dart';
import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import 'payment_qr_screen.dart';

class LicenseInfoPage extends StatefulWidget {
  @override
  _LicenseInfoPageState createState() => _LicenseInfoPageState();
}

class _LicenseInfoPageState extends State<LicenseInfoPage> {
  String? _licenseKey;
  String? _tier;
  int? _durationDays;
  int? _expiresAt;
  bool _isActive = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadLicenseInfo();
  }

  Future<void> _loadLicenseInfo() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _licenseKey = prefs.getString('afk_license_key');
      _tier = prefs.getString('afk_license_tier');
      _durationDays = prefs.getInt('afk_license_duration');
      _expiresAt = prefs.getInt('afk_license_expires_at');
      _isActive = prefs.getBool('afk_license_active') ?? false;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Thong tin License'),
        backgroundColor: Colors.deepPurple,
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _licenseKey == null
              ? Center(child: Text('Chua co license'))
              : SingleChildScrollView(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Card(
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: Column(
                            children: [
                              Text('License Key', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                              SizedBox(height: 8),
                              SelectableText(_licenseKey!, style: TextStyle(fontSize: 14)),
                              SizedBox(height: 8),
                              ElevatedButton.icon(
                                icon: Icon(Icons.copy),
                                label: Text('Copy'),
                                onPressed: () {
                                  Clipboard.setData(ClipboardData(text: _licenseKey!));
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(content: Text('Da copy license key')),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                      ),
                      SizedBox(height: 16),
                      if (_isActive && _expiresAt != null) ...[
                        Card(
                          child: Padding(
                            padding: EdgeInsets.all(16),
                            child: Column(
                              children: [
                                Text('Thong tin goi', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                                SizedBox(height: 12),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text('Tier:'),
                                    Text(_tier ?? 'N/A', style: TextStyle(fontWeight: FontWeight.bold)),
                                  ],
                                ),
                                SizedBox(height: 8),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text('Het han:'),
                                    Text(
                                      DateFormat('dd/MM/yyyy HH:mm').format(DateTime.fromMillisecondsSinceEpoch(_expiresAt!)),
                                      style: TextStyle(fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                        SizedBox(height: 16),
                        ElevatedButton.icon(
                          icon: Icon(Icons.refresh),
                          label: Text('Gia han License'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            minimumSize: Size(double.infinity, 50),
                          ),
                          onPressed: () => _showRenewDialog(),
                        ),
                      ],
                    ],
                  ),
                ),
    );
  }

  void _showRenewDialog() async {
    try {
      final products = await ProductService.fetchProducts();
      final sameTierProducts = products.where((p) => p.tier == _tier).toList();

      if (sameTierProducts.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Khong tim thay goi gia han')),
        );
        return;
      }

      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Chon goi gia han'),
          content: Container(
            width: double.maxFinite,
            child: ListView.builder(
              shrinkWrap: true,
              itemCount: sameTierProducts.length,
              itemBuilder: (context, index) {
                final product = sameTierProducts[index];
                return ListTile(
                  title: Text('${product.durationDays} ngay'),
                  trailing: Text(product.formattedPrice),
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (c) => PaymentQRScreen(
                          tier: product.tier,
                          durationDays: product.durationDays,
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Dong'),
            ),
          ],
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Loi: $e')),
      );
    }
  }
}


import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:intl/intl.dart';

class LicenseInfoPage extends StatefulWidget {
  @override
  _LicenseInfoPageState createState() => _LicenseInfoPageState();
}

class _LicenseInfoPageState extends State<LicenseInfoPage> {
  String? _licenseKey;
  String? _tier;
  int? _durationDays;
  int? _purchasedAt;
  int? _expiresAt;
  int? _maxDevices;
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
      _purchasedAt = prefs.getInt('afk_license_purchased_at');
      _expiresAt = prefs.getInt('afk_license_expires_at');
      _maxDevices = prefs.getInt('afk_max_devices');
      _isActive = prefs.getBool('afk_license_active') ?? false;
      _isLoading = false;
    });
  }

  String _formatDate(int? timestamp) {
    if (timestamp == null) return 'N/A';
    final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
    return DateFormat('dd/MM/yyyy HH:mm').format(date);
  }

  int _getDaysRemaining() {
    if (_expiresAt == null) return 0;
    final expiry = DateTime.fromMillisecondsSinceEpoch(_expiresAt!);
    final now = DateTime.now();
    return expiry.difference(now).inDays;
  }

  Color _getStatusColor() {
    final daysLeft = _getDaysRemaining();
    if (!_isActive || daysLeft <= 0) return Colors.red;
    if (daysLeft <= 7) return Colors.orange;
    return Colors.green;
  }

  String _getStatusText() {
    if (!_isActive) return 'Chưa kích hoạt';
    final daysLeft = _getDaysRemaining();
    if (daysLeft <= 0) return 'Hết hạn';
    if (daysLeft == 1) return 'Còn 1 ngày';
    return 'Còn $daysLeft ngày';
  }

  void _copyLicenseKey() {
    if (_licenseKey != null) {
      Clipboard.setData(ClipboardData(text: _licenseKey!));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Đã copy license key!'),
          duration: Duration(seconds: 2),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(
          title: Text('License Info'),
          backgroundColor: Colors.deepPurple,
        ),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_licenseKey == null) {
      return Scaffold(
        appBar: AppBar(
          title: Text('License Info'),
          backgroundColor: Colors.deepPurple,
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.info_outline, size: 64, color: Colors.grey),
              SizedBox(height: 16),
              Text(
                'Chưa có license',
                style: TextStyle(fontSize: 18, color: Colors.grey),
              ),
              SizedBox(height: 8),
              Text(
                'Mua license để sử dụng AFK Zone',
                style: TextStyle(fontSize: 14, color: Colors.grey),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('License Info'),
        backgroundColor: Colors.deepPurple,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadLicenseInfo,
            tooltip: 'Làm mới',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Card
            Card(
              elevation: 4,
              color: _getStatusColor().withOpacity(0.1),
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: _getStatusColor(),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        _isActive && _getDaysRemaining() > 0
                            ? Icons.check_circle
                            : Icons.warning,
                        color: Colors.white,
                        size: 32,
                      ),
                    ),
                    SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Trạng thái',
                            style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                          ),
                          SizedBox(height: 4),
                          Text(
                            _getStatusText(),
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: _getStatusColor(),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            SizedBox(height: 16),

            // License Key Card
            Card(
              elevation: 4,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'License Key',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        IconButton(
                          icon: Icon(Icons.copy, size: 20),
                          onPressed: _copyLicenseKey,
                          tooltip: 'Copy',
                        ),
                      ],
                    ),
                    SizedBox(height: 8),
                    Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey[300]!),
                      ),
                      child: SelectableText(
                        _licenseKey!,
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            SizedBox(height: 16),

            // Details Card
            Card(
              elevation: 4,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Thông tin chi tiết',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 16),
                    _buildInfoRow(
                      Icons.star,
                      'Gói',
                      _tier?.toUpperCase() ?? 'N/A',
                      Colors.purple,
                    ),
                    Divider(),
                    _buildInfoRow(
                      Icons.calendar_today,
                      'Thời hạn',
                      '$_durationDays ngày',
                      Colors.blue,
                    ),
                    Divider(),
                    _buildInfoRow(
                      Icons.shopping_cart,
                      'Ngày mua',
                      _formatDate(_purchasedAt),
                      Colors.green,
                    ),
                    Divider(),
                    _buildInfoRow(
                      Icons.event,
                      'Ngày hết hạn',
                      _formatDate(_expiresAt),
                      Colors.orange,
                    ),
                    Divider(),
                    _buildInfoRow(
                      Icons.devices,
                      'Số thiết bị tối đa',
                      '${_maxDevices ?? 1} thiết bị',
                      Colors.teal,
                    ),
                  ],
                ),
              ),
            ),

            SizedBox(height: 16),

            // Instructions Card
            Card(
              elevation: 4,
              color: Colors.blue.shade50,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.help_outline, color: Colors.blue),
                        SizedBox(width: 8),
                        Text(
                          'Hướng dẫn sử dụng',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.blue.shade900),
                        ),
                      ],
                    ),
                    SizedBox(height: 12),
                    Text('• Copy license key bằng nút Copy ở trên', style: TextStyle(fontSize: 13)),
                    SizedBox(height: 4),
                    Text('• Dán license key vào thiết bị khác để kích hoạt', style: TextStyle(fontSize: 13)),
                    SizedBox(height: 4),
                    Text('• Mỗi license có thể dùng cho ${_maxDevices ?? 1} thiết bị', style: TextStyle(fontSize: 13)),
                    SizedBox(height: 4),
                    Text('• License sẽ tự động gia hạn nếu bạn mua thêm gói mới', style: TextStyle(fontSize: 13)),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value, Color color) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            padding: EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
                SizedBox(height: 2),
                Text(
                  value,
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

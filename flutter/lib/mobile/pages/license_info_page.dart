import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;
import '../widgets/renewal_dialog.dart';
import '../../common/license_service.dart';

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

  void _showRenewalDialog() {
    if (_licenseKey == null || _tier == null) return;
    showDialog(
      context: context,
      builder: (context) => RenewalDialog(
        currentTier: _tier!,
        licenseKey: _licenseKey!,
        expiresAt: _expiresAt,
      ),
    );
  }

  void _showAssignLicenseDialog() {
    if (_licenseKey == null) return;
    showDialog(
      context: context,
      builder: (context) => _AssignLicenseDialogContent(
        licenseKey: _licenseKey!,
        onCopyKey: _copyLicenseKey,
      ),
    );
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

            SizedBox(height: 16),

            // Action Buttons Card
            Card(
              elevation: 4,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Thao tác',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 12),
                    // Renewal button
                    ElevatedButton.icon(
                      onPressed: () => _showRenewalDialog(),
                      icon: Icon(Icons.autorenew),
                      label: Text('Gia hạn License'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                        padding: EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                    SizedBox(height: 8),
                    // Assign license button
                    OutlinedButton.icon(
                      onPressed: () => _showAssignLicenseDialog(),
                      icon: Icon(Icons.devices),
                      label: Text('Gán license cho thiết bị khác'),
                      style: OutlinedButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
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

// Assign License Dialog Content - fetches from /api/devices/list
class _AssignLicenseDialogContent extends StatefulWidget {
  final String licenseKey;
  final VoidCallback onCopyKey;
  
  const _AssignLicenseDialogContent({
    Key? key,
    required this.licenseKey,
    required this.onCopyKey,
  }) : super(key: key);
  
  @override
  _AssignLicenseDialogContentState createState() => _AssignLicenseDialogContentState();
}

class _AssignLicenseDialogContentState extends State<_AssignLicenseDialogContent> {
  List<Map<String, dynamic>> _devices = [];
  bool _isLoading = true;
  bool _isAssigning = false;
  String? _error;
  
  @override
  void initState() {
    super.initState();
    _loadDevices();
  }
  
  Future<void> _loadDevices() async {
    try {
      final deviceId = await LicenseService.getDeviceFingerprint();
      final response = await http.get(
        Uri.parse('https://api.afkzone.cloud/api/devices/list?device_id=$deviceId'),
        headers: {'Cache-Control': 'no-cache'},
      ).timeout(Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> devicesJson = data['devices'] ?? [];
        setState(() {
          _devices = devicesJson.map((d) => Map<String, dynamic>.from(d)).toList();
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Không thể tải danh sách thiết bị';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Lỗi kết nối';
        _isLoading = false;
      });
    }
  }
  
  Future<void> _assignToDevice(Map<String, dynamic> device) async {
    setState(() => _isAssigning = true);
    try {
      final response = await http.post(
        Uri.parse('https://api.afkzone.cloud/api/license/assign'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'license_key': widget.licenseKey,
          'target_device_id': device['device_id'],
        }),
      ).timeout(Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Đã gán license cho ${device['alias'] ?? device['device_id']}'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        setState(() => _isAssigning = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Không thể gán license'), backgroundColor: Colors.red),
        );
      }
    } catch (e) {
      setState(() => _isAssigning = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Lỗi kết nối'), backgroundColor: Colors.red),
      );
    }
  }
  
  String _formatLastSeen(dynamic lastSeen) {
    if (lastSeen == null) return 'Chưa rõ';
    try {
      final date = DateTime.parse(lastSeen.toString());
      return DateFormat('dd/MM/yyyy HH:mm').format(date);
    } catch (e) {
      return lastSeen.toString();
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(
        children: [
          Icon(Icons.devices, color: Colors.blue),
          SizedBox(width: 8),
          Text('Gán License'),
        ],
      ),
      content: Container(
        width: double.maxFinite,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_isLoading)
              Center(child: CircularProgressIndicator())
            else if (_error != null)
              Column(
                children: [
                  Text(_error!, style: TextStyle(color: Colors.red)),
                  SizedBox(height: 12),
                  Text(
                    'Bạn có thể copy license key và nhập vào thiết bị khác.',
                    style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                  ),
                ],
              )
            else if (_devices.isEmpty)
              Column(
                children: [
                  Icon(Icons.devices_other, size: 48, color: Colors.grey),
                  SizedBox(height: 12),
                  Text('Chưa có thiết bị nào khác.'),
                  SizedBox(height: 8),
                  Text(
                    'Copy license key để kích hoạt trên thiết bị khác.',
                    style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                  ),
                ],
              )
            else ...[
              Text('Chọn thiết bị:', style: TextStyle(fontWeight: FontWeight.w500)),
              SizedBox(height: 8),
              ..._devices.map((device) => ListTile(
                title: Text(device['alias'] ?? 'Thiết bị'),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'ID: ${(device['device_id'] ?? '').toString().substring(0, 8)}...',
                      style: TextStyle(fontSize: 11, fontFamily: 'monospace'),
                    ),
                    Text(
                      'Lần cuối: ${_formatLastSeen(device['last_seen'])}',
                      style: TextStyle(fontSize: 11),
                    ),
                  ],
                ),
                leading: Icon(Icons.phone_android, color: Colors.blue),
                trailing: _isAssigning
                    ? SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : Icon(Icons.arrow_forward_ios, size: 16),
                onTap: _isAssigning ? null : () => _assignToDevice(device),
                dense: true,
              )).toList(),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Đóng'),
        ),
        ElevatedButton.icon(
          onPressed: () {
            widget.onCopyKey();
            Navigator.pop(context);
          },
          icon: Icon(Icons.copy, size: 16),
          label: Text('Copy License Key'),
        ),
      ],
    );
  }
}

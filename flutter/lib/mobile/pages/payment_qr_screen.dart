import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/payment_service.dart';
import '../../common/license_service.dart';

class PaymentQRScreen extends StatefulWidget {
  final String tier;
  final int durationDays;

  PaymentQRScreen({required this.tier, required this.durationDays});

  @override
  _PaymentQRScreenState createState() => _PaymentQRScreenState();
}

class _PaymentQRScreenState extends State<PaymentQRScreen> {
  bool _isLoading = true;
  String? _error;
  String? _transCode;
  String? _qrUrl;
  int? _amount;
  String? _bankAccount;
  String? _content;
  Timer? _pollingTimer;
  int _countdown = 600; // 10 minutes

  @override
  void initState() {
    super.initState();
    _createOrder();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }

  Future<void> _createOrder() async {
    try {
      final deviceId = await LicenseService.getDeviceFingerprint();
      final order = await PaymentService.createBankOrder(
        tier: widget.tier,
        durationDays: widget.durationDays,
        deviceId: deviceId,
      );

      setState(() {
        _transCode = order['trans_code'];
        _qrUrl = order['qr_url'];
        _amount = order['amount'];
        _bankAccount = order['bank_info']['account_no'];
        _content = order['bank_info']['content'];
        _isLoading = false;
      });

      _startPolling();
      _startCountdown();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _startPolling() {
    _pollingTimer = Timer.periodic(Duration(seconds: 2), (timer) async {
      try {
        final status = await PaymentService.checkPaymentStatus(_transCode!);
        if (status['status'] == 'success') {
          timer.cancel();
          final licenseKey = status['license_key'];
          _showSuccessDialog(licenseKey);
        }
      } catch (e) {
        print('Polling error: $e');
      }
    });
  }

  void _startCountdown() {
    Timer.periodic(Duration(seconds: 1), (timer) {
      if (_countdown > 0) {
        setState(() => _countdown--);
      } else {
        timer.cancel();
        _pollingTimer?.cancel();
      }
    });
  }

  void _showSuccessDialog(String licenseKey) async {
    // Save license info to SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('afk_license_key', licenseKey);
    await prefs.setString('afk_license_tier', widget.tier);
    await prefs.setInt('afk_license_duration', widget.durationDays);
    await prefs.setInt('afk_license_purchased_at', DateTime.now().millisecondsSinceEpoch);

    // Auto-activate license
    int? expiresAt;
    int? maxDevices;
    try {
      final deviceId = await LicenseService.getDeviceFingerprint();
      final result = await LicenseService.activateLicense(licenseKey, deviceId);
      if (result != null) {
        await prefs.setBool('afk_license_active', true);
        expiresAt = result['expires_at'];
        maxDevices = result['max_devices'] ?? 1;
        await prefs.setInt('afk_license_expires_at', expiresAt);
        await prefs.setInt('afk_max_devices', maxDevices);
      }
    } catch (e) {
      print('Auto-activation error: $e');
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 32),
            SizedBox(width: 12),
            Expanded(child: Text('Thanh toán thành công!')),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.green.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.green.shade200),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '🎉 Cảm ơn bạn đã chọn dịch vụ AFK Zone!',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 12),
                    Text('License của bạn:', style: TextStyle(fontWeight: FontWeight.bold)),
                    SizedBox(height: 4),
                    Container(
                      padding: EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: SelectableText(
                              licenseKey,
                              style: TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          IconButton(
                            icon: Icon(Icons.copy, size: 20),
                            padding: EdgeInsets.zero,
                            constraints: BoxConstraints(),
                            onPressed: () {
                              Clipboard.setData(ClipboardData(text: licenseKey));
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('Đã copy license key!'), duration: Duration(seconds: 2)),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 16),
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.info_outline, size: 20, color: Colors.blue),
                        SizedBox(width: 8),
                        Text(
                          'Thông tin quan trọng:',
                          style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue.shade900),
                        ),
                      ],
                    ),
                    SizedBox(height: 8),
                    Text('✓ License đã được tự động kích hoạt trên thiết bị này', style: TextStyle(fontSize: 13)),
                    SizedBox(height: 4),
                    Text('✓ Gói ${widget.tier.toUpperCase()}: ${widget.durationDays} ngày', style: TextStyle(fontSize: 13)),
                    SizedBox(height: 4),
                    Text('✓ Xem thông tin license tại: Settings → License Info', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                    SizedBox(height: 4),
                    Text('✓ Copy license key để kích hoạt trên thiết bị khác', style: TextStyle(fontSize: 13)),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          OutlinedButton.icon(
            icon: Icon(Icons.copy, size: 18),
            label: Text('Copy License'),
            onPressed: () {
              Clipboard.setData(ClipboardData(text: licenseKey));
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Đã copy license key!'), duration: Duration(seconds: 2)),
              );
            },
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Go back to payment screen
              Navigator.pop(context); // Go back to license page
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
            ),
            child: Text('Hoàn tất'),
          ),
        ],
      ),
    );
  }

  String _formatTime(int seconds) {
    final mins = seconds ~/ 60;
    final secs = seconds % 60;
    return '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: Text('Đang tạo đơn hàng...')),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: Text('Lỗi')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error, color: Colors.red, size: 64),
              SizedBox(height: 16),
              Text('Lỗi: $_error'),
              SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: Text('Quay lại'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('Thanh toán QR'),
        backgroundColor: Colors.deepPurple,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              'Quét mã QR để thanh toán',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 16),
            Card(
              elevation: 4,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  children: [
                    if (_qrUrl != null)
                      Image.network(
                        _qrUrl!,
                        width: 300,
                        height: 300,
                        errorBuilder: (context, error, stackTrace) {
                          return QrImageView(
                            data: _qrUrl!,
                            version: QrVersions.auto,
                            size: 300,
                          );
                        },
                      ),
                    SizedBox(height: 16),
                    Text(
                      'Số tiền: ${_formatCurrency(_amount ?? 0)}',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.green),
                    ),
                    SizedBox(height: 8),
                    Text('Nội dung: $_content', style: TextStyle(fontSize: 16)),
                    SizedBox(height: 8),
                    Text('TK: $_bankAccount', style: TextStyle(fontSize: 14, color: Colors.grey)),
                  ],
                ),
              ),
            ),
            SizedBox(height: 16),
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.timer, color: Colors.orange),
                  SizedBox(width: 8),
                  Text(
                    'Hết hạn sau: ${_formatTime(_countdown)}',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
            SizedBox(height: 16),
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  CircularProgressIndicator(strokeWidth: 2),
                  SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      'Đang chờ thanh toán...\nHệ thống sẽ tự động kiểm tra mỗi 2 giây',
                      style: TextStyle(fontSize: 14),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatCurrency(int amount) {
    return amount.toString().replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        ) +
        'đ';
  }
}

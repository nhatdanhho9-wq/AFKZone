import 'dart:async';
import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
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
        print('Polling error: \$e');
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

  void _showSuccessDialog(String licenseKey) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text('Thanh toán thành công!'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 64),
            SizedBox(height: 16),
            Text('License key của bạn:'),
            SizedBox(height: 8),
            SelectableText(
              licenseKey,
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Go back to home
            },
            child: Text('OK'),
          ),
        ],
      ),
    );
  }

  String _formatTime(int seconds) {
    final mins = seconds ~/ 60;
    final secs = seconds % 60;
    return '\${mins.toString().padLeft(2, '0')}:\${secs.toString().padLeft(2, '0')}';
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
              Text('Lỗi: \$_error'),
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
                      'Số tiền: \${_formatCurrency(_amount ?? 0)}',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.green),
                    ),
                    SizedBox(height: 8),
                    Text('Nội dung: \$_content', style: TextStyle(fontSize: 16)),
                    SizedBox(height: 8),
                    Text('TK: \$_bankAccount', style: TextStyle(fontSize: 14, color: Colors.grey)),
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
                    'Hết hạn sau: \${_formatTime(_countdown)}',
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
          (Match m) => '\${m[1]},',
        ) +
        'đ';
  }
}

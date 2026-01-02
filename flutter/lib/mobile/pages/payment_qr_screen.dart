import 'dart:async';
import 'package:flutter/material.dart' hide LicensePage;
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_hbb/services/payment_service.dart';
import 'package:flutter_hbb/common/license_service.dart';
import 'package:flutter_hbb/common/payment_websocket_service.dart';
import 'package:flutter_hbb/mobile/pages/license_page.dart';

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
  Timer? _countdownTimer;
  int _countdown = 600; // 10 minutes
  
  // WebSocket for real-time payment notification
  final PaymentWebSocketService _paymentWs = PaymentWebSocketService();
  bool _paymentReceived = false;

  @override
  void initState() {
    super.initState();
    _createOrder();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _countdownTimer?.cancel();
    _paymentWs.disconnect();
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

      // Start WebSocket connection for real-time notification (PRIMARY)
      _startWebSocket();
      
      // Start polling as fallback (will be stopped if WebSocket works)
      _startPolling();
      _startCountdown();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }
  
  void _startWebSocket() {
    if (_transCode == null) return;
    
    print('📡 Starting WebSocket for order: $_transCode');
    _paymentWs.connect(
      orderId: _transCode!,
      onPaymentComplete: (notification) {
        if (_paymentReceived) return; // Prevent duplicate
        _paymentReceived = true;
        
        // Stop polling since WebSocket succeeded
        _pollingTimer?.cancel();
        _countdownTimer?.cancel();
        
        print('🎉 WebSocket received payment notification!');
        _showSuccessDialog(notification.licenseKey);
      },
      onConnectionError: () {
        // WebSocket failed, polling will continue as fallback
        print('⚠️ WebSocket connection failed, using polling fallback');
      },
    );
  }

  void _startPolling() {
    _pollingTimer = Timer.periodic(Duration(seconds: 3), (timer) async {
      if (_paymentReceived) {
        timer.cancel();
        return;
      }
      
      try {
        final status = await PaymentService.checkPaymentStatus(_transCode!);
        if (status['status'] == 'success') {
          if (_paymentReceived) return; // Prevent duplicate
          _paymentReceived = true;
          
          timer.cancel();
          _countdownTimer?.cancel();
          _paymentWs.disconnect();
          
          final licenseKey = status['license_key'];
          print('✅ Polling detected payment success');
          _showSuccessDialog(licenseKey);
        }
      } catch (e) {
        print('Polling error: $e');
      }
    });
  }

  void _startCountdown() {
    _countdownTimer = Timer.periodic(Duration(seconds: 1), (timer) {
      if (_paymentReceived) {
        timer.cancel();
        return;
      }
      
      if (_countdown > 0) {
        setState(() => _countdown--);
      } else {
        timer.cancel();
        _pollingTimer?.cancel();
        _paymentWs.disconnect();
      }
    });
  }

  void _showSuccessDialog(String licenseKey) async {
    // Save license info to SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    
    // IMPORTANT: Save as 'license_key' to match LicenseWrapper expectations
    await prefs.setString('license_key', licenseKey);
    await prefs.setString('afk_license_tier', widget.tier);
    await prefs.setInt('afk_license_duration', widget.durationDays);
    await prefs.setInt('afk_license_purchased_at', DateTime.now().millisecondsSinceEpoch);

    // ALWAYS set afk_license_key after payment success
    await prefs.setString('afk_license_key', licenseKey);

    // Auto-activate license
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
        }
        
        // Handle max_devices - API now returns max_devices, fallback to device_limit
        maxDevices = result['max_devices'] ?? result['device_limit'] ?? 1;
        await prefs.setInt('afk_max_devices', maxDevices ?? 1);
        
        // Handle expires_at - could be ISO string or int
        final expiresRaw = result['expires_at'];
        if (expiresRaw != null) {
          if (expiresRaw is String) {
            // Parse ISO string to milliseconds
            try {
              final dateTime = DateTime.parse(expiresRaw);
              expiresAt = dateTime.millisecondsSinceEpoch;
            } catch (e) {
              print('Error parsing expires_at: $e');
            }
          } else if (expiresRaw is int) {
            expiresAt = expiresRaw;
          }
          
          if (expiresAt != null) {
            await prefs.setInt('afk_license_expires_at', expiresAt);
          }
        }
      }
    } catch (e) {
      print('Auto-activation error: $e');
    }

    // Set dirty flag so license page reloads history
    await prefs.setBool('license_history_dirty', true);

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => Theme(
        data: ThemeData.light(),  // Force light theme for dialog readability
        child: AlertDialog(
          backgroundColor: Colors.white,
          title: Row(
            children: [
              Icon(Icons.check_circle, color: Colors.green, size: 32),
              SizedBox(width: 12),
              Expanded(child: Text('Thanh toán thành công!', style: TextStyle(color: Colors.black87))),
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
                      activationSuccessful
                        ? '🎉 Cảm ơn bạn đã chọn dịch vụ AFK Zone!'
                        : '⚠️ Thanh toán thành công! Vui lòng kích hoạt license thủ công.',
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
                    Text('✓ Số thiết bị tối đa: ${maxDevices == -1 ? "Không giới hạn" : maxDevices}', style: TextStyle(fontSize: 13)),
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
          ElevatedButton.icon(
            icon: Icon(Icons.check_circle, size: 20),
            label: Text('Hoàn tất & Sử dụng'),
            onPressed: () {
              // Navigate to License Page to show active license immediately
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (context) => LicensePage()),
                (route) => route.isFirst,
              );
              
              // Show success snackbar
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Row(
                    children: [
                      Icon(Icons.check_circle, color: Colors.white),
                      SizedBox(width: 12),
                      Expanded(child: Text('License đã được kích hoạt! Bạn có thể sử dụng app ngay.')),
                    ],
                  ),
                  backgroundColor: Colors.green,
                  duration: Duration(seconds: 4),
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            ),
          ),
        ],
      ),  // Close AlertDialog
      ),  // Close Theme
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

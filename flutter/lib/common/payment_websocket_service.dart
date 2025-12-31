import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/material.dart';

/// Service to handle WebSocket payment notifications
class PaymentWebSocketService {
  static const String wsBaseUrl = 'wss://api.afkzone.cloud';
  
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _reconnectTimer;
  String? _currentOrderId;
  Function(PaymentNotification)? _onPaymentComplete;
  Function()? _onConnectionError;
  bool _isConnected = false;
  int _reconnectAttempts = 0;
  static const int maxReconnectAttempts = 10;
  
  /// Connect to WebSocket and listen for payment updates
  void connect({
    required String orderId,
    required Function(PaymentNotification) onPaymentComplete,
    Function()? onConnectionError,
  }) {
    _currentOrderId = orderId;
    _onPaymentComplete = onPaymentComplete;
    _onConnectionError = onConnectionError;
    _reconnectAttempts = 0;
    
    _establishConnection();
  }
  
  void _establishConnection() {
    if (_currentOrderId == null) return;
    
    try {
      final wsUrl = '$wsBaseUrl/ws/payment/$_currentOrderId';
      print('📡 Connecting to WebSocket: $wsUrl');
      
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _isConnected = true;
      _reconnectAttempts = 0;
      
      _subscription = _channel!.stream.listen(
        (message) {
          _handleMessage(message);
        },
        onError: (error) {
          print('❌ WebSocket error: $error');
          _handleDisconnect();
        },
        onDone: () {
          print('📡 WebSocket connection closed');
          _handleDisconnect();
        },
      );
      
      // Start heartbeat
      _startHeartbeat();
      
    } catch (e) {
      print('❌ Failed to connect WebSocket: $e');
      _scheduleReconnect();
    }
  }
  
  void _handleMessage(dynamic message) {
    try {
      final data = jsonDecode(message as String);
      print('📩 WebSocket message: $data');
      
      final type = data['type'];
      
      if (type == 'payment_complete') {
        final notification = PaymentNotification(
          orderId: data['order_id'] ?? '',
          licenseKey: data['license_key'] ?? '',
          expiresAt: data['expires_at'],
          message: data['message'] ?? 'Thanh toán thành công!',
        );
        
        _onPaymentComplete?.call(notification);
        
        // Disconnect after successful payment
        disconnect();
      } else if (type == 'keepalive') {
        // Respond to keepalive
        _channel?.sink.add('ping');
      }
    } catch (e) {
      print('❌ Error parsing WebSocket message: $e');
    }
  }
  
  void _handleDisconnect() {
    _isConnected = false;
    _subscription?.cancel();
    _subscription = null;
    
    // Try to reconnect
    _scheduleReconnect();
  }
  
  void _scheduleReconnect() {
    if (_reconnectAttempts >= maxReconnectAttempts) {
      print('❌ Max reconnect attempts reached, falling back to polling');
      _onConnectionError?.call();
      return;
    }
    
    _reconnectAttempts++;
    final delay = Duration(seconds: 2 * _reconnectAttempts);
    print('🔄 Reconnecting in ${delay.inSeconds}s (attempt $_reconnectAttempts)');
    
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, _establishConnection);
  }
  
  Timer? _heartbeatTimer;
  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(Duration(seconds: 25), (timer) {
      if (_isConnected && _channel != null) {
        try {
          _channel!.sink.add('ping');
        } catch (e) {
          print('❌ Heartbeat failed: $e');
          _handleDisconnect();
        }
      }
    });
  }
  
  /// Disconnect WebSocket
  void disconnect() {
    print('📡 Disconnecting WebSocket');
    _heartbeatTimer?.cancel();
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();
    _channel = null;
    _isConnected = false;
    _currentOrderId = null;
  }
  
  /// Check if connected
  bool get isConnected => _isConnected;
}

/// Data class for payment notification
class PaymentNotification {
  final String orderId;
  final String licenseKey;
  final int? expiresAt;
  final String message;
  
  PaymentNotification({
    required this.orderId,
    required this.licenseKey,
    this.expiresAt,
    required this.message,
  });
  
  String get formattedExpiryDate {
    if (expiresAt == null) return 'N/A';
    final date = DateTime.fromMillisecondsSinceEpoch(expiresAt!);
    return '${date.day}/${date.month}/${date.year}';
  }
}

/// Mixin to add payment notification dialog to any widget
mixin PaymentNotificationMixin<T extends StatefulWidget> on State<T> {
  final PaymentWebSocketService _paymentWs = PaymentWebSocketService();
  
  /// Start listening for payment on an order
  void startPaymentListener(String orderId) {
    _paymentWs.connect(
      orderId: orderId,
      onPaymentComplete: (notification) {
        _showPaymentSuccessDialog(notification);
      },
      onConnectionError: () {
        // Fallback: start polling
        _startPolling(orderId);
      },
    );
  }
  
  Timer? _pollingTimer;
  void _startPolling(String orderId) {
    _pollingTimer?.cancel();
    _pollingTimer = Timer.periodic(Duration(seconds: 5), (timer) async {
      try {
        // Check payment status via REST API
        // If success, show dialog and cancel timer
      } catch (e) {
        print('Polling error: $e');
      }
    });
  }
  
  void _showPaymentSuccessDialog(PaymentNotification notification) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 32),
            SizedBox(width: 12),
            Text('Thanh toán thành công!'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(notification.message),
            SizedBox(height: 16),
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.green),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('License Key:', style: TextStyle(fontWeight: FontWeight.bold)),
                  SizedBox(height: 8),
                  SelectableText(
                    notification.licenseKey,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.green[700],
                    ),
                  ),
                  SizedBox(height: 12),
                  Text('Hết hạn: ${notification.formattedExpiryDate}'),
                ],
              ),
            ),
            SizedBox(height: 16),
            Text(
              '⚠️ Vui lòng lưu lại License Key này!',
              style: TextStyle(color: Colors.orange[700], fontWeight: FontWeight.w500),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              // Copy to clipboard
              // Clipboard.setData(ClipboardData(text: notification.licenseKey));
              // ScaffoldMessenger.of(context).showSnackBar(
              //   SnackBar(content: Text('Đã copy License Key!')),
              // );
            },
            child: Text('Copy'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              // Navigate to activate page or refresh
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            child: Text('Kích hoạt ngay'),
          ),
        ],
      ),
    );
  }
  
  @override
  void dispose() {
    _paymentWs.disconnect();
    _pollingTimer?.cancel();
    super.dispose();
  }
}

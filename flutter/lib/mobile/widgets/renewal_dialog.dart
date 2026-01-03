import 'package:flutter/material.dart';
import 'package:flutter_hbb/services/product_service.dart';
import 'package:flutter_hbb/models/product_model.dart';
import '../pages/payment_screen.dart';

class RenewalDialog extends StatefulWidget {
  final String currentTier;
  final String licenseKey;
  final int? expiresAt;

  const RenewalDialog({
    Key? key,
    required this.currentTier,
    required this.licenseKey,
    this.expiresAt,
  }) : super(key: key);

  @override
  _RenewalDialogState createState() => _RenewalDialogState();
}

class _RenewalDialogState extends State<RenewalDialog> {
  List<Product> _products = [];
  bool _isLoading = true;
  String? _selectedTier;

  @override
  void initState() {
    super.initState();
    _loadProducts();
  }

  Future<void> _loadProducts() async {
    try {
      final products = await ProductService.fetchProducts();
      setState(() {
        _products = products;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  bool get _isSameTier => _selectedTier == widget.currentTier;

  int _getDaysRemaining() {
    if (widget.expiresAt == null) return 0;
    final expiry = DateTime.fromMillisecondsSinceEpoch(widget.expiresAt!);
    return expiry.difference(DateTime.now()).inDays;
  }

  @override
  Widget build(BuildContext context) {
    final daysRemaining = _getDaysRemaining();

    return AlertDialog(
      title: Row(
        children: [
          Icon(Icons.autorenew, color: Colors.blue),
          SizedBox(width: 8),
          Text('Gia hạn License'),
        ],
      ),
      content: _isLoading
          ? Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Gói hiện tại: ${widget.currentTier.toUpperCase()}',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  if (daysRemaining > 0) ...[
                    SizedBox(height: 8),
                    Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.orange.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.orange.shade200),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.warning_amber, color: Colors.orange, size: 20),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Còn $daysRemaining ngày. Nên chờ gói cũ hết hạn để tránh lãng phí.',
                              style: TextStyle(fontSize: 13, color: Colors.orange.shade900),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  SizedBox(height: 16),
                  Text('Chọn gói gia hạn:', style: TextStyle(fontWeight: FontWeight.w500)),
                  SizedBox(height: 8),
                  ..._products.map((product) => RadioListTile<String>(
                    title: Text(product.name),
                    subtitle: Text('${product.price.toStringAsFixed(0)}đ / ${product.durationDays} ngày'),
                    value: product.tier,
                    groupValue: _selectedTier,
                    onChanged: (value) => setState(() => _selectedTier = value),
                    dense: true,
                  )).toList(),
                  if (_selectedTier != null) ...[
                    SizedBox(height: 12),
                    Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: _isSameTier ? Colors.green.shade50 : Colors.blue.shade50,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            _isSameTier ? Icons.extension : Icons.add_circle,
                            color: _isSameTier ? Colors.green : Colors.blue,
                            size: 20,
                          ),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _isSameTier
                                  ? 'Cùng gói → Gia hạn license đang active'
                                  : 'Khác gói → Tạo license mới (không tự động kích hoạt)',
                              style: TextStyle(
                                fontSize: 13,
                                color: _isSameTier ? Colors.green.shade900 : Colors.blue.shade900,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Hủy'),
        ),
        ElevatedButton(
          onPressed: _selectedTier == null
              ? null
              : () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => PaymentScreen(
                        preSelectedTier: _selectedTier,
                        renewLicenseKey: _isSameTier ? widget.licenseKey : null,
                      ),
                    ),
                  );
                },
          child: Text('Tiếp tục'),
        ),
      ],
    );
  }
}

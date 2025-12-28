import 'package:flutter/material.dart';
import 'payment_qr_screen.dart';

class PaymentScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Mua License AFK Zone'),
        backgroundColor: Colors.deepPurple,
      ),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          Text(
            'Chọn gói license',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 24),
          _buildTierSection(context, 'Basic', Colors.blue, [
            {'days': 7, 'price': '1.000đ'},
            {'days': 30, 'price': '50.000đ'},
            {'days': 90, 'price': '120.000đ'},
          ], 'basic'),
          SizedBox(height: 16),
          _buildTierSection(context, 'Pro', Colors.purple, [
            {'days': 30, 'price': '100.000đ'},
            {'days': 90, 'price': '250.000đ'},
          ], 'pro'),
          SizedBox(height: 16),
          _buildTierSection(context, 'Enterprise', Colors.orange, [
            {'days': 30, 'price': '200.000đ'},
            {'days': 90, 'price': '500.000đ'},
          ], 'enterprise'),
        ],
      ),
    );
  }

  Widget _buildTierSection(BuildContext context, String name, Color color, List<Map<String, dynamic>> options, String tier) {
    return Card(
      elevation: 4,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              name,
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color),
            ),
            SizedBox(height: 12),
            ...options.map((opt) => Padding(
              padding: EdgeInsets.only(bottom: 8),
              child: ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (c) => PaymentQRScreen(
                        tier: tier,
                        durationDays: opt['days'] as int,
                      ),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: color,
                  minimumSize: Size(double.infinity, 56),
                ),
                child: Text(
                  '${opt['days']} ngày - ${opt['price']}',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
              ),
            )).toList(),
          ],
        ),
      ),
    );
  }
}

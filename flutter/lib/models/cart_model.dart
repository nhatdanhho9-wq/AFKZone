import 'product_model.dart';

class CartItem {
  final Product product;
  int quantity;

  CartItem({
    required this.product,
    this.quantity = 1,
  });

  int get totalPrice => product.price * quantity;

  String get formattedTotalPrice {
    final total = totalPrice;
    if (total >= 1000000) {
      return '${(total / 1000000).toStringAsFixed(1)}M';
    } else if (total >= 1000) {
      return '${(total / 1000).toStringAsFixed(0)}.000d';
    }
    return '${total}d';
  }

  Map<String, dynamic> toJson() {
    return {
      'product_id': product.id,
      'quantity': quantity,
      'price': product.price,
      'tier': product.tier,
      'duration_days': product.durationDays,
    };
  }
}


class Product {
  final int id;
  final String name;
  final String tier;
  final int durationDays;
  final int price;
  final int maxDevices;
  final bool isActive;
  final int displayOrder;
  final String? description;

  Product({
    required this.id,
    required this.name,
    required this.tier,
    required this.durationDays,
    required this.price,
    required this.maxDevices,
    required this.isActive,
    required this.displayOrder,
    this.description,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'],
      tier: json['tier'],
      durationDays: json['duration_days'],
      price: json['price'],
      maxDevices: json['max_devices'],
      isActive: json['is_active'],
      displayOrder: json['display_order'],
      description: json['description'],
    );
  }

  String get formattedPrice {
    if (price >= 1000000) {
      return '${(price / 1000000).toStringAsFixed(1)}M';
    } else if (price >= 1000) {
      return '${(price / 1000).toStringAsFixed(0)}.000d';
    }
    return '${price}d';
  }

  String get tierDisplayName {
    switch (tier) {
      case 'basic':
        return 'Basic';
      case 'pro':
        return 'Pro';
      case 'enterprise':
        return 'Enterprise';
      default:
        return tier;
    }
  }
}


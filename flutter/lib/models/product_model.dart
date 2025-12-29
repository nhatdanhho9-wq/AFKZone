class Product {
  final int id;
  final String name;
  final String tier;
  final int durationDays;
  final int price;
  final String displayPrice;  // NEW: from API
  final int maxDevices;
  final String maxDevicesDisplay;  // NEW: from API
  final bool isActive;
  final int displayOrder;
  final String? description;

  Product({
    required this.id,
    required this.name,
    required this.tier,
    required this.durationDays,
    required this.price,
    required this.displayPrice,
    required this.maxDevices,
    required this.maxDevicesDisplay,
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
      displayPrice: json['display_price'],  // NEW
      maxDevices: json['max_devices'],
      maxDevicesDisplay: json['max_devices_display'],  // NEW
      isActive: json['is_active'],
      displayOrder: json['display_order'],
      description: json['description'],
    );
  }

  // Simple accessor - all formatting done by API
  String get formattedPrice => displayPrice;

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


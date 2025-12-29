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
    // Ensure price is int (API might return string)
    int price;
    if (json['price'] is int) {
      price = json['price'];
    } else if (json['price'] is String) {
      price = int.tryParse(json['price']) ?? 0;
    } else {
      price = json['price']?.toInt() ?? 0;
    }
    
    return Product(
      id: json['id'],
      name: json['name'] ?? '',
      tier: json['tier'],
      durationDays: json['duration_days'],
      price: price,
      displayPrice: json['display_price'] ?? '',
      maxDevices: json['max_devices'],
      maxDevicesDisplay: json['max_devices_display'] ?? '',
      isActive: json['is_active'] ?? true,
      displayOrder: json['display_order'] ?? 0,
      description: json['description'],
    );
  }

  // Simple accessor - all formatting done by API
  String get formattedPrice => displayPrice;

  // Use name from API instead of hardcoded tier names
  String get tierDisplayName => name.isNotEmpty ? name : tier.toUpperCase();
}


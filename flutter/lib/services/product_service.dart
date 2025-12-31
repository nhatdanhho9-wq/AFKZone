import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_hbb/models/product_model.dart';

class ProductService {
  static const String API_URL = 'https://api.afkzone.cloud';

  static Future<List<Product>> fetchProducts({bool activeOnly = true, bool forceRefresh = true}) async {
    try {
      // Add cache-busting timestamp to ensure fresh data
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final uri = Uri.parse('$API_URL/products').replace(
        queryParameters: {
          'active_only': activeOnly.toString(),
          if (forceRefresh) '_t': timestamp.toString(), // Cache-busting parameter
        },
      );
      
      print('🔄 Fetching products from API: $uri');
      final response = await http.get(
        uri,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> productsJson = data['products'];
        final products = productsJson.map((json) => Product.fromJson(json)).toList();
        print('✅ Loaded ${products.length} products from API');
        // Log prices for debugging
        for (var p in products) {
          print('  - ${p.tier} ${p.durationDays} ngày: ${p.displayPrice} (price: ${p.price})');
        }
        return products;
      } else {
        throw Exception('Failed to load products: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Error fetching products: $e');
      rethrow;
    }
  }

  static Future<Map<String, List<Product>>> fetchProductsByTier() async {
    final products = await fetchProducts();
    // Group products by tier DYNAMICALLY instead of hardcoding
    final Map<String, List<Product>> productsByTier = {};

    for (var product in products) {
      final tier = product.tier;
      if (!productsByTier.containsKey(tier)) {
        productsByTier[tier] = [];
      }
      productsByTier[tier]!.add(product);
    }
    
    print('📦 Grouped products into ${productsByTier.keys.length} tiers: ${productsByTier.keys.join(", ")}');
    return productsByTier;
  }

  static Future<Product?> getProductById(int id) async {
    try {
      final products = await fetchProducts(activeOnly: false);
      return products.firstWhere(
        (p) => p.id == id,
        orElse: () => throw Exception('Product not found'),
      );
    } catch (e) {
      print('Error getting product by ID: $e');
      return null;
    }
  }

  /// Fetch tier names from /tiers API
  /// Returns: Map<tier_key, tier_name>
  static Future<Map<String, String>> fetchTierNames() async {
    try {
      final response = await http.get(
        Uri.parse('$API_URL/tiers'),
        headers: {'Cache-Control': 'no-cache'},
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> tiersJson = data['tiers'] ?? data ?? [];
        
        final Map<String, String> tierNames = {};
        for (var tier in tiersJson) {
          if (tier['is_active'] == true) {
            // tier_key -> name (use name field from API)
            tierNames[tier['tier_key']] = tier['name'] ?? tier['tier_key'];
          }
        }
        
        print('📋 Loaded tier names: $tierNames');
        return tierNames;
      } else {
        print('⚠️ Failed to load tiers: ${response.statusCode}');
        return {};
      }
    } catch (e) {
      print('❌ Error fetching tier names: $e');
      return {};
    }
  }
}


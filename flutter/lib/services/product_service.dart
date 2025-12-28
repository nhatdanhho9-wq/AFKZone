import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/product_model.dart';

class ProductService {
  static const String API_URL = 'https://api.afkzone.cloud';

  static Future<List<Product>> fetchProducts({bool activeOnly = true}) async {
    try {
      final uri = Uri.parse('$API_URL/products').replace(
        queryParameters: {'active_only': activeOnly.toString()},
      );
      
      final response = await http.get(uri).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> productsJson = data['products'];
        return productsJson.map((json) => Product.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load products: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching products: $e');
      rethrow;
    }
  }

  static Future<Map<String, List<Product>>> fetchProductsByTier() async {
    final products = await fetchProducts();
    final Map<String, List<Product>> productsByTier = {
      'basic': [],
      'pro': [],
      'enterprise': [],
    };

    for (var product in products) {
      if (productsByTier.containsKey(product.tier)) {
        productsByTier[product.tier]!.add(product);
      }
    }

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
}


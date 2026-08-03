import 'package:dio/dio.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/endpoints.dart';
import '../models/menu_model.dart';

class MenuService {
  final Dio _dio = ApiClient().dio;

  Future<Map<String, dynamic>> getMenu({
    int? categoryId,
    String? search,
    String? sort,
  }) async {
    final queryParams = <String, dynamic>{};
    if (categoryId != null) queryParams["category_id"] = categoryId;
    if (search != null && search.isNotEmpty) {
      queryParams["search"] = search;
    }
    if (sort != null && sort.isNotEmpty) queryParams["sort"] = sort;

    final response = await _dio.get(
      Endpoints.menu,
      queryParameters: queryParams.isNotEmpty ? queryParams : null,
    );

    return response.data as Map<String, dynamic>;
  }

  List<MenuModel> parseItems(Map<String, dynamic> data) {
    final items = data["items"] as List<dynamic>? ?? [];
    return items
        .map((e) => MenuModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  List<Map<String, dynamic>> parseCategories(Map<String, dynamic> data) {
    final categories = data["categories"] as List<dynamic>? ?? [];
    return categories
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }

  Future<Map<String, dynamic>> getMenuDetail(int id) async {
    final response = await _dio.get(Endpoints.menuDetail(id));
    return response.data as Map<String, dynamic>;
  }
}

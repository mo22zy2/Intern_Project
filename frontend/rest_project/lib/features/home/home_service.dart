import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/endpoints.dart';
import '../menu/models/menu_model.dart';

class HomeService {
  final Dio _dio = ApiClient().dio;

  Future<Map<String, dynamic>> getHomeData() async {
    final response = await _dio.get(Endpoints.home);
    return response.data as Map<String, dynamic>;
  }

  List<MenuModel> parsePopular(Map<String, dynamic> data) {
    final popular = data["popular"] as List<dynamic>? ?? [];
    return popular
        .map((e) => MenuModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}

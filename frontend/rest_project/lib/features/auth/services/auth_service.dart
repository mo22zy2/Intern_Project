import 'package:dio/dio.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/endpoints.dart';

class AuthService {
  final Dio _dio = ApiClient().dio;

  Future<Map<String, dynamic>> login({
    required String username,
    required String password,
  }) async {
    final response = await _dio.post(
      Endpoints.login,
      data: {
        "username": username,
        "password": password,
      },
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> register({
    required String username,
    required String password,
    required String confirmPassword,
    required String email,
    required String firstName,
    required String lastName,
    String? phone,
    String? birth,
  }) async {
    final response = await _dio.post(
      Endpoints.register,
      data: {
        "username": username,
        "password": password,
        "confirm_password": confirmPassword,
        "email": email,
        "first_name": firstName,
        "last_name": lastName,
        if (phone != null) "phone": phone,
        if (birth != null) "birth": birth,
      },
    );
    return response.data as Map<String, dynamic>;
  }
}

import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/endpoints.dart';

class ProfileService {
  final Dio _dio = ApiClient().dio;

  Future<Map<String, dynamic>> getProfile() async {
    final response = await _dio.get(Endpoints.profile);
    return response.data as Map<String, dynamic>;
  }

  Future<void> updateProfile({
    String? firstName,
    String? lastName,
    String? email,
    String? phone,
  }) async {
    await _dio.put(
      Endpoints.editProfile,
      data: {
        if (firstName != null) "first_name": firstName,
        if (lastName != null) "last_name": lastName,
        if (email != null) "email": email,
        if (phone != null) "phone": phone,
      },
    );
  }

  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
    required String confirmPassword,
  }) async {
    await _dio.put(
      Endpoints.changePassword,
      data: {
        "old_password": oldPassword,
        "new_password": newPassword,
        "confirm_password": confirmPassword,
      },
    );
  }
}

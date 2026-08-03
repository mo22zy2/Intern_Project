import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../../core/api/api_client.dart';
import '../services/auth_service.dart';

class AuthProvider extends ChangeNotifier {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  final AuthService _service = AuthService();

  bool _isLoading = false;
  String? _token;
  int? _userId;
  String? _username;

  bool get isLoading => _isLoading;
  bool get isAuthenticated => _token != null;
  String? get token => _token;
  int? get userId => _userId;
  String? get username => _username;

  Future<void> init() async {
    _token = await _storage.read(key: "auth_token");
    _userId = _token != null
        ? int.tryParse(
            await _storage.read(key: "user_id") ?? "",
          )
        : null;
    _username = await _storage.read(key: "username");
    ApiClient().setToken(_token);
    notifyListeners();
  }

  Future<String?> login({
    required String username,
    required String password,
  }) async {
    _isLoading = true;
    notifyListeners();

    try {
      final data = await _service.login(
        username: username,
        password: password,
      );

      _token = data["access_token"] as String;
      _userId = data["user_id"] as int;
      _username = data["username"] as String;

      ApiClient().setToken(_token);
      await _storage.write(key: "auth_token", value: _token);
      await _storage.write(key: "user_id", value: _userId.toString());
      await _storage.write(key: "username", value: _username);
      await _storage.write(key: "onboarding_done", value: "true");

      _isLoading = false;
      notifyListeners();
      return null;
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return _extractError(e);
    }
  }

  Future<String?> register({
    required String username,
    required String password,
    required String confirmPassword,
    required String email,
    required String firstName,
    required String lastName,
    String? phone,
    String? birth,
  }) async {
    _isLoading = true;
    notifyListeners();

    try {
      final data = await _service.register(
        username: username,
        password: password,
        confirmPassword: confirmPassword,
        email: email,
        firstName: firstName,
        lastName: lastName,
        phone: phone,
        birth: birth,
      );

      _token = data["access_token"] as String;
      _userId = data["user_id"] as int;
      _username = data["username"] as String;

      ApiClient().setToken(_token);
      await _storage.write(key: "auth_token", value: _token);
      await _storage.write(key: "user_id", value: _userId.toString());
      await _storage.write(key: "username", value: _username);
      await _storage.write(key: "onboarding_done", value: "true");

      _isLoading = false;
      notifyListeners();
      return null;
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return _extractError(e);
    }
  }

  Future<void> logout() async {
    _token = null;
    _userId = null;
    _username = null;
    ApiClient().setToken(null);
    await _storage.deleteAll();
    notifyListeners();
  }

  String _extractError(Object e) {
    if (e is DioException) {
      final data = e.response?.data;
      if (data is Map<String, dynamic> && data.containsKey("detail")) {
        return data["detail"] as String;
      }
      return "Connection error. Check your connection and try again.";
    }
    return "An unexpected error occurred.";
  }
}

import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/endpoints.dart';

class PaymentService {
  final Dio _dio = ApiClient().dio;

  Future<List<Map<String, dynamic>>> getMethods() async {
    final response = await _dio.get(Endpoints.paymentMethods);
    return (response.data as List<dynamic>)
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }

  Future<void> addMethod({
    required String cardNumber,
    required String cardholderName,
    required String expiry,
    required String cvv,
    bool isDefault = false,
  }) async {
    await _dio.post(
      Endpoints.addPaymentMethod,
      data: {
        "card_number": cardNumber,
        "cardholder_name": cardholderName,
        "expiry": expiry,
        "cvv": cvv,
        "is_default": isDefault,
      },
    );
  }

  Future<void> deleteMethod(int id) async {
    await _dio.delete(Endpoints.deletePaymentMethod(id));
  }

  Future<void> setDefault(int id) async {
    await _dio.put(Endpoints.defaultPaymentMethod(id));
  }

  Future<List<Map<String, dynamic>>> getPaymentHistory() async {
    final response = await _dio.get(Endpoints.payments);
    return (response.data as List<dynamic>)
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }
}

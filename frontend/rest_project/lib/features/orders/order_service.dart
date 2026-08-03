import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/endpoints.dart';
import '../cart/models/cart_item.dart';

class OrderService {
  final Dio _dio = ApiClient().dio;

  Future<Map<String, dynamic>> getCheckoutData() async {
    final response = await _dio.get(Endpoints.checkout);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> placeOrder({
    required String deliveryType,
    String? deliveryAddress,
    List<CartItem>? items,
    required String paymentType,
    int? paymentMethodId,
    int? reservationId,
    String? reservationDate,
    String? reservationTime,
    int? seats,
    String? cardNumber,
  }) async {
    final response = await _dio.post(
      Endpoints.placeOrder,
      data: {
        "delivery_type": deliveryType,
        if (deliveryAddress != null && deliveryAddress.isNotEmpty)
          "delivery_address": deliveryAddress,
        if (reservationId != null) "reservation_id": reservationId,
        if (reservationDate != null) "reservation_date": reservationDate,
        if (reservationTime != null) "reservation_time": reservationTime,
        if (seats != null) "seats": seats,
        "payment_type": paymentType,
        if (paymentMethodId != null) "payment_method_id": paymentMethodId,
        if (cardNumber != null) "card_number": cardNumber,
        "items": items?.map((item) => item.toOrderMap()).toList() ?? [],
      },
    );
    return response.data as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getOrders() async {
    final response = await _dio.get(Endpoints.orders);
    return (response.data as List<dynamic>)
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }

  Future<Map<String, dynamic>> getOrderDetail(int orderId) async {
    final response = await _dio.get(Endpoints.orderDetail(orderId));
    return response.data as Map<String, dynamic>;
  }
}

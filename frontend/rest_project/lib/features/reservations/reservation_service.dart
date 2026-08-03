import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/endpoints.dart';

class ReservationService {
  final Dio _dio = ApiClient().dio;

  Future<List<Map<String, dynamic>>> getReservations() async {
    final response = await _dio.get(Endpoints.reservations);
    return (response.data as List<dynamic>)
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }

  Future<void> createReservation({
    required String date,
    required String time,
    required int seats,
  }) async {
    await _dio.post(
      Endpoints.newReservation,
      data: {
        "reservation_date": date,
        "reservation_time": time,
        "seats": seats,
      },
    );
  }

  Future<void> updateReservation({
    required int id,
    String? date,
    String? time,
    int? seats,
  }) async {
    await _dio.put(
      Endpoints.editReservation(id),
      data: {
        if (date != null) "reservation_date": date,
        if (time != null) "reservation_time": time,
        if (seats != null) "seats": seats,
      },
    );
  }

  Future<void> cancelReservation(int id) async {
    await _dio.delete(Endpoints.cancelReservation(id));
  }
}

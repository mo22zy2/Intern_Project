import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/api/endpoints.dart';

class ReviewService {
  final Dio _dio = ApiClient().dio;

  Future<List<Map<String, dynamic>>> getMyReviews() async {
    final response = await _dio.get(Endpoints.reviews);
    return (response.data as List<dynamic>)
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }

  Future<void> addReview({
    required int menuId,
    required int rating,
    required String comment,
  }) async {
    await _dio.post(
      Endpoints.addReview(menuId),
      data: {
        "rating": rating,
        "comment": comment,
      },
    );
  }

  Future<void> updateReview({
    required int reviewId,
    required int rating,
    required String comment,
  }) async {
    await _dio.put(
      Endpoints.editReview(reviewId),
      data: {
        "rating": rating,
        "comment": comment,
      },
    );
  }

  Future<void> deleteReview(int reviewId) async {
    await _dio.delete(Endpoints.deleteReview(reviewId));
  }
}

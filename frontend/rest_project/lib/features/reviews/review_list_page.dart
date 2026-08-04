import 'package:flutter/material.dart';

import '../../core/routes.dart';
import '../../core/theme/app_colors.dart';
import 'review_service.dart';

class ReviewListPage extends StatefulWidget {
  const ReviewListPage({super.key});

  @override
  State<ReviewListPage> createState() => _ReviewListPageState();
}

class _ReviewListPageState extends State<ReviewListPage> {
  final ReviewService _service = ReviewService();
  List<Map<String, dynamic>>? _reviews;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final data = await _service.getMyReviews();
      if (mounted) setState(() => _reviews = data);
    } catch (_) {
      if (mounted) setState(() => _reviews = []);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _delete(int id) async {
    try {
      await _service.deleteReview(id);
      _load();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to delete review")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "MY REVIEWS",
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 2),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _reviews == null || _reviews!.isEmpty
              ? const Center(
                  child: Text(
                    "No reviews yet",
                    style: TextStyle(color: Colors.white54, fontSize: 18),
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(24),
                  itemCount: _reviews!.length,
                  itemBuilder: (context, index) {
                    final r = _reviews![index];
                    final rating = r["rating"] as int? ?? 0;
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: ListTile(
                        contentPadding: const EdgeInsets.all(16),
                        title: Text(
                          r["menu_name"] as String? ??
                              (r["menu_id"] != null
                                  ? "Menu #${r["menu_id"]}"
                                  : "Menu Item"),
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 4),
                            Row(
                              children: List.generate(
                                5,
                                (i) => Icon(
                                  i < rating
                                      ? Icons.star
                                      : Icons.star_border,
                                  color: AppColors.secondary,
                                  size: 16,
                                ),
                              ),
                            ),
                            if (r["comment"] != null) ...[
                              const SizedBox(height: 4),
                              Text(
                                r["comment"] as String,
                                style: const TextStyle(
                                  color: AppColors.subtitle,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                            const SizedBox(height: 4),
                            Text(
                              r["created_at"] as String? ?? "",
                              style: const TextStyle(
                                color: Colors.white24,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: const Icon(
                                Icons.edit_outlined,
                                size: 20,
                              ),
                              color: Colors.white54,
                              onPressed: () => Navigator.pushNamed(
                                context,
                                AppRoutes.reviewForm,
                                arguments: {
                                  'reviewId': r["id"] as int,
                                  'initialRating': rating,
                                  'initialComment':
                                      r["comment"] as String? ?? "",
                                },
                              ).then((_) => _load()),
                            ),
                            IconButton(
                              icon: const Icon(
                                Icons.delete_outline,
                                size: 20,
                              ),
                              color: Colors.red,
                              onPressed: () => _delete(r["id"] as int),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

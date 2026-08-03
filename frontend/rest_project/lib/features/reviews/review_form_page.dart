import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import 'review_service.dart';

class ReviewFormPage extends StatefulWidget {
  final int? reviewId;
  final int? menuId;
  final int initialRating;
  final String initialComment;

  const ReviewFormPage({
    super.key,
    this.reviewId,
    this.menuId,
    this.initialRating = 5,
    this.initialComment = "",
  });

  @override
  State<ReviewFormPage> createState() => _ReviewFormPageState();
}

class _ReviewFormPageState extends State<ReviewFormPage> {
  final _commentController = TextEditingController();
  final ReviewService _service = ReviewService();
  int _rating = 5;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _rating = widget.initialRating;
    _commentController.text = widget.initialComment;
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_commentController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please write a comment")),
      );
      return;
    }

    setState(() => _saving = true);

    try {
      if (widget.reviewId != null) {
        await _service.updateReview(
          reviewId: widget.reviewId!,
          rating: _rating,
          comment: _commentController.text.trim(),
        );
      } else if (widget.menuId != null) {
        await _service.addReview(
          menuId: widget.menuId!,
          rating: _rating,
          comment: _commentController.text.trim(),
        );
      }
      if (mounted) Navigator.of(context).pop();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to save review")),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.reviewId != null ? "EDIT REVIEW" : "NEW REVIEW",
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 400),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                "Rating",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  5,
                  (i) => IconButton(
                    icon: Icon(
                      i < _rating ? Icons.star : Icons.star_border,
                      color: AppColors.secondary,
                      size: 40,
                    ),
                    onPressed: () => setState(() => _rating = i + 1),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              TextFormField(
                controller: _commentController,
                decoration: const InputDecoration(
                  labelText: "Comment",
                  alignLabelWithHint: true,
                ),
                maxLines: 4,
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _saving ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: _saving
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text(
                          "SAVE",
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1,
                          ),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

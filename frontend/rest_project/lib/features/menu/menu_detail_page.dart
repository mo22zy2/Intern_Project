import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:rest_project/features/auth/provider/auth_provider.dart';
import 'package:rest_project/features/cart/provider/cart_provider.dart';
import 'package:rest_project/features/menu/services/menu_service.dart';

import '../../core/routes.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/app_navbar.dart';
import 'models/menu_model.dart';
import 'widgets/option_tile.dart';
import 'widgets/quantity_selector.dart';
import 'widgets/review_card.dart';

class MenuDetailPage extends StatelessWidget {
  final MenuModel item;

  const MenuDetailPage({
    super.key,
    required this.item,
  });

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;

    final isDesktop = width > 900;

    return Scaffold(
      appBar: const AppNavbar(),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(32),
        child: isDesktop
            ? Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: _ImageSection(item: item),
                  ),
                  const SizedBox(width: 40),
                  Expanded(
                    child: _InfoSection(item: item),
                  ),
                ],
              )
            : Column(
                children: [
                  _ImageSection(item: item),
                  const SizedBox(height: 30),
                  _InfoSection(item: item),
                ],
              ),
      ),
    );
  }
}

class _ImageSection extends StatelessWidget {
  final MenuModel item;

  const _ImageSection({
    required this.item,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Image.network(
        item.image,
        fit: BoxFit.cover,
        height: 500,
        width: double.infinity,
      ),
    );
  }
}

class _InfoSection extends StatefulWidget {
  final MenuModel item;

  const _InfoSection({
    required this.item,
  });

  @override
  State<_InfoSection> createState() => _InfoSectionState();
}

class _InfoSectionState extends State<_InfoSection> {
  final Set<String> _selectedOptionNames = {};
  int _quantity = 1;

  final MenuService _menuService = MenuService();
  List<Map<String, dynamic>> _reviews = [];
  Map<String, dynamic>? _userReview;
  bool _reviewsLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchReviews();
  }

  Future<void> _fetchReviews() async {
    try {
      final detail = await _menuService.getMenuDetail(
        int.parse(widget.item.id),
      );
      if (!mounted) return;
      setState(() {
        _reviews = (detail["reviews"] as List<dynamic>?)
                ?.map((e) => e as Map<String, dynamic>)
                .toList() ??
            [];
        _userReview = detail["user_review"] as Map<String, dynamic>?;
        _reviewsLoading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _reviewsLoading = false);
    }
  }

  Future<void> _handleReviewAction() async {
    final auth = context.read<AuthProvider>();

    if (!auth.isAuthenticated) {
      Navigator.pushNamed(context, AppRoutes.login);
      return;
    }

    if (_userReview != null) {
      await Navigator.pushNamed(
        context,
        AppRoutes.reviewForm,
        arguments: {
          'reviewId': _userReview!["id"] as int,
          'initialRating': _userReview!["rating"] as int? ?? 5,
          'initialComment': _userReview!["comment"] as String? ?? "",
        },
      );
    } else {
      await Navigator.pushNamed(
        context,
        AppRoutes.reviewForm,
        arguments: {
          'menuId': int.parse(widget.item.id),
          'initialRating': 5,
          'initialComment': "",
        },
      );
    }
    _fetchReviews();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.item.category.toUpperCase(),
          style: const TextStyle(
            color: AppColors.secondary,
            letterSpacing: 2,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          widget.item.name,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 42,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 20),
        Text(
          "${widget.item.price} EGP",
          style: const TextStyle(
            color: AppColors.primary,
            fontSize: 32,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 20),
        Row(
          children: [
            const Icon(
              Icons.star,
              color: AppColors.secondary,
            ),
            const SizedBox(width: 8),
            Text(
              widget.item.rating.toString(),
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Text(
          "Ordered ${widget.item.popularity}+ times",
          style: const TextStyle(
            color: Colors.white60,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 6,
          ),
          decoration: BoxDecoration(
            color: widget.item.available
                ? Colors.green.withOpacity(.15)
                : Colors.red.withOpacity(.15),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            widget.item.available ? "Available" : "Unavailable",
            style: TextStyle(
              color: widget.item.available ? Colors.green : Colors.red,
            ),
          ),
        ),
        const SizedBox(height: 35),
        const Divider(),
        const SizedBox(height: 25),
        const Text(
          "Customization",
          style: TextStyle(
            color: Colors.white,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 20),
        ...widget.item.options.map(
          (e) => OptionTile(
            option: e,
            isSelected: _selectedOptionNames.contains(e.name),
            onChanged: (v) {
              setState(() {
                if (v) {
                  _selectedOptionNames.add(e.name);
                } else {
                  _selectedOptionNames.remove(e.name);
                }
              });
            },
          ),
        ),
        const SizedBox(height: 30),
        const Text(
          "Quantity",
          style: TextStyle(
            color: Colors.white,
            fontSize: 22,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 15),
        QuantitySelector(
          value: _quantity,
          onChanged: (v) {
            setState(() {
              _quantity = v;
            });
          },
        ),
        const SizedBox(height: 35),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () {
              final selectedOptions = widget.item.options
                  .where((o) => _selectedOptionNames.contains(o.name))
                  .toList();
              context.read<CartProvider>().addItem(
                    widget.item,
                    options: selectedOptions,
                    quantity: _quantity,
                  );
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text("Added to cart"),
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: const Text(
              "ADD TO CART",
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        const SizedBox(height: 15),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: () {
              final selectedOptions = widget.item.options
                  .where((o) => _selectedOptionNames.contains(o.name))
                  .toList();
              context.read<CartProvider>().addItem(
                    widget.item,
                    options: selectedOptions,
                    quantity: _quantity,
                  );
              Navigator.pushNamed(context, AppRoutes.cart);
            },
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Text("PROCEED TO CHECKOUT"),
            ),
          ),
        ),
        const SizedBox(height: 45),
        const Divider(),
        const SizedBox(height: 25),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              "Reviews",
              style: TextStyle(
                color: Colors.white,
                fontSize: 30,
                fontWeight: FontWeight.bold,
              ),
            ),
            TextButton.icon(
              onPressed: _handleReviewAction,
              icon: Icon(
                _userReview != null
                    ? Icons.edit_outlined
                    : Icons.rate_review_outlined,
                size: 20,
              ),
              label: Text(
                !context.watch<AuthProvider>().isAuthenticated
                    ? "Log in"
                    : _userReview != null
                        ? "Edit"
                        : "Write",
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        if (_reviewsLoading)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(20),
              child: CircularProgressIndicator(),
            ),
          )
        else if (_reviews.isEmpty)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(20),
              child: Text(
                "No reviews yet. Be the first to review!",
                style: TextStyle(color: AppColors.subtitle, fontSize: 14),
              ),
            ),
          )
        else
          ...List.generate(
            _reviews.length,
            (i) => Padding(
              padding: EdgeInsets.only(bottom: i < _reviews.length - 1 ? 12 : 0),
              child: ReviewCard(
                name: _reviews[i]["username"] as String? ?? "",
                comment: _reviews[i]["comment"] as String? ?? "",
                rating: _reviews[i]["rating"] as int? ?? 0,
                createdAt: _reviews[i]["created_at"] as String?,
              ),
            ),
          ),
      ],
    );
  }
}

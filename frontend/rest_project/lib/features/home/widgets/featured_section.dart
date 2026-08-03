import 'package:flutter/material.dart';
import 'package:rest_project/features/home/widgets/featured_card.dart';

import '../../../core/theme/app_colors.dart';
import '../../menu/models/menu_model.dart';

class FeaturedSection extends StatelessWidget {
  final List<MenuModel> items;

  const FeaturedSection({super.key, this.items = const []});

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;

    int crossAxisCount;

    if (width >= 1200) {
      crossAxisCount = 4;
    } else if (width >= 900) {
      crossAxisCount = 3;
    } else if (width >= 600) {
      crossAxisCount = 2;
    } else {
      crossAxisCount = 1;
    }

    if (items.isEmpty) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      color: AppColors.background,
      padding: const EdgeInsets.symmetric(
        horizontal: 24,
        vertical: 60,
      ),
      child: Column(
        children: [
          const Text(
            "SIGNATURE DISHES",
            style: TextStyle(
              color: Colors.white,
              fontSize: 42,
              fontWeight: FontWeight.bold,
              letterSpacing: 3,
            ),
          ),
          const SizedBox(height: 40),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: items.length,
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: crossAxisCount,
              crossAxisSpacing: 20,
              mainAxisSpacing: 20,
              childAspectRatio: .72,
            ),
            itemBuilder: (context, index) {
              return FeaturedCard(
                item: items[index],
              );
            },
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

class StatsSection extends StatelessWidget {
  final int menuItems;
  final int categories;

  const StatsSection({
    super.key,
    this.menuItems = 0,
    this.categories = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.symmetric(vertical: 60),
      child: Row(
        children: [
          Expanded(
            child: _StatCard(
              number: "$menuItems",
              label: "MENU ITEMS",
            ),
          ),
          Expanded(
            child: _StatCard(
              number: "$categories",
              label: "CATEGORIES",
            ),
          ),
          const Expanded(
            child: _StatCard(
              number: "24/7",
              label: "FRESH KITCHEN",
            ),
          ),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String number;
  final String label;

  const _StatCard({
    required this.number,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          number,
          style: const TextStyle(
            color: AppColors.primary,
            fontSize: 42,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white54,
            letterSpacing: 2,
            fontSize: 12,
          ),
        ),
      ],
    );
  }
}

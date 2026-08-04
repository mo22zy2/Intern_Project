import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

class MenuFilterBar extends StatelessWidget {
  final List<Map<String, dynamic>> categories;
  final int? selectedCategoryId;
  final String selectedSort;
  final ValueChanged<int?>? onCategoryChanged;
  final ValueChanged<String?>? onSortChanged;

  const MenuFilterBar({
    super.key,
    this.categories = const [],
    this.selectedCategoryId,
    this.selectedSort = "popular",
    this.onCategoryChanged,
    this.onSortChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 16,
      runSpacing: 16,
      children: [
        SizedBox(
          width: 220,
          child: DropdownButtonFormField<int?>(
            dropdownColor: AppColors.surface,
            decoration: const InputDecoration(
              filled: true,
              fillColor: AppColors.surface,
            ),
            value: selectedCategoryId,
            items: [
              const DropdownMenuItem(
                value: null,
                child: Text("All Categories"),
              ),
              ...categories.map(
                (c) => DropdownMenuItem(
                  value: c["id"] as int,
                  child: Text(c["name"] as String),
                ),
              ),
            ],
            onChanged: onCategoryChanged,
          ),
        ),
        SizedBox(
          width: 220,
          child: DropdownButtonFormField<String>(
            dropdownColor: AppColors.surface,
            decoration: const InputDecoration(
              filled: true,
              fillColor: AppColors.surface,
            ),
            value: selectedSort,
            items: const [
              DropdownMenuItem(
                value: "popular",
                child: Text("Most Popular"),
              ),
              DropdownMenuItem(
                value: "price_low",
                child: Text("Price Low"),
              ),
              DropdownMenuItem(
                value: "price_high",
                child: Text("Price High"),
              ),
              DropdownMenuItem(
                value: "newest",
                child: Text("Newest"),
              ),
            ],
            onChanged: onSortChanged,
          ),
        ),
      ],
    );
  }
}

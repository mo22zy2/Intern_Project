import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../models/menu_option.dart';

class OptionTile extends StatelessWidget {
  final MenuOption option;
  final bool isSelected;
  final ValueChanged<bool> onChanged;

  const OptionTile({
    super.key,
    required this.option,
    required this.isSelected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return CheckboxListTile(
      value: isSelected,
      activeColor: AppColors.primary,
      title: Text(option.name),
      subtitle: Text(
        "+ ${option.extraPrice} EGP",
      ),
      onChanged: (v) {
        onChanged(v!);
      },
    );
  }
}

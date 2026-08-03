import 'package:flutter/material.dart';

class QuantitySelector extends StatelessWidget {
  final int value;
  final ValueChanged<int> onChanged;

  const QuantitySelector({
    super.key,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        IconButton(
          onPressed: value > 1
              ? () {
                  onChanged(value - 1);
                }
              : null,
          icon: const Icon(Icons.remove),
        ),
        Text(
          value.toString(),
          style: const TextStyle(
            fontSize: 22,
          ),
        ),
        IconButton(
          onPressed: () {
            onChanged(value + 1);
          },
          icon: const Icon(Icons.add),
        ),
      ],
    );
  }
}

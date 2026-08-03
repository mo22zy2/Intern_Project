import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import 'provider/cart_provider.dart';
import 'widgets/cart_item_card.dart';
import 'widgets/empty_cart.dart';
import 'widgets/order_summary.dart';

class CartPage extends StatelessWidget {
  const CartPage({super.key});

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "YOUR CART",
          style: TextStyle(
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
          ),
        ),
      ),
      body: cart.items.isEmpty
          ? const EmptyCart()
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "${cart.itemCount} item${cart.itemCount == 1 ? "" : "s"}",
                    style: const TextStyle(
                      color: AppColors.subtitle,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: cart.items.length,
                    separatorBuilder: (_, _) =>
                        const SizedBox(height: 12),
                    itemBuilder: (context, index) =>
                        CartItemCard(item: cart.items[index]),
                  ),
                  const SizedBox(height: 32),
                  const OrderSummary(),
                ],
              ),
            ),
    );
  }
}

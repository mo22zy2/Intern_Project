import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../features/auth/provider/auth_provider.dart';
import '../../features/cart/provider/cart_provider.dart';
import '../routes.dart';
import '../theme/app_colors.dart';

class AppNavbar extends StatelessWidget
    implements PreferredSizeWidget {
  const AppNavbar({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final cartCount = context.watch<CartProvider>().itemCount;

    return AppBar(
      title: const Text(
        "DJANGO EATS",
        style: TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.bold,
          letterSpacing: 2,
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pushNamed(context, AppRoutes.menu),
          child: const Text("MENU"),
        ),
        if (auth.isAuthenticated) ...[
          IconButton(
            icon: const Icon(Icons.receipt_outlined),
            tooltip: "Orders",
            onPressed: () =>
                Navigator.pushNamed(context, AppRoutes.orders),
          ),
          IconButton(
            icon: const Icon(Icons.calendar_month_outlined),
            tooltip: "Reservations",
            onPressed: () =>
                Navigator.pushNamed(context, AppRoutes.reservations),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: GestureDetector(
              onTap: () =>
                  Navigator.pushNamed(context, AppRoutes.profile),
              child: Center(
                child: Text(
                  auth.username ?? "",
                  style: const TextStyle(
                    color: AppColors.secondary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        ] else ...[
          TextButton(
            onPressed: () => Navigator.pushNamed(context, AppRoutes.login),
            child: const Text("LOGIN"),
          ),
          const SizedBox(width: 8),
          TextButton(
            onPressed: () =>
                Navigator.pushNamed(context, AppRoutes.register),
            child: const Text("REGISTER"),
          ),
        ],
        const SizedBox(width: 8),
        Stack(
          children: [
            IconButton(
              icon: const Icon(Icons.shopping_cart_outlined),
              onPressed: () =>
                  Navigator.pushNamed(context, AppRoutes.cart),
            ),
            if (cartCount > 0)
              Positioned(
                right: 4,
                top: 4,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: const BoxDecoration(
                    color: Colors.red,
                    shape: BoxShape.circle,
                  ),
                  child: Text(
                    "$cartCount",
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
          ],
        ),
        const SizedBox(width: 20),
      ],
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(70);
}

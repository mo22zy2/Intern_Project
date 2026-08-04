import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:rest_project/core/routes.dart';
import 'package:rest_project/core/theme/app_theme.dart';
import 'package:rest_project/features/auth/provider/auth_provider.dart';
import 'package:rest_project/features/cart/provider/cart_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final cartProvider = CartProvider();
  await cartProvider.loadFromStorage();

  final authProvider = AuthProvider();
  try {
    await authProvider.init();
  } catch (_) {
    // Startup must not crash if secure storage / network init fails.
  }

  runApp(
    DjangoEats(
      cartProvider: cartProvider,
      authProvider: authProvider,
    ),
  );
}

class DjangoEats extends StatelessWidget {
  final CartProvider cartProvider;
  final AuthProvider authProvider;

  const DjangoEats({
    super.key,
    required this.cartProvider,
    required this.authProvider,
  });

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: cartProvider),
        ChangeNotifierProvider.value(value: authProvider),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        initialRoute: AppRoutes.splash,
        onGenerateRoute: AppRoutes.onGenerateRoute,
      ),
    );
  }
}

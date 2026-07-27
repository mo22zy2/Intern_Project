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

  runApp(
    DjangoEats(cartProvider: cartProvider),
  );
}

class DjangoEats extends StatelessWidget {
  final CartProvider cartProvider;

  const DjangoEats({super.key, required this.cartProvider});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: cartProvider),
        ChangeNotifierProvider(create: (_) => AuthProvider()..init()),
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

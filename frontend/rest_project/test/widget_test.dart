import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:rest_project/core/theme/app_theme.dart';
import 'package:rest_project/features/auth/provider/auth_provider.dart';
import 'package:rest_project/features/cart/provider/cart_provider.dart';
import 'package:rest_project/features/home/home_page.dart';

import 'package:flutter/material.dart';

void main() {
  testWidgets('App renders home page', (WidgetTester tester) async {
    final cartProvider = CartProvider();
    final authProvider = AuthProvider();

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: cartProvider),
          ChangeNotifierProvider.value(value: authProvider),
        ],
        child: MaterialApp(
          theme: AppTheme.darkTheme,
          home: const HomePage(),
        ),
      ),
    );

    await tester.pump(const Duration(seconds: 11));

    expect(find.text("DJANGO EATS"), findsOneWidget);
  });
}

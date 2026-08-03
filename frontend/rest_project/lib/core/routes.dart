import 'package:flutter/material.dart';

import '../features/auth/login_page.dart';
import '../features/auth/register_page.dart';
import '../features/cart/cart_page.dart';
import '../features/checkout/checkout_page.dart';
import '../features/home/home_page.dart';
import '../features/menu/menu_detail_page.dart';
import '../features/menu/menu_page.dart';
import '../features/onboarding/onboarding_page.dart';
import '../features/orders/order_detail_page.dart';
import '../features/orders/order_history_page.dart';
import '../features/payment/payment_methods_page.dart';
import '../features/profile/profile_page.dart';
import '../features/reservations/reservation_form_page.dart';
import '../features/reservations/reservation_list_page.dart';
import '../features/reviews/review_form_page.dart';
import '../features/reviews/review_list_page.dart';
import '../features/splash/splash_page.dart';
import '../features/menu/models/menu_model.dart';

class AppRoutes {
  AppRoutes._();

  static const String home = '/';
  static const String menu = '/menu';
  static const String menuDetail = '/menu/detail';
  static const String cart = '/cart';
  static const String checkout = '/checkout';
  static const String orders = '/orders';
  static const String orderDetail = '/orders/detail';
  static const String reservations = '/reservations';
  static const String reservationCreate = '/reservations/create';
  static const String profile = '/profile';
  static const String editProfile = '/profile/edit';
  static const String changePassword = '/profile/change-password';
  static const String paymentMethods = '/payment-methods';
  static const String reviews = '/reviews';
  static const String reviewForm = '/reviews/form';
  static const String splash = '/splash';
  static const String onboarding = '/onboarding';
  static const String login = '/login';
  static const String register = '/register';
  static const String orderConfirmation = '/order-confirmation';

  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case home:
        return MaterialPageRoute(builder: (_) => const HomePage());
      case menu:
        return MaterialPageRoute(builder: (_) => const MenuPage());
      case menuDetail:
        final item = settings.arguments as MenuModel;
        return MaterialPageRoute(
          builder: (_) => MenuDetailPage(item: item),
        );
      case cart:
        return MaterialPageRoute(builder: (_) => const CartPage());
      case checkout:
        return MaterialPageRoute(builder: (_) => const CheckoutPage());
      case orders:
        return MaterialPageRoute(builder: (_) => const OrderHistoryPage());
      case orderDetail:
        final orderId = settings.arguments as int;
        return MaterialPageRoute(
          builder: (_) => OrderDetailPage(orderId: orderId),
        );
      case reservations:
        return MaterialPageRoute(
          builder: (_) => const ReservationListPage(),
        );
      case reservationCreate:
        return MaterialPageRoute(
          builder: (_) => const ReservationFormPage(),
        );
      case profile:
        return MaterialPageRoute(builder: (_) => const ProfilePage());
      case editProfile:
        return MaterialPageRoute(builder: (_) => const EditProfilePage());
      case changePassword:
        return MaterialPageRoute(
          builder: (_) => const ChangePasswordPage(),
        );
      case paymentMethods:
        return MaterialPageRoute(
          builder: (_) => const PaymentMethodsPage(),
        );
      case reviews:
        return MaterialPageRoute(builder: (_) => const ReviewListPage());
      case reviewForm:
        final args = settings.arguments as Map<String, dynamic>?;
        return MaterialPageRoute(
          builder: (_) => ReviewFormPage(
            reviewId: args?['reviewId'] as int?,
            menuId: args?['menuId'] as int?,
            initialRating: args?['initialRating'] as int? ?? 5,
            initialComment: args?['initialComment'] as String? ?? '',
          ),
        );
      case orderConfirmation:
        final orderData = settings.arguments as Map<String, dynamic>?;
        return MaterialPageRoute(
          builder: (_) => OrderConfirmationPage(orderData: orderData),
        );
      case splash:
        return MaterialPageRoute(builder: (_) => const SplashPage());
      case onboarding:
        return MaterialPageRoute(builder: (_) => const OnboardingPage());
      case login:
        return MaterialPageRoute(builder: (_) => const LoginPage());
      case register:
        return MaterialPageRoute(builder: (_) => const RegisterPage());
      default:
        return MaterialPageRoute(builder: (_) => const HomePage());
    }
  }
}

import 'dart:io';

import 'package:flutter/foundation.dart';

class Endpoints {
  Endpoints._();

  static String get baseUrl {
    const fromEnv = String.fromEnvironment('API_BASE_URL');
    if (fromEnv.isNotEmpty) return fromEnv;
    if (!kIsWeb && Platform.isAndroid) return 'http://10.0.2.2:8071';
    return 'http://localhost:8071';
  }

  static const String login = "/auth/login";
  static const String register = "/auth/register";
  static const String logout = "/auth/logout";

  static const String menu = "/menu/";
  static String menuDetail(int id) => "/menu/$id";

  static const String cart = "/cart/";
  static String cartAdd(int itemId) => "/cart/add/$itemId";
  static String cartUpdate(int itemId) => "/cart/update/$itemId";
  static String cartRemove(int itemId) => "/cart/remove/$itemId";

  static const String checkout = "/orders/checkout";
  static const String placeOrder = "/orders/checkout/place";
  static const String orders = "/orders/";
  static String orderDetail(int id) => "/orders/$id";

  static const String reservations = "/reservations/";
  static const String newReservation = "/reservations/new";
  static String editReservation(int id) => "/reservations/$id/edit";
  static String cancelReservation(int id) =>
      "/reservations/$id/cancel";

  static const String reviews = "/reviews/";
  static String addReview(int menuId) => "/reviews/add/$menuId";
  static String editReview(int id) => "/reviews/$id/edit";
  static String deleteReview(int id) => "/reviews/$id/delete";

  static const String profile = "/profile/";
  static const String editProfile = "/profile/edit";
  static const String changePassword = "/profile/change-password";

  static const String paymentMethods = "/payment-methods/";
  static const String addPaymentMethod = "/payment-methods/add";
  static String deletePaymentMethod(int id) =>
      "/payment-methods/$id/delete";
  static String defaultPaymentMethod(int id) =>
      "/payment-methods/$id/default";
  static const String payments = "/payment-methods/payments";

  static const String home = "/";
}

import 'package:flutter/material.dart';

import '../../../core/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/app_button.dart';

class HeroSection extends StatelessWidget {
  final bool isAuthenticated;

  const HeroSection({super.key, this.isAuthenticated = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: AppColors.background,
      padding: const EdgeInsets.symmetric(
        horizontal: 24,
        vertical: 80,
      ),
      child: Column(
        children: [
          Container(
            width: 220,
            height: 4,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppColors.primary,
                  AppColors.secondary,
                  AppColors.primary,
                ],
              ),
            ),
          ),

          const SizedBox(height: 35),

          const Text(
            "FLAVOR\nUNLEASHED",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 72,
              height: .9,
              fontWeight: FontWeight.bold,
              letterSpacing: 4,
            ),
          ),

          const SizedBox(height: 20),

          const Text(
            "Bold plates. Big flavors.\nZero compromise.",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white60,
              fontSize: 18,
              letterSpacing: 2,
              height: 1.5,
            ),
          ),

          const SizedBox(height: 40),

          Wrap(
            spacing: 20,
            runSpacing: 20,
            alignment: WrapAlignment.center,
            children: [
              AppButton(
                title: "VIEW MENU",
                onPressed: () =>
                    Navigator.pushNamed(context, AppRoutes.menu),
              ),
              if (!isAuthenticated)
                AppButton(
                  title: "JOIN NOW",
                  outlined: true,
                  onPressed: () =>
                      Navigator.pushNamed(context, AppRoutes.register),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
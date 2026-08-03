import 'package:flutter/material.dart';

import '../../../core/routes.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/app_button.dart';

class CTASection extends StatelessWidget {
  final bool isAuthenticated;

  const CTASection({super.key, this.isAuthenticated = false});
  @override
  Widget build(BuildContext context) {
    if (isAuthenticated) return const SizedBox.shrink();
    return Container(
      width: double.infinity,
      color: AppColors.primary,
      padding: const EdgeInsets.symmetric(vertical: 80, horizontal: 24),
      child: Column(
        children: [
          const Text(
            "DON'T JUST EAT.\nEXPERIENCE.",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 52,
              fontWeight: FontWeight.bold,
              height: 1,
              letterSpacing: 3,
            ),
          ),

          const SizedBox(height: 20),

          const Text(
            "Sign up today and taste the difference.",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white70, fontSize: 18),
          ),

          const SizedBox(height: 40),

          Wrap(
            spacing: 20,
            runSpacing: 20,
            alignment: WrapAlignment.center,
            children: [
              AppButton(
                title: "CREATE ACCOUNT",
                onPressed: () =>
                    Navigator.pushNamed(context, AppRoutes.register),
              ),
              AppButton(
                title: "SIGN IN",
                outlined: true,
                onPressed: () =>
                    Navigator.pushNamed(context, AppRoutes.login),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

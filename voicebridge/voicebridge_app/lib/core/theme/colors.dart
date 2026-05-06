import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  static const Color primary = Color(0xFF0D1B2A);
  static const Color secondary = Color(0xFF1B9AAA);
  static const Color surfaceLight = Color(0xFFF0F4F8);
  static const Color textPrimary = Color(0xFF546E7A);
  static const Color textSecondary = Color(0xFF78909C);

  static Color get surfaceGlass => Colors.white.withOpacity(0.72);
  static Color get surfaceGlassDark => const Color(0xFF0D1B2A).withOpacity(0.65);

  // Accent colors for UI sections
  static const Color accentViolet = Color(0xFF6A1B9A);
  static const Color accentTeal = Color(0xFF26C6DA);
  static const Color accentPink = Color(0xFFEC407A);
  static const Color accentAmber = Color(0xFFFFB74D);
  static const Color accentCyan = Color(0xFF29B6F6);

  // Gradient accents for modern cards
  static const Gradient primaryGradient = LinearGradient(
    colors: [secondary, accentTeal],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const Gradient vibrantGradient = LinearGradient(
    colors: [accentViolet, accentPink, accentAmber],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Triage level light tints for card backgrounds
  static Color get triageRedTint => const Color(0xFFFFCDD2).withOpacity(0.5);
  static Color get triageOrangeTint => const Color(0xFFFFE0B2).withOpacity(0.5);
  static Color get triageYellowTint => const Color(0xFFFFF9C4).withOpacity(0.5);
  static Color get triageGreenTint => const Color(0xFFC8E6C9).withOpacity(0.5);
  static Color get triageBlueTint => const Color(0xFFBBDEFB).withOpacity(0.5);

  // SATS triage levels
  static const Color triageRed = Color(0xFFD32F2F);
  static const Color triageOrange = Color(0xFFE65100);
  static const Color triageYellow = Color(0xFFF9A825);
  static const Color triageGreen = Color(0xFF2E7D32);
  static const Color triageBlue = Color(0xFF1565C0);

  // Gradient stops for mesh background
  static const Color gradientStart = Color(0xFF0D1B2A);
  static const Color gradientMid = Color(0xFF0E3047);
  static const Color gradientEnd = Color(0xFF1B9AAA);

  static Color triageLevelColor(String level) {
    switch (level.toLowerCase()) {
      case 'red':
        return triageRed;
      case 'orange':
        return triageOrange;
      case 'yellow':
        return triageYellow;
      case 'green':
        return triageGreen;
      case 'blue':
        return triageBlue;
      default:
        return textSecondary;
    }
  }

  static Color triageLevelTint(String level) {
    switch (level.toLowerCase()) {
      case 'red':
        return triageRedTint;
      case 'orange':
        return triageOrangeTint;
      case 'yellow':
        return triageYellowTint;
      case 'green':
        return triageGreenTint;
      case 'blue':
        return triageBlueTint;
      default:
        return Colors.grey.withOpacity(0.1);
    }
  }
}

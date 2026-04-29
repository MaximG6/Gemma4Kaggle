import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  static const Color primary = Color(0xFF0D1B2A);
  static const Color secondary = Color(0xFF1B9AAA);
  static const Color surfaceLight = Color(0xFFF0F4F8);
  static const Color textPrimary = Color(0xFF1A1A2E);
  static const Color textSecondary = Color(0xFF5A6577);

  static Color get surfaceGlass => Colors.white.withOpacity(0.72);
  static Color get surfaceGlassDark => const Color(0xFF0D1B2A).withOpacity(0.65);

  // SATS triage levels
  static const Color triageRed = Color(0xFFE24B4A);
  static const Color triageOrange = Color(0xFFEF9F27);
  static const Color triageYellow = Color(0xFFEFD927);
  static const Color triageGreen = Color(0xFF639922);
  static const Color triageBlue = Color(0xFF378ADD);

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
}

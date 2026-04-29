import 'package:flutter/material.dart';
import 'colors.dart';
import 'typography.dart';

class AppTheme {
  AppTheme._();

  static ThemeData get light {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.secondary,
        brightness: Brightness.light,
        primary: AppColors.primary,
        secondary: AppColors.secondary,
        surface: AppColors.surfaceLight,
      ),
      scaffoldBackgroundColor: AppColors.surfaceLight,
      fontFamily: 'Inter',
      textTheme: const TextTheme(
        displayLarge: AppTypography.displayLarge,
        displayMedium: AppTypography.displayMedium,
        headlineLarge: AppTypography.headlineLarge,
        headlineMedium: AppTypography.headlineMedium,
        headlineSmall: AppTypography.headlineSmall,
        bodyLarge: AppTypography.bodyLarge,
        bodyMedium: AppTypography.bodyMedium,
        bodySmall: AppTypography.bodySmall,
        labelLarge: AppTypography.labelLarge,
        labelMedium: AppTypography.labelMedium,
        labelSmall: AppTypography.labelSmall,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        titleTextStyle: AppTypography.headlineMedium,
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.secondary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: AppTypography.labelLarge
              .copyWith(fontWeight: FontWeight.w600),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: AppColors.secondary,
        foregroundColor: Colors.white,
        elevation: 8,
        shape: CircleBorder(),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: Colors.white,
        selectedColor: AppColors.secondary.withOpacity(0.15),
        side: BorderSide(color: AppColors.secondary.withOpacity(0.3)),
        labelStyle: AppTypography.labelMedium,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: AppColors.textSecondary.withOpacity(0.12),
        thickness: 1,
        space: 1,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        selectedItemColor: AppColors.secondary,
        unselectedItemColor: AppColors.textSecondary,
        elevation: 0,
        type: BottomNavigationBarType.fixed,
        selectedLabelStyle: AppTypography.labelSmall,
        unselectedLabelStyle: AppTypography.labelSmall,
      ),
    );
  }

  static ThemeData get dark {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.secondary,
        brightness: Brightness.dark,
        primary: AppColors.secondary,
        secondary: AppColors.secondary,
        surface: AppColors.primary,
      ),
      scaffoldBackgroundColor: AppColors.primary,
      fontFamily: 'Inter',
      textTheme: TextTheme(
        displayLarge: AppTypography.displayLarge.copyWith(color: Colors.white),
        displayMedium:
            AppTypography.displayMedium.copyWith(color: Colors.white),
        headlineLarge:
            AppTypography.headlineLarge.copyWith(color: Colors.white),
        headlineMedium:
            AppTypography.headlineMedium.copyWith(color: Colors.white),
        headlineSmall:
            AppTypography.headlineSmall.copyWith(color: Colors.white),
        bodyLarge: AppTypography.bodyLarge.copyWith(color: Colors.white70),
        bodyMedium: AppTypography.bodyMedium.copyWith(color: Colors.white70),
        bodySmall: AppTypography.bodySmall.copyWith(color: Colors.white54),
        labelLarge: AppTypography.labelLarge.copyWith(color: Colors.white),
        labelMedium:
            AppTypography.labelMedium.copyWith(color: Colors.white60),
        labelSmall: AppTypography.labelSmall.copyWith(color: Colors.white54),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
      ),
    );
  }
}

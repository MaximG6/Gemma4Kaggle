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
        onSurface: AppColors.textPrimary,
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
        iconTheme: IconThemeData(color: AppColors.textPrimary),
      ),
      cardTheme: CardThemeData(
        color: Colors.white.withOpacity(0.85),
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
        backgroundColor: AppColors.textSecondary.withOpacity(0.08),
        selectedColor: AppColors.secondary.withOpacity(0.15),
        side: BorderSide(color: AppColors.secondary.withOpacity(0.3)),
        labelStyle: AppTypography.labelMedium.copyWith(color: AppColors.textPrimary),
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
      // Input decoration theme for proper contrast in light mode
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.transparent,
        hintStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.textSecondary.withOpacity(0.6),
        ),
        labelStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.textSecondary,
        ),
        border: InputBorder.none,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
      textSelectionTheme: TextSelectionThemeData(
        cursorColor: AppColors.secondary,
        selectionColor: AppColors.secondary.withOpacity(0.3),
        selectionHandleColor: AppColors.secondary,
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
        surface: const Color(0xFF1A2B3C),
        onSurface: const Color(0xFFE0E0E0),
      ),
      scaffoldBackgroundColor: AppColors.primary,
      fontFamily: 'Inter',
      textTheme: TextTheme(
        displayLarge: AppTypography.displayLarge.copyWith(color: const Color(0xFFB0BEC5)),
        displayMedium:
            AppTypography.displayMedium.copyWith(color: const Color(0xFFB0BEC5)),
        headlineLarge:
            AppTypography.headlineLarge.copyWith(color: const Color(0xFFB0BEC5)),
        headlineMedium:
            AppTypography.headlineMedium.copyWith(color: const Color(0xFFB0BEC5)),
        headlineSmall:
            AppTypography.headlineSmall.copyWith(color: const Color(0xFFB0BEC5)),
        bodyLarge: AppTypography.bodyLarge.copyWith(color: const Color(0xFF90A4AE)),
        bodyMedium: AppTypography.bodyMedium.copyWith(color: const Color(0xFF90A4AE)),
        bodySmall: AppTypography.bodySmall.copyWith(color: const Color(0xFF78909C)),
        labelLarge: AppTypography.labelLarge.copyWith(color: const Color(0xFFB0BEC5)),
        labelMedium:
            AppTypography.labelMedium.copyWith(color: const Color(0xFF78909C)),
        labelSmall: AppTypography.labelSmall.copyWith(color: const Color(0xFF78909C)),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        iconTheme: IconThemeData(color: Color(0xFFB0BEC5)),
      ),
      cardTheme: CardThemeData(
        color: const Color(0xFF1A2B3C).withOpacity(0.7),
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
        backgroundColor: Colors.white.withOpacity(0.08),
        selectedColor: AppColors.secondary.withOpacity(0.2),
        side: BorderSide(color: AppColors.secondary.withOpacity(0.3)),
        labelStyle: AppTypography.labelMedium.copyWith(color: const Color(0xFF90A4AE)),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: Colors.white.withOpacity(0.1),
        thickness: 1,
        space: 1,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: const Color(0xFF1A2B3C),
        selectedItemColor: AppColors.secondary,
        unselectedItemColor: const Color(0xFF78909C),
        elevation: 0,
        type: BottomNavigationBarType.fixed,
        selectedLabelStyle: AppTypography.labelSmall.copyWith(color: AppColors.secondary),
        unselectedLabelStyle: AppTypography.labelSmall.copyWith(color: const Color(0xFF78909C)),
      ),
      // Input decoration theme for proper contrast in dark mode
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF1A2B3C).withOpacity(0.6),
        hintStyle: AppTypography.bodyMedium.copyWith(
          color: const Color(0xFF78909C).withOpacity(0.6),
        ),
        labelStyle: AppTypography.bodyMedium.copyWith(
          color: const Color(0xFF90A4AE),
        ),
        border: InputBorder.none,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
      textSelectionTheme: TextSelectionThemeData(
        cursorColor: AppColors.secondary,
        selectionColor: AppColors.secondary.withOpacity(0.3),
        selectionHandleColor: AppColors.secondary,
      ),
    );
  }
}

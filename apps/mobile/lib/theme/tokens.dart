/// Design tokens. Mirrors apps/web/src/styles/tokens.css exactly.
/// Change both files in the same commit.
library;

import 'package:flutter/material.dart';

abstract final class AppColors {
  static const bg = Color(0xFF0A0A0F);
  static const surface = Color(0xFF16161F);
  static const surface2 = Color(0xFF1E1E2A);
  static const line = Color(0xFF2A2A38);

  static const text = Color(0xFFF5F5F5);
  static const muted = Color(0xFFA6ABBA);
  static const faint = Color(0xFF6E7383);

  static const red = Color(0xFFE63950);
  static const redDark = Color(0xFFB22E42);
  static const gold = Color(0xFFF0B93B);
  static const green = Color(0xFF3FB98A);
}

abstract final class AppSpacing {
  static const x1 = 4.0;
  static const x2 = 8.0;
  static const x3 = 16.0;
  static const x4 = 24.0;
  static const x5 = 40.0;
}

abstract final class AppRadius {
  static const sm = 8.0;
  static const md = 14.0;
}

/// Base URL of the API, injected at build time:
/// flutter run --dart-define=API_URL=http://10.0.2.2:8000
const apiBaseUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

ThemeData buildTheme() {
  const scheme = ColorScheme.dark(
    surface: AppColors.bg,
    primary: AppColors.red,
    secondary: AppColors.gold,
    onPrimary: Colors.white,
    onSurface: AppColors.text,
    outline: AppColors.line,
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: AppColors.bg,
    fontFamily: 'Inter',
    textTheme: const TextTheme(
      displayLarge: TextStyle(
        fontFamily: 'PlayfairDisplay',
        fontWeight: FontWeight.w800,
        color: AppColors.text,
      ),
      headlineMedium: TextStyle(
        fontFamily: 'PlayfairDisplay',
        fontWeight: FontWeight.w800,
        color: AppColors.text,
      ),
      bodyMedium: TextStyle(color: AppColors.muted, height: 1.5),
    ),
    cardTheme: CardThemeData(
      color: AppColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
      ),
    ),
  );
}

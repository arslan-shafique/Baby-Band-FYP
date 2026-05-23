import 'package:flutter/material.dart';

/// Centralized color palette for the Smart Baby Band app.
/// All colors in the app should reference this file — never hardcode colors.
class AppColors {
  AppColors._(); // Prevent instantiation

  // ─── Brand Primary (Soft Teal / Cyan) ───
  static const Color primaryLight = Color(0xFF4DD0C8);
  static const Color primary = Color(0xFF00BFA5);
  static const Color primaryDark = Color(0xFF009688);

  // ─── Brand Secondary (Warm Amber) ───
  static const Color secondaryLight = Color(0xFFFFD54F);
  static const Color secondary = Color(0xFFFFC107);
  static const Color secondaryDark = Color(0xFFFFA000);

  // ─── Brand Tertiary (Soft Lavender) ───
  static const Color tertiary = Color(0xFF9C7CF4);
  static const Color tertiaryLight = Color(0xFFB9A0F8);

  // ─── Semantic Colors ───
  static const Color success = Color(0xFF4CAF50);
  static const Color successLight = Color(0xFFE8F5E9);
  static const Color warning = Color(0xFFFFA726);
  static const Color warningLight = Color(0xFFFFF3E0);
  static const Color error = Color(0xFFEF5350);
  static const Color errorLight = Color(0xFFFFEBEE);
  static const Color info = Color(0xFF42A5F5);
  static const Color infoLight = Color(0xFFE3F2FD);

  // ─── Light Theme Surface Colors ───
  static const Color lightBackground = Color(0xFFF8FAFC);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightSurfaceVariant = Color(0xFFF1F5F9);
  static const Color lightCard = Color(0xFFFFFFFF);
  static const Color lightDivider = Color(0xFFE2E8F0);

  // ─── Light Theme Text Colors ───
  static const Color lightTextPrimary = Color(0xFF0F172A);
  static const Color lightTextSecondary = Color(0xFF475569);
  static const Color lightTextTertiary = Color(0xFF94A3B8);
  static const Color lightTextOnPrimary = Color(0xFFFFFFFF);

  // ─── Dark Theme Surface Colors ───
  static const Color darkBackground = Color(0xFF0D1B2A);
  static const Color darkSurface = Color(0xFF1B2838);
  static const Color darkSurfaceVariant = Color(0xFF243447);
  static const Color darkCard = Color(0xFF1B2838);
  static const Color darkDivider = Color(0xFF2D3F52);

  // ─── Dark Theme Text Colors ───
  static const Color darkTextPrimary = Color(0xFFE2E8F0);
  static const Color darkTextSecondary = Color(0xFF94A3B8);
  static const Color darkTextTertiary = Color(0xFF64748B);
  static const Color darkTextOnPrimary = Color(0xFFFFFFFF);

  // ─── Chart / Data Visualization Colors ───
  // History sub-screen accent colors:
  //   Cry = amber, Temp = red, Heartbeat = pink, Sleep = indigo
  static const Color chartAmber = Color(0xFFFFC107);   // Cry accent
  static const Color chartRed = Color(0xFFEF5350);     // Temperature accent
  static const Color chartPink = Color(0xFFEC407A);     // Heartbeat accent
  static const Color chartIndigo = Color(0xFF5C6BC0);   // Sleep accent
  static const Color chartBlue = Color(0xFF42A5F5);
  static const Color chartPurple = Color(0xFF9C7CF4);
  static const Color chartOrange = Color(0xFFFF9800);
  static const Color chartGreen = Color(0xFF66BB6A);
  static const Color chartTeal = Color(0xFF00BFA5);

  // ─── Baby-specific Semantic Colors ───
  static const Color heartRate = Color(0xFFEC407A);
  static const Color heartRateBg = Color(0xFFFCE4EC);
  static const Color temperature = Color(0xFFEF5350);
  static const Color temperatureBg = Color(0xFFFFEBEE);
  static const Color sleep = Color(0xFF5C6BC0);
  static const Color sleepBg = Color(0xFFE8EAF6);
  static const Color cry = Color(0xFFFFC107);
  static const Color cryBg = Color(0xFFFFF8E1);

  // ─── Gradient Presets ───
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFF00BFA5), Color(0xFF009688)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient accentGradient = LinearGradient(
    colors: [Color(0xFF9C7CF4), Color(0xFF6C5CE7)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient warmGradient = LinearGradient(
    colors: [Color(0xFFFFD54F), Color(0xFFFFC107)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient darkCardGradient = LinearGradient(
    colors: [Color(0xFF1B2838), Color(0xFF243447)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // ─── Dashboard Metric Card Gradients ───
  static LinearGradient cryGradient(bool isDark) => LinearGradient(
    colors: isDark
        ? [const Color(0xFF3E2723), const Color(0xFF4E342E)]
        : [const Color(0xFFFFF8E1), const Color(0xFFFFF3E0)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static LinearGradient tempGradient(bool isDark) => LinearGradient(
    colors: isDark
        ? [const Color(0xFF3E1A1A), const Color(0xFF4A2020)]
        : [const Color(0xFFFFF0F0), const Color(0xFFFFEBEE)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static LinearGradient heartGradient(bool isDark) => LinearGradient(
    colors: isDark
        ? [const Color(0xFF3E1A2E), const Color(0xFF4A2038)]
        : [const Color(0xFFFCE4EC), const Color(0xFFF8BBD0)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static LinearGradient sleepGradient(bool isDark) => LinearGradient(
    colors: isDark
        ? [const Color(0xFF1A237E).withValues(alpha: 0.4), const Color(0xFF283593).withValues(alpha: 0.4)]
        : [const Color(0xFFE8EAF6), const Color(0xFFC5CAE9)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

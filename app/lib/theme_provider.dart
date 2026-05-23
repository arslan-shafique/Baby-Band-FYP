import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Manages app-wide theme mode (light / dark / system).
/// Persists the preference to SharedPreferences so it survives
/// app restarts. Theme is device-level — not cleared on auth flows.
///
/// Wrap your [MaterialApp] with a [ListenableBuilder] or use a
/// state-management solution to react to changes.
class ThemeProvider extends ChangeNotifier {
  static const String _prefKey = 'theme_mode';

  ThemeMode _themeMode = ThemeMode.light;

  ThemeMode get themeMode => _themeMode;

  bool get isDarkMode => _themeMode == ThemeMode.dark;

  /// Load the saved theme preference from SharedPreferences.
  /// Must be called BEFORE MaterialApp renders (in main()).
  Future<void> loadThemePreference() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_prefKey);
    if (saved != null) {
      switch (saved) {
        case 'dark':
          _themeMode = ThemeMode.dark;
          break;
        case 'system':
          _themeMode = ThemeMode.system;
          break;
        default:
          _themeMode = ThemeMode.light;
      }
    }
    notifyListeners();
  }

  /// Toggle between light and dark mode and persist the choice.
  void toggleTheme(bool enableDark) {
    _themeMode = enableDark ? ThemeMode.dark : ThemeMode.light;
    _persist();
    notifyListeners();
  }

  /// Set a specific theme mode and persist the choice.
  void setThemeMode(ThemeMode mode) {
    _themeMode = mode;
    _persist();
    notifyListeners();
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    String value;
    switch (_themeMode) {
      case ThemeMode.dark:
        value = 'dark';
        break;
      case ThemeMode.system:
        value = 'system';
        break;
      default:
        value = 'light';
    }
    await prefs.setString(_prefKey, value);
  }
}

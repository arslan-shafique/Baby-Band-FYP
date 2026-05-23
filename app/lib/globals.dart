import 'package:shared_preferences/shared_preferences.dart';

String globalDeviceId = ''; // Resolves dynamically after login

/// Persist device ID to SharedPreferences and update the in-memory global.
Future<void> saveDeviceId(String deviceId) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString('device_id', deviceId);
  globalDeviceId = deviceId;
}

/// Load persisted device ID from SharedPreferences into the in-memory global.
/// Must be called in main() before runApp().
Future<void> loadDeviceId() async {
  final prefs = await SharedPreferences.getInstance();
  final stored = prefs.getString('device_id') ?? '';
  globalDeviceId = stored;
}

/// Clear persisted device ID. Call before signOut.
Future<void> clearDeviceId() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.remove('device_id');
  globalDeviceId = '';
}

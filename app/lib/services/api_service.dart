import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

class ApiService {
  // Use 10.0.2.2 for Android emulator, or your actual local IP (e.g., 192.168.x.x) for physical device.
  static const String BASE_URL = 'http://10.0.2.2:8000/api';

  static Future<Map<String, dynamic>?> postSensors(Map<String, dynamic> payload) async {
    try {
      final response = await http.post(
        Uri.parse('$BASE_URL/sensor/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );
      if (response.statusCode == 200 || response.statusCode == 201) {
        return jsonDecode(response.body);
      }
      debugPrint('postSensors error: ${response.statusCode} - ${response.body}');
      return null;
    } catch (e) {
      debugPrint('postSensors exception: $e');
      return null;
    }
  }

  static Future<Map<String, dynamic>?> postSleep(Map<String, dynamic> payload) async {
    try {
      final response = await http.post(
        Uri.parse('$BASE_URL/sleep/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );
      if (response.statusCode == 200 || response.statusCode == 201) {
        return jsonDecode(response.body);
      }
      debugPrint('postSleep error: ${response.statusCode} - ${response.body}');
      return null;
    } catch (e) {
      debugPrint('postSleep exception: $e');
      return null;
    }
  }

  static Future<Map<String, dynamic>?> getAlerts(String deviceId) async {
    if (deviceId.isEmpty) return null;
    try {
      final response = await http.get(
        Uri.parse('$BASE_URL/alerts/?device_id=$deviceId'),
        headers: {'Content-Type': 'application/json'},
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      debugPrint('getAlerts error: ${response.statusCode} - ${response.body}');
      return null;
    } catch (e) {
      debugPrint('getAlerts exception: $e');
      return null;
    }
  }
}

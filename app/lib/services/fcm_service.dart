import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';

/// Handles all Firebase Cloud Messaging (FCM) logic:
/// 1. Requests notification permission from the user
/// 2. Retrieves the device's unique FCM token
/// 3. Saves the token to Firestore so the Python backend can send push notifications
/// 4. Listens for incoming push notifications (foreground + background)
class FcmService {
  static final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  /// Call this once after the user logs in.
  /// It requests permission, grabs the token, saves it, and starts listening.
  static Future<void> initialize() async {
    // 1. Request notification permission (required on iOS & Android 13+)
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      debugPrint('FCM: User denied notification permission.');
      return;
    }

    debugPrint('FCM: Permission granted — ${settings.authorizationStatus}');

    // 2. Get the FCM token and save it
    await _saveTokenToFirestore();

    // 3. Listen for token refresh (tokens can expire/rotate)
    _messaging.onTokenRefresh.listen((newToken) {
      debugPrint('FCM: Token refreshed.');
      _updateTokenInFirestore(newToken);
    });

    // 4. Handle foreground messages (app is open)
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('FCM: Foreground message received!');
      debugPrint('  Title: ${message.notification?.title}');
      debugPrint('  Body:  ${message.notification?.body}');
      debugPrint('  Data:  ${message.data}');

      // The notification will automatically appear as a system notification
      // on Android if the message contains a "notification" payload.
      // For custom in-app UI, you can handle it here.
    });

    // 5. Handle when user taps a notification (app was in background)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint('FCM: User tapped notification — ${message.data}');
      // You can navigate to a specific page here based on message.data
    });
  }

  /// Retrieves the current FCM token and saves it to the user's Firestore document.
  static Future<void> _saveTokenToFirestore() async {
    try {
      final token = await _messaging.getToken();
      if (token == null) {
        debugPrint('FCM: Could not retrieve token.');
        return;
      }

      debugPrint('FCM: Token retrieved — ${token.substring(0, 20)}...');
      await _updateTokenInFirestore(token);
    } catch (e) {
      debugPrint('FCM: Error saving token — $e');
    }
  }

  /// Writes the FCM token to the current user's Firestore document.
  /// This is the token your Python backend reads to send push notifications.
  static Future<void> _updateTokenInFirestore(String token) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      debugPrint('FCM: No authenticated user. Cannot save token.');
      return;
    }

    await FirebaseFirestore.instance.collection('users').doc(user.uid).set(
      {'fcm_token': token},
      SetOptions(merge: true), // merge so we don't overwrite other fields
    );

    debugPrint('FCM: Token saved to Firestore for user ${user.uid}');
  }
}

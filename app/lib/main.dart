import 'dart:async';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'firebase_options.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/app_colors.dart';
import 'services/firestore_service.dart';
import 'theme_provider.dart';
import 'globals.dart';
import 'login.dart';
import 'dash.dart';
import 'history.dart';
import 'notification.dart';
import 'settings.dart';

/// Global navigator key to navigate from anywhere in the app (including global alert listener)
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

/// Global [ThemeProvider] instance shared across the app.
/// Screens can access it via [MyApp.themeProvider].
final ThemeProvider _themeProvider = ThemeProvider();

/// This handler runs when the app is fully terminated and a push notification arrives.
/// It MUST be a top-level function (not inside a class).
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('FCM: Background message received — ${message.messageId}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  // Register the background message handler
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  // Load persisted theme preference BEFORE rendering MaterialApp
  await _themeProvider.loadThemePreference();
  
  // Restore persisted device ID so screens don't show "Device not linked"
  await loadDeviceId();
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  /// Public accessor so any screen can toggle the theme
  /// via `MyApp.themeProvider.toggleTheme(...)`.
  static ThemeProvider get themeProvider => _themeProvider;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _themeProvider,
      builder: (context, _) {
        return MaterialApp(
          debugShowCheckedModeBanner: false,
          title: 'Smart Baby Band',
          navigatorKey: navigatorKey,
          themeMode: _themeProvider.themeMode,
          theme: AppTheme.light,
          darkTheme: AppTheme.dark,
          home: FirebaseAuth.instance.currentUser != null 
              ? const DashboardPage() 
              : const LoginPage(),
          routes: {
            '/login': (context) => const LoginPage(),
            '/dashboard': (context) => const DashboardPage(),
            '/history': (context) => const HistoryPage(),
            '/notifications': (context) => const NotificationsPage(),
            '/settings': (context) => const SettingsPage(),
          },
          builder: (context, child) {
            return GlobalAlertListener(child: child!);
          },
        );
      },
    );
  }
}

/// GlobalAlertListener wraps the entire Navigator tree to listen for real-time unread 
/// critical alerts from Firestore and displays a gorgeous slide-down Heads-Up display.
class GlobalAlertListener extends StatefulWidget {
  final Widget child;
  const GlobalAlertListener({super.key, required this.child});

  @override
  State<GlobalAlertListener> createState() => _GlobalAlertListenerState();
}

class _GlobalAlertListenerState extends State<GlobalAlertListener> {
  StreamSubscription? _authSubscription;
  StreamSubscription? _notificationSubscription;
  String? _currentUserId;

  // Cache to track which notification IDs we have already shown during this app runtime session
  final Set<String> _seenNotificationIds = {};
  
  // State variables for the animated slide-down heads-up alert banner
  Map<String, dynamic>? _activeAlert;
  bool _isBannerVisible = false;
  Timer? _autoHideTimer;

  @override
  void initState() {
    super.initState();
    _initAuthListener();
  }

  void _initAuthListener() {
    _authSubscription = FirebaseAuth.instance.authStateChanges().listen((user) {
      if (user != null) {
        if (_currentUserId != user.uid) {
          _currentUserId = user.uid;
          _subscribeToNotifications(user.uid);
        }
      } else {
        _currentUserId = null;
        _unsubscribeNotifications();
      }
    });
  }

  void _subscribeToNotifications(String userId) {
    _unsubscribeNotifications();
    
    // Ignore old alerts created before the app run session (within last 15 seconds)
    final DateTime appSessionStartTime = DateTime.now().subtract(const Duration(seconds: 15));

    _notificationSubscription = FirestoreService.getNotifications(userId).listen((notifications) {
      if (notifications.isEmpty) return;

      // Check the latest alert
      final latest = notifications.first;
      final String id = latest['id'] ?? '';
      final bool isRead = latest['is_read'] ?? false;
      
      DateTime createdAt = DateTime.now();
      final ts = latest['created_at'];
      if (ts is Timestamp) {
        createdAt = ts.toDate();
      }

      // If it is unread, not seen during this run, and was triggered during the active session
      if (!isRead && !_seenNotificationIds.contains(id) && createdAt.isAfter(appSessionStartTime)) {
        _seenNotificationIds.add(id);
        _triggerHeadsUpDisplay(latest);
      }
    });
  }

  void _unsubscribeNotifications() {
    _notificationSubscription?.cancel();
    _notificationSubscription = null;
  }

  void _triggerHeadsUpDisplay(Map<String, dynamic> alert) {
    _autoHideTimer?.cancel();

    setState(() {
      _activeAlert = alert;
      _isBannerVisible = true;
    });

    // Auto-hide the heads-up banner after 6 seconds
    _autoHideTimer = Timer(const Duration(seconds: 6), () {
      if (mounted) {
        setState(() {
          _isBannerVisible = false;
        });
      }
    });
  }

  @override
  void dispose() {
    _authSubscription?.cancel();
    _unsubscribeNotifications();
    _autoHideTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // Position parameters: hidden above screen vs visible at top
    final double bannerTopPosition = _isBannerVisible 
        ? MediaQuery.of(context).padding.top + 16 
        : -200;

    return Stack(
      children: [
        // The main Navigator tree containing all app screens
        widget.child,

        // The high-priority slide-down heads-up banner
        AnimatedPositioned(
          duration: const Duration(milliseconds: 500),
          curve: Curves.easeOutBack, // Incredibly satisfying bouncy entry curve
          top: bannerTopPosition,
          left: 16,
          right: 16,
          child: _activeAlert == null 
              ? const SizedBox.shrink()
              : Material(
                  color: Colors.transparent,
                  child: _buildHeadsUpBanner(context, _activeAlert!, isDark),
                ),
        ),
      ],
    );
  }

  Widget _buildHeadsUpBanner(BuildContext context, Map<String, dynamic> alert, bool isDark) {
    final theme = Theme.of(context);
    final String id = alert['id'] ?? '';
    final String title = alert['title'] ?? 'Emergency Alert';
    final String message = alert['message'] ?? '';
    final String type = alert['type'] ?? 'info';

    final Color alertColor = type == 'critical' 
        ? AppColors.chartRed 
        : (type == 'warning' ? AppColors.chartOrange : AppColors.chartBlue);

    return Container(
      decoration: BoxDecoration(
        color: isDark ? Colors.grey[900] : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: alertColor.withValues(alpha: 0.4),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: alertColor.withValues(alpha: 0.25),
            blurRadius: 20,
            spreadRadius: 2,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: () {
            // Tap navigates user directly to alerts screen
            setState(() {
              _isBannerVisible = false;
            });
            navigatorKey.currentState?.pushNamed('/notifications');
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Glowing Left-side Status Icon
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: alertColor.withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    type == 'critical' 
                        ? Icons.warning_rounded 
                        : (type == 'warning' ? Icons.thermostat_rounded : Icons.info_rounded),
                    color: alertColor,
                    size: 28,
                  ),
                ),
                const SizedBox(width: 14),

                // Alert details Text
                Expanded(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: alertColor,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        message,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                          height: 1.3,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),

                // Fast Action Buttons (Close and Mark as Read)
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.close_rounded, size: 20),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                      onPressed: () {
                        setState(() {
                          _isBannerVisible = false;
                        });
                      },
                    ),
                    const SizedBox(height: 10),
                    IconButton(
                      icon: Icon(Icons.check_circle_outline_rounded, color: alertColor, size: 20),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                      tooltip: 'Mark as read',
                      onPressed: () async {
                        setState(() {
                          _isBannerVisible = false;
                        });
                        await FirestoreService.markNotificationAsRead(id);
                      },
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

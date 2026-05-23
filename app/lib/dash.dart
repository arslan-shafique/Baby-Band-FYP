import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'core/theme/app_colors.dart';
import 'history.dart';
import 'notification.dart';
import 'settings.dart';
import 'navigation.dart';
import 'services/firestore_service.dart';
import 'globals.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      _DashboardContent(),
      const HistoryPage(),
      const NotificationsPage(),
      const SettingsPage(),
    ];

    return Scaffold(
      body: SafeArea(child: pages[_selectedIndex]),
      bottomNavigationBar: AppBottomNav(currentIndex: _selectedIndex),
    );
  }
}

/// Extracted dashboard content as a separate widget to keep things clean.
class _DashboardContent extends StatelessWidget {
  String _formatDuration(Duration duration) {
    if (duration.inHours > 0) {
      return '${duration.inHours}h ${duration.inMinutes % 60}m';
    } else {
      return '${duration.inMinutes}m';
    }
  }

  String _getRelativeTimeString(DateTime? time) {
    if (time == null) return 'Syncing...';
    final diff = DateTime.now().difference(time);
    if (diff.inSeconds < 15) {
      return 'Updated just now';
    } else if (diff.inSeconds < 60) {
      return 'Updated ${diff.inSeconds}s ago';
    } else if (diff.inMinutes < 60) {
      return 'Updated ${diff.inMinutes}m ago';
    } else if (diff.inHours < 24) {
      return 'Updated ${diff.inHours}h ago';
    } else {
      return 'Updated ${diff.inDays}d ago';
    }
  }

  Widget _buildStatusBanner(
      BuildContext context,
      ThemeData theme,
      ColorScheme colorScheme,
      bool isDark,
      bool cryDetected,
      String cryType,
      String envOverall,
      String sleepState,
      List<Map<String, dynamic>> sleepSessions,
      String babyName) {
    String statusMessage = '';
    Color statusColor = Colors.green;
    IconData statusIcon = Icons.check_circle_outline_rounded;

    if (cryDetected) {
      statusColor = AppColors.chartRed;
      statusIcon = Icons.warning_amber_rounded;
      statusMessage = 'Cry Alert: $babyName is crying (${cryType.toUpperCase()})';
    } else if (envOverall == 'danger' || envOverall == 'warning') {
      statusColor = AppColors.chartOrange;
      statusIcon = Icons.thermostat_rounded;
      statusMessage = 'Environment Warning: Room is $envOverall';
    } else if (sleepState == 'deep' || sleepState == 'light') {
      statusColor = AppColors.chartIndigo;
      statusIcon = Icons.nights_stay_rounded;

      String elapsedStr = 'recently';
      if (sleepSessions.isNotEmpty) {
        final DateTime startTime = (sleepSessions.first['timestamp'] as Timestamp).toDate();
        final duration = DateTime.now().difference(startTime);
        elapsedStr = _formatDuration(duration);
      }
      statusMessage = 'Sleeping: ${sleepState.toUpperCase()} sleep for $elapsedStr';
    } else {
      statusColor = AppColors.chartTeal;
      statusIcon = Icons.sentiment_satisfied_alt_rounded;
      statusMessage = 'All Quiet: $babyName is awake and calm';
    }

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: statusColor.withValues(alpha: 0.12),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 72,
              color: statusColor,
            ),
            const SizedBox(width: 16),
            Icon(statusIcon, color: statusColor, size: 28),
            const SizedBox(width: 12),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
                child: Text(
                  statusMessage,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: isDark ? Colors.white : colorScheme.onSurface,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBabyHeader(ThemeData theme, ColorScheme colorScheme, String babyName, String lastUpdatedString) {
    return Column(
      children: [
        Container(
          width: 90,
          height: 90,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              colors: [
                colorScheme.primary.withValues(alpha: 0.18),
                colorScheme.tertiary.withValues(alpha: 0.12),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            border: Border.all(
              color: colorScheme.primary.withValues(alpha: 0.25),
              width: 2,
            ),
          ),
          child: Icon(
            Icons.child_care_rounded,
            size: 44,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          babyName,
          style: theme.textTheme.headlineSmall,
        ),
        Text(
          lastUpdatedString,
          style: theme.textTheme.bodySmall?.copyWith(
            color: colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _buildSleepCardContent(String sleepState, List<Map<String, dynamic>> sessions, ThemeData theme, ColorScheme colorScheme) {
    IconData sleepIcon = Icons.wb_sunny_rounded;
    Color iconColor = AppColors.chartOrange;
    String durationLabel = 'No active session';

    if (sleepState == 'deep') {
      sleepIcon = Icons.brightness_2_rounded;
      iconColor = AppColors.chartIndigo;
    } else if (sleepState == 'light') {
      sleepIcon = Icons.brightness_3_rounded;
      iconColor = AppColors.chartBlue;
    } else {
      sleepIcon = Icons.wb_sunny_rounded;
      iconColor = AppColors.chartOrange;
    }

    if (sessions.isNotEmpty) {
      final DateTime startTime = (sessions.first['timestamp'] as Timestamp).toDate();
      final duration = DateTime.now().difference(startTime);
      durationLabel = 'Active for ${_formatDuration(duration)}';
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                sleepState.toUpperCase(),
                style: theme.textTheme.displayMedium?.copyWith(
                  fontSize: 52,
                  fontWeight: FontWeight.w900,
                  color: iconColor,
                  letterSpacing: -1,
                ),
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(Icons.access_time_rounded, size: 14, color: colorScheme.onSurfaceVariant),
                  const SizedBox(width: 4),
                  Text(
                    durationLabel,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: colorScheme.onSurfaceVariant,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: iconColor.withValues(alpha: 0.12),
            shape: BoxShape.circle,
          ),
          child: Icon(sleepIcon, color: iconColor, size: 48),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;
    final user = FirebaseAuth.instance.currentUser;

    if (user == null) {
      return const Center(child: Text("Please log in again."));
    }

    return StreamBuilder<DocumentSnapshot>(
      stream: FirebaseFirestore.instance.collection('users').doc(user.uid).snapshots(),
      builder: (context, userSnap) {
        String babyName = '...';
        if (userSnap.hasData && userSnap.data != null && userSnap.data!.exists) {
          final data = userSnap.data!.data() as Map<String, dynamic>?;
          babyName = data?['baby_name'] ?? 'Baby';
        }

        return StreamBuilder<Map<String, dynamic>?>(
          stream: FirestoreService.getCryClassifications(globalDeviceId),
          builder: (context, crySnap) {
            return StreamBuilder<List<Map<String, dynamic>>>(
              stream: FirestoreService.getSleepSessions(globalDeviceId),
              builder: (context, sleepSnap) {
                return StreamBuilder<List<Map<String, dynamic>>>(
                  stream: FirestoreService.getEnvironmentLogs(globalDeviceId),
                  builder: (context, envSnap) {
                    // 1. Cry classification details
                    String cryType = 'unknown';
                    bool cryDetected = false;
                    if (crySnap.hasData && crySnap.data != null) {
                      cryDetected = crySnap.data!['cry_detected'] ?? false;
                      if (!cryDetected) {
                        cryType = 'unknown';
                      } else {
                        cryType = crySnap.data!['cry_label'] ?? 'unknown';
                      }
                    }

                    // 2. Sleep session details
                    String sleepState = 'Loading...';
                    List<Map<String, dynamic>> sleepSessions = [];
                    if (sleepSnap.hasData && sleepSnap.data != null) {
                      sleepSessions = sleepSnap.data!;
                      if (sleepSessions.isNotEmpty) {
                        sleepState = sleepSessions.first['sleep_state'] ?? 'awake';
                      } else {
                        sleepState = 'awake';
                      }
                    }

                    // 3. Environment log details
                    String temp = '--℃';
                    String hum = '--%';
                    String envOverall = 'normal';
                    Color tempColor = AppColors.chartTeal;
                    if (envSnap.hasData && envSnap.data != null && envSnap.data!.isNotEmpty) {
                      final latest = envSnap.data!.first;
                      temp = '${latest['temperature']}℃';
                      hum = '${latest['humidity']}%';
                      envOverall = latest['overall'] ?? 'normal';
                      if (envOverall == 'danger') {
                        tempColor = AppColors.error;
                      } else if (envOverall == 'warning') {
                        tempColor = AppColors.chartOrange;
                      } else {
                        tempColor = AppColors.chartTeal;
                      }
                    }

                    // 4. Reactive last updated calculation
                    DateTime? latestTime;
                    if (envSnap.hasData && envSnap.data != null && envSnap.data!.isNotEmpty) {
                      final envTime = (envSnap.data!.first['timestamp'] as Timestamp).toDate();
                      if (latestTime == null || envTime.isAfter(latestTime)) {
                        latestTime = envTime;
                      }
                    }
                    if (sleepSnap.hasData && sleepSnap.data != null && sleepSnap.data!.isNotEmpty) {
                      final sleepTime = (sleepSnap.data!.first['timestamp'] as Timestamp).toDate();
                      if (latestTime == null || sleepTime.isAfter(latestTime)) {
                        latestTime = sleepTime;
                      }
                    }
                    if (crySnap.hasData && crySnap.data != null && crySnap.data!['timestamp'] != null) {
                      try {
                        final cryTime = DateTime.parse(crySnap.data!['timestamp']);
                        if (latestTime == null || cryTime.isAfter(latestTime)) {
                          latestTime = cryTime;
                        }
                      } catch (_) {}
                    }
                    
                    final relativeTimeStr = _getRelativeTimeString(latestTime);

                    return SingleChildScrollView(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            'Dashboard',
                            style: theme.textTheme.headlineMedium,
                          ),
                          const SizedBox(height: 16),

                          // 1. Status Banner
                          _buildStatusBanner(
                            context,
                            theme,
                            colorScheme,
                            isDark,
                            cryDetected,
                            cryType,
                            envOverall,
                            sleepState,
                            sleepSessions,
                            babyName,
                          ),

                          // 2. Baby Avatar/Name
                          _buildBabyHeader(theme, colorScheme, babyName, relativeTimeStr),
                          const SizedBox(height: 24),

                          // 3. Sleep State Section
                          _buildGradientSectionCard(
                            context,
                            title: 'Current Sleep State',
                            gradient: AppColors.sleepGradient(isDark),
                            accentColor: AppColors.chartIndigo,
                            icon: Icons.nights_stay_rounded,
                            child: _buildSleepCardContent(sleepState, sleepSessions, theme, colorScheme),
                          ),
                          const SizedBox(height: 16),

                          // 4. Environment Card (with progressive disclosure)
                          EnvironmentSection(
                            temp: temp,
                            hum: hum,
                            overall: envOverall,
                            tempColor: tempColor,
                            gradient: AppColors.tempGradient(isDark),
                            accentColor: AppColors.chartRed,
                            isDark: isDark,
                          ),
                          const SizedBox(height: 16),

                          // 5. Cry Classification Section
                          _buildGradientSectionCard(
                            context,
                            title: 'Cry Classification',
                            gradient: AppColors.cryGradient(isDark),
                            accentColor: AppColors.chartAmber,
                            icon: Icons.mic_rounded,
                            child: (!cryDetected || cryType == 'unknown')
                                ? Container(
                                    padding: const EdgeInsets.symmetric(vertical: 20),
                                    width: double.infinity,
                                    alignment: Alignment.center,
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        Container(
                                          width: 10,
                                          height: 10,
                                          decoration: const BoxDecoration(
                                            color: Colors.green,
                                            shape: BoxShape.circle,
                                          ),
                                        ),
                                        const SizedBox(width: 10),
                                        Text(
                                          'No cry detected · All quiet',
                                          style: theme.textTheme.bodyLarge?.copyWith(
                                            fontWeight: FontWeight.bold,
                                            color: Colors.green.shade700,
                                          ),
                                        ),
                                      ],
                                    ),
                                  )
                                : Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                                    children: [
                                      _cryTypeCard(
                                        context,
                                        'images/hunger.jpg',
                                        'Hunger',
                                        AppColors.chartOrange,
                                        cryType == 'hungry',
                                      ),
                                      _cryTypeCard(
                                        context,
                                        'images/sleep.jpeg',
                                        'Deep',
                                        AppColors.chartIndigo,
                                        cryType == 'tired',
                                      ),
                                      _cryTypeCard(
                                        context,
                                        'images/cry.jpeg',
                                        'Pain',
                                        AppColors.chartRed,
                                        cryType == 'discomfort',
                                      ),
                                    ],
                                  ),
                          ),
                        ],
                      ),
                    );
                  },
                );
              },
            );
          },
        );
      },
    );
  }

  /// Gradient-background section card with glassmorphism-lite effect.
  Widget _buildGradientSectionCard(
    BuildContext context, {
    required String title,
    required LinearGradient gradient,
    required Color accentColor,
    required IconData icon,
    required Widget child,
  }) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: gradient,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: accentColor.withValues(alpha: isDark ? 0.15 : 0.10),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: accentColor.withValues(alpha: isDark ? 0.08 : 0.06),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: accentColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: accentColor, size: 18),
              ),
              const SizedBox(width: 10),
              Text(title, style: theme.textTheme.titleMedium),
            ],
          ),
          const SizedBox(height: 15),
          child,
        ],
      ),
    );
  }

  Widget _cryTypeCard(
      BuildContext context, String image, String label, Color accentColor, bool isActive) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    final Widget cardImage = Container(
      height: 70,
      width: 70,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: (isActive ? accentColor : Colors.grey).withValues(alpha: 0.10),
        shape: BoxShape.circle,
        border: Border.all(
          color: (isActive ? accentColor : Colors.grey).withValues(alpha: 0.25),
          width: 1.5,
        ),
      ),
      child: Image.asset(image),
    );

    return Column(
      children: [
        PulsingActiveCard(
          isActive: isActive,
          glowColor: accentColor,
          child: cardImage,
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: isActive ? FontWeight.w800 : FontWeight.w500,
            color: isActive ? accentColor : colorScheme.onSurfaceVariant,
            fontSize: isActive ? 16 : 14,
          ),
        ),
      ],
    );
  }
}

/// A stateful widget to pulse the active cry card for high accessibility in low light.
class PulsingActiveCard extends StatefulWidget {
  final Widget child;
  final Color glowColor;
  final bool isActive;

  const PulsingActiveCard({
    super.key,
    required this.child,
    required this.glowColor,
    required this.isActive,
  });

  @override
  State<PulsingActiveCard> createState() => _PulsingActiveCardState();
}

class _PulsingActiveCardState extends State<PulsingActiveCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _animation = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    if (widget.isActive) {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(covariant PulsingActiveCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isActive && !_controller.isAnimating) {
      _controller.repeat(reverse: true);
    } else if (!widget.isActive && _controller.isAnimating) {
      _controller.stop();
      _controller.reset();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isActive) {
      return widget.child;
    }

    return RepaintBoundary(
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          return Transform.scale(
            scale: _animation.value,
            child: Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: widget.glowColor.withValues(alpha: 0.35),
                    blurRadius: 12 * _animation.value,
                    spreadRadius: 3 * _animation.value,
                  ),
                ],
              ),
              child: widget.child,
            ),
          );
        },
      ),
    );
  }
}

/// A progressive disclosure environment card.
class EnvironmentSection extends StatefulWidget {
  final String temp;
  final String hum;
  final String overall;
  final Color tempColor;
  final LinearGradient gradient;
  final Color accentColor;
  final bool isDark;

  const EnvironmentSection({
    super.key,
    required this.temp,
    required this.hum,
    required this.overall,
    required this.tempColor,
    required this.gradient,
    required this.accentColor,
    required this.isDark,
  });

  @override
  State<EnvironmentSection> createState() => _EnvironmentSectionState();
}

class _EnvironmentSectionState extends State<EnvironmentSection> {
  late bool _isExpanded;

  @override
  void initState() {
    super.initState();
    _isExpanded = widget.overall == 'danger' || widget.overall == 'warning';
  }

  @override
  void didUpdateWidget(covariant EnvironmentSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.overall != oldWidget.overall &&
        (widget.overall == 'danger' || widget.overall == 'warning')) {
      _isExpanded = true;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    String statusText = 'Normal ✓';
    Color statusColor = AppColors.chartTeal;
    if (widget.overall == 'danger') {
      statusText = 'Danger ⚠️';
      statusColor = AppColors.error;
    } else if (widget.overall == 'warning') {
      statusText = 'Warning ⚠️';
      statusColor = AppColors.chartOrange;
    }

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: widget.gradient,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: widget.accentColor.withValues(alpha: widget.isDark ? 0.15 : 0.10),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: widget.accentColor.withValues(alpha: widget.isDark ? 0.08 : 0.06),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: () {
              setState(() {
                _isExpanded = !_isExpanded;
              });
            },
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        color: widget.accentColor.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(Icons.thermostat_rounded, color: widget.accentColor, size: 18),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      'Environment · ',
                      style: theme.textTheme.titleMedium,
                    ),
                    Text(
                      statusText,
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: statusColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                Icon(
                  _isExpanded ? Icons.expand_less_rounded : Icons.expand_more_rounded,
                  color: colorScheme.onSurfaceVariant,
                ),
              ],
            ),
          ),
          AnimatedSize(
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
            child: _isExpanded
                ? Column(
                    children: [
                      const SizedBox(height: 18),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _tempCard(context, widget.temp, widget.tempColor, widget.overall),
                          _tempCard(context, widget.hum, AppColors.chartTeal, 'normal'),
                        ],
                      ),
                    ],
                  )
                : const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }

  Widget _tempCard(BuildContext context, String value, Color accentColor, String overall) {
    final theme = Theme.of(context);

    IconData metricIcon = Icons.check_circle_outline_rounded;
    if (overall == 'danger' || overall == 'warning') {
      metricIcon = Icons.warning_amber_rounded;
    } else if (value.contains('%')) {
      metricIcon = Icons.water_drop_outlined;
    } else {
      metricIcon = Icons.thermostat_outlined;
    }

    return Container(
      width: 130,
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 12),
      decoration: BoxDecoration(
        color: accentColor.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: accentColor.withValues(alpha: 0.20),
          width: 1,
        ),
      ),
      alignment: Alignment.center,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(metricIcon, color: accentColor, size: 18),
          const SizedBox(width: 6),
          Text(
            value,
            style: theme.textTheme.titleMedium?.copyWith(
              color: accentColor,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

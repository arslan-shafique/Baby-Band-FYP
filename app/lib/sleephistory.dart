import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'core/theme/app_colors.dart';
import 'services/firestore_service.dart';
import 'globals.dart';

class SleepPage extends StatelessWidget {
  const SleepPage({super.key});

  // Sleep history accent color: Indigo
  static const Color _accent = AppColors.chartIndigo;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    if (globalDeviceId.isEmpty) {
      return FutureBuilder(
        future: loadDeviceId(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Scaffold(body: Center(child: CircularProgressIndicator()));
          }
          if (globalDeviceId.isEmpty) {
            return const Scaffold(
              body: Center(child: Text('Device not linked. Please configure a baby profile.')),
            );
          }
          return build(context);
        },
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: StreamBuilder<List<Map<String, dynamic>>>(
        stream: FirestoreService.getSleepSessions(globalDeviceId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Text('Error loading data: ${snapshot.error}',
              style: theme.textTheme.bodyMedium);
          }
          if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return Text('No data yet', style: theme.textTheme.bodyMedium?.copyWith(
              color: colorScheme.onSurfaceVariant,
            ));
          }

          final data = snapshot.data!;
          final latest = data.first;
          final state = latest['sleep_state'] ?? 'awake';

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Real-Time Sleep Summary
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: AppColors.sleepGradient(isDark),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: _accent.withValues(alpha: 0.15),
                    width: 1,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: _accent.withValues(alpha: isDark ? 0.08 : 0.06),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Current Sleep State',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: colorScheme.onSurfaceVariant,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          state.toString().toUpperCase(),
                          style: theme.textTheme.displaySmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: state == 'deep' ? _accent : (state == 'light' ? AppColors.chartBlue : AppColors.chartOrange),
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: _accent.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        Icons.nights_stay_rounded,
                        color: _accent,
                        size: 40,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Recent Sleep Log
              Text(
                'Recent Sleep Logs',
                style: theme.textTheme.titleMedium,
              ),
              const SizedBox(height: 10),
              Column(
                children: data.map((session) {
                  final sState = session['sleep_state'] ?? 'awake';
                  
                  String timeStr = '--:--';
                  final ts = session['timestamp'];
                  if (ts != null) {
                    DateTime dt;
                    if (ts is int) {
                      dt = DateTime.fromMillisecondsSinceEpoch(ts);
                    } else {
                      dt = ts.toDate();
                    }
                    timeStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
                  }

                  final sColor = sState == 'deep' ? _accent : (sState == 'light' ? AppColors.chartBlue : AppColors.chartOrange);

                  return Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    decoration: BoxDecoration(
                      color: colorScheme.surface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: sColor.withValues(alpha: 0.12),
                        width: 0.5,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: colorScheme.shadow,
                          blurRadius: 4,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: ListTile(
                      leading: Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: sColor.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(Icons.bed_rounded, color: sColor, size: 22),
                      ),
                      title: Text(
                        sState.toString().toUpperCase(),
                        style: theme.textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      trailing: Text(timeStr, style: theme.textTheme.bodyMedium),
                    ),
                  );
                }).toList(),
              ),
            ],
          );
        },
      ),
    );
  }
}

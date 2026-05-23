import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'core/theme/app_colors.dart';
import 'services/firestore_service.dart';
import 'globals.dart';

class HeartbeatPage extends StatelessWidget {
  const HeartbeatPage({super.key});

  // Heartbeat history accent color: Pink
  static const Color _accent = AppColors.chartPink;

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
            return const Center(child: CircularProgressIndicator());
          }
          if (globalDeviceId.isEmpty) {
            return Center(
              child: Text(
                'Device not linked. Please configure a baby profile.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: colorScheme.onSurfaceVariant,
                ),
              ),
            );
          }
          return build(context);
        },
      );
    }

    return StreamBuilder<List<Map<String, dynamic>>>(
      stream: FirestoreService.getSensorData(globalDeviceId),
      builder: (context, snapshot) {
        final data = snapshot.data ?? [];
        final latestBpm = _getLatestBpm(data);

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Heart Rate Live Display
              _buildHeartRateLive(theme, colorScheme, isDark, latestBpm, data),
              const SizedBox(height: 20),

              // 24-Hour Heart Rate Trend
              _build24HourTrendChart(theme, colorScheme, isDark, data),
            ],
          ),
        );
      },
    );
  }

  double _getLatestBpm(List<Map<String, dynamic>> data) {
    if (data.isEmpty) return 0;
    return (data.first['heart_rate'] ?? data.first['bpm'] ?? 0).toDouble();
  }

  String _getBpmStatus(double bpm) {
    if (bpm <= 0) return 'No signal';
    if (bpm < 100) return 'Low';
    if (bpm >= 100 && bpm <= 160) return 'Normal';
    if (bpm > 160 && bpm <= 180) return 'Slightly High';
    return 'High';
  }

  Color _getBpmStatusColor(double bpm) {
    if (bpm <= 0) return Colors.grey;
    if (bpm < 100) return const Color(0xFF42A5F5);
    if (bpm >= 100 && bpm <= 160) return AppColors.chartGreen;
    if (bpm > 160 && bpm <= 180) return AppColors.chartOrange;
    return _accent;
  }

  Widget _buildHeartRateLive(ThemeData theme, ColorScheme colorScheme, bool isDark, double bpm, List<Map<String, dynamic>> data) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: AppColors.heartGradient(isDark),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _accent.withValues(alpha: 0.15)),
        boxShadow: [
          BoxShadow(
            color: _accent.withValues(alpha: isDark ? 0.08 : 0.06),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        children: [
          Text(
            'Live Heart Rate',
            style: theme.textTheme.titleMedium,
          ),
          const SizedBox(height: 15),

          // Concentric circles with live BPM
          Container(
            width: 150,
            height: 150,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _accent.withValues(alpha: 0.08),
            ),
            child: Center(
              child: Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _accent.withValues(alpha: 0.14),
                ),
                child: Center(
                  child: Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _accent.withValues(alpha: 0.22),
                    ),
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.favorite, color: _accent, size: 20),
                          const SizedBox(height: 2),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.baseline,
                            textBaseline: TextBaseline.alphabetic,
                            children: [
                              Text(
                                bpm > 0 ? bpm.toStringAsFixed(0) : '--',
                                style: theme.textTheme.displaySmall?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: _accent,
                                ),
                              ),
                              const SizedBox(width: 4),
                              Text(
                                'BPM',
                                style: theme.textTheme.bodyMedium?.copyWith(
                                  color: _accent,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _getBpmStatus(bpm),
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: _getBpmStatusColor(bpm),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),

          const SizedBox(height: 15),

          // Mini sparkline from recent data
          if (data.length >= 3)
            SizedBox(
              height: 40,
              child: LineChart(
                LineChartData(
                  gridData: const FlGridData(show: false),
                  titlesData: const FlTitlesData(show: false),
                  borderData: FlBorderData(show: false),
                  minX: 0,
                  maxX: (data.length > 10 ? 10 : data.length - 1).toDouble(),
                  lineBarsData: [
                    LineChartBarData(
                      spots: _buildSparklineSpots(data),
                      isCurved: true,
                      color: _accent,
                      barWidth: 2,
                      dotData: const FlDotData(show: false),
                    ),
                  ],
                ),
              ),
            ),

          const SizedBox(height: 10),
          Text(
            data.isEmpty ? 'Waiting for data...' : 'Last ${data.length > 10 ? 10 : data.length} readings',
            style: theme.textTheme.bodySmall?.copyWith(
              color: colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  List<FlSpot> _buildSparklineSpots(List<Map<String, dynamic>> data) {
    final recent = data.length > 10 ? data.sublist(0, 10) : data;
    final reversed = recent.reversed.toList();
    final spots = <FlSpot>[];
    for (int i = 0; i < reversed.length; i++) {
      final hr = (reversed[i]['heart_rate'] ?? reversed[i]['bpm'] ?? 0).toDouble();
      if (hr > 0) spots.add(FlSpot(i.toDouble(), hr));
    }
    return spots;
  }

  Widget _build24HourTrendChart(ThemeData theme, ColorScheme colorScheme, bool isDark, List<Map<String, dynamic>> data) {
    // Reverse so oldest is first (data comes descending from Firestore)
    final chronological = data.reversed.toList();
    if (chronological.isEmpty) return const SizedBox.shrink();

    // Build time-based spots: x = hours from start (0 = 24h ago, 24 = now)
    final now = DateTime.now();
    final spots = <FlSpot>[];
    double minBpm = 300;
    double maxBpm = 0;
    double sumBpm = 0;
    int count = 0;

    for (final entry in chronological) {
      final hr = (entry['heart_rate'] ?? entry['bpm'] ?? 0).toDouble();
      if (hr <= 0 || hr > 300) continue; // skip invalid readings

      // Parse timestamp
      DateTime? entryTime;
      final ts = entry['timestamp'];
      if (ts is Timestamp) {
        entryTime = ts.toDate();
      } else if (ts is String) {
        entryTime = DateTime.tryParse(ts);
      }
      if (entryTime == null) continue;

      // Only include data from the last 24 hours
      final hoursAgo = now.difference(entryTime).inMinutes / 60.0;
      if (hoursAgo > 24) continue;

      final x = 24.0 - hoursAgo; // 0 = 24h ago, 24 = now
      spots.add(FlSpot(x, hr));

      if (hr < minBpm) minBpm = hr;
      if (hr > maxBpm) maxBpm = hr;
      sumBpm += hr;
      count++;
    }

    if (spots.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: AppColors.heartGradient(isDark),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _accent.withValues(alpha: 0.15)),
        ),
        child: Center(
          child: Text('Not enough data for 24-hour trend yet',
            style: theme.textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant)),
        ),
      );
    }

    final avgBpm = sumBpm / count;
    // Add padding to Y axis
    final chartMinY = (minBpm - 20).clamp(40.0, 80.0);
    final chartMaxY = (maxBpm + 20).clamp(160.0, 220.0);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: AppColors.heartGradient(isDark),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _accent.withValues(alpha: 0.15)),
        boxShadow: [
          BoxShadow(
            color: _accent.withValues(alpha: isDark ? 0.08 : 0.06),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  '24-Hour Heart Rate Trend',
                  style: theme.textTheme.titleMedium,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _accent.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '$count readings',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: _accent,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 200,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: 20,
                  getDrawingHorizontalLine: (value) {
                    // Highlight the normal range boundaries
                    if (value == 100 || value == 160) {
                      return FlLine(
                        color: _accent.withValues(alpha: 0.3),
                        strokeWidth: 1,
                        dashArray: [5, 5],
                      );
                    }
                    return FlLine(
                      color: colorScheme.outlineVariant.withValues(alpha: 0.3),
                      strokeWidth: 0.5,
                    );
                  },
                ),
                titlesData: FlTitlesData(
                  show: true,
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      interval: 20,
                      reservedSize: 40,
                      getTitlesWidget: (value, meta) {
                        return Text(
                          '${value.toInt()}',
                          style: theme.textTheme.bodySmall?.copyWith(fontSize: 10),
                        );
                      },
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      interval: 6,
                      reservedSize: 32,
                      getTitlesWidget: (value, meta) {
                        final hoursAgo = (24 - value).toInt();
                        String label;
                        if (hoursAgo == 0) {
                          label = 'Now';
                        } else {
                          label = '${hoursAgo}h ago';
                        }
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            label,
                            style: theme.textTheme.bodySmall?.copyWith(fontSize: 10),
                          ),
                        );
                      },
                    ),
                  ),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: false),
                minX: 0,
                maxX: 24,
                minY: chartMinY,
                maxY: chartMaxY,
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    tooltipBgColor: colorScheme.surfaceContainerHighest,
                    getTooltipItems: (touchedSpots) {
                      return touchedSpots.map((spot) {
                        final hoursAgo = (24 - spot.x).toStringAsFixed(1);
                        return LineTooltipItem(
                          '${spot.y.toStringAsFixed(0)} BPM\n${hoursAgo}h ago',
                          TextStyle(color: colorScheme.onSurface, fontSize: 12),
                        );
                      }).toList();
                    },
                  ),
                ),
                lineBarsData: [
                  LineChartBarData(
                    spots: spots,
                    isCurved: true,
                    curveSmoothness: 0.3,
                    color: _accent,
                    barWidth: 2.5,
                    isStrokeCapRound: true,
                    dotData: FlDotData(
                      show: spots.length < 30,
                      getDotPainter: (spot, percent, barData, index) {
                        return FlDotCirclePainter(
                          radius: 2.5,
                          color: _accent,
                          strokeWidth: 1.5,
                          strokeColor: colorScheme.surface,
                        );
                      },
                    ),
                    belowBarData: BarAreaData(
                      show: true,
                      gradient: LinearGradient(
                        colors: [
                          _accent.withValues(alpha: 0.25),
                          _accent.withValues(alpha: 0.02),
                        ],
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Stats row
          Row(
            children: [
              _buildStatChip(theme, colorScheme, 'Min', '${minBpm.toStringAsFixed(0)} BPM', const Color(0xFF42A5F5)),
              const SizedBox(width: 10),
              _buildStatChip(theme, colorScheme, 'Avg', '${avgBpm.toStringAsFixed(0)} BPM', AppColors.chartGreen),
              const SizedBox(width: 10),
              _buildStatChip(theme, colorScheme, 'Max', '${maxBpm.toStringAsFixed(0)} BPM', _accent),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatChip(ThemeData theme, ColorScheme colorScheme, String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.2)),
        ),
        child: Column(
          children: [
            Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                color: colorScheme.onSurfaceVariant,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              value,
              style: theme.textTheme.titleSmall?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'core/theme/app_colors.dart';
import 'services/firestore_service.dart';
import 'globals.dart';

class TemperaturePage extends StatelessWidget {
  const TemperaturePage({super.key});

  // Temperature history accent color: Red
  static const Color _accent = AppColors.chartRed;

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
          // Device ID recovered — rebuild with data
          return build(context);
        },
      );
    }

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: StreamBuilder<List<Map<String, dynamic>>>(
            stream: FirestoreService.getEnvironmentLogs(globalDeviceId),
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
              final double currentTemp = (latest['temperature'] ?? 36.5).toDouble();

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Temperature Gauge (no indicator line)
                  _buildTemperatureGauge(theme, colorScheme, isDark, currentTemp),
                  const SizedBox(height: 20),

                  // 24-Hour Temperature Trend
                  _build24HourTrendChart(theme, colorScheme, isDark, data),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildTemperatureGauge(ThemeData theme, ColorScheme colorScheme, bool isDark, double currentTemp) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: AppColors.tempGradient(isDark),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _accent.withValues(alpha: 0.12)),
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
            'Current Temperature',
            style: theme.textTheme.titleMedium,
          ),
          const SizedBox(height: 15),

          // Gauge Circle — NO indicator line
          SizedBox(
            height: 180,
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Background Circle
                Container(
                  width: 180,
                  height: 180,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: colorScheme.outlineVariant,
                      width: 15,
                    ),
                  ),
                ),

                // Temperature Arc
                ClipOval(
                  child: Container(
                    width: 180,
                    height: 180,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: SweepGradient(
                        colors: [
                          Color(0xFF42A5F5),
                          Color(0xFF66BB6A),
                          Color(0xFFFFC107),
                          Color(0xFFFF9800),
                          Color(0xFFEF5350),
                        ],
                        stops: [0.0, 0.25, 0.5, 0.75, 1.0],
                        startAngle: 3.14,
                        endAngle: 6.28,
                      ),
                    ),
                  ),
                ),

                // Inner Circle with value
                Container(
                  width: 150,
                  height: 150,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: colorScheme.surface,
                  ),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.baseline,
                          textBaseline: TextBaseline.alphabetic,
                          children: [
                            Text(
                              currentTemp.toStringAsFixed(1),
                              style: theme.textTheme.displayMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: _getTempStatusColor(currentTemp),
                              ),
                            ),
                            const SizedBox(width: 5),
                            Text(
                              '°C',
                              style: theme.textTheme.titleLarge?.copyWith(
                                color: _getTempStatusColor(currentTemp),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 5),
                        Text(
                          _getTempStatus(currentTemp),
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: _getTempStatusColor(currentTemp),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 15),

          // Temperature Range Labels
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('35°C', style: theme.textTheme.bodySmall?.copyWith(
                color: const Color(0xFF42A5F5), fontWeight: FontWeight.w600)),
              Text('36°C', style: theme.textTheme.bodySmall?.copyWith(
                color: const Color(0xFF66BB6A), fontWeight: FontWeight.w600)),
              Text('37°C', style: theme.textTheme.bodySmall?.copyWith(
                color: const Color(0xFFFF9800), fontWeight: FontWeight.w600)),
              Text('38°C', style: theme.textTheme.bodySmall?.copyWith(
                color: _accent, fontWeight: FontWeight.w600)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _build24HourTrendChart(ThemeData theme, ColorScheme colorScheme, bool isDark, List<Map<String, dynamic>> data) {
    // Reverse so oldest is first (data comes descending from Firestore)
    final chronological = data.reversed.toList();
    if (chronological.isEmpty) return const SizedBox.shrink();

    // Build time-based spots: x = hours ago (0 = oldest, max = now)
    final now = DateTime.now();
    final spots = <FlSpot>[];
    double minTemp = 40.0;
    double maxTemp = 30.0;
    double sumTemp = 0;
    int count = 0;

    for (final entry in chronological) {
      final temp = (entry['temperature'] ?? 0).toDouble();
      if (temp < 30 || temp > 45) continue; // skip invalid readings

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
      spots.add(FlSpot(x, temp));

      if (temp < minTemp) minTemp = temp;
      if (temp > maxTemp) maxTemp = temp;
      sumTemp += temp;
      count++;
    }

    if (spots.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: AppColors.tempGradient(isDark),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _accent.withValues(alpha: 0.12)),
        ),
        child: Center(
          child: Text('Not enough data for 24-hour trend yet',
            style: theme.textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant)),
        ),
      );
    }

    final avgTemp = sumTemp / count;
    // Add padding to Y axis
    final chartMinY = (minTemp - 0.5).clamp(34.0, 36.0);
    final chartMaxY = (maxTemp + 0.5).clamp(37.0, 40.0);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: AppColors.tempGradient(isDark),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _accent.withValues(alpha: 0.12)),
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
                  '24-Hour Temperature Trend',
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
                  horizontalInterval: 0.5,
                  getDrawingHorizontalLine: (value) {
                    // Highlight the normal range boundaries
                    if (value == 37.0 || value == 37.5) {
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
                      interval: 0.5,
                      reservedSize: 44,
                      getTitlesWidget: (value, meta) {
                        return Text(
                          '${value.toStringAsFixed(1)}°',
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
                        // value: 0=24h ago, 6=18h ago, 12=12h ago, 18=6h ago, 24=now
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
                          '${spot.y.toStringAsFixed(1)}°C\n${hoursAgo}h ago',
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
              _buildStatChip(theme, colorScheme, 'Min', '${minTemp.toStringAsFixed(1)}°C', const Color(0xFF42A5F5)),
              const SizedBox(width: 10),
              _buildStatChip(theme, colorScheme, 'Avg', '${avgTemp.toStringAsFixed(1)}°C', const Color(0xFFFF9800)),
              const SizedBox(width: 10),
              _buildStatChip(theme, colorScheme, 'Max', '${maxTemp.toStringAsFixed(1)}°C', _accent),
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
              style: theme.textTheme.titleMedium?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getTempStatusColor(double temp) {
    if (temp < 36.5) return const Color(0xFF42A5F5);
    if (temp >= 36.5 && temp <= 37.0) return AppColors.chartGreen;
    if (temp > 37.0 && temp <= 37.5) return AppColors.chartOrange;
    return _accent;
  }

  String _getTempStatus(double temp) {
    if (temp < 36.5) return 'Slightly Low';
    if (temp >= 36.5 && temp <= 37.0) return 'Normal';
    if (temp > 37.0 && temp <= 37.5) return 'Slightly High';
    return 'High Temperature';
  }
}

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'core/theme/app_colors.dart';
import 'services/firestore_service.dart';
import 'globals.dart';

class CryPage extends StatelessWidget {
  const CryPage({super.key});

  // Cry history accent color: Amber
  static const Color _accent = AppColors.chartAmber;

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
      child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Summary Cards
            _buildSummaryCards(theme, isDark),
            const SizedBox(height: 20),

            // Line Chart
            _buildLineChart(theme, colorScheme, isDark),
            const SizedBox(height: 20),

            // Bar Chart for Cry Reasons
            _buildReasonChart(theme, colorScheme, isDark),
            const SizedBox(height: 20),

            // Recent Cries List
            _buildRecentCries(context, theme, colorScheme, isDark),
          ],
        ),
      );
  }

  Widget _buildSummaryCards(ThemeData theme, bool isDark) {
    return Row(
      children: [
        Expanded(
          child: _buildSummaryCard(
            theme, isDark,
            'Today\'s Cries',
            '8',
            Icons.mic_rounded,
            _accent,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildSummaryCard(
            theme, isDark,
            'Avg Duration',
            '4.2 min',
            Icons.timer_rounded,
            AppColors.chartBlue,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildSummaryCard(
            theme, isDark,
            'Most Reason',
            'Hunger',
            Icons.local_dining_rounded,
            AppColors.chartOrange,
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryCard(
      ThemeData theme, bool isDark,
      String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isDark
              ? [color.withValues(alpha: 0.12), color.withValues(alpha: 0.06)]
              : [color.withValues(alpha: 0.08), color.withValues(alpha: 0.03)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 8),
          Text(
            value,
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            title,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildLineChart(ThemeData theme, ColorScheme colorScheme, bool isDark) {
    final List<FlSpot> cryData = [
      const FlSpot(0, 20),
      const FlSpot(2, 45),
      const FlSpot(4, 15),
      const FlSpot(6, 85),
      const FlSpot(8, 40),
      const FlSpot(10, 25),
      const FlSpot(12, 60),
      const FlSpot(14, 35),
      const FlSpot(16, 90),
      const FlSpot(18, 50),
      const FlSpot(20, 30),
      const FlSpot(22, 70),
      const FlSpot(24, 40),
    ];

    final gridColor = isDark ? colorScheme.outlineVariant : Colors.grey[300]!;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _accent.withValues(alpha: 0.10)),
        boxShadow: [
          BoxShadow(
            color: colorScheme.shadow,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Cry Pattern (Last 24 Hours)',
            style: theme.textTheme.titleMedium,
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 200,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: true,
                  getDrawingHorizontalLine: (value) {
                    return FlLine(color: gridColor, strokeWidth: 1);
                  },
                  getDrawingVerticalLine: (value) {
                    return FlLine(color: gridColor, strokeWidth: 1);
                  },
                ),
                titlesData: FlTitlesData(
                  show: true,
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 30,
                      getTitlesWidget: (value, meta) {
                        List<String> hours = [
                          '12AM', '6AM', '12PM', '6PM', '12AM'
                        ];
                        int index = (value ~/ 6).toInt();
                        return index >= 0 && index < hours.length
                            ? Padding(
                                padding: const EdgeInsets.only(top: 8.0),
                                child: Text(hours[index],
                                  style: theme.textTheme.bodySmall),
                              )
                            : const SizedBox();
                      },
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 40,
                      getTitlesWidget: (value, meta) {
                        return Text('${value.toInt()}%',
                          style: theme.textTheme.bodySmall);
                      },
                    ),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                ),
                borderData: FlBorderData(
                  show: true,
                  border: Border.all(color: gridColor),
                ),
                minX: 0,
                maxX: 24,
                minY: 0,
                maxY: 100,
                lineBarsData: [
                  LineChartBarData(
                    spots: cryData,
                    isCurved: true,
                    color: _accent,
                    barWidth: 3,
                    isStrokeCapRound: true,
                    belowBarData: BarAreaData(
                      show: true,
                      gradient: LinearGradient(
                        colors: [
                          _accent.withValues(alpha: 0.3),
                          _accent.withValues(alpha: 0.05),
                        ],
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                      ),
                    ),
                    dotData: const FlDotData(show: false),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Time of Day', style: theme.textTheme.bodySmall?.copyWith(
                color: colorScheme.onSurfaceVariant,
              )),
              Text('Cry Intensity (%)', style: theme.textTheme.bodySmall?.copyWith(
                color: colorScheme.onSurfaceVariant,
              )),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildReasonChart(ThemeData theme, ColorScheme colorScheme, bool isDark) {
    final Map<String, double> reasonData = {
      'Hunger': 45,
      'Sleepy': 25,
      'Discomfort': 15,
      'Need Burping': 10,
      'Other': 5,
    };

    final List<BarChartGroupData> barGroups = [];
    int x = 0;

    reasonData.forEach((reason, percentage) {
      barGroups.add(
        BarChartGroupData(
          x: x,
          barRods: [
            BarChartRodData(
              toY: percentage,
              color: _getReasonColor(reason),
              width: 20,
              borderRadius: BorderRadius.circular(6),
            ),
          ],
        ),
      );
      x++;
    });

    final gridColor = isDark ? colorScheme.outlineVariant : Colors.grey[300]!;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _accent.withValues(alpha: 0.10)),
        boxShadow: [
          BoxShadow(
            color: colorScheme.shadow,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Cry Reasons Distribution',
            style: theme.textTheme.titleMedium,
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 200,
            child: BarChart(
              BarChartData(
                barTouchData: BarTouchData(
                  touchTooltipData: BarTouchTooltipData(
                    tooltipBgColor: colorScheme.surface,
                  ),
                ),
                titlesData: FlTitlesData(
                  show: true,
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        List<String> reasons = reasonData.keys.toList();
                        int index = value.toInt();
                        return index >= 0 && index < reasons.length
                            ? Padding(
                                padding: const EdgeInsets.only(top: 8.0),
                                child: Text(
                                  reasons[index],
                                  style: theme.textTheme.bodySmall,
                                  textAlign: TextAlign.center,
                                ),
                              )
                            : const SizedBox();
                      },
                      reservedSize: 40,
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (value, meta) {
                        return Text('${value.toInt()}%',
                          style: theme.textTheme.bodySmall);
                      },
                      reservedSize: 30,
                    ),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                ),
                borderData: FlBorderData(
                  show: true,
                  border: Border.all(color: gridColor),
                ),
                barGroups: barGroups,
                gridData: const FlGridData(show: true),
                alignment: BarChartAlignment.spaceAround,
                maxY: 50,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecentCries(BuildContext context, ThemeData theme, ColorScheme colorScheme, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _accent.withValues(alpha: 0.10)),
        boxShadow: [
          BoxShadow(
            color: colorScheme.shadow,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Recent Cries',
            style: theme.textTheme.titleMedium,
          ),
          const SizedBox(height: 10),
          StreamBuilder<List<Map<String, dynamic>>>(
            stream: FirestoreService.getCryEvents(globalDeviceId),
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text('Error loading data: ${snapshot.error}'),
                );
              }
              if (!snapshot.hasData || snapshot.data!.isEmpty) {
                return Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text('No data yet', style: theme.textTheme.bodyMedium?.copyWith(
                    color: colorScheme.onSurfaceVariant,
                  )),
                );
              }

              return Column(
                children: snapshot.data!.map((cry) {
                  final reason = cry['cry_type'] ?? 'Unknown';
                  
                  String timeStr = '--:--';
                  final ts = cry['timestamp'];
                  if (ts != null) {
                    DateTime dt;
                    if (ts is int) {
                      dt = DateTime.fromMillisecondsSinceEpoch(ts);
                    } else {
                      // Assuming Timestamp from cloud_firestore
                      dt = ts.toDate();
                    }
                    timeStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
                  }

                  final confidenceVal = cry['confidence'];
                  int confidence = 0;
                  if (confidenceVal is double) {
                    confidence = (confidenceVal * 100).toInt();
                  } else if (confidenceVal is int) {
                    confidence = confidenceVal;
                  }

                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Row(
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: _getReasonColor(reason).withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Icon(
                            _getReasonIcon(reason),
                            color: _getReasonColor(reason),
                            size: 20,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                reason.toString().toUpperCase(),
                                style: theme.textTheme.bodyMedium?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(timeStr, style: theme.textTheme.bodyMedium),
                            Text(
                              '$confidence% confidence',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: _getIntensityColor(confidence),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  );
                }).toList(),
              );
            },
          ),
        ],
      ),
    );
  }

  Color _getReasonColor(String reason) {
    switch (reason.toLowerCase()) {
      case 'hungry':
        return AppColors.chartOrange;
      case 'tired':
        return AppColors.chartIndigo;
      case 'discomfort':
        return AppColors.chartRed;
      case 'diaper':
        return AppColors.chartGreen;
      default:
        return AppColors.chartAmber;
    }
  }

  Color _getIntensityColor(int intensity) {
    if (intensity >= 80) return AppColors.chartRed;
    if (intensity >= 60) return AppColors.chartOrange;
    return AppColors.chartGreen;
  }

  IconData _getReasonIcon(String reason) {
    switch (reason.toLowerCase()) {
      case 'hungry':
        return Icons.local_dining;
      case 'tired':
        return Icons.bedtime;
      case 'discomfort':
        return Icons.sick;
      case 'diaper':
        return Icons.baby_changing_station;
      default:
        return Icons.help;
    }
  }
}

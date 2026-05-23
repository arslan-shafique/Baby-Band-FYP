import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'core/theme/app_colors.dart';
import 'navigation.dart';
import 'services/firestore_service.dart';

class NotificationsPage extends StatelessWidget {
  const NotificationsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;
    final user = FirebaseAuth.instance.currentUser;

    if (user == null) {
      return const Scaffold(
        body: Center(child: Text("Please log in again.")),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('Alerts', style: theme.textTheme.headlineMedium),
        actions: [
          StreamBuilder<List<Map<String, dynamic>>>(
            stream: FirestoreService.getNotifications(user.uid),
            builder: (context, snapshot) {
              if (snapshot.hasData && snapshot.data!.isNotEmpty) {
                return IconButton(
                  icon: const Icon(Icons.delete_sweep_rounded),
                  tooltip: 'Clear All',
                  onPressed: () async {
                    final confirm = await showDialog<bool>(
                      context: context,
                      builder: (context) => AlertDialog(
                        title: const Text('Clear All Alerts?'),
                        content: const Text('This will delete all alert history permanentely.'),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(context, false),
                            child: const Text('Cancel'),
                          ),
                          TextButton(
                            onPressed: () => Navigator.pop(context, true),
                            child: const Text('Clear', style: TextStyle(color: Colors.red)),
                          ),
                        ],
                      ),
                    );

                    if (confirm == true) {
                      await FirestoreService.clearAllNotifications(user.uid);
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('All alerts cleared.')),
                        );
                      }
                    }
                  },
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: StreamBuilder<List<Map<String, dynamic>>>(
          stream: FirestoreService.getNotifications(user.uid),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }

            if (snapshot.hasError) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Text(
                    'Error loading alerts: ${snapshot.error}',
                    style: theme.textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                ),
              );
            }

            final notifications = snapshot.data ?? [];

            if (notifications.isEmpty) {
              return Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: AppColors.chartGreen.withValues(alpha: 0.08),
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppColors.chartGreen.withValues(alpha: 0.2),
                          width: 1.5,
                        ),
                      ),
                      child: Icon(
                        Icons.check_circle_outline_rounded,
                        size: 64,
                        color: AppColors.chartGreen,
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'All Clear',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        color: AppColors.chartGreen,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'No active alerts. Your baby is completely safe!',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              );
            }

            return ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              itemCount: notifications.length,
              itemBuilder: (context, index) {
                final item = notifications[index];
                final String id = item['id'] ?? '';
                final String title = item['title'] ?? 'Alert';
                final String message = item['message'] ?? '';
                final String type = item['type'] ?? 'info';
                final bool isRead = item['is_read'] ?? false;
                
                DateTime? time;
                final ts = item['created_at'];
                if (ts is Timestamp) {
                  time = ts.toDate();
                }

                final Color categoryColor = type == 'critical' 
                    ? AppColors.chartRed 
                    : (type == 'warning' ? AppColors.chartOrange : AppColors.chartBlue);

                final String timeStr = time != null 
                    ? '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}'
                    : '--:--';

                return Dismissible(
                  key: Key(id),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    margin: const EdgeInsets.symmetric(vertical: 6),
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    decoration: BoxDecoration(
                      color: Colors.red.shade400,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Icon(Icons.delete_rounded, color: Colors.white),
                  ),
                  onDismissed: (direction) async {
                    // Quick batch delete of a single doc
                    await FirebaseFirestore.instance.collection('notifications').doc(id).delete();
                  },
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 6),
                    decoration: BoxDecoration(
                      color: isRead 
                          ? colorScheme.surface
                          : categoryColor.withValues(alpha: isDark ? 0.08 : 0.05),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isRead 
                            ? colorScheme.outlineVariant.withValues(alpha: 0.5)
                            : categoryColor.withValues(alpha: 0.25),
                        width: isRead ? 0.5 : 1,
                      ),
                      boxShadow: isRead ? null : [
                        BoxShadow(
                          color: categoryColor.withValues(alpha: isDark ? 0.05 : 0.03),
                          blurRadius: 8,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      leading: Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: categoryColor.withValues(alpha: 0.15),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          type == 'critical' 
                              ? Icons.warning_rounded 
                              : (type == 'warning' ? Icons.thermostat_rounded : Icons.info_rounded),
                          color: categoryColor,
                          size: 24,
                        ),
                      ),
                      title: Row(
                        children: [
                          Expanded(
                            child: Text(
                              title,
                              style: theme.textTheme.bodyLarge?.copyWith(
                                fontWeight: isRead ? FontWeight.w500 : FontWeight.bold,
                                color: isRead ? colorScheme.onSurface : categoryColor,
                              ),
                            ),
                          ),
                          Text(
                            timeStr,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ],
                      ),
                      subtitle: Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(
                          message,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: colorScheme.onSurfaceVariant,
                            height: 1.3,
                          ),
                        ),
                      ),
                      trailing: !isRead 
                          ? IconButton(
                              icon: const Icon(Icons.mark_chat_read_rounded, size: 20),
                              tooltip: 'Mark as read',
                              onPressed: () async {
                                await FirestoreService.markNotificationAsRead(id);
                              },
                            )
                          : null,
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 2),
    );
  }
}

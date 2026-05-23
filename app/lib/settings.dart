import 'package:flutter/material.dart';
import 'core/theme/app_colors.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'main.dart';
import 'navigation.dart';
import 'login.dart';
import 'globals.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _notifications = true;
  String _temperatureUnit = '°C';

  // Alert thresholds (persisted to Firestore)
  double _hrThreshold = 150;
  double _tempThreshold = 37.5;
  String _crySensitivity = 'Medium'; // Low / Medium / High

  @override
  void initState() {
    super.initState();
    _loadAlertSettings();
  }

  Future<void> _loadAlertSettings() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;
    try {
      final doc = await FirebaseFirestore.instance.collection('users').doc(user.uid).get();
      if (doc.exists) {
        final data = doc.data() ?? {};
        final settings = data['settings'] as Map<String, dynamic>? ?? {};
        setState(() {
          _hrThreshold = (settings['hr_alert_threshold'] ?? 150).toDouble();
          _tempThreshold = (settings['temp_alert_threshold'] ?? 37.5).toDouble();
          _crySensitivity = settings['cry_sensitivity'] ?? 'Medium';
        });
      }
    } catch (e) {
      debugPrint('Error loading alert settings: $e');
    }
  }

  Future<void> _saveAlertSettings() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;
    try {
      await FirebaseFirestore.instance.collection('users').doc(user.uid).set({
        'settings': {
          'hr_alert_threshold': _hrThreshold,
          'temp_alert_threshold': _tempThreshold,
          'cry_sensitivity': _crySensitivity,
        }
      }, SetOptions(merge: true));
    } catch (e) {
      debugPrint('Error saving alert settings: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isDark = MyApp.themeProvider.isDarkMode;

    return Scaffold(
      appBar: AppBar(
        title: Text('Settings', style: theme.textTheme.headlineMedium),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Profile Section
          _buildProfileSection(theme, colorScheme),
          const SizedBox(height: 30),

          // Appearance
          _buildSectionTitle('Appearance', colorScheme),
          _buildSettingCard(theme, [
            _buildSettingTile(
              theme: theme,
              colorScheme: colorScheme,
              icon: Icons.dark_mode_rounded,
              title: 'Dark Mode',
              trailing: Switch(
                value: isDark,
                onChanged: (value) {
                  MyApp.themeProvider.toggleTheme(value);
                  setState(() {});
                },
              ),
            ),
          ]),
          const SizedBox(height: 20),

          // Notifications & Display
          _buildSectionTitle('Notifications & Display', colorScheme),
          _buildSettingCard(theme, [
            _buildSettingTile(
              theme: theme,
              colorScheme: colorScheme,
              icon: Icons.notifications_rounded,
              title: 'Push Notifications',
              subtitle: _notifications ? 'Enabled' : 'Disabled',
              trailing: Switch(
                value: _notifications,
                onChanged: (value) {
                  setState(() {
                    _notifications = value;
                  });
                },
              ),
            ),
            _buildDivider(theme),
            _buildSettingTile(
              theme: theme,
              colorScheme: colorScheme,
              icon: Icons.thermostat_rounded,
              title: 'Temperature Unit',
              subtitle: _temperatureUnit,
              trailing: DropdownButton<String>(
                value: _temperatureUnit,
                onChanged: (String? newValue) {
                  setState(() {
                    _temperatureUnit = newValue!;
                  });
                },
                items: <String>['°C', '°F']
                    .map<DropdownMenuItem<String>>((String value) {
                  return DropdownMenuItem<String>(
                    value: value,
                    child: Text(value),
                  );
                }).toList(),
                underline: Container(),
              ),
            ),
          ]),
          const SizedBox(height: 20),

          // Alert Settings
          _buildSectionTitle('Alert Settings', colorScheme),
          _buildSettingCard(theme, [
            _buildSettingTile(
              theme: theme,
              colorScheme: colorScheme,
              icon: Icons.warning_rounded,
              title: 'Critical Alerts',
              subtitle: 'Heart rate > ${_hrThreshold.toInt()} BPM',
              trailing: Icon(
                Icons.arrow_forward_ios,
                size: 16,
                color: colorScheme.onSurfaceVariant,
              ),
              onTap: () {
                _showHeartRateSettings();
              },
            ),
            _buildDivider(theme),
            _buildSettingTile(
              theme: theme,
              colorScheme: colorScheme,
              icon: Icons.thermostat_rounded,
              title: 'Temperature Alerts',
              subtitle: 'Above ${_tempThreshold.toStringAsFixed(1)}°C',
              trailing: Icon(
                Icons.arrow_forward_ios,
                size: 16,
                color: colorScheme.onSurfaceVariant,
              ),
              onTap: () {
                _showTemperatureSettings();
              },
            ),
            _buildDivider(theme),
            _buildSettingTile(
              theme: theme,
              colorScheme: colorScheme,
              icon: Icons.mic_rounded,
              title: 'Cry Detection Sensitivity',
              subtitle: _crySensitivity,
              trailing: Icon(
                Icons.arrow_forward_ios,
                size: 16,
                color: colorScheme.onSurfaceVariant,
              ),
              onTap: () {
                _showCrySensitivitySettings();
              },
            ),
          ]),
          const SizedBox(height: 20),

          // About App
          _buildSettingCard(theme, [
            _buildSettingTile(
              theme: theme,
              colorScheme: colorScheme,
              icon: Icons.info_outline_rounded,
              title: 'About App',
              onTap: () {
                showAboutDialog(
                  context: context,
                  applicationName: 'Smart Baby Monitor',
                  applicationVersion: '1.2.0',
                  applicationIcon: Icon(
                    Icons.child_care_rounded,
                    color: colorScheme.primary,
                    size: 48,
                  ),
                  children: [
                    const SizedBox(height: 10),
                    const Text(
                      'Monitor your baby\'s health and well-being with real-time tracking of temperature, heart rate, and cry patterns.',
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 15),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.star, color: Colors.amber[600], size: 16),
                        Icon(Icons.star, color: Colors.amber[600], size: 16),
                        Icon(Icons.star, color: Colors.amber[600], size: 16),
                        Icon(Icons.star, color: Colors.amber[600], size: 16),
                        Icon(Icons.star_half,
                            color: Colors.amber[600], size: 16),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text('4.5 • 2.8K reviews'),
                  ],
                );
              },
            ),
          ]),
          const SizedBox(height: 30),

          // Logout Button — uses OutlinedButton (M3)
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () {
                _showLogoutConfirmation();
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.error,
                side: BorderSide(color: AppColors.error.withValues(alpha: 0.4)),
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                'Log Out',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 3),
    );
  }

  Widget _buildProfileSection(ThemeData theme, ColorScheme colorScheme) {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return const SizedBox.shrink();
    final isDark = theme.brightness == Brightness.dark;

    return StreamBuilder<DocumentSnapshot>(
      stream: FirebaseFirestore.instance.collection('users').doc(user.uid).snapshots(),
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(
            child: Text(
              'Database Error: ${snapshot.error}',
              style: TextStyle(color: colorScheme.error),
            ),
          );
        }

        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Padding(
            padding: EdgeInsets.all(20),
            child: Center(child: CircularProgressIndicator()),
          );
        }

        final doc = snapshot.data;
        final userData = (doc != null && doc.exists) 
            ? doc.data() as Map<String, dynamic>? ?? {} 
            : {};
            
        final String parentName = userData['name'] ?? 'Parent';
        final String babyName = userData['baby_name'] ?? 'Baby';

        return Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: isDark
                ? AppColors.darkCardGradient
                : const LinearGradient(
                    colors: [Colors.white, Color(0xFFF0FDFA)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: colorScheme.primary.withValues(alpha: 0.12),
              width: 1,
            ),
            boxShadow: [
              BoxShadow(
                color: colorScheme.shadow,
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 70,
                height: 70,
                decoration: BoxDecoration(
                  color: colorScheme.primary.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: colorScheme.primary.withValues(alpha: 0.3),
                    width: 2,
                  ),
                ),
                child: Icon(
                  Icons.person_rounded,
                  size: 35,
                  color: colorScheme.primary,
                ),
              ),
              const SizedBox(width: 20),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      parentName,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      'Parent of $babyName',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding:
                          const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: colorScheme.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        'Premium Plan',
                        style: theme.textTheme.labelMedium?.copyWith(
                          color: colorScheme.primary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: Icon(Icons.edit_outlined, color: colorScheme.primary),
                onPressed: () => _showEditProfileDialog(parentName, babyName),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSectionTitle(String title, ColorScheme colorScheme) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: colorScheme.primary,
        ),
      ),
    );
  }

  Widget _buildSettingCard(ThemeData theme, List<Widget> children) {
    final colorScheme = theme.colorScheme;
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        color: colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: colorScheme.outlineVariant.withValues(alpha: 0.3),
          width: 0.5,
        ),
        boxShadow: [
          BoxShadow(
            color: colorScheme.shadow,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: children,
      ),
    );
  }

  Widget _buildSettingTile({
    required ThemeData theme,
    required ColorScheme colorScheme,
    required IconData icon,
    required String title,
    String? subtitle,
    Widget? trailing,
    VoidCallback? onTap,
  }) {
    return ListTile(
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: colorScheme.primary.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(
          icon,
          color: colorScheme.primary,
          size: 22,
        ),
      ),
      title: Text(
        title,
        style: theme.textTheme.bodyLarge?.copyWith(
          fontWeight: FontWeight.w500,
        ),
      ),
      subtitle: subtitle != null
          ? Text(
              subtitle,
              style: theme.textTheme.bodySmall?.copyWith(
                color: colorScheme.onSurfaceVariant,
              ),
            )
          : null,
      trailing: trailing ??
          Icon(
            Icons.arrow_forward_ios,
            size: 16,
            color: colorScheme.onSurfaceVariant,
          ),
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    );
  }

  Widget _buildDivider(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.only(left: 72.0, right: 16.0),
      child: Divider(
        height: 1,
        color: theme.dividerColor,
      ),
    );
  }

  void _showHeartRateSettings() {
    double tempValue = _hrThreshold;
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            final colorScheme = Theme.of(context).colorScheme;
            return AlertDialog(
              title: const Row(
                children: [
                  Icon(Icons.favorite_rounded, color: Colors.red),
                  SizedBox(width: 10),
                  Text('Heart Rate Alert', style: TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Set the heart rate threshold. You will be notified when BPM exceeds this value.',
                    style: TextStyle(fontSize: 14),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    '${tempValue.toInt()} BPM',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.bold,
                      color: tempValue > 180 ? Colors.red : colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Slider(
                    value: tempValue,
                    min: 60,
                    max: 220,
                    divisions: 32,
                    label: '${tempValue.toInt()} BPM',
                    onChanged: (value) {
                      setDialogState(() => tempValue = value);
                    },
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('60', style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 12)),
                      Text('Normal: 120-160', style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 12)),
                      Text('220', style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 12)),
                    ],
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () {
                    setState(() => _hrThreshold = tempValue);
                    _saveAlertSettings();
                    Navigator.of(context).pop();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Heart rate alert set to ${tempValue.toInt()} BPM')),
                    );
                  },
                  child: const Text('Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _showTemperatureSettings() {
    double tempValue = _tempThreshold;
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            final colorScheme = Theme.of(context).colorScheme;
            return AlertDialog(
              title: const Row(
                children: [
                  Icon(Icons.thermostat_rounded, color: Colors.orange),
                  SizedBox(width: 10),
                  Text('Temperature Alert', style: TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Set the temperature threshold. You will be notified when temperature exceeds this value.',
                    style: TextStyle(fontSize: 14),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    '${tempValue.toStringAsFixed(1)}°C',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.bold,
                      color: tempValue > 38.5 ? Colors.red : Colors.orange,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Slider(
                    value: tempValue,
                    min: 35.0,
                    max: 40.0,
                    divisions: 50,
                    label: '${tempValue.toStringAsFixed(1)}°C',
                    onChanged: (value) {
                      setDialogState(() => tempValue = value);
                    },
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('35.0°C', style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 12)),
                      Text('Normal: 36.5-37.5', style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 12)),
                      Text('40.0°C', style: TextStyle(color: colorScheme.onSurfaceVariant, fontSize: 12)),
                    ],
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () {
                    setState(() => _tempThreshold = tempValue);
                    _saveAlertSettings();
                    Navigator.of(context).pop();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Temperature alert set to ${tempValue.toStringAsFixed(1)}°C')),
                    );
                  },
                  child: const Text('Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _showCrySensitivitySettings() {
    String tempValue = _crySensitivity;
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            final colorScheme = Theme.of(context).colorScheme;
            return AlertDialog(
              title: const Row(
                children: [
                  Icon(Icons.mic_rounded, color: Colors.purple),
                  SizedBox(width: 10),
                  Text('Cry Sensitivity', style: TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Adjust how sensitive the cry detection is. Higher sensitivity means more alerts but may include false positives.',
                    style: TextStyle(fontSize: 14),
                  ),
                  const SizedBox(height: 20),
                  ...['Low', 'Medium', 'High'].map((level) {
                    final isSelected = tempValue == level;
                    final descriptions = {
                      'Low': 'Only very confident detections (>80%)',
                      'Medium': 'Balanced detection (>60%)',
                      'High': 'More sensitive, may have false alerts (>40%)',
                    };
                    final icons = {
                      'Low': Icons.volume_mute_rounded,
                      'Medium': Icons.volume_down_rounded,
                      'High': Icons.volume_up_rounded,
                    };
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: InkWell(
                        onTap: () => setDialogState(() => tempValue = level),
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? colorScheme.primary.withValues(alpha: 0.1)
                                : colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: isSelected
                                  ? colorScheme.primary
                                  : colorScheme.outlineVariant.withValues(alpha: 0.3),
                              width: isSelected ? 2 : 1,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                icons[level],
                                color: isSelected ? colorScheme.primary : colorScheme.onSurfaceVariant,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      level,
                                      style: TextStyle(
                                        fontWeight: FontWeight.w600,
                                        color: isSelected ? colorScheme.primary : null,
                                      ),
                                    ),
                                    Text(
                                      descriptions[level]!,
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: colorScheme.onSurfaceVariant,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              if (isSelected)
                                Icon(Icons.check_circle_rounded, color: colorScheme.primary),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () {
                    setState(() => _crySensitivity = tempValue);
                    _saveAlertSettings();
                    Navigator.of(context).pop();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Cry sensitivity set to $tempValue')),
                    );
                  },
                  child: const Text('Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _showLogoutConfirmation() {
    final colorScheme = Theme.of(context).colorScheme;

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text(
            'Log Out',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          content: const Text('Are you sure you want to log out?'),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(
                'Cancel',
                style: TextStyle(color: colorScheme.onSurfaceVariant),
              ),
            ),
            FilledButton(
              onPressed: () async {
                Navigator.of(context).pop(); // close the dialog
                
                try {
                  final user = FirebaseAuth.instance.currentUser;
                  if (user != null) {
                    // 1. Delete the FCM token so this device stops receiving push notifications
                    // We don't await this so that it doesn't hang if there's no internet
                    FirebaseFirestore.instance.collection('users').doc(user.uid).update({
                      'fcm_token': FieldValue.delete(),
                    }).catchError((e) => debugPrint('FCM token deletion error: $e'));
                    
                    // 2. Clear persisted device ID
                    await clearDeviceId();
                    
                    // 3. Sign out of Firebase
                    await FirebaseAuth.instance.signOut();
                  }
                  
                  if (context.mounted) {
                    // 3. Navigate back to the Login Page and clear navigation history
                    Navigator.of(context).pushAndRemoveUntil(
                      MaterialPageRoute(builder: (context) => const LoginPage()),
                      (Route<dynamic> route) => false,
                    );
                    
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Logged out successfully'),
                        duration: Duration(seconds: 2),
                      ),
                    );
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error logging out: $e')),
                    );
                  }
                }
              },
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.error,
                foregroundColor: Colors.white,
              ),
              child: const Text('Log Out'),
            ),
          ],
        );
      },
    );
  }

  void _showEditProfileDialog(String currentName, String currentBabyName) {
    final nameController = TextEditingController(text: currentName);
    final babyNameController = TextEditingController(text: currentBabyName);

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Edit Profile', style: TextStyle(fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Parent Name'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: babyNameController,
                decoration: const InputDecoration(labelText: 'Baby Name'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () async {
                final user = FirebaseAuth.instance.currentUser;
                if (user != null) {
                  await FirebaseFirestore.instance.collection('users').doc(user.uid).set({
                    'name': nameController.text.trim(),
                    'baby_name': babyNameController.text.trim(),
                  }, SetOptions(merge: true));
                }
                if (context.mounted) Navigator.pop(context);
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }
}

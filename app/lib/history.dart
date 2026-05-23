import 'package:flutter/material.dart';
import 'core/theme/app_colors.dart';
import 'navigation.dart';
import 'cryhistory.dart';
import 'sleephistory.dart';
import 'tempraturehistory.dart';
import 'heartratehistory.dart';

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: Text("History", style: theme.textTheme.headlineMedium),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(
              icon: Icon(Icons.mic_rounded, size: 18, color: AppColors.chartAmber),
              text: "Cry",
            ),
            Tab(
              icon: Icon(Icons.nights_stay_rounded, size: 18, color: AppColors.chartIndigo),
              text: "Sleep",
            ),
            Tab(
              icon: Icon(Icons.thermostat_rounded, size: 18, color: AppColors.chartRed),
              text: "Temp",
            ),
            Tab(
              icon: Icon(Icons.favorite_rounded, size: 18, color: AppColors.chartPink),
              text: "Heart",
            ),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          CryPage(),
          SleepPage(),
          TemperaturePage(),
          HeartbeatPage(),
        ],
      ),
      bottomNavigationBar: const AppBottomNav(currentIndex: 1),
    );
  }
}

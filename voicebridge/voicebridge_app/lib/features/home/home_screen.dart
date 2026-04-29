import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';
import '../../core/constants.dart';
import '../../data/models/app_record.dart';
import '../../providers/records_provider.dart';
import 'widgets/quick_action_card.dart';
import 'widgets/recent_cases_list.dart';
import 'widgets/stats_row.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recordsAsync = ref.watch(recordsProvider);
    final records = recordsAsync.valueOrNull ?? const [];

    final today = DateTime.now();
    final casesToday = records
        .where((r) =>
            r.createdAt.year == today.year &&
            r.createdAt.month == today.month &&
            r.createdAt.day == today.day)
        .length;
    final redCount =
        records.where((r) => r.output.triageLevel == 'red').length;
    final orangeCount =
        records.where((r) => r.output.triageLevel == 'orange').length;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: CustomScrollView(
        slivers: [
          _buildAppBar(context),
          SliverToBoxAdapter(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 20),
                StatsRow(
                  casesToday: casesToday,
                  redCount: redCount,
                  orangeCount: orangeCount,
                  avgMinutes: 6.2,
                ),
                const SizedBox(height: 20),
                const QuickActionCard(),
                const SizedBox(height: 24),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Text(
                    'Recent Cases',
                    style: AppTypography.headlineSmall,
                  ),
                ),
                const SizedBox(height: 12),
                recordsAsync.when(
                  loading: () => const Padding(
                    padding: EdgeInsets.all(32),
                    child: Center(
                      child: CircularProgressIndicator(
                        color: AppColors.secondary,
                      ),
                    ),
                  ),
                  error: (e, _) => Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(
                      'Could not load records — is the server running?',
                      style: AppTypography.bodySmall,
                    ),
                  ),
                  data: (data) => RecentCasesList(
                    records: data.take(5).toList(),
                  ),
                ),
                const SizedBox(height: 100),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/record'),
        backgroundColor: AppColors.secondary,
        child: const Icon(Icons.mic_rounded, color: Colors.white),
      ),
    );
  }

  SliverAppBar _buildAppBar(BuildContext context) {
    return SliverAppBar(
      expandedHeight: 80,
      floating: true,
      pinned: true,
      backgroundColor: Colors.transparent,
      elevation: 0,
      flexibleSpace: FlexibleSpaceBar(
        background: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              decoration: BoxDecoration(
                color: Theme.of(context).brightness == Brightness.dark
                    ? const Color(0xFF0D1B2A).withOpacity(0.8)
                    : Colors.white.withOpacity(0.75),
                border: Border(
                  bottom: BorderSide(
                    color: Theme.of(context).brightness == Brightness.dark
                        ? Colors.white.withOpacity(0.06)
                        : Colors.black.withOpacity(0.04),
                    width: 1,
                  ),
                ),
              ),
            ),
          ),
        ),
        titlePadding: const EdgeInsets.only(left: 16, bottom: 12, right: 16),
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.secondary, Color(0xFF0E7A88)],
                ),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.mic_rounded, size: 16, color: Colors.white),
            ),
            const SizedBox(width: 10),
            Text(
              AppConstants.appName,
              style: AppTypography.headlineMedium.copyWith(fontSize: 18),
            ),
            const Spacer(),
            IconButton(
              icon: const Icon(
                Icons.settings_outlined,
                color: AppColors.textSecondary,
                size: 22,
              ),
              onPressed: () => context.go('/settings'),
            ),
          ],
        ),
      ),
    );
  }
}

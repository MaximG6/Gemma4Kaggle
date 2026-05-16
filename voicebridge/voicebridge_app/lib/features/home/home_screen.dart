import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';
import '../../core/constants.dart';
import '../../providers/records_provider.dart';
import '../../providers/settings_provider.dart';

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
    final redCount    = records.where((r) => r.output.triageLevel == 'red').length;
    final orangeCount = records.where((r) => r.output.triageLevel == 'orange').length;
    final yellowCount = records.where((r) => r.output.triageLevel == 'yellow').length;
    final greenCount  = records.where((r) => r.output.triageLevel == 'green').length;
    final blueCount   = records.where((r) => r.output.triageLevel == 'blue').length;

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
                _buildOfflineBanner(context),
                const SizedBox(height: 16),
                StatsRow(
                  casesToday: casesToday,
                  redCount: redCount,
                  orangeCount: orangeCount,
                  yellowCount: yellowCount,
                  greenCount: greenCount,
                  blueCount: blueCount,
                ),
                const SizedBox(height: 20),
                _buildModeButtons(context),
                const SizedBox(height: 24),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    children: [
                      Container(
                        width: 4,
                        height: 22,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [AppColors.accentPink, AppColors.accentViolet],
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                          ),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        'Recent Cases',
                        style: AppTypography.headlineSmall,
                      ),
                    ],
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

    );
  }

  Widget _buildModeButtons(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: isDark
              ? Colors.white.withOpacity(0.03)
              : Colors.white.withOpacity(0.6),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isDark
                ? Colors.white.withOpacity(0.08)
                : Colors.black.withOpacity(0.06),
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(isDark ? 0.15 : 0.04),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                'Try VoiceBridge',
                style: AppTypography.labelMedium.copyWith(
                  color: isDark ? const Color(0xFF78909C) : AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.5,
                ),
              ),
            ),
            Row(
              children: [
                Expanded(
                  child: _ModeButton(
                    icon: Icons.mic_rounded,
                    title: 'Audio',
                    color: AppColors.accentTeal,
                    onTap: () => context.go('/record'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _ModeButton(
                    icon: Icons.text_fields_rounded,
                    title: 'Text',
                    color: AppColors.accentViolet,
                    onTap: () => context.go('/record?mode=text'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _ModeButton(
                    icon: Icons.chat_bubble_outline_rounded,
                    title: 'Interactive',
                    color: AppColors.accentPink,
                    onTap: () => context.go('/interactive'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOfflineBanner(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.triageGreen.withOpacity(0.18),
              AppColors.triageGreen.withOpacity(0.07),
            ],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: AppColors.triageGreen.withOpacity(0.35),
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(5),
              decoration: BoxDecoration(
                color: AppColors.triageGreen.withOpacity(0.15),
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Icon(
                Icons.security_rounded,
                color: AppColors.triageGreen,
                size: 14,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                'Live demo: running on server (GTX 1080) — in practice runs fully offline on-device',
                style: AppTypography.labelSmall.copyWith(
                  color: AppColors.triageGreen,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLanguageSelector(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final languages = ['English', 'Swahili', 'Hausa', 'Bengali', 'Tagalog'];

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        decoration: BoxDecoration(
          color: isDark
              ? Colors.white.withOpacity(0.05)
              : Colors.black.withOpacity(0.04),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isDark
                ? Colors.white.withOpacity(0.1)
                : Colors.black.withOpacity(0.08),
          ),
        ),
        child: DropdownButton<String>(
          value: languages.contains(settings.selectedLanguage)
              ? settings.selectedLanguage
              : 'English',
          underline: const SizedBox(),
          dropdownColor: isDark ? const Color(0xFF1B2838) : Colors.white,
          iconEnabledColor: isDark ? Colors.white : AppColors.textPrimary,
          items: languages.map((lang) {
            return DropdownMenuItem(
              value: lang,
              child: Text(
                lang,
                style: AppTypography.labelMedium.copyWith(
                  fontSize: 12,
                  color: isDark ? Colors.white70 : AppColors.textPrimary,
                ),
              ),
            );
          }).toList(),
          onChanged: (value) {
            if (value != null) {
              ref.read(settingsProvider.notifier).setLanguage(value);
            }
          },
        ),
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
            filter: ImageFilter.blur(sigmaX: 6, sigmaY: 6),
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
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF26C6DA), AppColors.secondary, Color(0xFF0E4A55)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(10),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.secondary.withOpacity(0.4),
                    blurRadius: 8,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: const Icon(Icons.mic_rounded, size: 17, color: Colors.white),
            ),
            const SizedBox(width: 10),
            Text(
              AppConstants.appName,
              style: AppTypography.headlineMedium.copyWith(fontSize: 18),
            ),
            const Spacer(),
          ],
        ),
      ),
    );
  }
}

class _ModeButton extends StatefulWidget {
  const _ModeButton({
    required this.icon,
    required this.title,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final Color color;
  final VoidCallback onTap;

  @override
  State<_ModeButton> createState() => _ModeButtonState();
}

class _ModeButtonState extends State<_ModeButton> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
          decoration: BoxDecoration(
            color: isDark
                ? (_isHovered ? widget.color.withOpacity(0.15) : Colors.white.withOpacity(0.04))
                : (_isHovered ? widget.color.withOpacity(0.08) : Colors.black.withOpacity(0.02)),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: _isHovered ? widget.color : widget.color.withOpacity(0.3),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: widget.color.withOpacity(_isHovered ? 0.2 : 0.08),
                blurRadius: _isHovered ? 16 : 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(widget.icon, color: widget.color, size: 20),
              const SizedBox(width: 8),
              Text(
                widget.title,
                style: AppTypography.labelLarge.copyWith(
                  color: isDark ? const Color(0xFFB0BEC5) : AppColors.textPrimary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

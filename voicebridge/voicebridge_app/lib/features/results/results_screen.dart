import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/glass.dart';
import '../../core/theme/typography.dart';
import '../../core/utils/triage_level_utils.dart';
import '../../data/models/triage_output.dart';
import '../../providers/pipeline_provider.dart';
import '../../providers/records_provider.dart';
import 'widgets/triage_banner.dart';
import 'widgets/detail_card.dart';
import 'widgets/red_flags_card.dart';
import 'widgets/action_card.dart';

class _ThinkingDropdown extends StatefulWidget {
  const _ThinkingDropdown({required this.thinking});
  final String thinking;

  @override
  State<_ThinkingDropdown> createState() => _ThinkingDropdownState();
}

class _ThinkingDropdownState extends State<_ThinkingDropdown>
    with SingleTickerProviderStateMixin {
  bool _expanded = false;
  late final AnimationController _controller;
  late final Animation<double> _chevronTurn;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
    _chevronTurn = Tween<double>(begin: 0, end: 0.5).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _toggle() {
    setState(() => _expanded = !_expanded);
    _expanded ? _controller.forward() : _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final headerTextColor =
        isDark ? const Color(0xFFBDBDBD) : AppColors.textSecondary;
    final bodyTextColor =
        isDark ? const Color(0xFFBDBDBD) : AppColors.textPrimary;
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark
              ? Colors.white.withOpacity(0.06)
              : Colors.white.withOpacity(0.3),
          width: 1.0,
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 6, sigmaY: 6),
          child: Container(
            decoration: BoxDecoration(
              color: isDark
                  ? const Color(0xFF1A2B3C).withOpacity(0.7)
                  : Colors.white.withOpacity(0.85),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              children: [
                InkWell(
                  onTap: _toggle,
                  borderRadius: BorderRadius.circular(20),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Row(
                      children: [
                        Container(
                          width: 28,
                          height: 28,
                          decoration: BoxDecoration(
                            color: AppColors.secondary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(
                            Icons.psychology_outlined,
                            size: 16,
                            color: AppColors.secondary,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'MODEL THINKING',
                          style: AppTypography.labelLarge.copyWith(
                            color: headerTextColor,
                            letterSpacing: 0.8,
                          ),
                        ),
                        const Spacer(),
                        RotationTransition(
                          turns: _chevronTurn,
                          child: Icon(
                            Icons.expand_more_rounded,
                            color: headerTextColor,
                            size: 20,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                AnimatedCrossFade(
                  firstChild: const SizedBox.shrink(),
                  secondChild: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Divider(
                          color: AppColors.textSecondary.withOpacity(0.15),
                          height: 1,
                        ),
                        const SizedBox(height: 14),
                        ConstrainedBox(
                          constraints: const BoxConstraints(maxHeight: 240),
                          child: SingleChildScrollView(
                            child: Text(
                              widget.thinking,
                              style: AppTypography.monoSmall.copyWith(
                                color: bodyTextColor,
                                height: 1.6,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  crossFadeState: _expanded
                      ? CrossFadeState.showSecond
                      : CrossFadeState.showFirst,
                  duration: const Duration(milliseconds: 200),
                  sizeCurve: Curves.easeInOut,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class ResultsScreen extends ConsumerWidget {
  const ResultsScreen({super.key, required this.id});

  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Fetch the specific record by ID for history navigation
    final recordAsync = ref.watch(recordByIdProvider(id));
    final pipelineAsync = ref.watch(pipelineProvider);

    // Try to get output from the fetched record first, then pipeline, then mock
    TriageOutput output;
    final record = recordAsync.whenOrNull(data: (r) => r);
    if (record != null) {
      output = record.output;
    } else {
      output = pipelineAsync.whenOrNull(
            data: (s) => s.result,
          ) ??
          TriageOutput.mock();
    }

    final level = triageLevelFromString(output.triageLevel);

    // Show loading while fetching record
    final isLoading = recordAsync.isLoading;
    if (isLoading) {
      return Scaffold(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        body: const Center(
          child: CircularProgressIndicator(
            color: AppColors.secondary,
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Stack(
        children: [
          CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: SafeArea(
                  bottom: false,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      TriageBanner(level: level),
                      const SizedBox(height: 16),
                      _buildCards(output, level),
                      const SizedBox(height: 100),
                    ],
                  ),
                ),
              ),
            ],
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: _buildActionBar(context, ref, output),
          ),
        ],
      ),
    );
  }

  Widget _buildCards(TriageOutput output, TriageLevel level) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          DetailCard(
            title: 'PRIMARY COMPLAINT',
            icon: Icons.person_outline_rounded,
            accentColor: AppColors.accentTeal,
            child: DetailText(output.primaryComplaint),
          ),
          const SizedBox(height: 12),
          if (output.reportedSymptoms.isNotEmpty) ...[
            DetailCard(
              title: 'SYMPTOMS',
              icon: Icons.list_alt_rounded,
              accentColor: AppColors.accentPink,
              child: DetailChips(items: output.reportedSymptoms, color: AppColors.accentPink),
            ),
            const SizedBox(height: 12),
          ],
          if (output.vitalSignsReported.isNotEmpty) ...[
            DetailCard(
              title: 'VITALS',
              icon: Icons.monitor_heart_outlined,
              accentColor: AppColors.accentCyan,
              child: VitalsGrid(vitals: output.vitalSignsReported),
            ),
            const SizedBox(height: 12),
          ],
          DetailCard(
            title: 'DURATION',
            icon: Icons.schedule_rounded,
            accentColor: AppColors.accentAmber,
            child: DetailText(output.durationOfSymptoms),
          ),
          const SizedBox(height: 12),
          if (output.relevantHistory.isNotEmpty) ...[
            DetailCard(
              title: 'HISTORY',
              icon: Icons.history_rounded,
              accentColor: AppColors.accentViolet,
              child: DetailText(output.relevantHistory),
            ),
            const SizedBox(height: 12),
          ],
          RedFlagsCard(flags: output.redFlagIndicators),
          if (output.redFlagIndicators.isNotEmpty) const SizedBox(height: 12),
          ActionCard(action: output.recommendedAction, level: level),
          if (output.rawThinking != null && output.rawThinking!.isNotEmpty) ...[
            const SizedBox(height: 12),
            _ThinkingDropdown(thinking: output.rawThinking!),
          ],
          const SizedBox(height: 12),
          GlassCard(
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Referral needed',
                          style: AppTypography.labelMedium),
                      Text(
                        output.referralNeeded ? 'YES' : 'NO',
                        style: AppTypography.headlineSmall.copyWith(
                          color: output.referralNeeded
                              ? AppColors.triageRed
                              : AppColors.triageGreen,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                    width: 1,
                    height: 40,
                    color: AppColors.textSecondary.withOpacity(0.15)),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(left: 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Confidence', style: AppTypography.labelMedium),
                        Text(
                          '${(output.confidenceScore * 100).toStringAsFixed(0)}%',
                          style: AppTypography.headlineSmall,
                        ),
                      ],
                    ),
                  ),
                ),
                Container(
                    width: 1,
                    height: 40,
                    color: AppColors.textSecondary.withOpacity(0.15)),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(left: 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Language', style: AppTypography.labelMedium),
                        Text(
                          output.sourceLanguage.toUpperCase(),
                          style: AppTypography.headlineSmall,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionBar(
    BuildContext context,
    WidgetRef ref,
    TriageOutput output,
  ) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return ClipRRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
        child: Container(
          padding: EdgeInsets.only(
            left: 16,
            right: 16,
            bottom: MediaQuery.of(context).padding.bottom + 16,
            top: 12,
          ),
          decoration: BoxDecoration(
            color: isDark
                ? const Color(0xFF0D1B2A).withOpacity(0.75)
                : Colors.white.withOpacity(0.75),
            border: Border(
              top: BorderSide(
                color: isDark
                    ? Colors.white.withOpacity(0.1)
                    : Colors.white.withOpacity(0.4),
                width: 1,
              ),
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(isDark ? 0.3 : 0.06),
                blurRadius: 20,
                offset: const Offset(0, -4),
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.share_rounded, size: 18),
                  label: const Text('Share'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.secondary,
                    side: const BorderSide(color: AppColors.secondary),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: ElevatedButton.icon(
                  onPressed: () {
                    ref.read(pipelineProvider.notifier).reset();
                    context.go('/record');
                  },
                  icon: const Icon(Icons.mic_rounded, size: 18),
                  label: const Text('New Intake'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.secondary,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

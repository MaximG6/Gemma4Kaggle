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
        backgroundColor: AppColors.surfaceLight,
        body: const Center(
          child: CircularProgressIndicator(
            color: AppColors.secondary,
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.surfaceLight,
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
            child: DetailText(output.primaryComplaint),
          ),
          const SizedBox(height: 12),
          if (output.reportedSymptoms.isNotEmpty) ...[
            DetailCard(
              title: 'SYMPTOMS',
              icon: Icons.list_alt_rounded,
              child: DetailChips(items: output.reportedSymptoms),
            ),
            const SizedBox(height: 12),
          ],
          if (output.vitalSignsReported.isNotEmpty) ...[
            DetailCard(
              title: 'VITALS',
              icon: Icons.monitor_heart_outlined,
              child: VitalsGrid(vitals: output.vitalSignsReported),
            ),
            const SizedBox(height: 12),
          ],
          DetailCard(
            title: 'DURATION',
            icon: Icons.schedule_rounded,
            child: DetailText(output.durationOfSymptoms),
          ),
          const SizedBox(height: 12),
          if (output.relevantHistory.isNotEmpty) ...[
            DetailCard(
              title: 'HISTORY',
              icon: Icons.history_rounded,
              child: DetailText(output.relevantHistory),
            ),
            const SizedBox(height: 12),
          ],
          RedFlagsCard(flags: output.redFlagIndicators),
          if (output.redFlagIndicators.isNotEmpty) const SizedBox(height: 12),
          ActionCard(action: output.recommendedAction, level: level),
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
    return Container(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        bottom: MediaQuery.of(context).padding.bottom + 16,
        top: 12,
      ),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.95),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
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
    );
  }
}

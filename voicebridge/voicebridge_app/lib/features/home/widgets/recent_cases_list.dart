import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/colors.dart';
import '../../../core/theme/glass.dart';
import '../../../core/theme/typography.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../core/utils/triage_level_utils.dart';
import '../../../data/models/app_record.dart';

class RecentCasesList extends StatelessWidget {
  const RecentCasesList({super.key, required this.records});

  final List<AppRecord> records;

  @override
  Widget build(BuildContext context) {
    if (records.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: GlassCard(
          child: Column(
            children: [
              Icon(Icons.inbox_rounded,
                  size: 40, color: AppColors.textSecondary.withOpacity(0.4)),
              const SizedBox(height: 12),
              Text('No cases yet', style: AppTypography.bodyMedium),
              const SizedBox(height: 4),
              Text(
                'Tap Record to start your first intake',
                style: AppTypography.bodySmall,
              ),
            ],
          ),
        ),
      );
    }

    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: records.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (ctx, i) => _CaseCard(record: records[i]),
    );
  }
}

class _CaseCard extends StatelessWidget {
  const _CaseCard({required this.record});

  final AppRecord record;

  @override
  Widget build(BuildContext context) {
    final level = triageLevelFromString(record.output.triageLevel);

    return GestureDetector(
      onTap: () => context.go('/case/${record.id}'),
      child: GlassCard(
        padding: EdgeInsets.zero,
        child: Row(
          children: [
            Container(
              width: 6,
              height: 72,
              decoration: BoxDecoration(
                color: level.color,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(20),
                  bottomLeft: Radius.circular(20),
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: level.color.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            level.label,
                            style: AppTypography.labelSmall.copyWith(
                              color: level.color,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        const Spacer(),
                        Text(
                          formatRelativeTime(record.createdAt),
                          style: AppTypography.bodySmall,
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      record.output.primaryComplaint,
                      style: AppTypography.bodyMedium.copyWith(
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      record.output.sourceLanguage.toUpperCase(),
                      style: AppTypography.bodySmall,
                    ),
                  ],
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.only(right: 14),
              child: Icon(
                Icons.chevron_right_rounded,
                color: AppColors.textSecondary,
                size: 20,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

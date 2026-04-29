import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/colors.dart';
import '../../../core/theme/glass.dart';
import '../../../core/theme/typography.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../core/utils/triage_level_utils.dart';
import '../../../data/models/app_record.dart';

class CaseCard extends StatelessWidget {
  const CaseCard({
    super.key,
    required this.record,
    required this.onDelete,
  });

  final AppRecord record;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final level = triageLevelFromString(record.output.triageLevel);

    return Dismissible(
      key: Key(record.id),
      direction: DismissDirection.endToStart,
      onDismissed: (_) => onDelete(),
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        decoration: BoxDecoration(
          color: AppColors.triageRed.withOpacity(0.12),
          borderRadius: BorderRadius.circular(20),
        ),
        child: const Icon(Icons.delete_outline, color: AppColors.triageRed),
      ),
      child: GestureDetector(
        onTap: () => context.go('/case/${record.id}'),
        child: GlassCard(
          padding: EdgeInsets.zero,
          child: Row(
            children: [
              Container(
                width: 5,
                height: 80,
                decoration: BoxDecoration(
                  color: level.color,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(20),
                    bottomLeft: Radius.circular(20),
                  ),
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
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
                      const SizedBox(height: 6),
                      Text(
                        record.output.primaryComplaint,
                        style: AppTypography.bodyMedium
                            .copyWith(fontWeight: FontWeight.w500),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${record.output.sourceLanguage.toUpperCase()} · '
                        '${(record.output.confidenceScore * 100).toStringAsFixed(0)}% confidence',
                        style: AppTypography.bodySmall,
                      ),
                    ],
                  ),
                ),
              ),
              const Padding(
                padding: EdgeInsets.only(right: 12),
                child: Icon(
                  Icons.chevron_right_rounded,
                  color: AppColors.textSecondary,
                  size: 20,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

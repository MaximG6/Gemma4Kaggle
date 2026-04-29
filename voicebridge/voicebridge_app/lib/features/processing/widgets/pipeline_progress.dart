import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';
import '../../../core/theme/typography.dart';
import '../../../domain/pipeline/voicebridge_pipeline.dart';

class PipelineProgressStepper extends StatelessWidget {
  const PipelineProgressStepper({
    super.key,
    required this.currentStatus,
    required this.elapsed,
  });

  final PipelineStatus currentStatus;
  final Duration elapsed;

  static const _steps = [
    (PipelineStatus.transcribing, Icons.hearing_rounded, 'Preparing audio'),
    (PipelineStatus.transcribing, Icons.translate_rounded, 'Detecting language'),
    (PipelineStatus.transcribing, Icons.record_voice_over_rounded, 'Transcribing'),
    (PipelineStatus.triaging, Icons.analytics_rounded, 'Analyzing triage'),
    (PipelineStatus.generatingReport, Icons.picture_as_pdf_rounded, 'Generating report'),
  ];

  @override
  Widget build(BuildContext context) {
    final currentIdx = currentStatus.stepIndex;

    return Column(
      children: List.generate(_steps.length, (i) {
        final (_, icon, label) = _steps[i];
        final isDone = currentIdx > i;
        final isActive = currentIdx == i;

        return _StepRow(
          icon: icon,
          label: label,
          isDone: isDone,
          isActive: isActive,
          isLast: i == _steps.length - 1,
        );
      }),
    );
  }
}

class _StepRow extends StatelessWidget {
  const _StepRow({
    required this.icon,
    required this.label,
    required this.isDone,
    required this.isActive,
    required this.isLast,
  });

  final IconData icon;
  final String label;
  final bool isDone;
  final bool isActive;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    Color iconColor;
    Color lineColor;

    if (isDone) {
      iconColor = AppColors.secondary;
      lineColor = AppColors.secondary;
    } else if (isActive) {
      iconColor = Colors.white;
      lineColor = Colors.white24;
    } else {
      iconColor = Colors.white30;
      lineColor = Colors.white12;
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isDone
                    ? AppColors.secondary.withOpacity(0.2)
                    : isActive
                        ? Colors.white.withOpacity(0.15)
                        : Colors.white.withOpacity(0.05),
                border: Border.all(
                  color: iconColor.withOpacity(0.5),
                  width: 1.5,
                ),
              ),
              child: isDone
                  ? const Icon(Icons.check_rounded,
                      color: AppColors.secondary, size: 18)
                  : Icon(icon, color: iconColor, size: 18),
            ),
            if (!isLast)
              Container(
                width: 2,
                height: 32,
                color: lineColor,
              ),
          ],
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(top: 10, bottom: 32),
            child: AnimatedDefaultTextStyle(
              duration: const Duration(milliseconds: 200),
              style: isDone
                  ? AppTypography.bodyMedium.copyWith(
                      color: Colors.white60,
                      decoration: TextDecoration.lineThrough,
                    )
                  : isActive
                      ? AppTypography.bodyMedium.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        )
                      : AppTypography.bodyMedium.copyWith(color: Colors.white30),
              child: Text(label),
            ),
          ),
        ),
      ],
    );
  }
}

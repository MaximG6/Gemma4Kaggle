import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';
import '../../../core/theme/typography.dart';
import '../../../domain/pipeline/voicebridge_pipeline.dart';

class _StepDef {
  final int stage;
  final IconData icon;
  final String label;
  const _StepDef(this.stage, this.icon, this.label);
}

class PipelineProgressStepper extends StatelessWidget {
  const PipelineProgressStepper({
    super.key,
    required this.currentStatus,
    required this.elapsed,
    this.inputMode = 'audio',
  });

  final PipelineStatus currentStatus;
  final Duration elapsed;
  final String inputMode;

  List<_StepDef> _getSteps() {
    if (inputMode == 'text') {
      return [
        const _StepDef(0, Icons.text_fields, 'Receiving text input'),
        const _StepDef(1, Icons.language, 'Detecting language'),
        const _StepDef(1, Icons.local_hospital, 'Extracting symptoms'),
        const _StepDef(2, Icons.checklist, 'Applying triage rules'),
        const _StepDef(2, Icons.warning_amber, 'Evaluating urgency level'),
        const _StepDef(3, Icons.picture_as_pdf, 'Generating clinical report'),
      ];
    }
    return [
      const _StepDef(0, Icons.file_upload, 'Loading audio file'),
      const _StepDef(1, Icons.equalizer, 'Processing audio stream'),
      const _StepDef(1, Icons.mic_none, 'Transcribing speech to text'),
      const _StepDef(2, Icons.language, 'Detecting language'),
      const _StepDef(2, Icons.local_hospital, 'Extracting symptoms'),
      const _StepDef(2, Icons.checklist, 'Applying triage rules'),
      const _StepDef(3, Icons.picture_as_pdf, 'Generating clinical report'),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final steps = _getSteps();
    return Column(
      children: List.generate(steps.length, (i) {
        final step = steps[i];
        final isDone = currentStatus.stepIndex > step.stage;
        final isActive = currentStatus.stepIndex == step.stage;

        return _StepRow(
          icon: step.icon,
          label: step.label,
          isDone: isDone,
          isActive: isActive,
          isLast: i == steps.length - 1,
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
    final isDark = Theme.of(context).brightness == Brightness.dark;
    Color iconColor;
    Color lineColor;
    BoxDecoration boxDecoration;

    if (isDone) {
      iconColor = AppColors.secondary;
      lineColor = AppColors.secondary;
      boxDecoration = BoxDecoration(
        shape: BoxShape.circle,
        color: AppColors.secondary.withOpacity(0.2),
        border: Border.all(color: AppColors.secondary.withOpacity(0.5), width: 1.5),
      );
    } else if (isActive) {
      iconColor = Colors.white;
      lineColor = AppColors.accentTeal.withOpacity(0.4);
      boxDecoration = BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          colors: [AppColors.secondary, AppColors.accentTeal],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.secondary.withOpacity(0.4),
            blurRadius: 12,
            spreadRadius: 2,
          ),
        ],
      );
    } else {
      iconColor = isDark ? Colors.white30 : AppColors.textSecondary.withOpacity(0.4);
      lineColor = isDark ? Colors.white12 : Colors.black.withOpacity(0.08);
      boxDecoration = BoxDecoration(
        shape: BoxShape.circle,
        color: isDark ? Colors.white.withOpacity(0.05) : Colors.black.withOpacity(0.04),
        border: Border.all(color: iconColor, width: 1.5),
      );
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
              decoration: boxDecoration,
              child: isDone
                  ? const Icon(Icons.check_rounded,
                      color: AppColors.secondary, size: 18)
                  : Icon(icon, color: iconColor, size: 18),
            ),
            if (!isLast)
              Container(
                width: 2,
                height: 32,
                decoration: BoxDecoration(
                  gradient: isActive ? LinearGradient(
                    colors: [AppColors.secondary.withOpacity(0.6), AppColors.accentTeal.withOpacity(0.2)],
                  ) : null,
                  color: isActive ? null : lineColor,
                ),
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
                      color: isDark ? Colors.white60 : const Color(0xFF37474F),
                    )
                  : isActive
                      ? AppTypography.bodyMedium.copyWith(
                          color: isDark ? Colors.white : const Color(0xFF263238),
                          fontWeight: FontWeight.w600,
                        )
                      : AppTypography.bodyMedium.copyWith(color: isDark ? Colors.white30 : const Color(0xFF90A4AE)),
              child: Text(label),
            ),
          ),
        ),
      ],
    );
  }
}

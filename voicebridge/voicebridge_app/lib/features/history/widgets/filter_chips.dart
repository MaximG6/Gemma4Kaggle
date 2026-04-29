import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';
import '../../../core/theme/typography.dart';
import '../../../core/utils/triage_level_utils.dart';

class TriageFilterChips extends StatelessWidget {
  const TriageFilterChips({
    super.key,
    required this.selected,
    required this.onSelected,
  });

  final String selected;
  final ValueChanged<String> onSelected;

  static const _options = ['All', 'RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE'];

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: _options.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (_, i) {
          final opt = _options[i];
          final isSelected = opt == selected;
          final level = opt == 'All'
              ? null
              : triageLevelFromString(opt.toLowerCase());
          final color =
              level != null ? level.color : AppColors.secondary;

          return GestureDetector(
            onTap: () => onSelected(opt),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: isSelected ? color : color.withOpacity(0.08),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: isSelected ? color : color.withOpacity(0.3),
                ),
              ),
              child: Text(
                opt,
                style: AppTypography.labelMedium.copyWith(
                  color: isSelected ? Colors.white : color,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

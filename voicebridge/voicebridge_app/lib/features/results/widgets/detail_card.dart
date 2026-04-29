import 'package:flutter/material.dart';
import '../../../core/theme/glass.dart';
import '../../../core/theme/typography.dart';
import '../../../core/theme/colors.dart';

class DetailCard extends StatelessWidget {
  const DetailCard({
    super.key,
    required this.title,
    required this.child,
    this.icon,
  });

  final String title;
  final Widget child;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
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
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                if (icon != null) ...[
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: AppColors.secondary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(icon, size: 16, color: AppColors.secondary),
                  ),
                  const SizedBox(width: 8),
                ],
                Text(
                  title,
                  style: AppTypography.labelLarge.copyWith(
                    color: isDark ? Colors.white70 : AppColors.textSecondary,
                    letterSpacing: 0.8,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            child,
          ],
        ),
      ),
    );
  }
}

class DetailText extends StatelessWidget {
  const DetailText(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(text, style: AppTypography.bodyMedium);
  }
}

class DetailChips extends StatelessWidget {
  const DetailChips({super.key, required this.items, this.color});

  final List<String> items;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 6,
      children: items
          .map(
            (s) => Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: (color ?? AppColors.secondary).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: (color ?? AppColors.secondary).withOpacity(0.25),
                ),
              ),
              child: Text(
                s,
                style: AppTypography.bodySmall.copyWith(
                  color: color ?? AppColors.secondary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          )
          .toList(),
    );
  }
}

class VitalsGrid extends StatelessWidget {
  const VitalsGrid({super.key, required this.vitals});

  final Map<String, String> vitals;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final entries = vitals.entries.toList();
    return Wrap(
      spacing: 12,
      runSpacing: 10,
      children: entries
          .map(
            (e) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(e.key, style: AppTypography.bodySmall),
                Text(
                  e.value,
                  style: AppTypography.monoMedium.copyWith(
                    color: isDark ? Colors.white : AppColors.textPrimary,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          )
          .toList(),
    );
  }
}

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
    this.accentColor,
  });

  final String title;
  final Widget child;
  final IconData? icon;
  final Color? accentColor;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final color = accentColor ?? AppColors.secondary;
    return GlassCard(
      accentColor: accentColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (icon != null) ...[
                Container(
                  width: 30,
                  height: 30,
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.16),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, size: 16, color: color),
                ),
                const SizedBox(width: 8),
              ],
              Text(
                title,
                style: AppTypography.labelLarge.copyWith(
                  color: isDark
                      ? const Color(0xFFBDBDBD)
                      : color.withOpacity(0.75),
                  letterSpacing: 0.8,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          child,
        ],
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
                color: (color ?? AppColors.secondary).withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: (color ?? AppColors.secondary).withOpacity(0.28),
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
                    color: isDark ? const Color(0xFFE0E0E0) : AppColors.textPrimary,
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

import 'package:flutter/material.dart';
import '../../../core/theme/typography.dart';
import '../../../core/utils/triage_level_utils.dart';

class TriageBanner extends StatelessWidget {
  const TriageBanner({super.key, required this.level});

  final TriageLevel level;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      color: level.color,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(level.icon, color: Colors.white, size: 28),
              const SizedBox(width: 12),
              Text(
                'SATS — ${level.label}',
                style: AppTypography.headlineLarge.copyWith(
                  color: Colors.white,
                  fontSize: 24,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            level.waitTime,
            style: AppTypography.headlineSmall.copyWith(
              color: Colors.white.withOpacity(0.85),
            ),
          ),
          const SizedBox(height: 2),
          Text(
            level.description,
            style:
                AppTypography.bodySmall.copyWith(color: Colors.white70),
          ),
        ],
      ),
    );
  }
}

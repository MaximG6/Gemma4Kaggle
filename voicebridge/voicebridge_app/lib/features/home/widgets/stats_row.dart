import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';
import '../../../core/theme/glass.dart';
import '../../../core/theme/typography.dart';

class StatsRow extends StatelessWidget {
  const StatsRow({
    super.key,
    required this.casesToday,
    required this.redCount,
    required this.orangeCount,
    required this.avgMinutes,
  });

  final int casesToday;
  final int redCount;
  final int orangeCount;
  final double avgMinutes;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 90,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: [
          _StatCard(
            label: 'Cases Today',
            value: casesToday.toString(),
            icon: Icons.folder_open_rounded,
            color: AppColors.secondary,
          ),
          const SizedBox(width: 12),
          _StatCard(
            label: 'RED / ORANGE',
            value: '$redCount / $orangeCount',
            icon: Icons.warning_rounded,
            color: AppColors.triageOrange,
          ),
          const SizedBox(width: 12),
          _StatCard(
            label: 'Avg Time',
            value: '${avgMinutes.toStringAsFixed(1)}m',
            icon: Icons.timer_outlined,
            color: AppColors.triageGreen,
          ),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      accentColor: color,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [color, color.withOpacity(0.6)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: color.withOpacity(0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Icon(icon, color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(value,
                  style: AppTypography.headlineSmall.copyWith(
                    fontWeight: FontWeight.w700,
                    fontSize: 18,
                    color: color,
                  )),
              Text(label, style: AppTypography.bodySmall),
            ],
          ),
        ],
      ),
    );
  }
}

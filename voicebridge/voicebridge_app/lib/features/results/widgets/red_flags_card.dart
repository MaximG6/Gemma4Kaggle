import 'package:flutter/material.dart';
import 'dart:ui';
import '../../../core/theme/colors.dart';
import '../../../core/theme/typography.dart';

class RedFlagsCard extends StatelessWidget {
  const RedFlagsCard({super.key, required this.flags});

  final List<String> flags;

  @override
  Widget build(BuildContext context) {
    if (flags.isEmpty) return const SizedBox.shrink();

    return ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          decoration: BoxDecoration(
            color: AppColors.triageRed.withOpacity(0.08),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: AppColors.triageRed.withOpacity(0.3),
              width: 1.0,
            ),
          ),
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.flag_rounded,
                    color: AppColors.triageRed,
                    size: 16,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'RED FLAG INDICATORS',
                    style: AppTypography.labelLarge.copyWith(
                      color: AppColors.triageRed,
                      letterSpacing: 0.8,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ...flags.map(
                (f) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Container(
                          width: 6,
                          height: 6,
                          decoration: const BoxDecoration(
                            shape: BoxShape.circle,
                            color: AppColors.triageRed,
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(f, style: AppTypography.bodyMedium),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

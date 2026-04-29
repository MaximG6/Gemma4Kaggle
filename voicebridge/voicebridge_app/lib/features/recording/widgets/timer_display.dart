import 'package:flutter/material.dart';
import '../../../core/theme/typography.dart';

class TimerDisplay extends StatelessWidget {
  const TimerDisplay({super.key, required this.elapsed});

  final Duration elapsed;

  @override
  Widget build(BuildContext context) {
    final minutes = elapsed.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = elapsed.inSeconds.remainder(60).toString().padLeft(2, '0');

    return Text(
      '$minutes:$seconds',
      style: AppTypography.monoLarge.copyWith(color: Colors.white),
    );
  }
}

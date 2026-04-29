import 'dart:math' as math;
import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class WaveformVisualizer extends StatefulWidget {
  const WaveformVisualizer({
    super.key,
    required this.amplitudes,
    required this.isRecording,
  });

  final List<double> amplitudes;
  final bool isRecording;

  @override
  State<WaveformVisualizer> createState() => _WaveformVisualizerState();
}

class _WaveformVisualizerState extends State<WaveformVisualizer>
    with SingleTickerProviderStateMixin {
  late AnimationController _breathController;
  late Animation<double> _breathAnimation;

  @override
  void initState() {
    super.initState();
    _breathController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _breathAnimation = Tween<double>(begin: 0.3, end: 0.7).animate(
      CurvedAnimation(parent: _breathController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _breathController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          decoration: BoxDecoration(
            color: isDark
                ? Colors.white.withOpacity(0.04)
                : Colors.white.withOpacity(0.3),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isDark
                  ? Colors.white.withOpacity(0.08)
                  : Colors.white.withOpacity(0.4),
              width: 1.0,
            ),
          ),
          child: AnimatedBuilder(
            animation: _breathAnimation,
            builder: (_, __) {
              return CustomPaint(
                painter: _WaveformPainter(
                  amplitudes: widget.amplitudes,
                  isRecording: widget.isRecording,
                  breathValue: _breathAnimation.value,
                  isDark: isDark,
                ),
                child: const SizedBox.expand(),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _WaveformPainter extends CustomPainter {
  _WaveformPainter({
    required this.amplitudes,
    required this.isRecording,
    required this.breathValue,
    required this.isDark,
  });

  final List<double> amplitudes;
  final bool isRecording;
  final double breathValue;
  final bool isDark;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;

    const barCount = 40;
    final barWidth = size.width / (barCount * 2);
    final centerY = size.height / 2;

    for (int i = 0; i < barCount; i++) {
      double amp;
      if (!isRecording || amplitudes.isEmpty) {
        // Breathing animation
        final wave = math.sin((i / barCount) * math.pi * 2 + breathValue * math.pi * 2);
        amp = (breathValue * 0.3 + 0.1) * (0.5 + 0.5 * wave);
      } else {
        final dataIndex = ((i / barCount) * amplitudes.length).floor()
            .clamp(0, amplitudes.length - 1);
        amp = amplitudes[dataIndex].clamp(0.0, 1.0);
      }

      final barHeight = math.max(4.0, amp * (size.height * 0.7));
      final x = (i * 2 + 0.5) * barWidth + barWidth / 2;

      final opacity = isRecording
          ? 0.6 + 0.4 * amp
          : 0.3 + 0.3 * breathValue;

      paint.color = isRecording
          ? AppColors.secondary.withOpacity(opacity)
          : (isDark ? Colors.white : Colors.black38).withOpacity(opacity);

      canvas.drawLine(
        Offset(x, centerY - barHeight / 2),
        Offset(x, centerY + barHeight / 2),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(_WaveformPainter old) =>
      old.amplitudes != amplitudes ||
      old.isRecording != isRecording ||
      old.breathValue != breathValue ||
      old.isDark != isDark;
}

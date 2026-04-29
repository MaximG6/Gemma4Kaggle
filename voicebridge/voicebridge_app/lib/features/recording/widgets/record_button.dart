import 'package:flutter/material.dart';
import '../../../core/theme/colors.dart';

class RecordButton extends StatefulWidget {
  const RecordButton({
    super.key,
    required this.isRecording,
    required this.onTap,
  });

  final bool isRecording;
  final VoidCallback onTap;

  @override
  State<RecordButton> createState() => _RecordButtonState();
}

class _RecordButtonState extends State<RecordButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );

    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.25).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void didUpdateWidget(RecordButton old) {
    super.didUpdateWidget(old);
    if (widget.isRecording && !old.isRecording) {
      _pulseController.repeat(reverse: true);
    } else if (!widget.isRecording && old.isRecording) {
      _pulseController.stop();
      _pulseController.reset();
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onTap,
      child: AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (_, child) {
          return Stack(
            alignment: Alignment.center,
            children: [
              if (widget.isRecording)
                Transform.scale(
                  scale: _pulseAnimation.value,
                  child: Container(
                    width: 88,
                    height: 88,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppColors.triageRed.withOpacity(0.25),
                    ),
                  ),
                ),
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: widget.isRecording
                        ? [AppColors.triageRed, const Color(0xFFC0392B)]
                        : [AppColors.secondary, const Color(0xFF0E7A88)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: (widget.isRecording
                              ? AppColors.triageRed
                              : AppColors.secondary)
                          .withOpacity(0.45),
                      blurRadius: 24,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: Icon(
                  widget.isRecording ? Icons.stop_rounded : Icons.mic_rounded,
                  color: Colors.white,
                  size: 36,
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

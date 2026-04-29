import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/constants.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/typography.dart';
import '../../core/theme/glass.dart';
import '../../data/api/voicebridge_api.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late AnimationController _fadeController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _fadeAnimation;

  String _statusText = 'Initialising...';
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    )..forward();

    _pulseAnimation = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeOut),
    );

    _checkReadiness();
  }

  Future<void> _checkReadiness() async {
    // Give the animation time to settle.
    await Future.delayed(const Duration(milliseconds: 800));

    setState(() => _statusText = 'Checking server connection...');

    bool serverOk = false;
    try {
      serverOk = await VoicebridgeApi()
          .healthCheck()
          .timeout(const Duration(seconds: 5));
    } catch (_) {
      serverOk = false;
    }

    if (!mounted) return;

    if (serverOk) {
      setState(() => _statusText = 'Connected — Loading...');
    } else {
      setState(() => _statusText = 'Offline mode — using on-device model');
    }

    await Future.delayed(const Duration(seconds: 1));

    if (!mounted) return;
    setState(() {
      _ready = true;
      _statusText = 'Ready';
    });

    await Future.delayed(const Duration(milliseconds: 400));
    if (mounted) context.go('/home');
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: MeshGradientBackground(
        child: FadeTransition(
          opacity: _fadeAnimation,
          child: SafeArea(
            child: Column(
              children: [
                const Spacer(flex: 2),
                _buildLogo(),
                const SizedBox(height: 24),
                _buildTitle(),
                const Spacer(flex: 3),
                _buildStatus(),
                const SizedBox(height: 48),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLogo() {
    return Container(
      width: 100,
      height: 100,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          colors: [AppColors.secondary, Color(0xFF0E7A88)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.secondary.withOpacity(0.4),
            blurRadius: 32,
            spreadRadius: 4,
          ),
        ],
      ),
      child: const Icon(Icons.mic_rounded, size: 48, color: Colors.white),
    );
  }

  Widget _buildTitle() {
    return Column(
      children: [
        Text(
          AppConstants.appName,
          style: AppTypography.displayLarge.copyWith(color: Colors.white),
        ),
        const SizedBox(height: 8),
        Text(
          AppConstants.appTagline,
          style: AppTypography.bodyMedium.copyWith(color: Colors.white60),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildStatus() {
    return Column(
      children: [
        AnimatedBuilder(
          animation: _pulseAnimation,
          builder: (_, __) => Opacity(
            opacity: _ready ? 1.0 : _pulseAnimation.value,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _ready ? AppColors.triageGreen : AppColors.secondary,
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  _statusText,
                  style: AppTypography.bodySmall.copyWith(
                    color: Colors.white60,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

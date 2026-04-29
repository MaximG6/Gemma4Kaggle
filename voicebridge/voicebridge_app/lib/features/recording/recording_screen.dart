import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/constants.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/glass.dart';
import '../../core/theme/typography.dart';
import '../../providers/recording_provider.dart';
import '../../providers/pipeline_provider.dart';
import 'widgets/waveform_visualizer.dart';
import 'widgets/record_button.dart';
import 'widgets/timer_display.dart';

class RecordingScreen extends ConsumerStatefulWidget {
  const RecordingScreen({super.key});

  @override
  ConsumerState<RecordingScreen> createState() => _RecordingScreenState();
}

class _RecordingScreenState extends ConsumerState<RecordingScreen> {
  String _selectedLanguage = 'English';
  Timer? _timer;
  Duration _elapsed = Duration.zero;

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _toggleRecording() {
    final recording = ref.read(recordingProvider);
    if (recording.state == RecordingState.recording) {
      _stopRecording();
    } else {
      _startRecording();
    }
  }

  void _startRecording() {
    ref.read(recordingProvider.notifier).startRecording();
    _elapsed = Duration.zero;
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() => _elapsed += const Duration(seconds: 1));
      ref.read(recordingProvider.notifier).tick(_elapsed);

      if (_elapsed.inSeconds >= AppConstants.maxRecordingSeconds) {
        _stopRecording();
      }
    });
  }

  Future<void> _stopRecording() async {
    _timer?.cancel();
    final bytes = await ref.read(recordingProvider.notifier).stopRecording();
    if (!mounted) return;

    if (bytes != null) {
      context.go('/processing');
      await ref.read(pipelineProvider.notifier).runPipeline(bytes);
    }
  }

  @override
  Widget build(BuildContext context) {
    final recording = ref.watch(recordingProvider);
    final isRecording = recording.state == RecordingState.recording;

    return Scaffold(
      body: MeshGradientBackground(
        child: SafeArea(
          child: Column(
            children: [
              _buildHeader(context),
              _buildLanguageChips(),
              Expanded(child: _buildWaveformArea(recording, isRecording)),
              _buildBottomControls(isRecording),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_ios_rounded, color: Colors.white),
            onPressed: () => context.go('/home'),
          ),
          Text(
            'Record Intake',
            style: AppTypography.headlineMedium.copyWith(color: Colors.white),
          ),
          const Spacer(),
          GlassCard(
            darkMode: true,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            child: Row(
              children: [
                const Icon(Icons.language, color: Colors.white70, size: 16),
                const SizedBox(width: 6),
                Text(
                  _selectedLanguage,
                  style: AppTypography.labelMedium.copyWith(
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageChips() {
    return SizedBox(
      height: 44,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: AppConstants.supportedLanguages.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (_, i) {
          final lang = AppConstants.supportedLanguages[i];
          final selected = lang == _selectedLanguage;
          return GestureDetector(
            onTap: () => setState(() => _selectedLanguage = lang),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: selected
                    ? AppColors.secondary
                    : Colors.white.withOpacity(0.12),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: selected
                      ? AppColors.secondary
                      : Colors.white.withOpacity(0.2),
                ),
              ),
              child: Text(
                lang,
                style: AppTypography.labelMedium.copyWith(
                  color: Colors.white,
                  fontWeight:
                      selected ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildWaveformArea(RecordingStatus recording, bool isRecording) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        GlassCard(
          margin: const EdgeInsets.symmetric(horizontal: 24),
          darkMode: true,
          padding: const EdgeInsets.all(0),
          child: SizedBox(
            height: 160,
            child: WaveformVisualizer(
              amplitudes: recording.amplitudes,
              isRecording: isRecording,
            ),
          ),
        ),
        const SizedBox(height: 32),
        TimerDisplay(elapsed: _elapsed),
        const SizedBox(height: 8),
        Text(
          isRecording ? 'Recording...' : 'Tap to start',
          style: AppTypography.bodySmall.copyWith(color: Colors.white60),
        ),
      ],
    );
  }

  Widget _buildBottomControls(bool isRecording) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          IconButton(
            icon: const Icon(
              Icons.upload_file_rounded,
              color: Colors.white54,
              size: 28,
            ),
            onPressed: () {},
          ),
          RecordButton(isRecording: isRecording, onTap: _toggleRecording),
          IconButton(
            icon: const Icon(
              Icons.stop_circle_outlined,
              color: Colors.white54,
              size: 28,
            ),
            onPressed: isRecording ? _stopRecording : null,
          ),
        ],
      ),
    );
  }
}

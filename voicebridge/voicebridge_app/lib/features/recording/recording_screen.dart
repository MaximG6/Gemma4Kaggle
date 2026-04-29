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

enum InputMode { audio, text, interactive }

class RecordingScreen extends ConsumerStatefulWidget {
  const RecordingScreen({super.key});

  @override
  ConsumerState<RecordingScreen> createState() => _RecordingScreenState();
}

class _RecordingScreenState extends ConsumerState<RecordingScreen> {
  String _selectedLanguage = 'English';
  Timer? _timer;
  Duration _elapsed = Duration.zero;
  InputMode _inputMode = InputMode.audio;
  final _textController = TextEditingController();

  @override
  void dispose() {
    _timer?.cancel();
    _textController.dispose();
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
              _buildModeToggle(),
              if (_inputMode == InputMode.audio) ...[
                _buildLanguageChips(),
              ],
              Expanded(
                child: _inputMode == InputMode.audio
                    ? _buildWaveformArea(recording, isRecording)
                    : _buildTextInput(),
              ),
              if (_inputMode == InputMode.audio)
                _buildBottomControls(isRecording),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModeToggle() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
        borderRadius: 14,
        child: Row(
          children: [
            Expanded(
              child: _ModeButton(
                icon: Icons.mic_rounded,
                label: 'Audio',
                active: _inputMode == InputMode.audio,
                onTap: () => setState(() => _inputMode = InputMode.audio),
              ),
            ),
            Expanded(
              child: _ModeButton(
                icon: Icons.text_fields_rounded,
                label: 'Text',
                active: _inputMode == InputMode.text,
                onTap: () => setState(() => _inputMode = InputMode.text),
              ),
            ),
            Expanded(
              child: _ModeButton(
                icon: Icons.chat_rounded,
                label: 'Interactive',
                active: false,
                onTap: () => context.go('/interactive'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTextInput() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Expanded(
            child: GlassCard(
              child: TextField(
                controller: _textController,
                maxLines: null,
                autofocus: true,
                style: AppTypography.bodyMedium.copyWith(
                  color: Colors.white,
                ),
                decoration: InputDecoration(
                  hintText: 'Enter patient symptoms, complaints, or nurse notes...',
                  hintStyle: AppTypography.bodyMedium.copyWith(
                    color: Colors.white38,
                  ),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton.icon(
              onPressed: _submitText,
              icon: const Icon(Icons.arrow_forward_rounded),
              label: const Text('Submit for Triage'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.secondary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                textStyle: AppTypography.labelLarge.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _submitText() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    context.go('/processing');
    ref.read(pipelineProvider.notifier).runTextPipeline(text);
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

class _ModeButton extends StatelessWidget {
  const _ModeButton({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: active
              ? AppColors.secondary
              : Colors.white.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon,
                color: active ? Colors.white : Colors.white70, size: 18),
            const SizedBox(width: 6),
            Text(
              label,
              style: AppTypography.labelMedium.copyWith(
                color: active ? Colors.white : Colors.white70,
                fontWeight: active ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

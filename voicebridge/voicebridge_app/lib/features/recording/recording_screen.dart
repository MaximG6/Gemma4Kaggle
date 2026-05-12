import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/constants.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/glass.dart';
import '../../core/theme/typography.dart';
import '../../providers/pipeline_provider.dart';

enum InputMode { audio, text, interactive }

class RecordingScreen extends ConsumerStatefulWidget {
  const RecordingScreen({super.key});

  @override
  ConsumerState<RecordingScreen> createState() => _RecordingScreenState();
}

class _RecordingScreenState extends ConsumerState<RecordingScreen> {
  String _selectedLanguage = 'English';
  InputMode _inputMode = InputMode.audio;
  final _textController = TextEditingController();

  @override
  void initState() {
    super.initState();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final mode = GoRouterState.of(context).uri.queryParameters['mode'];
    if (mode == 'text' && _inputMode != InputMode.text) {
      setState(() => _inputMode = InputMode.text);
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
                    ? _buildUploadArea()
                    : _buildTextInput(),
              ),
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
    final isDark = Theme.of(context).brightness == Brightness.dark;
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
                  color: isDark ? Colors.white : AppColors.textPrimary,
                ),
                decoration: InputDecoration(
                  hintText: 'Enter patient symptoms, complaints, or nurse notes...',
                  hintStyle: AppTypography.bodyMedium.copyWith(
                    color: isDark ? Colors.white38 : AppColors.textSecondary.withOpacity(0.6),
                  ),
                  filled: true,
                  fillColor: Colors.transparent,
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
    context.go('/processing?mode=text');
    ref.read(pipelineProvider.notifier).runTextPipeline(text);
  }

  Future<void> _uploadAudioFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.audio,
        allowMultiple: false,
      );
      if (result == null || result.files.isEmpty) return;
      final fileBytes = result.files.single.bytes;
      if (fileBytes == null || !mounted) return;

      context.go('/processing?mode=audio');
      await ref.read(pipelineProvider.notifier).runPipeline(
        Uint8List.fromList(fileBytes),
        lang: 'en',
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load file: $e')),
      );
    }
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
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final chipColors = [
      AppColors.secondary,
      AppColors.accentTeal,
      AppColors.accentCyan,
      AppColors.accentAmber,
      AppColors.accentPink,
    ];
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
          final color = chipColors[i % chipColors.length];
          return GestureDetector(
            onTap: () => setState(() => _selectedLanguage = lang),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                gradient: selected ? LinearGradient(
                  colors: [color, color.withOpacity(0.7)],
                ) : null,
                color: selected ? null : (isDark ? Colors.white.withOpacity(0.12) : Colors.black.withOpacity(0.04)),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: selected
                      ? color
                      : (isDark ? Colors.white.withOpacity(0.2) : Colors.black.withOpacity(0.1)),
                ),
                boxShadow: selected ? [
                  BoxShadow(
                    color: color.withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ] : null,
              ),
              child: Text(
                lang,
                style: AppTypography.labelMedium.copyWith(
                  color: selected ? Colors.white : (isDark ? Colors.white70 : AppColors.textPrimary),
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

  Widget _buildUploadArea() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          GlassCard(
            margin: const EdgeInsets.symmetric(horizontal: 24),
            padding: const EdgeInsets.all(48),
            child: Column(
              children: [
                const Icon(
                  Icons.audiotrack_rounded,
                  color: AppColors.textSecondary,
                  size: 64,
                ),
                const SizedBox(height: 16),
                Text(
                  'Upload Audio File',
                  style: AppTypography.headlineSmall.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Select an audio recording for triage',
                  style: AppTypography.bodyMedium.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          FilledButton.icon(
            onPressed: _uploadAudioFile,
            icon: const Icon(Icons.upload_file_rounded),
            label: const Text('Choose File'),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.secondary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
              textStyle: AppTypography.labelLarge.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
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
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          gradient: active ? const LinearGradient(
            colors: [AppColors.secondary, AppColors.accentTeal],
          ) : null,
          color: active ? null : (isDark ? Colors.white.withOpacity(0.1) : AppColors.surfaceLight),
          borderRadius: BorderRadius.circular(12),
          boxShadow: active ? [
            BoxShadow(
              color: AppColors.secondary.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ] : null,
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon,
                color: active ? Colors.white : (isDark ? Colors.white70 : AppColors.textSecondary), size: 18),
            const SizedBox(width: 6),
            Text(
              label,
              style: AppTypography.labelMedium.copyWith(
                color: active ? Colors.white : (isDark ? Colors.white70 : AppColors.textPrimary),
                fontWeight: active ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

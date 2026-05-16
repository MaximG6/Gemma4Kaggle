// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/constants.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/glass.dart';
import '../../core/theme/typography.dart';
import '../../providers/pipeline_provider.dart';

enum InputMode { audio, text, interactive }

// Preset demo audio samples shown on the audio upload screen.
typedef _Preset = ({String label, String asset, String level, String lang, Color color});

const List<_Preset> _presets = [
  (label: 'Bengali — RED',    asset: 'audio/intake_bengali.wav', level: 'RED',    lang: 'bn', color: AppColors.triageRed),
  (label: 'English — YELLOW', asset: 'audio/intake_yellow.wav',  level: 'YELLOW', lang: 'en', color: AppColors.triageYellow),
  (label: 'English — GREEN',  asset: 'audio/intake_green.wav',   level: 'GREEN',  lang: 'en', color: AppColors.triageGreen),
];

// Example text cases shown on the text input screen.
typedef _TextExample = ({String lang, String levelLabel, Color color, String text});

const List<_TextExample> _textExamples = [
  (
    lang: 'English',
    levelLabel: 'RED',
    color: AppColors.triageRed,
    text: 'Woman 28 weeks pregnant. Seized 2 minutes ago. Still convulsing. BP 180/120.',
  ),
  (
    lang: 'Bengali',
    levelLabel: 'ORANGE',
    color: AppColors.triageOrange,
    text: 'প্রাপ্তবয়স্ক পুরুষ। ৪৫ মিনিট ধরে বুকের মাঝখানে ব্যথা। বাম হাতে ছড়িয়ে পড়ছে। ঘামছেন। HR 112, RR 22।',
  ),
  (
    lang: 'Swahili',
    levelLabel: 'GREEN',
    color: AppColors.triageGreen,
    text: 'Mgonjwa mwenye kikohozi kwa wiki 6. Hakuna homa, hakuna damu kwenye makohozi. Macho wazi kamili. Ishara za kawaida.',
  ),
];

class RecordingScreen extends ConsumerStatefulWidget {
  const RecordingScreen({super.key});

  @override
  ConsumerState<RecordingScreen> createState() => _RecordingScreenState();
}

class _RecordingScreenState extends ConsumerState<RecordingScreen> {
  String _selectedLanguage = 'English';
  InputMode _inputMode = InputMode.audio;
  final _textController = TextEditingController();

  html.AudioElement? _audioElement;
  String? _playingPreset;
  String? _selectedPreset;

  static const _langCodes = <String, String>{
    'English': 'en', 'Swahili': 'sw', 'Hausa': 'ha',
    'Bengali': 'bn', 'Tagalog': 'tl', 'Hindi': 'hi', 'French': 'fr',
  };

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
    _audioElement?.pause();
    _audioElement = null;
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

  // ── Preset playback ──────────────────────────────────────────────

  void _togglePreset(_Preset preset) {
    if (_playingPreset == preset.asset) {
      _audioElement?.pause();
      _audioElement = null;
      setState(() => _playingPreset = null);
      return;
    }

    _audioElement?.pause();
    _audioElement = null;

    // Flutter web bundles pubspec assets under assets/assets/ relative to the web root,
    // so the browser URL has a double assets/ prefix (e.g. assets/assets/audio/file.wav).
    final el = html.AudioElement('assets/assets/${preset.asset}');
    _audioElement = el;

    el.onEnded.listen((_) {
      if (mounted && identical(_audioElement, el)) {
        setState(() => _playingPreset = null);
      }
    });

    setState(() {
      _playingPreset = preset.asset;
      _selectedPreset = preset.asset;
    });

    el.play();
  }

  Future<void> _useDemoAudio(_Preset preset) async {
    _audioElement?.pause();
    _audioElement = null;
    setState(() => _playingPreset = null);

    final byteData = await rootBundle.load('assets/${preset.asset}');
    final bytes = byteData.buffer.asUint8List();

    if (!mounted) return;
    context.go('/processing?mode=audio');
    ref.read(pipelineProvider.notifier).runPipeline(bytes, lang: preset.lang);
  }

  // ── Upload area ───────────────────────────────────────────────────

  Widget _buildUploadArea() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(height: 16),
            GlassCard(
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
            const SizedBox(height: 28),
            _buildPresetSection(),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildPresetSection() {
    final selectedPreset = _presets.where((p) => p.asset == _selectedPreset).firstOrNull;

    return Column(
      children: [
        // Divider row
        Row(
          children: [
            const Expanded(child: Divider(color: Colors.white24, thickness: 1)),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Text(
                'or try a demo',
                style: AppTypography.labelSmall.copyWith(
                  color: Colors.white54,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const Expanded(child: Divider(color: Colors.white24, thickness: 1)),
          ],
        ),
        const SizedBox(height: 14),
        // Pill buttons
        Row(
          children: _presets.map((preset) {
            final isPlaying = _playingPreset == preset.asset;
            return Expanded(
              child: Padding(
                padding: EdgeInsets.only(
                  left: preset == _presets.first ? 0 : 5,
                  right: preset == _presets.last ? 0 : 5,
                ),
                child: _PresetPill(
                  preset: preset,
                  isPlaying: isPlaying,
                  onTap: () => _togglePreset(preset),
                ),
              ),
            );
          }).toList(),
        ),
        // "Use this demo audio" button — appears after any preset has been played
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          transitionBuilder: (child, anim) => FadeTransition(
            opacity: anim,
            child: SizeTransition(sizeFactor: anim, child: child),
          ),
          child: selectedPreset != null
              ? Padding(
                  key: ValueKey(selectedPreset.asset),
                  padding: const EdgeInsets.only(top: 14),
                  child: GestureDetector(
                    onTap: () => _useDemoAudio(selectedPreset),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      decoration: BoxDecoration(
                        color: selectedPreset.color,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          const Icon(Icons.upload_rounded, size: 18, color: Colors.white),
                          const SizedBox(width: 8),
                          Text(
                            'Use this demo audio',
                            style: AppTypography.labelLarge.copyWith(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                )
              : const SizedBox.shrink(),
        ),
      ],
    );
  }

  // ── Rest of screen ────────────────────────────────────────────────

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
          _buildTextExamples(isDark),
          const SizedBox(height: 16),
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

  Widget _buildTextExamples(bool isDark) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: Divider(color: isDark ? Colors.white24 : Colors.black12, thickness: 1)),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Text(
                'try an example',
                style: AppTypography.labelSmall.copyWith(
                  color: isDark ? Colors.white54 : AppColors.textSecondary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            Expanded(child: Divider(color: isDark ? Colors.white24 : Colors.black12, thickness: 1)),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: _textExamples.map((ex) {
            return Expanded(
              child: Padding(
                padding: EdgeInsets.only(
                  left: ex == _textExamples.first ? 0 : 5,
                  right: ex == _textExamples.last ? 0 : 5,
                ),
                child: _TextExampleChip(
                  example: ex,
                  isDark: isDark,
                  onTap: () {
                    _textController.text = ex.text;
                    _textController.selection = TextSelection.fromPosition(
                      TextPosition(offset: ex.text.length),
                    );
                  },
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  void _submitText() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    context.go('/processing?mode=text');
    ref.read(pipelineProvider.notifier).runTextPipeline(text);
  }

  Future<void> _uploadAudioFile() async {
    _audioElement?.pause();
    _audioElement = null;
    if (mounted) setState(() => _playingPreset = null);

    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.audio,
        allowMultiple: false,
      );
      if (result == null || result.files.isEmpty) return;
      final fileBytes = result.files.single.bytes;
      if (fileBytes == null || !mounted) return;

      final langCode = _langCodes[_selectedLanguage] ?? 'en';
      context.go('/processing?mode=audio');
      await ref.read(pipelineProvider.notifier).runPipeline(
        Uint8List.fromList(fileBytes),
        lang: langCode,
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
                gradient: selected
                    ? LinearGradient(colors: [color, color.withOpacity(0.7)])
                    : null,
                color: selected
                    ? null
                    : (isDark
                        ? Colors.white.withOpacity(0.12)
                        : Colors.black.withOpacity(0.04)),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: selected
                      ? color
                      : (isDark
                          ? Colors.white.withOpacity(0.2)
                          : Colors.black.withOpacity(0.1)),
                ),
                boxShadow: selected
                    ? [
                        BoxShadow(
                          color: color.withOpacity(0.3),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ]
                    : null,
              ),
              child: Text(
                lang,
                style: AppTypography.labelMedium.copyWith(
                  color: selected
                      ? Colors.white
                      : (isDark ? Colors.white70 : AppColors.textPrimary),
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
}

// ── Text example chip ─────────────────────────────────────────────────────────

class _TextExampleChip extends StatelessWidget {
  const _TextExampleChip({
    required this.example,
    required this.isDark,
    required this.onTap,
  });

  final _TextExample example;
  final bool isDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = example.color;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
        decoration: BoxDecoration(
          color: color.withOpacity(isDark ? 0.1 : 0.07),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.4)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  example.lang,
                  style: AppTypography.labelSmall.copyWith(
                    color: color,
                    fontWeight: FontWeight.w700,
                    fontSize: 11,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    example.levelLabel,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 9,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              example.text,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: AppTypography.bodySmall.copyWith(
                color: isDark ? Colors.white60 : AppColors.textSecondary,
                fontSize: 10,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Preset pill button ────────────────────────────────────────────────────────

class _PresetPill extends StatelessWidget {
  const _PresetPill({
    required this.preset,
    required this.isPlaying,
    required this.onTap,
  });

  final _Preset preset;
  final bool isPlaying;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = preset.color;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
        decoration: BoxDecoration(
          color: isPlaying ? color.withOpacity(0.18) : color.withOpacity(0.07),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isPlaying ? color : color.withOpacity(0.45),
            width: isPlaying ? 1.5 : 1,
          ),
          boxShadow: isPlaying
              ? [BoxShadow(color: color.withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 3))]
              : null,
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isPlaying ? Icons.stop_rounded : Icons.play_arrow_rounded,
              color: color,
              size: 16,
            ),
            const SizedBox(width: 4),
            Flexible(
              child: Text(
                preset.label,
                overflow: TextOverflow.ellipsis,
                style: AppTypography.labelSmall.copyWith(
                  color: color,
                  fontWeight: FontWeight.w700,
                  fontSize: 11,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Mode toggle button ────────────────────────────────────────────────────────

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
          gradient: active
              ? const LinearGradient(
                  colors: [AppColors.secondary, AppColors.accentTeal],
                )
              : null,
          color: active
              ? null
              : (isDark ? Colors.white.withOpacity(0.1) : AppColors.surfaceLight),
          borderRadius: BorderRadius.circular(12),
          boxShadow: active
              ? [
                  BoxShadow(
                    color: AppColors.secondary.withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon,
                color: active
                    ? Colors.white
                    : (isDark ? Colors.white70 : AppColors.textSecondary),
                size: 18),
            const SizedBox(width: 6),
            Text(
              label,
              style: AppTypography.labelMedium.copyWith(
                color: active
                    ? Colors.white
                    : (isDark ? Colors.white70 : AppColors.textPrimary),
                fontWeight: active ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

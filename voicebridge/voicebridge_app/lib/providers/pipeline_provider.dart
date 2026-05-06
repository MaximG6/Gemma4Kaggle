import 'dart:typed_data';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/triage_output.dart';
import '../domain/pipeline/voicebridge_pipeline.dart';
import '../domain/pipeline/pipeline_web.dart';
import 'settings_provider.dart';

class PipelineState {
  const PipelineState({
    this.status = PipelineStatus.idle,
    this.result,
    this.recordId,
    this.error,
    this.elapsed = Duration.zero,
  });

  final PipelineStatus status;
  final TriageOutput? result;
  final String? recordId;
  final String? error;
  final Duration elapsed;

  PipelineState copyWith({
    PipelineStatus? status,
    TriageOutput? result,
    String? recordId,
    String? error,
    Duration? elapsed,
  }) {
    return PipelineState(
      status: status ?? this.status,
      result: result ?? this.result,
      recordId: recordId ?? this.recordId,
      error: error ?? this.error,
      elapsed: elapsed ?? this.elapsed,
    );
  }
}

class PipelineNotifier extends AsyncNotifier<PipelineState> {
  late VoicebridgePipeline _pipeline;

  @override
  Future<PipelineState> build() async {
    _pipeline = WebPipeline();
    ref.onDispose(_pipeline.dispose);
    return const PipelineState();
  }

  Future<void> runPipeline(Uint8List audioBytes, {String? lang}) async {
    final language = lang ?? ref.read(settingsProvider).selectedLanguage;
    final langCode = _getLangCode(language);
    state = AsyncData(
      state.valueOrNull?.copyWith(
            status: PipelineStatus.transcribing,
            error: null,
          ) ??
          const PipelineState(status: PipelineStatus.transcribing),
    );

    final start = DateTime.now();

    try {
      final result = await _pipeline.runPipeline(
        audioBytes,
        lang: langCode,
        onStatusChange: (s) {
          state = AsyncData(
            state.valueOrNull?.copyWith(
                  status: s,
                  elapsed: DateTime.now().difference(start),
                ) ??
                PipelineState(status: s),
          );
        },
      );

      state = AsyncData(
        PipelineState(
          status: PipelineStatus.done,
          result: result['output'] as TriageOutput,
          recordId: result['record_id'] as String?,
          elapsed: DateTime.now().difference(start),
        ),
      );
    } catch (e, st) {
      state = AsyncError(e, st);
    }
  }

  Future<void> runTextPipeline(String text, {String? lang}) async {
    final language = lang ?? ref.read(settingsProvider).selectedLanguage;
    final langCode = _getLangCode(language);
    state = AsyncData(
      state.valueOrNull?.copyWith(
            status: PipelineStatus.triaging,
            error: null,
          ) ??
          const PipelineState(status: PipelineStatus.triaging),
    );

    final start = DateTime.now();

    try {
      final result = await _pipeline.runTextPipeline(
        text,
        lang: langCode,
        onStatusChange: (s) {
          state = AsyncData(
            state.valueOrNull?.copyWith(
                  status: s,
                  elapsed: DateTime.now().difference(start),
                ) ??
                PipelineState(status: s),
          );
        },
      );

      state = AsyncData(
        PipelineState(
          status: PipelineStatus.done,
          result: result['output'] as TriageOutput,
          recordId: result['record_id'] as String?,
          elapsed: DateTime.now().difference(start),
        ),
      );
    } catch (e, st) {
      state = AsyncError(e, st);
    }
  }

  Future<Map<String, dynamic>> runInteractivePipeline(
    String text, {
    String? sessionId,
    String? lang,
  }) async {
    final language = lang ?? ref.read(settingsProvider).selectedLanguage;
    final langCode = _getLangCode(language);
    state = AsyncData(
      state.valueOrNull?.copyWith(
            status: PipelineStatus.triaging,
            error: null,
          ) ??
          const PipelineState(status: PipelineStatus.triaging),
    );

    try {
      final result = await _pipeline.runInteractiveTurn(
        text,
        sessionId: sessionId,
        lang: langCode,
      );
      state = const AsyncData(PipelineState());
      return result;
    } catch (e, st) {
      state = AsyncError(e, st);
      rethrow;
    }
  }

  static String _getLangCode(String language) {
    final codes = <String, String>{
      'English': 'en',
      'Swahili': 'sw',
      'Hausa': 'ha',
      'Bengali': 'bn',
      'Tagalog': 'tl',
      'Hindi': 'hi',
      'French': 'fr',
    };
    return codes[language] ?? 'en';
  }

  void setInteractiveResult(TriageOutput result) {
    state = AsyncData(
      PipelineState(
        status: PipelineStatus.done,
        result: result,
      ),
    );
  }

  void reset() {
    state = const AsyncData(PipelineState());
  }
}

final pipelineProvider =
    AsyncNotifierProvider<PipelineNotifier, PipelineState>(
  PipelineNotifier.new,
);

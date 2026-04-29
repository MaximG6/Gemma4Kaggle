import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/models/triage_output.dart';
import '../domain/pipeline/voicebridge_pipeline.dart';
import '../domain/pipeline/pipeline_web.dart';
import '../domain/pipeline/pipeline_mobile.dart';

class PipelineState {
  const PipelineState({
    this.status = PipelineStatus.idle,
    this.result,
    this.error,
    this.elapsed = Duration.zero,
  });

  final PipelineStatus status;
  final TriageOutput? result;
  final String? error;
  final Duration elapsed;

  PipelineState copyWith({
    PipelineStatus? status,
    TriageOutput? result,
    String? error,
    Duration? elapsed,
  }) {
    return PipelineState(
      status: status ?? this.status,
      result: result ?? this.result,
      error: error ?? this.error,
      elapsed: elapsed ?? this.elapsed,
    );
  }
}

class PipelineNotifier extends AsyncNotifier<PipelineState> {
  late VoicebridgePipeline _pipeline;

  @override
  Future<PipelineState> build() async {
    _pipeline = kIsWeb ? WebPipeline() : MobilePipeline();
    ref.onDispose(_pipeline.dispose);
    return const PipelineState();
  }

  Future<void> runPipeline(Uint8List audioBytes) async {
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
          result: result,
          elapsed: DateTime.now().difference(start),
        ),
      );
    } catch (e, st) {
      state = AsyncError(e, st);
    }
  }

  Future<void> runTextPipeline(String text) async {
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
          result: result,
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
  }) async {
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
      );
      state = const AsyncData(PipelineState());
      return result;
    } catch (e, st) {
      state = AsyncError(e, st);
      rethrow;
    }
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

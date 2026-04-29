import 'dart:typed_data';
import '../../data/models/triage_output.dart';
import 'voicebridge_pipeline.dart';

/// Stub for llama.cpp FFI integration (Phase 6).
/// Currently returns mock data so the UI is exercisable.
class MobilePipeline implements VoicebridgePipeline {
  @override
  Future<TriageOutput> runPipeline(
    Uint8List audioBytes, {
    void Function(PipelineStatus)? onStatusChange,
  }) async {
    onStatusChange?.call(PipelineStatus.transcribing);
    await Future.delayed(const Duration(seconds: 2));

    onStatusChange?.call(PipelineStatus.triaging);
    await Future.delayed(const Duration(seconds: 4));

    onStatusChange?.call(PipelineStatus.generatingReport);
    await Future.delayed(const Duration(seconds: 1));

    onStatusChange?.call(PipelineStatus.done);
    return TriageOutput.mock();
  }

  @override
  void dispose() {}
}

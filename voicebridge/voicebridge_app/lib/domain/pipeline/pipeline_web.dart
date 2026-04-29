import 'dart:typed_data';
import '../../data/api/voicebridge_api.dart';
import '../../data/models/triage_output.dart';
import 'voicebridge_pipeline.dart';

class WebPipeline implements VoicebridgePipeline {
  WebPipeline({VoicebridgeApi? api})
      : _api = api ?? VoicebridgeApi();

  final VoicebridgeApi _api;

  @override
  Future<TriageOutput> runPipeline(
    Uint8List audioBytes, {
    void Function(PipelineStatus)? onStatusChange,
  }) async {
    onStatusChange?.call(PipelineStatus.transcribing);
    await Future.delayed(const Duration(milliseconds: 500));

    onStatusChange?.call(PipelineStatus.triaging);
    final output = await _api.postIntake(audioBytes, filename: 'recording.webm');

    onStatusChange?.call(PipelineStatus.generatingReport);
    await Future.delayed(const Duration(milliseconds: 300));

    onStatusChange?.call(PipelineStatus.done);
    return output;
  }

  @override
  Future<TriageOutput> runTextPipeline(
    String text, {
    void Function(PipelineStatus)? onStatusChange,
  }) async {
    onStatusChange?.call(PipelineStatus.triaging);
    final output = await _api.postText(text);

    onStatusChange?.call(PipelineStatus.generatingReport);
    await Future.delayed(const Duration(milliseconds: 300));

    onStatusChange?.call(PipelineStatus.done);
    return output;
  }

  @override
  Future<Map<String, dynamic>> runInteractiveTurn(
    String text, {
    String? sessionId,
  }) async {
    return _api.postInteractive(text, sessionId: sessionId);
  }

  @override
  void dispose() {}
}

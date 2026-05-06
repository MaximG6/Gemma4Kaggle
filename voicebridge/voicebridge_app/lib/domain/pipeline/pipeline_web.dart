import 'dart:typed_data';
import '../../data/api/voicebridge_api.dart';
import 'voicebridge_pipeline.dart';

class WebPipeline implements VoicebridgePipeline {
  WebPipeline({VoicebridgeApi? api})
      : _api = api ?? VoicebridgeApi();

  final VoicebridgeApi _api;

  @override
  Future<Map<String, dynamic>> runPipeline(
    Uint8List audioBytes, {
    String lang = 'en',
    void Function(PipelineStatus)? onStatusChange,
  }) async {
    onStatusChange?.call(PipelineStatus.transcribing);
    await Future.delayed(const Duration(milliseconds: 500));

    onStatusChange?.call(PipelineStatus.triaging);
    final result = await _api.postIntake(audioBytes, lang: lang);

    onStatusChange?.call(PipelineStatus.generatingReport);
    await Future.delayed(const Duration(milliseconds: 300));

    onStatusChange?.call(PipelineStatus.done);
    return result;
  }

  @override
  Future<Map<String, dynamic>> runTextPipeline(
    String text, {
    String lang = 'en',
    void Function(PipelineStatus)? onStatusChange,
  }) async {
    onStatusChange?.call(PipelineStatus.triaging);
    final result = await _api.postText(text, lang: lang);

    onStatusChange?.call(PipelineStatus.generatingReport);
    await Future.delayed(const Duration(milliseconds: 300));

    onStatusChange?.call(PipelineStatus.done);
    return result;
  }

  @override
  Future<Map<String, dynamic>> runInteractiveTurn(
    String text, {
    String? sessionId,
    String lang = 'en',
  }) async {
    return _api.postInteractive(text, sessionId: sessionId, lang: lang);
  }

  @override
  void dispose() {}
}

import 'dart:typed_data';

enum PipelineStatus {
  idle,
  recording,
  transcribing,
  triaging,
  generatingReport,
  done,
  error,
}

extension PipelineStatusExtension on PipelineStatus {
  String get label {
    switch (this) {
      case PipelineStatus.idle:
        return 'Ready';
      case PipelineStatus.recording:
        return 'Recording';
      case PipelineStatus.transcribing:
        return 'Transcribing';
      case PipelineStatus.triaging:
        return 'Analyzing triage';
      case PipelineStatus.generatingReport:
        return 'Generating report';
      case PipelineStatus.done:
        return 'Complete';
      case PipelineStatus.error:
        return 'Error';
    }
  }

  String get detail {
    switch (this) {
      case PipelineStatus.idle:
        return 'Tap record to begin intake';
      case PipelineStatus.recording:
        return 'Listening to patient...';
      case PipelineStatus.transcribing:
        return 'Converting speech to text';
      case PipelineStatus.triaging:
        return 'Applying SATS 2023 decision tree';
      case PipelineStatus.generatingReport:
        return 'Building clinical PDF';
      case PipelineStatus.done:
        return 'Triage complete';
      case PipelineStatus.error:
        return 'An error occurred';
    }
  }

  int get stepIndex {
    switch (this) {
      case PipelineStatus.idle:
        return -1;
      case PipelineStatus.recording:
        return 0;
      case PipelineStatus.transcribing:
        return 1;
      case PipelineStatus.triaging:
        return 2;
      case PipelineStatus.generatingReport:
        return 3;
      case PipelineStatus.done:
        return 4;
      case PipelineStatus.error:
        return -1;
    }
  }
}

abstract class VoicebridgePipeline {
  Future<Map<String, dynamic>> runPipeline(
    Uint8List audioBytes, {
    String lang = 'en',
    void Function(PipelineStatus)? onStatusChange,
  });

  Future<Map<String, dynamic>> runTextPipeline(
    String text, {
    String lang = 'en',
    void Function(PipelineStatus)? onStatusChange,
  });

  Future<Map<String, dynamic>> runInteractiveTurn(
    String text, {
    String? sessionId,
    String lang = 'en',
  });

  void dispose();
}

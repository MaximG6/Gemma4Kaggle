import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:record/record.dart';

enum RecordingState { idle, recording, stopped, error }

class RecordingStatus {
  const RecordingStatus({
    this.state = RecordingState.idle,
    this.duration = Duration.zero,
    this.audioBytes,
    this.amplitudes = const [],
    this.error,
  });

  final RecordingState state;
  final Duration duration;
  final Uint8List? audioBytes;
  final List<double> amplitudes;
  final String? error;

  RecordingStatus copyWith({
    RecordingState? state,
    Duration? duration,
    Uint8List? audioBytes,
    List<double>? amplitudes,
    String? error,
  }) {
    return RecordingStatus(
      state: state ?? this.state,
      duration: duration ?? this.duration,
      audioBytes: audioBytes ?? this.audioBytes,
      amplitudes: amplitudes ?? this.amplitudes,
      error: error ?? this.error,
    );
  }
}

class RecordingNotifier extends Notifier<RecordingStatus> {
  AudioRecorder? _recorder;
  StreamSubscription<Uint8List>? _audioSub;
  StreamSubscription<Amplitude>? _ampSub;
  final _audioBuffer = <int>[];

  @override
  RecordingStatus build() {
    ref.onDispose(_cleanup);
    return const RecordingStatus();
  }

  void _cleanup() {
    _ampSub?.cancel();
    _audioSub?.cancel();
    _recorder?.dispose();
    _recorder = null;
  }

  Future<void> startRecording() async {
    _cleanup();
    _recorder = AudioRecorder();
    _audioBuffer.clear();

    final hasPermission = await _recorder!.hasPermission();
    if (!hasPermission) {
      state = state.copyWith(
        state: RecordingState.error,
        error: 'Microphone permission denied',
      );
      return;
    }

    // Web: opus in webm container (browser MediaRecorder default).
    // Native: WAV at 16 kHz mono for direct server consumption.
    final config = kIsWeb
        ? const RecordConfig(encoder: AudioEncoder.opus, numChannels: 1)
        : const RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 16000,
            numChannels: 1,
          );

    final audioStream = await _recorder!.startStream(config);
    _audioSub = audioStream.listen(
      (chunk) => _audioBuffer.addAll(chunk),
      onError: (_) {},
    );

    _ampSub = _recorder!
        .onAmplitudeChanged(const Duration(milliseconds: 100))
        .listen(
          (amp) {
            // amp.current is dBFS in [-160, 0]; map [-60, 0] → [0, 1].
            final normalized = ((amp.current + 60) / 60).clamp(0.0, 1.0);
            updateAmplitude(normalized);
          },
          onError: (_) {},
        );

    state = const RecordingStatus(state: RecordingState.recording);
  }

  Future<Uint8List?> stopRecording() async {
    await _ampSub?.cancel();
    _ampSub = null;

    await _recorder?.stop();
    // Give the final audio chunk time to arrive (important on web).
    await Future.delayed(const Duration(milliseconds: 200));

    await _audioSub?.cancel();
    _audioSub = null;
    _recorder?.dispose();
    _recorder = null;

    if (_audioBuffer.isEmpty) {
      state = state.copyWith(state: RecordingState.stopped);
      return null;
    }

    final bytes = Uint8List.fromList(_audioBuffer);
    state = state.copyWith(state: RecordingState.stopped, audioBytes: bytes);
    return bytes;
  }

  void reset() {
    state = const RecordingStatus();
  }

  void updateAmplitude(double amplitude) {
    final updated = List<double>.from(state.amplitudes)..add(amplitude);
    if (updated.length > 80) updated.removeAt(0);
    state = state.copyWith(amplitudes: updated);
  }

  void tick(Duration elapsed) {
    state = state.copyWith(duration: elapsed);
  }
}

final recordingProvider =
    NotifierProvider<RecordingNotifier, RecordingStatus>(RecordingNotifier.new);

import 'dart:typed_data';
import 'dart:math' as math;

class AudioProcessor {
  static const int _targetSampleRate = 16000;
  static const double _silenceThreshold = 0.01;

  /// Normalises amplitude to peak = 1.0.
  static Float32List normalize(Float32List samples) {
    double peak = 0;
    for (final s in samples) {
      final abs = s.abs();
      if (abs > peak) peak = abs;
    }
    if (peak == 0) return samples;
    return Float32List.fromList(samples.map((s) => s / peak).toList());
  }

  /// Strips leading and trailing silence below [threshold].
  static Float32List trimSilence(
    Float32List samples, {
    double threshold = _silenceThreshold,
    int frameSize = 512,
  }) {
    int start = 0;
    while (start < samples.length) {
      final end = math.min(start + frameSize, samples.length);
      final rms = _rms(samples, start, end);
      if (rms > threshold) break;
      start = end;
    }

    int stop = samples.length;
    while (stop > start) {
      final begin = math.max(stop - frameSize, start);
      final rms = _rms(samples, begin, stop);
      if (rms > threshold) break;
      stop = begin;
    }

    if (start >= stop) return Float32List(0);
    return Float32List.sublistView(samples, start, stop);
  }

  /// Resamples [samples] from [sourceRate] to [_targetSampleRate] if needed.
  static Float32List resampleIfNeeded(
    Float32List samples,
    int sourceRate,
  ) {
    if (sourceRate == _targetSampleRate) return samples;

    final ratio = _targetSampleRate / sourceRate;
    final newLength = (samples.length * ratio).round();
    final result = Float32List(newLength);

    for (int i = 0; i < newLength; i++) {
      final srcIndex = i / ratio;
      final lo = srcIndex.floor();
      final hi = math.min(lo + 1, samples.length - 1);
      final frac = srcIndex - lo;
      result[i] = samples[lo] * (1 - frac) + samples[hi] * frac;
    }

    return result;
  }

  static double _rms(Float32List samples, int start, int end) {
    double sum = 0;
    for (int i = start; i < end; i++) {
      sum += samples[i] * samples[i];
    }
    return math.sqrt(sum / (end - start));
  }

  /// Converts raw PCM bytes (16-bit little-endian) to normalised float samples.
  static Float32List pcmBytesToFloat(Uint8List bytes) {
    final shorts = bytes.buffer.asInt16List();
    final floats = Float32List(shorts.length);
    for (int i = 0; i < shorts.length; i++) {
      floats[i] = shorts[i] / 32768.0;
    }
    return floats;
  }
}

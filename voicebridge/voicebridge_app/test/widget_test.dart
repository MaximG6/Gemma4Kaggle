import 'package:flutter_test/flutter_test.dart';
import 'package:voicebridge_app/core/utils/triage_level_utils.dart';
import 'package:voicebridge_app/data/models/triage_output.dart';

void main() {
  group('TriageLevel parsing', () {
    test('parses all valid levels', () {
      expect(triageLevelFromString('red'), TriageLevel.red);
      expect(triageLevelFromString('ORANGE'), TriageLevel.orange);
      expect(triageLevelFromString('Yellow'), TriageLevel.yellow);
      expect(triageLevelFromString('green'), TriageLevel.green);
      expect(triageLevelFromString('BLUE'), TriageLevel.blue);
    });

    test('returns unknown for invalid input', () {
      expect(triageLevelFromString(''), TriageLevel.unknown);
      expect(triageLevelFromString('purple'), TriageLevel.unknown);
    });

    test('level order is correct', () {
      expect(TriageLevel.red.order < TriageLevel.orange.order, isTrue);
      expect(TriageLevel.orange.order < TriageLevel.yellow.order, isTrue);
    });

    test('wait time strings are non-empty', () {
      for (final level in TriageLevel.values) {
        expect(level.waitTime, isNotEmpty);
      }
    });
  });

  group('TriageOutput JSON roundtrip', () {
    test('serialises and deserialises without data loss', () {
      final original = TriageOutput.mock();
      final json = original.toJson();
      final restored = TriageOutput.fromJson(json);

      expect(restored.triageLevel, original.triageLevel);
      expect(restored.primaryComplaint, original.primaryComplaint);
      expect(restored.reportedSymptoms, original.reportedSymptoms);
      expect(restored.confidenceScore, original.confidenceScore);
      expect(restored.referralNeeded, original.referralNeeded);
    });

    test('fromJson handles missing optional fields gracefully', () {
      final output = TriageOutput.fromJson({
        'triage_level': 'green',
        'primary_complaint': 'Headache',
      });

      expect(output.triageLevel, 'green');
      expect(output.reportedSymptoms, isEmpty);
      expect(output.redFlagIndicators, isEmpty);
      expect(output.confidenceScore, 0.0);
    });
  });
}

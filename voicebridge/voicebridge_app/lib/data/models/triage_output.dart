class TriageOutput {
  const TriageOutput({
    required this.triageLevel,
    required this.primaryComplaint,
    required this.reportedSymptoms,
    required this.vitalSignsReported,
    required this.durationOfSymptoms,
    required this.relevantHistory,
    required this.redFlagIndicators,
    required this.recommendedAction,
    required this.referralNeeded,
    required this.confidenceScore,
    required this.sourceLanguage,
    required this.rawTranscript,
  });

  final String triageLevel;
  final String primaryComplaint;
  final List<String> reportedSymptoms;
  final Map<String, String> vitalSignsReported;
  final String durationOfSymptoms;
  final String relevantHistory;
  final List<String> redFlagIndicators;
  final String recommendedAction;
  final bool referralNeeded;
  final double confidenceScore;
  final String sourceLanguage;
  final String rawTranscript;

  factory TriageOutput.fromJson(Map<String, dynamic> json) {
    return TriageOutput(
      triageLevel: json['triage_level'] as String? ?? 'unknown',
      primaryComplaint: json['primary_complaint'] as String? ?? '',
      reportedSymptoms: (json['reported_symptoms'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      vitalSignsReported:
          (json['vital_signs_reported'] as Map<String, dynamic>?)?.map(
                (k, v) => MapEntry(k, v.toString()),
              ) ??
              {},
      durationOfSymptoms: json['duration_of_symptoms'] as String? ?? '',
      relevantHistory: json['relevant_history'] as String? ?? '',
      redFlagIndicators: (json['red_flag_indicators'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      recommendedAction: json['recommended_action'] as String? ?? '',
      referralNeeded: json['referral_needed'] as bool? ?? false,
      confidenceScore:
          (json['confidence_score'] as num?)?.toDouble() ?? 0.0,
      sourceLanguage: json['source_language'] as String? ?? 'en',
      rawTranscript: json['raw_transcript'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'triage_level': triageLevel,
      'primary_complaint': primaryComplaint,
      'reported_symptoms': reportedSymptoms,
      'vital_signs_reported': vitalSignsReported,
      'duration_of_symptoms': durationOfSymptoms,
      'relevant_history': relevantHistory,
      'red_flag_indicators': redFlagIndicators,
      'recommended_action': recommendedAction,
      'referral_needed': referralNeeded,
      'confidence_score': confidenceScore,
      'source_language': sourceLanguage,
      'raw_transcript': rawTranscript,
    };
  }

  static TriageOutput mock() {
    return const TriageOutput(
      triageLevel: 'orange',
      primaryComplaint: 'Chest pain with shortness of breath',
      reportedSymptoms: [
        'Chest tightness',
        'Dyspnoea on exertion',
        'Diaphoresis',
        'Nausea',
      ],
      vitalSignsReported: {
        'HR': '110 bpm',
        'BP': '95/60 mmHg',
        'SpO2': '94%',
        'RR': '22/min',
      },
      durationOfSymptoms: '2 hours',
      relevantHistory: 'Hypertension, type 2 diabetes, no known cardiac history',
      redFlagIndicators: [
        'Chest pain radiating to left arm',
        'Diaphoresis',
        'BP below threshold',
      ],
      recommendedAction:
          'Immediate ECG, IV access, oxygen therapy, call cardiology',
      referralNeeded: true,
      confidenceScore: 0.91,
      sourceLanguage: 'en',
      rawTranscript:
          'Patient reports chest pain for the last two hours with shortness of breath and sweating...',
    );
  }
}

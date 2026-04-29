import 'dart:convert';
import 'triage_output.dart';

class AppRecord {
  const AppRecord({
    required this.id,
    required this.output,
    required this.createdAt,
    this.audioFilePath,
  });

  final String id;
  final TriageOutput output;
  final DateTime createdAt;
  final String? audioFilePath;

  factory AppRecord.fromJson(Map<String, dynamic> json) {
    return AppRecord(
      id: json['id'] as String,
      output: TriageOutput.fromJson(
        jsonDecode(json['output_json'] as String) as Map<String, dynamic>,
      ),
      createdAt: DateTime.parse(json['created_at'] as String),
      audioFilePath: json['audio_file_path'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'output_json': jsonEncode(output.toJson()),
      'created_at': createdAt.toIso8601String(),
      'audio_file_path': audioFilePath,
    };
  }

  AppRecord copyWith({
    String? id,
    TriageOutput? output,
    DateTime? createdAt,
    String? audioFilePath,
  }) {
    return AppRecord(
      id: id ?? this.id,
      output: output ?? this.output,
      createdAt: createdAt ?? this.createdAt,
      audioFilePath: audioFilePath ?? this.audioFilePath,
    );
  }
}

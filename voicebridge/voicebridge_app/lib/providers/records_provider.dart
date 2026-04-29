import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/api/voicebridge_api.dart';
import '../data/models/app_record.dart';
import '../data/models/triage_output.dart';
import 'database_provider.dart';

class RecordsNotifier extends AsyncNotifier<List<AppRecord>> {
  @override
  Future<List<AppRecord>> build() => _load();

  Future<List<AppRecord>> _load() async {
    if (kIsWeb) {
      return VoicebridgeApi().getRecords();
    } else {
      final db = ref.read(databaseProvider);
      final rows = await db.recordDao.getRecentRecords(50);
      return rows.map((r) => AppRecord(
        id: r.id,
        output: TriageOutput.fromJson(
          jsonDecode(r.outputJson) as Map<String, dynamic>,
        ),
        createdAt: r.createdAt,
        audioFilePath: r.audioFilePath,
      )).toList();
    }
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_load);
  }
}

final recordsProvider =
    AsyncNotifierProvider<RecordsNotifier, List<AppRecord>>(
  RecordsNotifier.new,
);

// Provider for fetching a single record by ID
final recordByIdProvider = FutureProvider.family<AppRecord?, String>((ref, id) async {
  return VoicebridgeApi().getRecord(id);
});

import 'package:drift/drift.dart';
import 'app_database.dart';
import 'schemas.dart';

part 'daos.g.dart';

@DriftAccessor(tables: [TriageRecords])
class RecordDao extends DatabaseAccessor<AppDatabase>
    with _$RecordDaoMixin {
  RecordDao(super.db);

  Future<void> insertRecord(TriageRecordsCompanion record) async {
    await into(triageRecords).insertOnConflictUpdate(record);
  }

  Future<List<TriageRecord>> getRecentRecords(int limit) {
    return (select(triageRecords)
          ..orderBy([(t) => OrderingTerm.desc(t.createdAt)])
          ..limit(limit))
        .get();
  }

  Future<List<TriageRecord>> getAllRecords() {
    return (select(triageRecords)
          ..orderBy([(t) => OrderingTerm.desc(t.createdAt)]))
        .get();
  }

  Future<TriageRecord?> getRecordById(String id) {
    return (select(triageRecords)..where((t) => t.id.equals(id)))
        .getSingleOrNull();
  }

  Future<int> deleteRecord(String id) {
    return (delete(triageRecords)..where((t) => t.id.equals(id))).go();
  }

  Future<List<TriageRecord>> getRecordsByLevel(String level) {
    // Filter by triage level via JSON — production would use a column index.
    return getAllRecords().then(
      (records) => records
          .where((r) => r.outputJson.contains('"triage_level": "$level"') ||
              r.outputJson.contains('"triage_level":"$level"'))
          .toList(),
    );
  }

  Future<List<TriageRecord>> getRecordsByDateRange(
    DateTime from,
    DateTime to,
  ) {
    return (select(triageRecords)
          ..where(
            (t) => t.createdAt.isBetweenValues(from, to),
          )
          ..orderBy([(t) => OrderingTerm.desc(t.createdAt)]))
        .get();
  }
}

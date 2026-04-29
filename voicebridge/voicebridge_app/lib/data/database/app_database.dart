import 'package:drift/drift.dart';
import 'schemas.dart';
import 'daos.dart';
import 'connection.dart';

part 'app_database.g.dart';

@DriftDatabase(tables: [TriageRecords, AppSettings], daos: [RecordDao])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(openConnection());

  AppDatabase.forTesting(QueryExecutor e) : super(e);

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration {
    return MigrationStrategy(
      onCreate: (m) async {
        await m.createAll();
      },
    );
  }
}

import 'package:drift/drift.dart';

class TriageRecords extends Table {
  TextColumn get id => text()();
  TextColumn get outputJson => text().named('output_json')();
  DateTimeColumn get createdAt => dateTime().named('created_at')();
  TextColumn get audioFilePath =>
      text().named('audio_file_path').nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class AppSettings extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();

  @override
  Set<Column> get primaryKey => {key};
}

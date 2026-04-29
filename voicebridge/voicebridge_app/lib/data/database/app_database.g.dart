// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $TriageRecordsTable extends TriageRecords
    with TableInfo<$TriageRecordsTable, TriageRecord> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $TriageRecordsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _outputJsonMeta =
      const VerificationMeta('outputJson');
  @override
  late final GeneratedColumn<String> outputJson = GeneratedColumn<String>(
      'output_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _audioFilePathMeta =
      const VerificationMeta('audioFilePath');
  @override
  late final GeneratedColumn<String> audioFilePath = GeneratedColumn<String>(
      'audio_file_path', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns =>
      [id, outputJson, createdAt, audioFilePath];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'triage_records';
  @override
  VerificationContext validateIntegrity(Insertable<TriageRecord> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('output_json')) {
      context.handle(
          _outputJsonMeta,
          outputJson.isAcceptableOrUnknown(
              data['output_json']!, _outputJsonMeta));
    } else if (isInserting) {
      context.missing(_outputJsonMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('audio_file_path')) {
      context.handle(
          _audioFilePathMeta,
          audioFilePath.isAcceptableOrUnknown(
              data['audio_file_path']!, _audioFilePathMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  TriageRecord map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return TriageRecord(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      outputJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}output_json'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      audioFilePath: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}audio_file_path']),
    );
  }

  @override
  $TriageRecordsTable createAlias(String alias) {
    return $TriageRecordsTable(attachedDatabase, alias);
  }
}

class TriageRecord extends DataClass implements Insertable<TriageRecord> {
  final String id;
  final String outputJson;
  final DateTime createdAt;
  final String? audioFilePath;
  const TriageRecord(
      {required this.id,
      required this.outputJson,
      required this.createdAt,
      this.audioFilePath});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['output_json'] = Variable<String>(outputJson);
    map['created_at'] = Variable<DateTime>(createdAt);
    if (!nullToAbsent || audioFilePath != null) {
      map['audio_file_path'] = Variable<String>(audioFilePath);
    }
    return map;
  }

  TriageRecordsCompanion toCompanion(bool nullToAbsent) {
    return TriageRecordsCompanion(
      id: Value(id),
      outputJson: Value(outputJson),
      createdAt: Value(createdAt),
      audioFilePath: audioFilePath == null && nullToAbsent
          ? const Value.absent()
          : Value(audioFilePath),
    );
  }

  factory TriageRecord.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return TriageRecord(
      id: serializer.fromJson<String>(json['id']),
      outputJson: serializer.fromJson<String>(json['outputJson']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      audioFilePath: serializer.fromJson<String?>(json['audioFilePath']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'outputJson': serializer.toJson<String>(outputJson),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'audioFilePath': serializer.toJson<String?>(audioFilePath),
    };
  }

  TriageRecord copyWith(
          {String? id,
          String? outputJson,
          DateTime? createdAt,
          Value<String?> audioFilePath = const Value.absent()}) =>
      TriageRecord(
        id: id ?? this.id,
        outputJson: outputJson ?? this.outputJson,
        createdAt: createdAt ?? this.createdAt,
        audioFilePath:
            audioFilePath.present ? audioFilePath.value : this.audioFilePath,
      );
  TriageRecord copyWithCompanion(TriageRecordsCompanion data) {
    return TriageRecord(
      id: data.id.present ? data.id.value : this.id,
      outputJson:
          data.outputJson.present ? data.outputJson.value : this.outputJson,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      audioFilePath: data.audioFilePath.present
          ? data.audioFilePath.value
          : this.audioFilePath,
    );
  }

  @override
  String toString() {
    return (StringBuffer('TriageRecord(')
          ..write('id: $id, ')
          ..write('outputJson: $outputJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('audioFilePath: $audioFilePath')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, outputJson, createdAt, audioFilePath);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is TriageRecord &&
          other.id == this.id &&
          other.outputJson == this.outputJson &&
          other.createdAt == this.createdAt &&
          other.audioFilePath == this.audioFilePath);
}

class TriageRecordsCompanion extends UpdateCompanion<TriageRecord> {
  final Value<String> id;
  final Value<String> outputJson;
  final Value<DateTime> createdAt;
  final Value<String?> audioFilePath;
  final Value<int> rowid;
  const TriageRecordsCompanion({
    this.id = const Value.absent(),
    this.outputJson = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.audioFilePath = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  TriageRecordsCompanion.insert({
    required String id,
    required String outputJson,
    required DateTime createdAt,
    this.audioFilePath = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        outputJson = Value(outputJson),
        createdAt = Value(createdAt);
  static Insertable<TriageRecord> custom({
    Expression<String>? id,
    Expression<String>? outputJson,
    Expression<DateTime>? createdAt,
    Expression<String>? audioFilePath,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (outputJson != null) 'output_json': outputJson,
      if (createdAt != null) 'created_at': createdAt,
      if (audioFilePath != null) 'audio_file_path': audioFilePath,
      if (rowid != null) 'rowid': rowid,
    });
  }

  TriageRecordsCompanion copyWith(
      {Value<String>? id,
      Value<String>? outputJson,
      Value<DateTime>? createdAt,
      Value<String?>? audioFilePath,
      Value<int>? rowid}) {
    return TriageRecordsCompanion(
      id: id ?? this.id,
      outputJson: outputJson ?? this.outputJson,
      createdAt: createdAt ?? this.createdAt,
      audioFilePath: audioFilePath ?? this.audioFilePath,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (outputJson.present) {
      map['output_json'] = Variable<String>(outputJson.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (audioFilePath.present) {
      map['audio_file_path'] = Variable<String>(audioFilePath.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('TriageRecordsCompanion(')
          ..write('id: $id, ')
          ..write('outputJson: $outputJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('audioFilePath: $audioFilePath, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $AppSettingsTable extends AppSettings
    with TableInfo<$AppSettingsTable, AppSetting> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AppSettingsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
      'key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
      'value', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'app_settings';
  @override
  VerificationContext validateIntegrity(Insertable<AppSetting> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
          _keyMeta, key.isAcceptableOrUnknown(data['key']!, _keyMeta));
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
          _valueMeta, value.isAcceptableOrUnknown(data['value']!, _valueMeta));
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  AppSetting map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AppSetting(
      key: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}key'])!,
      value: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}value'])!,
    );
  }

  @override
  $AppSettingsTable createAlias(String alias) {
    return $AppSettingsTable(attachedDatabase, alias);
  }
}

class AppSetting extends DataClass implements Insertable<AppSetting> {
  final String key;
  final String value;
  const AppSetting({required this.key, required this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    return map;
  }

  AppSettingsCompanion toCompanion(bool nullToAbsent) {
    return AppSettingsCompanion(
      key: Value(key),
      value: Value(value),
    );
  }

  factory AppSetting.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AppSetting(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
    };
  }

  AppSetting copyWith({String? key, String? value}) => AppSetting(
        key: key ?? this.key,
        value: value ?? this.value,
      );
  AppSetting copyWithCompanion(AppSettingsCompanion data) {
    return AppSetting(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AppSetting(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AppSetting &&
          other.key == this.key &&
          other.value == this.value);
}

class AppSettingsCompanion extends UpdateCompanion<AppSetting> {
  final Value<String> key;
  final Value<String> value;
  final Value<int> rowid;
  const AppSettingsCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  AppSettingsCompanion.insert({
    required String key,
    required String value,
    this.rowid = const Value.absent(),
  })  : key = Value(key),
        value = Value(value);
  static Insertable<AppSetting> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  AppSettingsCompanion copyWith(
      {Value<String>? key, Value<String>? value, Value<int>? rowid}) {
    return AppSettingsCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AppSettingsCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $TriageRecordsTable triageRecords = $TriageRecordsTable(this);
  late final $AppSettingsTable appSettings = $AppSettingsTable(this);
  late final RecordDao recordDao = RecordDao(this as AppDatabase);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities =>
      [triageRecords, appSettings];
}

typedef $$TriageRecordsTableCreateCompanionBuilder = TriageRecordsCompanion
    Function({
  required String id,
  required String outputJson,
  required DateTime createdAt,
  Value<String?> audioFilePath,
  Value<int> rowid,
});
typedef $$TriageRecordsTableUpdateCompanionBuilder = TriageRecordsCompanion
    Function({
  Value<String> id,
  Value<String> outputJson,
  Value<DateTime> createdAt,
  Value<String?> audioFilePath,
  Value<int> rowid,
});

class $$TriageRecordsTableFilterComposer
    extends Composer<_$AppDatabase, $TriageRecordsTable> {
  $$TriageRecordsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get outputJson => $composableBuilder(
      column: $table.outputJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get audioFilePath => $composableBuilder(
      column: $table.audioFilePath, builder: (column) => ColumnFilters(column));
}

class $$TriageRecordsTableOrderingComposer
    extends Composer<_$AppDatabase, $TriageRecordsTable> {
  $$TriageRecordsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get outputJson => $composableBuilder(
      column: $table.outputJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get audioFilePath => $composableBuilder(
      column: $table.audioFilePath,
      builder: (column) => ColumnOrderings(column));
}

class $$TriageRecordsTableAnnotationComposer
    extends Composer<_$AppDatabase, $TriageRecordsTable> {
  $$TriageRecordsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get outputJson => $composableBuilder(
      column: $table.outputJson, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get audioFilePath => $composableBuilder(
      column: $table.audioFilePath, builder: (column) => column);
}

class $$TriageRecordsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $TriageRecordsTable,
    TriageRecord,
    $$TriageRecordsTableFilterComposer,
    $$TriageRecordsTableOrderingComposer,
    $$TriageRecordsTableAnnotationComposer,
    $$TriageRecordsTableCreateCompanionBuilder,
    $$TriageRecordsTableUpdateCompanionBuilder,
    (
      TriageRecord,
      BaseReferences<_$AppDatabase, $TriageRecordsTable, TriageRecord>
    ),
    TriageRecord,
    PrefetchHooks Function()> {
  $$TriageRecordsTableTableManager(_$AppDatabase db, $TriageRecordsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$TriageRecordsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$TriageRecordsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$TriageRecordsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> outputJson = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<String?> audioFilePath = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              TriageRecordsCompanion(
            id: id,
            outputJson: outputJson,
            createdAt: createdAt,
            audioFilePath: audioFilePath,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String outputJson,
            required DateTime createdAt,
            Value<String?> audioFilePath = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              TriageRecordsCompanion.insert(
            id: id,
            outputJson: outputJson,
            createdAt: createdAt,
            audioFilePath: audioFilePath,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$TriageRecordsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $TriageRecordsTable,
    TriageRecord,
    $$TriageRecordsTableFilterComposer,
    $$TriageRecordsTableOrderingComposer,
    $$TriageRecordsTableAnnotationComposer,
    $$TriageRecordsTableCreateCompanionBuilder,
    $$TriageRecordsTableUpdateCompanionBuilder,
    (
      TriageRecord,
      BaseReferences<_$AppDatabase, $TriageRecordsTable, TriageRecord>
    ),
    TriageRecord,
    PrefetchHooks Function()>;
typedef $$AppSettingsTableCreateCompanionBuilder = AppSettingsCompanion
    Function({
  required String key,
  required String value,
  Value<int> rowid,
});
typedef $$AppSettingsTableUpdateCompanionBuilder = AppSettingsCompanion
    Function({
  Value<String> key,
  Value<String> value,
  Value<int> rowid,
});

class $$AppSettingsTableFilterComposer
    extends Composer<_$AppDatabase, $AppSettingsTable> {
  $$AppSettingsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnFilters(column));
}

class $$AppSettingsTableOrderingComposer
    extends Composer<_$AppDatabase, $AppSettingsTable> {
  $$AppSettingsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnOrderings(column));
}

class $$AppSettingsTableAnnotationComposer
    extends Composer<_$AppDatabase, $AppSettingsTable> {
  $$AppSettingsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$AppSettingsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $AppSettingsTable,
    AppSetting,
    $$AppSettingsTableFilterComposer,
    $$AppSettingsTableOrderingComposer,
    $$AppSettingsTableAnnotationComposer,
    $$AppSettingsTableCreateCompanionBuilder,
    $$AppSettingsTableUpdateCompanionBuilder,
    (AppSetting, BaseReferences<_$AppDatabase, $AppSettingsTable, AppSetting>),
    AppSetting,
    PrefetchHooks Function()> {
  $$AppSettingsTableTableManager(_$AppDatabase db, $AppSettingsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$AppSettingsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$AppSettingsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$AppSettingsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> key = const Value.absent(),
            Value<String> value = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AppSettingsCompanion(
            key: key,
            value: value,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String key,
            required String value,
            Value<int> rowid = const Value.absent(),
          }) =>
              AppSettingsCompanion.insert(
            key: key,
            value: value,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$AppSettingsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $AppSettingsTable,
    AppSetting,
    $$AppSettingsTableFilterComposer,
    $$AppSettingsTableOrderingComposer,
    $$AppSettingsTableAnnotationComposer,
    $$AppSettingsTableCreateCompanionBuilder,
    $$AppSettingsTableUpdateCompanionBuilder,
    (AppSetting, BaseReferences<_$AppDatabase, $AppSettingsTable, AppSetting>),
    AppSetting,
    PrefetchHooks Function()>;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$TriageRecordsTableTableManager get triageRecords =>
      $$TriageRecordsTableTableManager(_db, _db.triageRecords);
  $$AppSettingsTableTableManager get appSettings =>
      $$AppSettingsTableTableManager(_db, _db.appSettings);
}

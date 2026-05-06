import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppSettings {
  const AppSettings({
    this.themeMode = ThemeMode.light,
    this.selectedLanguage = 'English',
    this.modelPath = '',
    this.maxRecordingSeconds = 120,
    this.enableHaptics = true,
  });

  final ThemeMode themeMode;
  final String selectedLanguage;
  final String modelPath;
  final int maxRecordingSeconds;
  final bool enableHaptics;

  AppSettings copyWith({
    ThemeMode? themeMode,
    String? selectedLanguage,
    String? modelPath,
    int? maxRecordingSeconds,
    bool? enableHaptics,
  }) {
    return AppSettings(
      themeMode: themeMode ?? this.themeMode,
      selectedLanguage: selectedLanguage ?? this.selectedLanguage,
      modelPath: modelPath ?? this.modelPath,
      maxRecordingSeconds: maxRecordingSeconds ?? this.maxRecordingSeconds,
      enableHaptics: enableHaptics ?? this.enableHaptics,
    );
  }

  Map<String, String> toJson() {
    return {
      'themeMode': themeMode.name,
      'selectedLanguage': selectedLanguage,
      'modelPath': modelPath,
      'maxRecordingSeconds': maxRecordingSeconds.toString(),
      'enableHaptics': enableHaptics.toString(),
    };
  }

  static AppSettings fromJson(Map<String, String> json) {
    return AppSettings(
      themeMode: json['themeMode'] == 'dark' ? ThemeMode.dark : ThemeMode.light,
      selectedLanguage: json['selectedLanguage'] ?? 'English',
      modelPath: json['modelPath'] ?? '',
      maxRecordingSeconds: int.tryParse(json['maxRecordingSeconds'] ?? '') ?? 120,
      enableHaptics: json['enableHaptics'] != 'false',
    );
  }
}

class SettingsNotifier extends Notifier<AppSettings> {
  SharedPreferences? _prefs;

  @override
  AppSettings build() {
    _load();
    return const AppSettings();
  }

  Future<void> _load() async {
    _prefs = await SharedPreferences.getInstance();
    final json = _prefs!.getKeys().fold(<String, String>{}, (map, key) {
      map[key] = _prefs!.getString(key) ?? '';
      return map;
    });
    if (json.isNotEmpty) {
      state = AppSettings.fromJson(json);
    }
  }

  Future<void> _save() async {
    _prefs ??= await SharedPreferences.getInstance();
    for (final entry in state.toJson().entries) {
      await _prefs!.setString(entry.key, entry.value);
    }
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    state = state.copyWith(themeMode: mode);
    await _save();
  }

  Future<void> setLanguage(String language) async {
    state = state.copyWith(selectedLanguage: language);
    await _save();
  }

  Future<void> setModelPath(String path) async {
    state = state.copyWith(modelPath: path);
    await _save();
  }

  Future<void> setMaxRecordingSeconds(int seconds) async {
    state = state.copyWith(maxRecordingSeconds: seconds);
    await _save();
  }

  Future<void> setHaptics(bool enabled) async {
    state = state.copyWith(enableHaptics: enabled);
    await _save();
  }
}

final settingsProvider =
    NotifierProvider<SettingsNotifier, AppSettings>(SettingsNotifier.new);

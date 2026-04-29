import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
}

class SettingsNotifier extends Notifier<AppSettings> {
  @override
  AppSettings build() => const AppSettings();

  void setThemeMode(ThemeMode mode) {
    state = state.copyWith(themeMode: mode);
  }

  void setLanguage(String language) {
    state = state.copyWith(selectedLanguage: language);
  }

  void setModelPath(String path) {
    state = state.copyWith(modelPath: path);
  }

  void setMaxRecordingSeconds(int seconds) {
    state = state.copyWith(maxRecordingSeconds: seconds);
  }

  void setHaptics(bool enabled) {
    state = state.copyWith(enableHaptics: enabled);
  }
}

final settingsProvider =
    NotifierProvider<SettingsNotifier, AppSettings>(SettingsNotifier.new);

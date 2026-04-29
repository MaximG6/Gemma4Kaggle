import 'package:flutter/material.dart';
import '../theme/colors.dart';

enum TriageLevel { red, orange, yellow, green, blue, unknown }

extension TriageLevelExtension on TriageLevel {
  String get label => name.toUpperCase();

  Color get color {
    switch (this) {
      case TriageLevel.red:
        return AppColors.triageRed;
      case TriageLevel.orange:
        return AppColors.triageOrange;
      case TriageLevel.yellow:
        return AppColors.triageYellow;
      case TriageLevel.green:
        return AppColors.triageGreen;
      case TriageLevel.blue:
        return AppColors.triageBlue;
      case TriageLevel.unknown:
        return AppColors.textSecondary;
    }
  }

  String get waitTime {
    switch (this) {
      case TriageLevel.red:
        return 'Immediate';
      case TriageLevel.orange:
        return '≤ 10 min';
      case TriageLevel.yellow:
        return '≤ 60 min';
      case TriageLevel.green:
        return '≤ 4 hours';
      case TriageLevel.blue:
        return 'Non-urgent';
      case TriageLevel.unknown:
        return '—';
    }
  }

  String get description {
    switch (this) {
      case TriageLevel.red:
        return 'Resuscitation — Immediate life threat';
      case TriageLevel.orange:
        return 'Emergency — Very urgent';
      case TriageLevel.yellow:
        return 'Urgent — Needs prompt attention';
      case TriageLevel.green:
        return 'Less urgent — Can wait';
      case TriageLevel.blue:
        return 'Routine — Non-urgent';
      case TriageLevel.unknown:
        return 'Level undetermined';
    }
  }

  IconData get icon {
    switch (this) {
      case TriageLevel.red:
        return Icons.emergency;
      case TriageLevel.orange:
        return Icons.warning_amber_rounded;
      case TriageLevel.yellow:
        return Icons.schedule;
      case TriageLevel.green:
        return Icons.check_circle_outline;
      case TriageLevel.blue:
        return Icons.info_outline;
      case TriageLevel.unknown:
        return Icons.help_outline;
    }
  }

  int get order {
    switch (this) {
      case TriageLevel.red:
        return 0;
      case TriageLevel.orange:
        return 1;
      case TriageLevel.yellow:
        return 2;
      case TriageLevel.green:
        return 3;
      case TriageLevel.blue:
        return 4;
      case TriageLevel.unknown:
        return 5;
    }
  }
}

TriageLevel triageLevelFromString(String s) {
  switch (s.toLowerCase().trim()) {
    case 'red':
      return TriageLevel.red;
    case 'orange':
      return TriageLevel.orange;
    case 'yellow':
      return TriageLevel.yellow;
    case 'green':
      return TriageLevel.green;
    case 'blue':
      return TriageLevel.blue;
    default:
      return TriageLevel.unknown;
  }
}

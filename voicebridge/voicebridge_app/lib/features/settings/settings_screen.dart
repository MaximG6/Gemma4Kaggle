import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/glass.dart';
import '../../core/theme/typography.dart';
import '../../providers/settings_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            floating: true,
            backgroundColor: Colors.transparent,
            elevation: 0,
            flexibleSpace: FlexibleSpaceBar(
              background: ClipRect(
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Theme.of(context).brightness == Brightness.dark
                          ? const Color(0xFF0D1B2A).withOpacity(0.8)
                          : Colors.white.withOpacity(0.75),
                      border: Border(
                        bottom: BorderSide(
                          color: Theme.of(context).brightness == Brightness.dark
                              ? Colors.white.withOpacity(0.06)
                              : Colors.black.withOpacity(0.04),
                          width: 1,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              titlePadding: const EdgeInsets.only(left: 16, bottom: 12, right: 16),
              title: Text('Settings', style: AppTypography.headlineMedium),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _Section(
                  title: 'Model Management',
                  children: [
                    _SettingTile(
                      icon: Icons.memory_rounded,
                      title: 'Model file',
                      subtitle: settings.modelPath.isEmpty
                          ? 'Not configured'
                          : settings.modelPath,
                    ),
                    _SettingTile(
                      icon: Icons.download_rounded,
                      title: 'Download model',
                      subtitle: AppConstants.modelFileName,
                      trailing: const Icon(
                        Icons.arrow_forward_ios_rounded,
                        size: 14,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _Section(
                  title: 'Language',
                  children: [
                    _DropdownTile(
                      icon: Icons.language_rounded,
                      title: 'Default language',
                      value: settings.selectedLanguage,
                      items: AppConstants.supportedLanguages,
                      onChanged: (v) => ref
                          .read(settingsProvider.notifier)
                          .setLanguage(v!),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _Section(
                  title: 'Audio',
                  children: [
                    _SliderTile(
                      icon: Icons.timer_outlined,
                      title: 'Max recording duration',
                      value: settings.maxRecordingSeconds.toDouble(),
                      min: 30,
                      max: 300,
                      divisions: 9,
                      label: '${settings.maxRecordingSeconds}s',
                      onChanged: (v) => ref
                          .read(settingsProvider.notifier)
                          .setMaxRecordingSeconds(v.round()),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _Section(
                  title: 'Appearance',
                  children: [
                    _SwitchTile(
                      icon: Icons.dark_mode_rounded,
                      title: 'Dark mode',
                      value: settings.themeMode == ThemeMode.dark,
                      onChanged: (v) => ref
                          .read(settingsProvider.notifier)
                          .setThemeMode(v ? ThemeMode.dark : ThemeMode.light),
                    ),
                    _SwitchTile(
                      icon: Icons.vibration_rounded,
                      title: 'Haptic feedback',
                      value: settings.enableHaptics,
                      onChanged: (v) => ref
                          .read(settingsProvider.notifier)
                          .setHaptics(v),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _Section(
                  title: 'Privacy',
                  children: [
                    _SettingTile(
                      icon: Icons.delete_sweep_rounded,
                      title: 'Clear all records',
                      subtitle: 'Cannot be undone',
                      onTap: () => _confirmClear(context),
                      titleColor: AppColors.triageRed,
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _Section(
                  title: 'About',
                  children: [
                    _SettingTile(
                      icon: Icons.info_outline_rounded,
                      title: AppConstants.appName,
                      subtitle: 'v${AppConstants.appVersion}',
                    ),
                    _SettingTile(
                      icon: Icons.health_and_safety_rounded,
                      title: 'Triage standard',
                      subtitle: 'SATS 2023 + WHO ETAT',
                    ),
                    _SettingTile(
                      icon: Icons.offline_bolt_rounded,
                      title: 'Mode',
                      subtitle: 'Fully offline inference',
                    ),
                  ],
                ),
                const SizedBox(height: 80),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  void _confirmClear(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Clear all records?'),
        content: const Text('This will permanently delete all triage records.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Clear', style: TextStyle(color: AppColors.triageRed)),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8, left: 4),
          child: Text(
            title.toUpperCase(),
            style: AppTypography.labelSmall.copyWith(letterSpacing: 1.2),
          ),
        ),
        GlassCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: children
                .asMap()
                .entries
                .map(
                  (e) => Column(
                    children: [
                      e.value,
                      if (e.key < children.length - 1)
                        Divider(
                          height: 1,
                          indent: 56,
                          color: AppColors.textSecondary.withOpacity(0.1),
                        ),
                    ],
                  ),
                )
                .toList(),
          ),
        ),
      ],
    );
  }
}

class _SettingTile extends StatelessWidget {
  const _SettingTile({
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    this.onTap,
    this.titleColor,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;
  final Color? titleColor;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppColors.secondary, size: 22),
      title: Text(
        title,
        style: AppTypography.bodyMedium.copyWith(
          fontWeight: FontWeight.w500,
          color: titleColor,
        ),
      ),
      subtitle: subtitle != null
          ? Text(subtitle!, style: AppTypography.bodySmall)
          : null,
      trailing: trailing,
      onTap: onTap,
    );
  }
}

class _SwitchTile extends StatelessWidget {
  const _SwitchTile({
    required this.icon,
    required this.title,
    required this.value,
    required this.onChanged,
  });

  final IconData icon;
  final String title;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppColors.secondary, size: 22),
      title: Text(
        title,
        style:
            AppTypography.bodyMedium.copyWith(fontWeight: FontWeight.w500),
      ),
      trailing: Switch.adaptive(
        value: value,
        onChanged: onChanged,
        activeColor: AppColors.secondary,
      ),
    );
  }
}

class _DropdownTile extends StatelessWidget {
  const _DropdownTile({
    required this.icon,
    required this.title,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  final IconData icon;
  final String title;
  final String value;
  final List<String> items;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppColors.secondary, size: 22),
      title: Text(
        title,
        style:
            AppTypography.bodyMedium.copyWith(fontWeight: FontWeight.w500),
      ),
      trailing: DropdownButton<String>(
        value: value,
        underline: const SizedBox.shrink(),
        items: items
            .map((i) => DropdownMenuItem(value: i, child: Text(i)))
            .toList(),
        onChanged: onChanged,
        style: AppTypography.bodySmall.copyWith(color: AppColors.textPrimary),
      ),
    );
  }
}

class _SliderTile extends StatelessWidget {
  const _SliderTile({
    required this.icon,
    required this.title,
    required this.value,
    required this.min,
    required this.max,
    required this.divisions,
    required this.label,
    required this.onChanged,
  });

  final IconData icon;
  final String title;
  final double value;
  final double min;
  final double max;
  final int divisions;
  final String label;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: AppColors.secondary, size: 22),
              const SizedBox(width: 16),
              Text(
                title,
                style: AppTypography.bodyMedium
                    .copyWith(fontWeight: FontWeight.w500),
              ),
              const Spacer(),
              Text(label, style: AppTypography.bodySmall),
            ],
          ),
          Slider(
            value: value,
            min: min,
            max: max,
            divisions: divisions,
            activeColor: AppColors.secondary,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}

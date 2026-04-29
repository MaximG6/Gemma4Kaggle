import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/colors.dart';
import 'core/constants.dart';
import 'features/splash/splash_screen.dart';
import 'features/home/home_screen.dart';
import 'features/recording/recording_screen.dart';
import 'features/processing/processing_screen.dart';
import 'features/results/results_screen.dart';
import 'features/history/history_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/interactive/interactive_screen.dart';
import 'providers/settings_provider.dart';

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (_, __) => const SplashScreen()),
    ShellRoute(
      builder: (ctx, state, child) => _Shell(child: child),
      routes: [
        GoRoute(
          path: '/home',
          builder: (_, __) => const HomeScreen(),
        ),
        GoRoute(
          path: '/history',
          builder: (_, __) => const HistoryScreen(),
        ),
        GoRoute(
          path: '/settings',
          builder: (_, __) => const SettingsScreen(),
        ),
        GoRoute(
          path: '/case/:id',
          builder: (_, state) =>
              ResultsScreen(id: state.pathParameters['id']!),
        ),
      ],
    ),
    GoRoute(path: '/record', builder: (_, __) => const RecordingScreen()),
    GoRoute(path: '/interactive', builder: (_, __) => const InteractiveScreen()),
    GoRoute(path: '/processing', builder: (_, __) => const ProcessingScreen()),
    GoRoute(
      path: '/results/:id',
      builder: (_, state) =>
          ResultsScreen(id: state.pathParameters['id']!),
    ),
  ],
);

class VoiceBridgeApp extends ConsumerWidget {
  const VoiceBridgeApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);

    return MaterialApp.router(
      title: AppConstants.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: settings.themeMode,
      routerConfig: _router,
    );
  }
}

class _Shell extends StatefulWidget {
  const _Shell({required this.child});

  final Widget child;

  @override
  State<_Shell> createState() => _ShellState();
}

class _ShellState extends State<_Shell> {
  int _index = 0;

  static const _destinations = [
    ('/home', Icons.home_outlined, Icons.home_rounded, 'Home'),
    ('/history', Icons.history_outlined, Icons.history_rounded, 'History'),
    ('/settings', Icons.settings_outlined, Icons.settings_rounded, 'Settings'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: widget.child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 16,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: SafeArea(
          child: NavigationBar(
            selectedIndex: _index,
            onDestinationSelected: (i) {
              setState(() => _index = i);
              context.go(_destinations[i].$1);
            },
            backgroundColor: Colors.transparent,
            elevation: 0,
            indicatorColor: AppColors.secondary.withOpacity(0.12),
            destinations: _destinations
                .map(
                  (d) => NavigationDestination(
                    icon: Icon(d.$2),
                    selectedIcon: Icon(d.$3, color: AppColors.secondary),
                    label: d.$4,
                  ),
                )
                .toList(),
          ),
        ),
      ),
    );
  }
}

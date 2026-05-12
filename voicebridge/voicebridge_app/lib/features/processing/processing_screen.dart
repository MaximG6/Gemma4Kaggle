import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/glass.dart';
import '../../core/theme/typography.dart';
import '../../core/utils/date_formatter.dart';
import '../../domain/pipeline/voicebridge_pipeline.dart';
import '../../providers/pipeline_provider.dart';
import 'widgets/pipeline_progress.dart';

class ProcessingScreen extends ConsumerStatefulWidget {
  final String inputMode;

  const ProcessingScreen({super.key, this.inputMode = 'audio'});

  @override
  ConsumerState<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends ConsumerState<ProcessingScreen> {
  Timer? _elapsedTimer;
  Duration _elapsed = Duration.zero;

  @override
  void initState() {
    super.initState();
    _elapsedTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() => _elapsed += const Duration(seconds: 1));
    });
  }

  @override
  void dispose() {
    _elapsedTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pipelineAsync = ref.watch(pipelineProvider);

    ref.listen(pipelineProvider, (_, next) {
      next.whenData((state) {
        if (state.status == PipelineStatus.done && state.result != null) {
          _elapsedTimer?.cancel();
          if (context.mounted) {
            if (state.recordId != null && state.recordId!.isNotEmpty) {
              context.go('/case/${state.recordId}');
            } else {
              context.go('/home');
            }
          }
        }
      });
    });

    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      body: MeshGradientBackground(
        child: SafeArea(
          child: Column(
            children: [
              Align(
                alignment: Alignment.topLeft,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: IconButton(
                    icon: Icon(Icons.arrow_back_ios_rounded, color: isDark ? Colors.white : AppColors.textPrimary),
                    onPressed: () => context.go('/home'),
                  ),
                ),
              ),
              Expanded(
                child: pipelineAsync.when(
                  data: (state) => _buildContent(state),
                  loading: () => const Center(
                    child: CircularProgressIndicator(color: AppColors.secondary),
                  ),
                  error: (e, _) => _buildError(e.toString()),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildContent(PipelineState state) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: isDark ? Colors.white.withOpacity(0.1) : AppColors.secondary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(Icons.hourglass_top_rounded,
                    color: isDark ? Colors.white70 : AppColors.secondary, size: 20),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Processing',
                    style: AppTypography.headlineMedium
                        .copyWith(color: isDark ? Colors.white : AppColors.textPrimary),
                  ),
                  Text(
                    'Elapsed: ${formatDuration(_elapsed)}',
                    style: AppTypography.bodySmall
                        .copyWith(color: isDark ? Colors.white60 : AppColors.textSecondary),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 40),
          GlassCard(
            child: PipelineProgressStepper(
              currentStatus: state.status,
              elapsed: _elapsed,
              inputMode: widget.inputMode,
            ),
          ),
          const SizedBox(height: 24),
          GlassCard(
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: isDark ? Colors.white.withOpacity(0.08) : AppColors.secondary.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(Icons.audio_file_rounded,
                      color: isDark ? Colors.white54 : AppColors.textSecondary, size: 18),
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Audio clip',
                      style: AppTypography.labelMedium
                          .copyWith(color: isDark ? Colors.white60 : AppColors.textPrimary),
                    ),
                    Text(
                      'Recording in progress',
                      style: AppTypography.bodySmall
                          .copyWith(color: isDark ? Colors.white38 : AppColors.textSecondary),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildError(String message) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: GlassCard(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline,
                  color: AppColors.triageRed, size: 40),
              const SizedBox(height: 16),
              Text('Pipeline Error',
                  style: AppTypography.headlineSmall
                      .copyWith(color: isDark ? Colors.white : AppColors.textPrimary)),
              const SizedBox(height: 8),
              Text(message,
                  style:
                      AppTypography.bodySmall.copyWith(color: isDark ? Colors.white60 : AppColors.textSecondary),
                  textAlign: TextAlign.center),
              const SizedBox(height: 20),
              TextButton(
                onPressed: () => context.go('/home'),
                child: Text('Go Home', style: AppTypography.labelMedium.copyWith(color: isDark ? Colors.white : AppColors.textPrimary)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

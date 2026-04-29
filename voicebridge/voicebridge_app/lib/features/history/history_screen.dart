import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/glass.dart';
import '../../core/theme/typography.dart';
import '../../core/utils/date_formatter.dart';
import '../../data/models/app_record.dart';
import '../../providers/records_provider.dart';
import 'widgets/case_card.dart';
import 'widgets/filter_chips.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  String _filter = 'All';
  String _searchQuery = '';
  final _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<AppRecord> _filtered(List<AppRecord> records) {
    var result = records;
    if (_filter != 'All') {
      result = result
          .where((r) => r.output.triageLevel.toUpperCase() == _filter)
          .toList();
    }
    if (_searchQuery.isNotEmpty) {
      final q = _searchQuery.toLowerCase();
      result = result
          .where(
            (r) =>
                r.output.primaryComplaint.toLowerCase().contains(q) ||
                r.output.triageLevel.toLowerCase().contains(q),
          )
          .toList();
    }
    return result;
  }

  Map<String, List<AppRecord>> _grouped(List<AppRecord> records) {
    final filtered = _filtered(records);
    final result = <String, List<AppRecord>>{};
    for (final r in filtered) {
      final key = formatGroupHeader(r.createdAt);
      result.putIfAbsent(key, () => []).add(r);
    }
    return result;
  }

  @override
  Widget build(BuildContext context) {
    final recordsAsync = ref.watch(recordsProvider);
    final records = recordsAsync.valueOrNull ?? const [];
    final filtered = _filtered(records);
    final grouped = _grouped(records);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(130),
        child: SafeArea(
          child: ClipRect(
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
                child: Column(
                  children: [
                    Padding(
                      padding:
                          const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      child: Row(
                        children: [
                          Text(
                            'History',
                            style: AppTypography.headlineLarge,
                          ),
                          const Spacer(),
                          Text(
                            '${filtered.length} case${filtered.length == 1 ? '' : 's'}',
                            style: AppTypography.bodySmall,
                          ),
                        ],
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: GlassCard(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 8),
                        child: Row(
                          children: [
                            const Icon(Icons.search,
                                color: AppColors.textSecondary, size: 20),
                            const SizedBox(width: 8),
                            Expanded(
                              child: TextField(
                                controller: _searchController,
                                onChanged: (v) =>
                                    setState(() => _searchQuery = v),
                                style: AppTypography.bodyMedium,
                                decoration: const InputDecoration(
                                  hintText: 'Search cases...',
                                  border: InputBorder.none,
                                  isDense: true,
                                  contentPadding: EdgeInsets.zero,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(recordsProvider.notifier).refresh(),
        color: AppColors.secondary,
        child: recordsAsync.when(
          loading: () => const Center(
            child: CircularProgressIndicator(color: AppColors.secondary),
          ),
          error: (e, _) => Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Text(
                'Could not load records — is the server running?',
                style: AppTypography.bodySmall,
                textAlign: TextAlign.center,
              ),
            ),
          ),
          data: (_) => CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Column(
                  children: [
                    const SizedBox(height: 12),
                    TriageFilterChips(
                      selected: _filter,
                      onSelected: (v) => setState(() => _filter = v),
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
              if (grouped.isEmpty)
                SliverFillRemaining(
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.inbox_rounded,
                            size: 48,
                            color: AppColors.textSecondary.withOpacity(0.3)),
                        const SizedBox(height: 12),
                        Text('No cases found',
                            style: AppTypography.bodyMedium),
                      ],
                    ),
                  ),
                )
              else
                SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (ctx, i) {
                      final keys = grouped.keys.toList();
                      final key = keys[i];
                      final groupRecords = grouped[key]!;

                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                            child: Text(key, style: AppTypography.labelMedium),
                          ),
                          ...groupRecords.map(
                            (r) => Padding(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 16, vertical: 5),
                              child: CaseCard(
                                record: r,
                                onDelete: () =>
                                    ref.read(recordsProvider.notifier).refresh(),
                              ),
                            ),
                          ),
                          const SizedBox(height: 8),
                        ],
                      );
                    },
                    childCount: grouped.length,
                  ),
                ),
              const SliverToBoxAdapter(child: SizedBox(height: 80)),
            ],
          ),
        ),
      ),
    );
  }
}

import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/colors.dart';
import '../../core/theme/glass.dart';
import '../../core/theme/typography.dart';
import '../../data/api/voicebridge_api.dart';
import '../../providers/pipeline_provider.dart';

class InteractiveScreen extends ConsumerStatefulWidget {
  const InteractiveScreen({super.key});

  @override
  ConsumerState<InteractiveScreen> createState() => _InteractiveScreenState();
}

class _InteractiveScreenState extends ConsumerState<InteractiveScreen> {
  final _api = VoicebridgeApi();
  final _controller = TextEditingController();
  String? _sessionId;
  bool _loading = false;
  int _turnCount = 0;
  static const _maxTurns = 6;

  // Chat messages: {role: 'model'|'user', content: '...'}
  final List<Map<String, String>> _messages = [];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _loading) return;
    _controller.clear();

    setState(() {
      _messages.add({'role': 'user', 'content': text});
      _loading = true;
    });

    try {
      final result = await _api.postInteractive(
        text,
        sessionId: _sessionId,
      );

      _sessionId = result['session_id'] as String?;
      _turnCount++;

      final response = result['response'] as String;
      final isFinal = result['is_final'] as bool;

      setState(() {
        _messages.add({'role': 'model', 'content': response});
        _loading = false;
      });

      if (isFinal) {
        final triage = result['triage'];
        if (triage != null) {
          // Navigate to results - for now go to processing then results
          // The triage is already saved by backend
          if (mounted) {
            context.go('/home');
            // Show a snackbar or dialog about the result
            // For now, just navigate home - the result is in history
          }
        }
      }
    } catch (e) {
      setState(() {
        _messages.add({
          'role': 'model',
          'content': 'Error: ${e.toString()}',
        });
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context, isDark),
            Expanded(
              child: _buildChatArea(isDark),
            ),
            _buildInputArea(isDark),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, bool isDark) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          IconButton(
            icon: Icon(
              Icons.arrow_back_ios_rounded,
              color: isDark ? Colors.white : Colors.black87,
            ),
            onPressed: () => context.go('/home'),
          ),
          Text(
            'Interactive Triage',
            style: AppTypography.headlineMedium.copyWith(
              color: isDark ? Colors.white : Colors.black87,
            ),
          ),
          const Spacer(),
          if (_turnCount > 0)
            GlassCard(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: Text(
                '${_turnCount}/$_maxTurns turns',
                style: AppTypography.labelMedium.copyWith(
                  color: isDark ? Colors.white70 : Colors.black54,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildChatArea(bool isDark) {
    if (_messages.isEmpty && !_loading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.chat_bubble_outline_rounded,
              size: 64,
              color: isDark ? Colors.white24 : Colors.black26,
            ),
            const SizedBox(height: 16),
            Text(
              'Describe the patient symptoms',
              style: AppTypography.bodyLarge.copyWith(
                color: isDark ? Colors.white60 : Colors.black54,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'The AI will ask follow-up questions',
              style: AppTypography.bodySmall.copyWith(
                color: isDark ? Colors.white.withOpacity(0.4) : Colors.black38,
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _messages.length + (_loading ? 1 : 0),
      itemBuilder: (context, index) {
        if (index < _messages.length) {
          final msg = _messages[index];
          return _buildMessageBubble(msg, isDark);
        }
        return _buildLoadingBubble();
      },
    );
  }

  Widget _buildMessageBubble(Map<String, String> msg, bool isDark) {
    final isUser = msg['role'] == 'user';
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!isUser) ...[
            CircleAvatar(
              radius: 14,
              backgroundColor: AppColors.secondary,
              child: const Icon(Icons.medical_services_rounded,
                  size: 16, color: Colors.white),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: _buildBubble(isUser, isDark, msg['content']!),
          ),
          if (isUser) ...[
            const SizedBox(width: 8),
            CircleAvatar(
              radius: 14,
              backgroundColor: isDark ? Colors.white24 : AppColors.secondary.withOpacity(0.3),
              child: Icon(Icons.person_rounded,
                  size: 16, color: isDark ? Colors.white70 : Colors.white),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBubble(bool isUser, bool isDark, String text) {
    if (isUser) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.secondary,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: const Radius.circular(16),
            bottomRight: const Radius.circular(4),
          ),
        ),
        child: Text(
          text,
          style: AppTypography.bodyMedium.copyWith(
            color: Colors.white,
          ),
        ),
      );
    }
    return ClipRRect(
      borderRadius: BorderRadius.only(
        topLeft: const Radius.circular(16),
        topRight: const Radius.circular(16),
        bottomLeft: const Radius.circular(4),
        bottomRight: const Radius.circular(16),
      ),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: isDark
                ? Colors.white.withOpacity(0.08)
                : Colors.white.withOpacity(0.65),
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(16),
              topRight: const Radius.circular(16),
              bottomLeft: const Radius.circular(4),
              bottomRight: const Radius.circular(16),
            ),
            border: Border.all(
              color: isDark
                  ? Colors.white.withOpacity(0.1)
                  : Colors.white.withOpacity(0.5),
              width: 1.0,
            ),
          ),
          child: Text(
            text,
            style: AppTypography.bodyMedium.copyWith(
              color: isDark ? Colors.white.withOpacity(0.9) : Colors.black87,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLoadingBubble() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          CircleAvatar(
            radius: 14,
            backgroundColor: AppColors.secondary,
            child: const Icon(Icons.medical_services_rounded,
                size: 16, color: Colors.white),
          ),
          const SizedBox(width: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.white.withOpacity(0.1),
                    width: 1.0,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppColors.secondary,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Thinking...',
                      style: AppTypography.bodySmall.copyWith(
                        color: Colors.white70,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea(bool isDark) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: GlassCard(
              child: TextField(
                controller: _controller,
                enabled: !_loading,
                style: AppTypography.bodyMedium.copyWith(
                  color: isDark ? Colors.white : Colors.black87,
                ),
                decoration: InputDecoration(
                  hintText: 'Type your answer...',
                  hintStyle: AppTypography.bodyMedium.copyWith(
                    color: isDark ? Colors.white38 : Colors.black38,
                  ),
                  border: InputBorder.none,
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                ),
                onSubmitted: (_) => _send(),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              color: _loading
                  ? Colors.white24
                  : AppColors.secondary,
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: Icon(
                _loading
                    ? Icons.hourglass_bottom_rounded
                    : Icons.send_rounded,
                color: Colors.white,
              ),
              onPressed: _loading ? null : _send,
            ),
          ),
        ],
      ),
    );
  }
}

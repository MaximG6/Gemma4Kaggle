import 'package:intl/intl.dart';

String formatDate(DateTime dt) {
  return DateFormat('dd MMM yyyy, HH:mm').format(dt);
}

String formatDateShort(DateTime dt) {
  return DateFormat('dd MMM').format(dt);
}

String formatRelativeTime(DateTime dt) {
  final now = DateTime.now();
  final diff = now.difference(dt);

  if (diff.inSeconds < 60) return 'just now';
  if (diff.inMinutes < 60) {
    final m = diff.inMinutes;
    return '$m min${m == 1 ? '' : 's'} ago';
  }
  if (diff.inHours < 24) {
    final h = diff.inHours;
    return '$h hour${h == 1 ? '' : 's'} ago';
  }
  if (diff.inDays == 1) return 'yesterday';
  if (diff.inDays < 7) return '${diff.inDays} days ago';
  return formatDateShort(dt);
}

String formatGroupHeader(DateTime dt) {
  final now = DateTime.now();
  final today = DateTime(now.year, now.month, now.day);
  final d = DateTime(dt.year, dt.month, dt.day);

  if (d == today) return 'Today';
  if (d == today.subtract(const Duration(days: 1))) return 'Yesterday';
  if (today.difference(d).inDays < 7) return DateFormat('EEEE').format(dt);
  return DateFormat('MMMM d, yyyy').format(dt);
}

String formatDuration(Duration d) {
  final minutes = d.inMinutes.remainder(60).toString().padLeft(2, '0');
  final seconds = d.inSeconds.remainder(60).toString().padLeft(2, '0');
  return '$minutes:$seconds';
}

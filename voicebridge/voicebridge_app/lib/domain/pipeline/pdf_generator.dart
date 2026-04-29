import 'dart:typed_data';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import '../../core/utils/triage_level_utils.dart';
import '../../data/models/triage_output.dart';

Future<Uint8List> generateTriagePdf(TriageOutput output) async {
  final doc = pw.Document();
  final level = triageLevelFromString(output.triageLevel);
  final levelColor = _pdfColor(level);

  doc.addPage(
    pw.Page(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(40),
      build: (ctx) {
        return pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            _triageBanner(level, levelColor),
            pw.SizedBox(height: 20),
            _sectionHeader('Clinical Summary'),
            _labelValue('Primary Complaint', output.primaryComplaint),
            _labelValue('Duration', output.durationOfSymptoms),
            _labelValue('Relevant History', output.relevantHistory),
            _labelValue('Source Language', output.sourceLanguage.toUpperCase()),
            pw.SizedBox(height: 16),
            _sectionHeader('Reported Symptoms'),
            ...output.reportedSymptoms.map(_bullet),
            pw.SizedBox(height: 16),
            if (output.vitalSignsReported.isNotEmpty) ...[
              _sectionHeader('Vital Signs'),
              ...output.vitalSignsReported.entries
                  .map((e) => _labelValue(e.key, e.value)),
              pw.SizedBox(height: 16),
            ],
            if (output.redFlagIndicators.isNotEmpty) ...[
              _redFlagsSection(output.redFlagIndicators),
              pw.SizedBox(height: 16),
            ],
            _sectionHeader('Recommended Action'),
            pw.Container(
              padding: const pw.EdgeInsets.all(12),
              decoration: pw.BoxDecoration(
                color: levelColor.shade(50),
                borderRadius: const pw.BorderRadius.all(pw.Radius.circular(8)),
              ),
              child: pw.Text(
                output.recommendedAction,
                style: pw.TextStyle(fontWeight: pw.FontWeight.bold),
              ),
            ),
            pw.SizedBox(height: 16),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text(
                  'Referral needed: ${output.referralNeeded ? "YES" : "NO"}',
                  style: pw.TextStyle(fontWeight: pw.FontWeight.bold),
                ),
                pw.Text(
                  'Confidence: ${(output.confidenceScore * 100).toStringAsFixed(0)}%',
                ),
              ],
            ),
            pw.Spacer(),
            _footer(),
          ],
        );
      },
    ),
  );

  return doc.save();
}

pw.Widget _triageBanner(TriageLevel level, PdfColor color) {
  return pw.Container(
    width: double.infinity,
    padding: const pw.EdgeInsets.symmetric(horizontal: 20, vertical: 16),
    decoration: pw.BoxDecoration(
      color: color,
      borderRadius: const pw.BorderRadius.all(pw.Radius.circular(8)),
    ),
    child: pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Text(
          'VoiceBridge Triage Report',
          style: pw.TextStyle(
            color: PdfColors.white,
            fontSize: 10,
            fontWeight: pw.FontWeight.normal,
          ),
        ),
        pw.SizedBox(height: 4),
        pw.Text(
          'SATS Level: ${level.label}',
          style: pw.TextStyle(
            color: PdfColors.white,
            fontSize: 22,
            fontWeight: pw.FontWeight.bold,
          ),
        ),
        pw.Text(
          level.waitTime,
          style: const pw.TextStyle(
            color: PdfColors.white,
            fontSize: 13,
          ),
        ),
      ],
    ),
  );
}

pw.Widget _sectionHeader(String text) {
  return pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 6),
    child: pw.Text(
      text,
      style: pw.TextStyle(
        fontSize: 13,
        fontWeight: pw.FontWeight.bold,
        color: const PdfColor(0.07, 0.11, 0.16),
      ),
    ),
  );
}

pw.Widget _labelValue(String label, String value) {
  return pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 4),
    child: pw.RichText(
      text: pw.TextSpan(
        children: [
          pw.TextSpan(
            text: '$label: ',
            style: pw.TextStyle(fontWeight: pw.FontWeight.bold, fontSize: 11),
          ),
          pw.TextSpan(
            text: value,
            style: const pw.TextStyle(fontSize: 11),
          ),
        ],
      ),
    ),
  );
}

pw.Widget _bullet(String text) {
  return pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 3, left: 12),
    child: pw.Row(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Text('• ', style: const pw.TextStyle(fontSize: 11)),
        pw.Expanded(
          child: pw.Text(text, style: const pw.TextStyle(fontSize: 11)),
        ),
      ],
    ),
  );
}

pw.Widget _redFlagsSection(List<String> flags) {
  return pw.Column(
    crossAxisAlignment: pw.CrossAxisAlignment.start,
    children: [
      _sectionHeader('Red Flag Indicators'),
      pw.Container(
        padding: const pw.EdgeInsets.all(12),
        decoration: pw.BoxDecoration(
          color: const PdfColor(0.98, 0.94, 0.94),
          border: pw.Border.all(color: const PdfColor(0.89, 0.29, 0.29)),
          borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6)),
        ),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: flags.map(_bullet).toList(),
        ),
      ),
    ],
  );
}

pw.Widget _footer() {
  return pw.Container(
    padding: const pw.EdgeInsets.only(top: 12),
    decoration: const pw.BoxDecoration(
      border: pw.Border(top: pw.BorderSide(color: PdfColors.grey300)),
    ),
    child: pw.Text(
      'Generated by VoiceBridge v1.0 — For clinical use only. '
      'Not a substitute for professional medical judgement.',
      style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600),
    ),
  );
}

PdfColor _pdfColor(TriageLevel level) {
  switch (level) {
    case TriageLevel.red:
      return const PdfColor(0.89, 0.29, 0.29);
    case TriageLevel.orange:
      return const PdfColor(0.94, 0.62, 0.15);
    case TriageLevel.yellow:
      return const PdfColor(0.94, 0.85, 0.15);
    case TriageLevel.green:
      return const PdfColor(0.39, 0.60, 0.13);
    case TriageLevel.blue:
      return const PdfColor(0.22, 0.54, 0.87);
    case TriageLevel.unknown:
      return PdfColors.grey600;
  }
}

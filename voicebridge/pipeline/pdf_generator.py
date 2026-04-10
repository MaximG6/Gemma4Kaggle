"""
Printable PDF triage form generator (Task 2.3).

Takes a TriageOutput and renders a colour-coded A4 PDF that looks like
a real clinical intake form:
  - Colour-coded triage-level banner (red/orange/yellow/green/blue)
  - Patient details table
  - Vital signs section
  - Red-flag indicators highlighted
  - Recommended action block
  - Footer with facility name, timestamp, and confidence score

Output is raw PDF bytes suitable for a FastAPI StreamingResponse.
"""

from __future__ import annotations

import datetime
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)

from .triage import TriageLevel, TriageOutput

# ---------------------------------------------------------------------------
# Colour palette — one per SATS level
# ---------------------------------------------------------------------------

LEVEL_COLORS: dict[TriageLevel, colors.HexColor] = {
    TriageLevel.RED:    colors.HexColor("#E24B4A"),
    TriageLevel.ORANGE: colors.HexColor("#EF9F27"),
    TriageLevel.YELLOW: colors.HexColor("#EFD927"),
    TriageLevel.GREEN:  colors.HexColor("#639922"),
    TriageLevel.BLUE:   colors.HexColor("#378ADD"),
}

LEVEL_WAIT: dict[TriageLevel, str] = {
    TriageLevel.RED:    "IMMEDIATE — see within seconds",
    TriageLevel.ORANGE: "VERY URGENT — see within 10 minutes",
    TriageLevel.YELLOW: "URGENT — see within 60 minutes",
    TriageLevel.GREEN:  "ROUTINE — see within 4 hours",
    TriageLevel.BLUE:   "EXPECTANT — palliative care",
}

_STYLES = getSampleStyleSheet()

_TITLE_STYLE = ParagraphStyle(
    "VBTitle",
    parent=_STYLES["Title"],
    fontSize=16,
    spaceAfter=4,
)
_NORMAL = _STYLES["Normal"]
_BOLD = ParagraphStyle(
    "VBBold",
    parent=_NORMAL,
    fontName="Helvetica-Bold",
)
_SMALL = ParagraphStyle(
    "VBSmall",
    parent=_NORMAL,
    fontSize=8,
    textColor=colors.grey,
)


def _banner(level: TriageLevel) -> Table:
    """Full-width coloured triage-level banner."""
    bg = LEVEL_COLORS[level]
    text_color = colors.black if level == TriageLevel.YELLOW else colors.white
    cell = Paragraph(
        f"<b>TRIAGE LEVEL: {level.value.upper()}</b><br/>"
        f"<font size='10'>{LEVEL_WAIT[level]}</font>",
        ParagraphStyle(
            "Banner",
            parent=_NORMAL,
            textColor=text_color,
            alignment=1,  # centre
            fontSize=18,
            leading=24,
        ),
    )
    tbl = Table([[cell]], colWidths=[170 * mm])
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ])
    )
    return tbl


def _two_col_table(rows: list[tuple[str, str]]) -> Table:
    """Labelled two-column data table."""
    data = [[Paragraph(f"<b>{k}</b>", _NORMAL), Paragraph(str(v), _NORMAL)]
            for k, v in rows]
    tbl = Table(data, colWidths=[55 * mm, 115 * mm])
    tbl.setStyle(
        TableStyle([
            ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
            ("BACKGROUND",  (0, 0), (0, -1),  colors.HexColor("#F5F5F5")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ])
    )
    return tbl


def _red_flags_table(flags: list[str], level: TriageLevel) -> Table:
    """Red-flag indicators table — highlighted red when RED."""
    if not flags:
        flags = ["None identified"]
    bg = LEVEL_COLORS[level] if level == TriageLevel.RED else colors.HexColor("#FFF3F3")
    text_col = colors.white if level == TriageLevel.RED else colors.HexColor("#C0392B")
    rows = [[Paragraph(f"• {f}", ParagraphStyle("RF", parent=_NORMAL, textColor=text_col))]
            for f in flags]
    tbl = Table(rows, colWidths=[170 * mm])
    tbl.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#FFCCCC")),
        ])
    )
    return tbl


def generate_triage_pdf(
    result: TriageOutput,
    facility: str = "Health Post",
    compress: bool = True,
) -> bytes:
    """
    Render a colour-coded A4 triage form as PDF bytes.

    Args:
        result:   Validated TriageOutput from the classifier.
        facility: Facility name printed in the header.

    Returns:
        Raw PDF bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        compress=compress,
    )

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    vitals_text = (
        ", ".join(f"{k}: {v}" for k, v in result.vital_signs_reported.items())
        or "Not reported"
    )

    els = []

    # Header
    els.append(Paragraph(f"<b>{facility}</b> — Patient Intake Triage Form", _TITLE_STYLE))
    els.append(Paragraph(now, _SMALL))
    els.append(Spacer(1, 6 * mm))

    # Triage level banner
    els.append(_banner(result.triage_level))
    els.append(Spacer(1, 5 * mm))

    # Core details
    els.append(Paragraph("<b>Clinical Summary</b>", _BOLD))
    els.append(Spacer(1, 2 * mm))
    els.append(_two_col_table([
        ("Primary complaint",  result.primary_complaint),
        ("Symptoms",           ", ".join(result.reported_symptoms) or "—"),
        ("Vital signs",        vitals_text),
        ("Duration",           result.duration_of_symptoms),
        ("Relevant history",   result.relevant_history or "None reported"),
        ("Source language",    result.source_language),
    ]))
    els.append(Spacer(1, 5 * mm))

    # Red flags
    els.append(Paragraph("<b>Red Flag Indicators</b>", _BOLD))
    els.append(Spacer(1, 2 * mm))
    els.append(_red_flags_table(result.red_flag_indicators, result.triage_level))
    els.append(Spacer(1, 5 * mm))

    # Recommended action
    els.append(Paragraph("<b>Recommended Action</b>", _BOLD))
    els.append(Spacer(1, 2 * mm))
    action_bg = LEVEL_COLORS[result.triage_level]
    action_text_col = (
        colors.black if result.triage_level == TriageLevel.YELLOW else colors.white
    )
    action_tbl = Table(
        [[Paragraph(result.recommended_action,
                    ParagraphStyle("Act", parent=_NORMAL, textColor=action_text_col))]],
        colWidths=[170 * mm],
    )
    action_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), action_bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    els.append(action_tbl)
    els.append(Spacer(1, 5 * mm))

    # Referral + confidence row
    els.append(_two_col_table([
        ("Referral needed",  "YES — transfer required" if result.referral_needed else "No"),
        ("AI confidence",    f"{result.confidence_score:.0%}"),
    ]))
    els.append(Spacer(1, 8 * mm))

    # Separator + footer
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    els.append(Spacer(1, 2 * mm))
    els.append(Paragraph(
        "Generated by VoiceBridge — offline multilingual clinical intake AI. "
        "This output is a decision-support aid only. Clinical judgement must prevail.",
        _SMALL,
    ))

    doc.build(els)
    return buf.getvalue()

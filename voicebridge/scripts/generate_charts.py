"""
VoiceBridge Benchmark Chart Generator
======================================
Reads docs/model_comparison.json and saves a 6-panel chart to
docs/benchmark_charts.png.

Panels:
  1. Overall metrics comparison bar chart (base vs tuned side by side)
  2. Per-level accuracy comparison (base vs tuned)
  3. Per-language accuracy (tuned only)
  4. Latency from tuned_latency
  5. Delta improvements bar chart
  6. Per-case results heatmap (tuned model)

Usage (from voicebridge/ repo root):
    python scripts/generate_charts.py
    python scripts/generate_charts.py --input docs/model_comparison.json
                                       --output docs/benchmark_charts.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # non-interactive backend — no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------------------------------------------------------------------------
# Colour palette — matches SATS triage colours
# ---------------------------------------------------------------------------

SATS_COLOURS = {
    "red":    "#E24B4A",
    "orange": "#EF9F27",
    "yellow": "#EFD927",
    "green":  "#4CAF50",
    "blue":   "#378ADD",
}

LANG_LABELS = {
    "en": "English", "sw": "Swahili", "tl": "Tagalog",
    "ha": "Hausa",   "bn": "Bengali", "hi": "Hindi",
    "am": "Amharic", "fr": "French",
}

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Colours for base vs tuned series
_BASE_COL  = "#78909C"   # blue-grey
_TUNED_COL = "#42A5F5"   # mid-blue


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def _add_value_labels(ax, bars, fmt="{:.0%}", offset=0.01):
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + offset,
            fmt.format(h),
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )


def panel_overall_comparison(ax, data: dict) -> None:
    """Grouped bar chart: base vs tuned for three headline metrics."""
    base  = data["base"]
    tuned = data["tuned"]

    metric_keys   = ["exact_match_accuracy", "safe_escalation_rate", "validator_agreement"]
    metric_labels = ["Exact\nAccuracy", "Safe\nEscalation", "Validator\nAgreement"]

    x     = np.arange(len(metric_keys))
    width = 0.35

    bars_base  = ax.bar(x - width / 2, [base[k]  for k in metric_keys],
                        width, color=_BASE_COL,  label="Base",  zorder=3)
    bars_tuned = ax.bar(x + width / 2, [tuned[k] for k in metric_keys],
                        width, color=_TUNED_COL, label="Tuned", zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, fontsize=9)
    ax.set_ylim(0, 1.20)
    ax.set_ylabel("Rate", fontsize=10)
    ax.set_title("Overall Metrics", fontsize=11, fontweight="bold")
    ax.axhline(1.0, color="grey", linestyle="--", linewidth=0.8, zorder=2)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", alpha=0.3, zorder=1)
    ax.legend(fontsize=8)

    _add_value_labels(ax, bars_base)
    _add_value_labels(ax, bars_tuned)

    # Unsafe count annotation
    unsafe_t = tuned["unsafe_count"]
    colour = "#E24B4A" if unsafe_t > 0 else "#4CAF50"
    label  = f"Tuned: {unsafe_t} unsafe" if unsafe_t > 0 else "Tuned: 0 unsafe"
    ax.text(0.5, -0.20, label, transform=ax.transAxes,
            ha="center", fontsize=9, color=colour, fontweight="bold")


def panel_per_level_comparison(ax, data: dict) -> None:
    """Grouped bars per SATS level: base vs tuned."""
    base_pl  = data["base"]["per_level"]
    tuned_pl = data["tuned"]["per_level"]

    levels = [l for l in ["red", "orange", "yellow", "green", "blue"]
              if l in tuned_pl]

    x     = np.arange(len(levels))
    width = 0.35

    base_accs  = [base_pl.get(l, {}).get("accuracy", 0)  for l in levels]
    tuned_accs = [tuned_pl[l]["accuracy"] for l in levels]

    bars_base  = ax.bar(x - width / 2, base_accs,  width,
                        color=_BASE_COL,  label="Base",  zorder=3)
    bars_tuned = ax.bar(x + width / 2, tuned_accs, width,
                        color=_TUNED_COL, label="Tuned", zorder=3)

    # Colour the x-tick labels with SATS colours
    ax.set_xticks(x)
    ax.set_xticklabels([l.capitalize() for l in levels], fontsize=9)
    for tick, lv in zip(ax.get_xticklabels(), levels):
        tick.set_color(SATS_COLOURS[lv])
        tick.set_fontweight("bold")

    ax.set_ylim(0, 1.20)
    ax.set_ylabel("Accuracy", fontsize=10)
    ax.set_title("Accuracy by Triage Level", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", alpha=0.3, zorder=1)
    ax.legend(fontsize=8)

    _add_value_labels(ax, bars_base)
    _add_value_labels(ax, bars_tuned)


def panel_per_language(ax, data: dict) -> None:
    """Tuned-only accuracy per language."""
    per_lang = data["tuned"]["per_language"]
    langs    = sorted(per_lang.keys())
    accs     = [per_lang[l]["accuracy"] for l in langs]
    ns       = [per_lang[l]["n"]        for l in langs]
    labels   = [f"{LANG_LABELS.get(l, l.upper())}\n(n={n})"
                for l, n in zip(langs, ns)]

    bars = ax.bar(labels, accs, color=_TUNED_COL, width=0.55, zorder=3)
    ax.set_ylim(0, 1.20)
    ax.set_ylabel("Accuracy", fontsize=10)
    ax.set_title("Accuracy by Language (Tuned)", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", alpha=0.3, zorder=1)
    _add_value_labels(ax, bars)


def panel_latency(ax, data: dict) -> None:
    """Tuned model latency bars vs 8-second target."""
    lat      = data["tuned_latency"]
    hardware = data["meta"].get("hardware", "")
    target   = 8.0

    metrics = {
        "Mean":        lat["mean_s"],
        "Median\n(p50)": lat["median_s"],
        "p95":         lat["p95_s"],
        "Min":         lat["min_s"],
        "Max":         lat["max_s"],
    }
    x    = list(metrics.keys())
    vals = list(metrics.values())
    cols = ["#42A5F5" if v < target else "#EF5350" for v in vals]

    bars = ax.bar(x, vals, color=cols, width=0.5, zorder=3)
    ax.axhline(target, color="#E24B4A", linestyle="--", linewidth=1.2,
               label=f"Target p95 = {target}s", zorder=4)
    ax.set_ylabel("Latency (seconds)", fontsize=10)
    ax.set_title(
        f"Tuned Model Latency\n{hardware}",
        fontsize=11, fontweight="bold",
    )
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3, zorder=1)
    _add_value_labels(ax, bars, fmt="{:.2f}s")

    sim_note = "(simulated)" if data["meta"].get("simulated") else ""
    ax.text(0.5, -0.12, f"10-second audio clip  {sim_note}",
            transform=ax.transAxes, ha="center", fontsize=8, color="grey")


def panel_delta(ax, data: dict) -> None:
    """Bar chart of tuned − base deltas for headline metrics."""
    delta = data["delta"]

    metric_keys   = ["exact_match_accuracy", "safe_escalation_rate", "validator_agreement"]
    metric_labels = ["Exact\nAccuracy", "Safe\nEscalation", "Validator\nAgreement"]
    vals   = [delta[k] for k in metric_keys]
    colours = ["#4CAF50" if v >= 0 else "#E24B4A" for v in vals]

    bars = ax.bar(metric_labels, vals, color=colours, width=0.5, zorder=3)
    ax.axhline(0, color="grey", linewidth=0.8, zorder=2)
    ax.set_ylabel("Δ Rate (tuned − base)", fontsize=10)
    ax.set_title("Delta Improvements", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", alpha=0.3, zorder=1)

    for bar, v in zip(bars, vals):
        sign = "+" if v >= 0 else ""
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + (0.005 if v >= 0 else -0.015),
            f"{sign}{v:.0%}",
            ha="center", va="bottom" if v >= 0 else "top",
            fontsize=9, fontweight="bold",
        )

    # Unsafe count delta as annotation
    unsafe_delta = delta.get("unsafe_count", 0)
    colour = "#4CAF50" if unsafe_delta <= 0 else "#E24B4A"
    label  = f"Unsafe count Δ: {unsafe_delta:+d}"
    ax.text(0.5, -0.20, label, transform=ax.transAxes,
            ha="center", fontsize=9, color=colour, fontweight="bold")


def panel_case_heatmap(ax, data: dict) -> None:
    """Per-case heatmap for the tuned model."""
    cases = data["tuned"]["case_results"]
    ids   = [c["id"] for c in cases]
    cols  = ["Correct", "Safe", "Validator\nSafe"]

    matrix = np.array([
        [int(c["correct"]), int(c["safe"]), int(c["validator_safe"])]
        for c in cases
    ], dtype=float)

    im = ax.imshow(matrix.T, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)

    ax.set_xticks(range(len(ids)))
    ax.set_xticklabels(ids, fontsize=7, rotation=45, ha="right")
    ax.set_yticks(range(len(cols)))
    ax.set_yticklabels(cols, fontsize=9)
    ax.set_title("Per-Case Results (Tuned)", fontsize=11, fontweight="bold")

    # Annotate cells
    for j in range(len(cols)):
        for i, case in enumerate(cases):
            val  = matrix[i, j]
            tick = "✓" if val else "✗"
            colour = "white" if val == 0 else "black"
            ax.text(i, j, tick, ha="center", va="center",
                    fontsize=8, color=colour, fontweight="bold")

    # Predicted label below x-axis ticks
    for i, c in enumerate(cases):
        label = f"{c['predicted'][0].upper()}"
        col   = SATS_COLOURS.get(c["predicted"], "#999")
        ax.text(i, len(cols) - 0.5 + 0.7, label,
                ha="center", va="bottom", fontsize=7,
                color=col, fontweight="bold",
                transform=ax.transData)

    plt.colorbar(im, ax=ax, fraction=0.03, pad=0.04)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_charts(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        print(f"Error: {input_path} not found. Run compare_models.py first.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(input_path.read_text())

    meta     = data.get("meta", {})
    hardware = meta.get("hardware", "")
    n_cases  = meta.get("test_cases", len(data["tuned"]["case_results"]))

    fig = plt.figure(figsize=(20, 12))
    fig.suptitle(
        f"VoiceBridge — Base vs Fine-Tuned Model Comparison\n"
        f"Hardware: {hardware}  |  Test cases: {n_cases}  |  "
        f"Inference: {meta.get('inference', 'llama-cli')}",
        fontsize=13, fontweight="bold", y=0.98,
    )

    gs = fig.add_gridspec(2, 3, hspace=0.55, wspace=0.40)

    ax_overall = fig.add_subplot(gs[0, 0])
    ax_level   = fig.add_subplot(gs[0, 1])
    ax_lang    = fig.add_subplot(gs[0, 2])
    ax_latency = fig.add_subplot(gs[1, 0])
    ax_delta   = fig.add_subplot(gs[1, 1])
    ax_heatmap = fig.add_subplot(gs[1, 2])

    panel_overall_comparison(ax_overall, data)
    panel_per_level_comparison(ax_level, data)
    panel_per_language(ax_lang, data)
    panel_latency(ax_latency, data)
    panel_delta(ax_delta, data)
    panel_case_heatmap(ax_heatmap, data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Charts saved → {output_path.relative_to(_REPO_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate VoiceBridge benchmark charts")
    parser.add_argument(
        "--input",  default=str(_REPO_ROOT / "docs" / "model_comparison.json"),
        help="Path to model_comparison.json",
    )
    parser.add_argument(
        "--output", default=str(_REPO_ROOT / "docs" / "benchmark_charts.png"),
        help="Output PNG path",
    )
    args = parser.parse_args()
    generate_charts(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

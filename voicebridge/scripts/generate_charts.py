"""
VoiceBridge Benchmark Chart Generator
======================================
Reads docs/benchmark_results.json and saves a multi-panel chart to
docs/benchmark_charts.png.

Panels:
  1. Overall metrics bar chart (accuracy, safe rate, validator agreement)
  2. Per-level accuracy
  3. Per-language accuracy
  4. Latency distribution (p50 / p95 vs. 8-second target)
  5. Per-case result heatmap (correct / safe / validator)

Usage (from voicebridge/ repo root):
    python scripts/generate_charts.py
    python scripts/generate_charts.py --input docs/benchmark_results.json
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


def panel_overall(ax, data: dict) -> None:
    acc  = data["accuracy"]
    metrics = {
        "Exact\nAccuracy":     acc["overall"],
        "Safe\nEscalation":    acc["safe_rate"],
        "Validator\nAgreement": acc["validator_agreement"],
    }
    colours = ["#2196F3", "#4CAF50", "#9C27B0"]
    bars = ax.bar(metrics.keys(), metrics.values(), color=colours,
                  width=0.5, zorder=3)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Rate", fontsize=10)
    ax.set_title("Overall Metrics", fontsize=11, fontweight="bold")
    ax.axhline(1.0, color="grey", linestyle="--", linewidth=0.8, zorder=2)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", alpha=0.3, zorder=1)
    _add_value_labels(ax, bars)

    # Unsafe count annotation
    unsafe = acc["unsafe_count"]
    colour = "#E24B4A" if unsafe > 0 else "#4CAF50"
    label  = f"⚠ {unsafe} unsafe under-call(s)" if unsafe > 0 else "✓ 0 unsafe under-calls"
    ax.text(0.5, -0.18, label, transform=ax.transAxes,
            ha="center", fontsize=9, color=colour, fontweight="bold")


def panel_per_level(ax, data: dict) -> None:
    per_level = data["accuracy"]["per_level"]
    levels    = [l for l in ["red", "orange", "yellow", "green", "blue"]
                 if l in per_level]
    accuracies = [per_level[l]["accuracy"] for l in levels]
    colours    = [SATS_COLOURS[l] for l in levels]
    text_cols  = ["white" if l != "yellow" else "#333" for l in levels]

    bars = ax.bar(
        [l.capitalize() for l in levels],
        accuracies,
        color=colours, width=0.55, zorder=3,
    )
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Accuracy", fontsize=10)
    ax.set_title("Accuracy by Triage Level", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", alpha=0.3, zorder=1)

    for bar, acc_val, txt_col in zip(bars, accuracies, text_cols):
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h / 2,
            f"{acc_val:.0%}",
            ha="center", va="center",
            fontsize=10, fontweight="bold", color=txt_col,
        )


def panel_per_language(ax, data: dict) -> None:
    per_lang = data["accuracy"]["per_language"]
    langs    = sorted(per_lang.keys())
    accs     = [per_lang[l]["accuracy"] for l in langs]
    ns       = [per_lang[l]["n"]        for l in langs]
    labels   = [f"{LANG_LABELS.get(l, l.upper())}\n(n={n})"
                for l, n in zip(langs, ns)]

    colours = ["#5C6BC0"] * len(langs)
    bars = ax.bar(labels, accs, color=colours, width=0.55, zorder=3)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Accuracy", fontsize=10)
    ax.set_title("Accuracy by Language", fontsize=11, fontweight="bold")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", alpha=0.3, zorder=1)
    _add_value_labels(ax, bars)


def panel_latency(ax, data: dict) -> None:
    lat = data["latency"]
    target = lat.get("target_p95_s", 8.0)

    metrics = {
        "Mean":   lat["mean_s"],
        "Median\n(p50)": lat["median_s"],
        "p95":    lat["p95_s"],
        "Min":    lat["min_s"],
        "Max":    lat["max_s"],
    }
    x    = list(metrics.keys())
    vals = list(metrics.values())
    cols = ["#42A5F5" if v < target else "#EF5350" for v in vals]

    bars = ax.bar(x, vals, color=cols, width=0.5, zorder=3)
    ax.axhline(target, color="#E24B4A", linestyle="--", linewidth=1.2,
               label=f"Target p95 = {target}s", zorder=4)
    ax.set_ylabel("Latency (seconds)", fontsize=10)
    ax.set_title(
        f"Transcription Latency\n{lat['hardware']}",
        fontsize=11, fontweight="bold",
    )
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3, zorder=1)
    _add_value_labels(ax, bars, fmt="{:.2f}s")

    sim_note = "(simulated)" if lat.get("simulated") else ""
    ax.text(0.5, -0.12, f"10-second audio clip  {sim_note}",
            transform=ax.transAxes, ha="center", fontsize=8, color="grey")


def panel_case_heatmap(ax, data: dict) -> None:
    cases = data["cases"]
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
    ax.set_title("Per-Case Results", fontsize=11, fontweight="bold")

    # Annotate cells
    for j, col_name in enumerate(cols):
        for i, case in enumerate(cases):
            val  = matrix[i, j]
            tick = "✓" if val else "✗"
            colour = "white" if val == 0 else "black"
            ax.text(i, j, tick, ha="center", va="center",
                    fontsize=8, color=colour, fontweight="bold")

    # Add predicted/expected labels below x-axis
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
        print(f"Error: {input_path} not found. Run benchmark.py first.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(input_path.read_text())

    fig = plt.figure(figsize=(18, 12))
    fig.suptitle(
        "VoiceBridge — Benchmark Results (Phase 3.3)\n"
        f"Model: {data['latency']['model']}  |  "
        f"Hardware: {data['latency']['hardware']}",
        fontsize=13, fontweight="bold", y=0.98,
    )

    gs = fig.add_gridspec(2, 3, hspace=0.50, wspace=0.38)

    ax_overall  = fig.add_subplot(gs[0, 0])
    ax_level    = fig.add_subplot(gs[0, 1])
    ax_lang     = fig.add_subplot(gs[0, 2])
    ax_latency  = fig.add_subplot(gs[1, 0])
    ax_heatmap  = fig.add_subplot(gs[1, 1:])

    panel_overall(ax_overall, data)
    panel_per_level(ax_level, data)
    panel_per_language(ax_lang, data)
    panel_latency(ax_latency, data)
    panel_case_heatmap(ax_heatmap, data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Charts saved → {output_path.relative_to(_REPO_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate VoiceBridge benchmark charts")
    parser.add_argument(
        "--input",  default=str(_REPO_ROOT / "docs" / "benchmark_results.json"),
        help="Path to benchmark_results.json",
    )
    parser.add_argument(
        "--output", default=str(_REPO_ROOT / "docs" / "benchmark_charts.png"),
        help="Output PNG path",
    )
    args = parser.parse_args()
    generate_charts(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

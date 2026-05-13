"""
visualization.py
NILM Projekt - Milestone 1
P und Q kombiniert + Einzelgeräte + Ground Truth
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
from config import MODE
from storage import load_data, load_ground_truth
from device_profiles import DEVICE_PROFILES

OUTPUT_FILE = "plots/nilm_visualization.png"

DEVICE_COLORS = {
    "fridge":          "#1f77b4",
    "pc":              "#ff7f0e",
    "washing_machine": "#2ca02c",
    "hairdryer":       "#d62728",
    "ev_charger":      "#9467bd",
    "sync_machine":    "#8c564b",
    "resistive_load":  "#e377c2",
    "pv_inverter":     "#17becf",
    "kettle":          "#bcbd22",
    "laptop":          "#7f7f7f",
}

def get_devices():
    return list(DEVICE_PROFILES.keys())

def plot_pq_fingerprints():
    """P-Q-Fingerprints der Laborgeräte"""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("P-Q-Fingerprints der Laborgeräte", fontsize=14)
    ax.set_xlabel("Wirkleistung P [W]")
    ax.set_ylabel("Blindleistung Q [var]")
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='black', linewidth=0.5)
    ax.axvline(0, color='black', linewidth=0.5)

    for dev, profile in DEVICE_PROFILES.items():
        p_vals = []
        q_vals = []
        for state, vals in profile["states"].items():
            p_vals.append(vals["P_W"])
            q_vals.append(vals["Q_VAR"])
        ax.scatter(p_vals, q_vals, color=DEVICE_COLORS.get(dev, "#aaaaaa"), label=dev, s=50)
        # Linien für Multi-State
        if len(p_vals) > 1:
            ax.plot(p_vals, q_vals, color=DEVICE_COLORS.get(dev, "#aaaaaa"), alpha=0.7)

    ax.legend()
    plt.tight_layout()
    plt.savefig("plots/pq_fingerprints.png", dpi=150)
    plt.close()
    print("  P-Q-Fingerprints gespeichert: plots/pq_fingerprints.png")

def visualize():
    print("=" * 55)
    print(f"  NILM Visualization – Modus: {MODE}")
    print("=" * 55)

    df = load_data()
    df_gt = load_ground_truth() if MODE == "TEST" else pd.DataFrame()
    t = df.index
    devices = get_devices()
    print(f"  Geräte  : {devices}")
    print(f"  Samples : {len(df)}")

    BG      = "#1a1a2e"
    SURFACE = "#16213e"
    GRID    = "#0f3460"
    TEXT    = "#e0e0e0"
    WHITE   = "#ffffff"
    YELLOW  = "#f0c040"

    fig, axes = plt.subplots(2, 1, figsize=(16, 11),
                             facecolor=BG,
                             gridspec_kw={"hspace": 0.50})

    for ax in axes:
        ax.set_facecolor(SURFACE)
        ax.tick_params(colors=TEXT, labelsize=9)
        ax.xaxis.label.set_color(TEXT)
        ax.yaxis.label.set_color(TEXT)
        ax.title.set_color(TEXT)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        ax.grid(True, color=GRID, linewidth=0.5, alpha=0.7)

    # ── Plot 1: P + Q aggregiert in einem Plot (zwei Y-Achsen) ────────────────
    ax1 = axes[0]
    ax1.set_title("Plot 1 – Wirkleistung P & Blindleistung Q (aggregiert)",
                  fontsize=12, pad=10)

    # Linke Y-Achse: P
    ax1.plot(t, df["total_active_power_W"], color=WHITE, linewidth=2.0,
             label="P total [W]", zorder=5)
    ax1.set_ylabel("P [W]", color=WHITE)
    ax1.tick_params(axis="y", colors=WHITE)

    # Rechte Y-Achse: Q
    ax1_q = ax1.twinx()
    ax1_q.set_facecolor(SURFACE)
    ax1_q.tick_params(colors=YELLOW, labelsize=9)
    ax1_q.spines["right"].set_edgecolor(YELLOW)
    ax1_q.plot(t, df["total_reactive_power_VAR"], color=YELLOW, linewidth=1.5,
               linestyle="--", label="Q total [VAR]", zorder=4)
    ax1_q.set_ylabel("Q [VAR]", color=YELLOW)

    # Gemeinsame Legende
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_q.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc="upper right", fontsize=9, facecolor=BG,
               edgecolor=GRID, labelcolor=TEXT, framealpha=0.8)

    # ── Plot 2: Ground Truth Overlay auf aggregiertem Signal ─────────────────────────────
    ax2 = axes[1]
    ax2.set_title("Plot 2 – Ground Truth Overlay auf Aggregat-Signal",
                  fontsize=12, pad=10)
    ax2.plot(t, df["total_active_power_W"], color=WHITE, linewidth=2.0,
             label="P_total (aggregiert)", zorder=5)
    if not df_gt.empty:
        # Bänder für aktive Geräte
        for dev in devices:
            mask = df_gt["active_device"] == dev
            if mask.any():
                y_vals = df["total_active_power_W"].where(mask, 0)
                ax2.fill_between(t, 0, y_vals,
                                 color=DEVICE_COLORS.get(dev, "#aaaaaa"),
                                 alpha=0.3, label=f"{dev} aktiv")
    ax2.set_ylabel("P [W]", color=TEXT)
    ax2.legend(loc="upper right", fontsize=8, facecolor=BG,
               edgecolor=GRID, labelcolor=TEXT, ncol=2, framealpha=0.8)

    # ── X-Achse alle Plots ─────────────────────────────────────────────────────
    for ax in [ax1, ax2]:
        ax.set_xlabel("Zeit", color=TEXT)
        ax.set_xlim(t[0], t[-1])

    fig.suptitle(
        f"NILM – Milestone 1  |  Modus: {MODE}  |  Signal Acquisition & Visualization",
        fontsize=13, color=TEXT, y=0.98, fontweight="bold"
    )

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    plt.close()
    print(f"  Gespeichert : {OUTPUT_FILE}")
    print("=" * 55)

if __name__ == "__main__":
    visualize()
    plot_pq_fingerprints()
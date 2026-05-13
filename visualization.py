"""
visualization.py
NILM Projekt - Milestone 1
P und Q kombiniert + Einzelgeräte + Ground Truth
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from config import PREPROCESSED_CSV, COL_P_TOTAL, COL_Q_TOTAL, COL_TIME, MODE

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

def get_devices(df):
    if MODE == "TEST":
        return [c.replace("_P", "") for c in df.columns
                if c.endswith("_P") and c != COL_P_TOTAL]
    else:
        return [c.replace("appliance_", "").replace("_W", "")
                for c in df.columns if c.startswith("appliance_")]

def get_device_col(dev, signal="P"):
    if MODE == "TEST":
        return f"{dev}_{signal}"
    else:
        return f"appliance_{dev}_W"

def visualize():
    print("=" * 55)
    print(f"  NILM Visualization – Modus: {MODE}")
    print("=" * 55)

    df      = pd.read_csv(PREPROCESSED_CSV)
    t       = df[COL_TIME].values
    devices = get_devices(df)
    print(f"  Geräte  : {devices}")
    print(f"  Samples : {len(df)}")

    BG      = "#1a1a2e"
    SURFACE = "#16213e"
    GRID    = "#0f3460"
    TEXT    = "#e0e0e0"
    WHITE   = "#ffffff"
    YELLOW  = "#f0c040"

    fig, axes = plt.subplots(3, 1, figsize=(16, 15),
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
    ax1.set_title("Plot 1 – Wirkleistung P & Reaktivleistung Q (aggregiert)",
                  fontsize=12, pad=10)

    # Linke Y-Achse: P
    ax1.plot(t, df[COL_P_TOTAL], color=WHITE, linewidth=2.0,
             label=f"P total [W]", zorder=5)
    ax1.set_ylabel("P [W]", color=WHITE)
    ax1.tick_params(axis="y", colors=WHITE)

    # Rechte Y-Achse: Q
    ax1_q = ax1.twinx()
    ax1_q.set_facecolor(SURFACE)
    ax1_q.tick_params(colors=YELLOW, labelsize=9)
    ax1_q.spines["right"].set_edgecolor(YELLOW)
    if COL_Q_TOTAL in df.columns:
        ax1_q.plot(t, df[COL_Q_TOTAL], color=YELLOW, linewidth=1.5,
                   linestyle="--", label="Q total [VAR]", zorder=4)
    ax1_q.set_ylabel("Q [VAR]", color=YELLOW)

    # Gemeinsame Legende
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_q.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc="upper right", fontsize=9, facecolor=BG,
               edgecolor=GRID, labelcolor=TEXT, framealpha=0.8)

    # ── Plot 2: P Einzelgeräte (Linien) ───────────────────────────────────────
    ax2 = axes[1]
    ax2.set_title("Plot 2 – Wirkleistung P: Einzelgeräte",
                  fontsize=12, pad=10)
    ax2.plot(t, df[COL_P_TOTAL], color=WHITE, linewidth=2.0,
             label="P_total (aggregiert)", zorder=5)
    for dev in devices:
        col = get_device_col(dev, "P")
        if col in df.columns:
            ax2.plot(t, df[col],
                     color=DEVICE_COLORS.get(dev, "#aaaaaa"),
                     linewidth=1.0, alpha=0.85, label=dev)
    ax2.set_ylabel("P [W]", color=TEXT)
    ax2.legend(loc="upper right", fontsize=8, facecolor=BG,
               edgecolor=GRID, labelcolor=TEXT, ncol=2, framealpha=0.8)

    # ── Plot 3: Ground Truth – gestapelte Flächen ─────────────────────────────
    ax3 = axes[2]
    ax3.set_title("Plot 3 – Ground Truth: Gestapelte Wirkleistung P",
                  fontsize=12, pad=10)

    pos_devs = [d for d in devices
                if get_device_col(d, "P") in df.columns
                and df[get_device_col(d, "P")].max() > 0]
    neg_devs = [d for d in devices
                if get_device_col(d, "P") in df.columns
                and df[get_device_col(d, "P")].min() < 0]

    if pos_devs:
        stacks = [df[get_device_col(d, "P")].clip(lower=0).values
                  for d in pos_devs]
        colors = [DEVICE_COLORS.get(d, "#aaaaaa") for d in pos_devs]
        ax3.stackplot(t, stacks, labels=pos_devs,
                      colors=colors, alpha=0.85)
    for dev in neg_devs:
        ax3.plot(t, df[get_device_col(dev, "P")],
                 color=DEVICE_COLORS.get(dev, "#aaaaaa"),
                 linewidth=1.5, linestyle="--",
                 label=f"{dev} (Einspeisung)", alpha=0.9)

    ax3.set_ylabel("P [W]", color=TEXT)
    ax3.legend(loc="upper right", fontsize=8, facecolor=BG,
               edgecolor=GRID, labelcolor=TEXT, ncol=2, framealpha=0.8)

    # ── X-Achse alle Plots ─────────────────────────────────────────────────────
    for ax in [ax1, ax2, ax3]:
        ax.set_xlabel("Zeit", color=TEXT)
        ax.set_xlim(t[0], t[-1])
        if MODE == "TEST":
            ticks = np.arange(0, t[-1] + 1, 120)
            ax.set_xticks(ticks)
            ax.set_xticklabels([f"{int(x)}s" for x in ticks],
                                rotation=30, ha="right")

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
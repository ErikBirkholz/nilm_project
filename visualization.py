"""
visualization.py
NILM Projekt - Milestone 1.1
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

INPUT_FILE  = "data/nilm_preprocessed.csv"
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
}

def get_devices(df):
    return [c.replace("_P", "") for c in df.columns
            if c.endswith("_P") and c != "P_total_W"]

def visualize():
    print("=" * 55)
    print("  NILM Visualization – Milestone 1.1")
    print("=" * 55)

    df      = pd.read_csv(INPUT_FILE)
    t       = df["time_s"].values
    devices = get_devices(df)
    print(f"  Geräte  : {devices}")
    print(f"  Samples : {len(df)}")

    BG      = "#1a1a2e"
    SURFACE = "#16213e"
    GRID    = "#0f3460"
    TEXT    = "#e0e0e0"

    fig, axes = plt.subplots(3, 1, figsize=(16, 14),
                             facecolor=BG,
                             gridspec_kw={"hspace": 0.45})

    for ax in axes:
        ax.set_facecolor(SURFACE)
        ax.tick_params(colors=TEXT, labelsize=9)
        ax.xaxis.label.set_color(TEXT)
        ax.yaxis.label.set_color(TEXT)
        ax.title.set_color(TEXT)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        ax.grid(True, color=GRID, linewidth=0.5, alpha=0.7)

    # ── Plot 1: P aggregiert + Einzelgeräte ───────────────────────────────────
    axes[0].set_title("Plot 1 – Wirkleistung P: Gesamt + Einzelgeräte", fontsize=12, pad=10)
    axes[0].plot(t, df["P_total_W"], color="#ffffff", linewidth=2.0,
                 label="P_total (aggregiert)", zorder=5)
    for dev in devices:
        axes[0].plot(t, df[f"{dev}_P"],
                     color=DEVICE_COLORS.get(dev, "#aaaaaa"),
                     linewidth=1.0, alpha=0.85, label=dev)
    axes[0].set_ylabel("P [W]", color=TEXT)
    axes[0].legend(loc="upper right", fontsize=8, facecolor=BG,
                   edgecolor=GRID, labelcolor=TEXT, ncol=2, framealpha=0.8)

    # ── Plot 2: Q aggregiert + Einzelgeräte ───────────────────────────────────
    axes[1].set_title("Plot 2 – Reaktivleistung Q: Gesamt + Einzelgeräte", fontsize=12, pad=10)
    axes[1].plot(t, df["Q_total_VAR"], color="#ffffff", linewidth=2.0,
                 label="Q_total (aggregiert)", zorder=5)
    for dev in devices:
        axes[1].plot(t, df[f"{dev}_Q"],
                     color=DEVICE_COLORS.get(dev, "#aaaaaa"),
                     linewidth=1.0, alpha=0.85, label=dev)
    axes[1].set_ylabel("Q [VAR]", color=TEXT)
    axes[1].legend(loc="upper right", fontsize=8, facecolor=BG,
                   edgecolor=GRID, labelcolor=TEXT, ncol=2, framealpha=0.8)

    # ── Plot 3: Ground Truth – gestapelte Flächen ─────────────────────────────
    axes[2].set_title("Plot 3 – Ground Truth: Gestapelte Wirkleistung P", fontsize=12, pad=10)

    pos_devs = [d for d in devices if df[f"{d}_P"].max() > 0]
    neg_devs = [d for d in devices if df[f"{d}_P"].min() < 0]

    if pos_devs:
        stacks = [df[f"{d}_P"].clip(lower=0).values for d in pos_devs]
        colors = [DEVICE_COLORS.get(d, "#aaaaaa") for d in pos_devs]
        axes[2].stackplot(t, stacks, labels=pos_devs, colors=colors, alpha=0.85)

    for dev in neg_devs:
        axes[2].plot(t, df[f"{dev}_P"],
                     color=DEVICE_COLORS.get(dev, "#aaaaaa"),
                     linewidth=1.5, linestyle="--",
                     label=f"{dev} (Einspeisung)", alpha=0.9)

    axes[2].set_ylabel("P [W]", color=TEXT)
    axes[2].legend(loc="upper right", fontsize=8, facecolor=BG,
                   edgecolor=GRID, labelcolor=TEXT, ncol=2, framealpha=0.8)

    # ── X-Achse ────────────────────────────────────────────────────────────────
    for ax in axes:
        ax.set_xlabel("Zeit [s]", color=TEXT)
        ticks = np.arange(0, t[-1] + 1, 120)
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{int(x)}s" for x in ticks], rotation=30, ha="right")
        ax.set_xlim(t[0], t[-1])

    fig.suptitle("NILM – Milestone 1  |  Signal Acquisition & Visualization",
                 fontsize=14, color=TEXT, y=0.98, fontweight="bold")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    plt.close()

    print(f"  Gespeichert : {OUTPUT_FILE}")
    print("=" * 55)

if __name__ == "__main__":
    visualize()
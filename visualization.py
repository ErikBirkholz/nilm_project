"""
visualization.py
NILM Projekt - Milestone 1
Visualisierung der Messdaten:
  - Gesamtleistung über Zeit (Overall Power)
  - Einzelgeräte (Single Appliances)
  - Harmonics-Spektrum (Fingerabdruck)
  - Erkannte Events
  - Speicherung als PNG
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import os

# ─────────────────────────────────────────────
# KONFIGURATION
# ─────────────────────────────────────────────
PREPROCESSED_CSV = "data/preprocessed_measurements.csv"
EVENTS_CSV       = "data/detected_events.csv"
OUTPUT_DIR       = "plots"

COLORS = {
    "total":   "#01696f",
    "kettle":  "#e05c2a",
    "fridge":  "#4a90d9",
    "laptop":  "#8e44ad",
    "smooth":  "#aaaaaa",
}

def load_data():
    if not os.path.exists(PREPROCESSED_CSV):
        raise FileNotFoundError(
            f"Datei nicht gefunden: {PREPROCESSED_CSV}\n"
            "Bitte zuerst preprocessing.py ausführen!"
        )
    df = pd.read_csv(PREPROCESSED_CSV, parse_dates=["timestamp"], index_col="timestamp")
    events_df = pd.DataFrame()
    if os.path.exists(EVENTS_CSV):
        events_df = pd.read_csv(EVENTS_CSV, parse_dates=["timestamp"], index_col="timestamp")
    print(f"[OK] {len(df)} Datenpunkte geladen | {len(events_df)} Events")
    return df, events_df

def plot_overall_power(df, events_df, ax):
    col_raw    = "total_active_power_W"
    col_smooth = "total_active_power_W_smooth"
    if col_raw not in df.columns:
        ax.text(0.5, 0.5, "Keine Leistungsdaten", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        return
    ax.plot(df.index, df[col_raw], color=COLORS["smooth"],
            alpha=0.35, linewidth=0.8, label="Rohsignal")
    if col_smooth in df.columns:
        ax.plot(df.index, df[col_smooth], color=COLORS["total"],
                linewidth=1.8, label="Geglättet (∅5s)")
    if not events_df.empty:
        on_events  = events_df[events_df["event_type"] == "ON"]
        off_events = events_df[events_df["event_type"] == "OFF"]
        ax.scatter(on_events.index,  on_events["power_after_W"],
                   marker="^", color="#27ae60", s=60, zorder=5, label="Event: ON")
        ax.scatter(off_events.index, off_events["power_after_W"],
                   marker="v", color="#e74c3c", s=60, zorder=5, label="Event: OFF")
    ax.set_title("Gesamtleistung (Overall Power)", fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("Leistung [W]")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=8)

def plot_appliances(df, ax):
    appliance_map = {
        "appliance_kettle_W": ("Wasserkocher", COLORS["kettle"]),
        "appliance_fridge_W": ("Kühlschrank",  COLORS["fridge"]),
        "appliance_laptop_W": ("Laptop",        COLORS["laptop"]),
    }
    found = False
    for col, (label, color) in appliance_map.items():
        if col in df.columns and df[col].notna().any():
            ax.plot(df.index, df[col], color=color, linewidth=1.5, label=label)
            found = True
    if not found:
        ax.text(0.5, 0.5, "Keine Einzelgerätedaten\n(nur mit echtem PAC4200 + Submetern)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=10, color="gray")
    ax.set_title("Einzelgeräte (Single Appliances)", fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("Leistung [W]")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=8)

def plot_harmonics_spectrum(df, ax):
    harmonic_cols = [c for c in df.columns
                     if c.startswith("H") and "current_L1_pct" in c and "_smooth" not in c]
    if not harmonic_cols:
        ax.text(0.5, 0.5, "Keine Harmonics-Daten\n(ENABLE_HARMONICS = False)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=10, color="gray")
        ax.set_title("Harmonics-Spektrum (H2–H31)", fontsize=13, fontweight="bold", pad=10)
        return
    orders, values = [], []
    for col in sorted(harmonic_cols, key=lambda c: int(c.replace("H","").replace("_current_L1_pct",""))):
        order = int(col.replace("H","").replace("_current_L1_pct",""))
        orders.append(order)
        values.append(df[col].mean())
    bar_colors = [COLORS["total"] if o in [3,5,7,11,13] else "#b0c4c4" for o in orders]
    bars = ax.bar(orders, values, color=bar_colors, edgecolor="white", linewidth=0.5)
    for order, val, bar in zip(orders, values, bars):
        if order in [3, 5, 7, 11, 13] and val > 0.5:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f"H{order}", ha="center", va="bottom", fontsize=7,
                    color=COLORS["total"], fontweight="bold")
    ax.set_title("Harmonics-Spektrum (H2–H31, Ø über Messzeit)", fontsize=13,
                 fontweight="bold", pad=10)
    ax.set_xlabel("Harmonische Ordnung")
    ax.set_ylabel("Amplitude [% Grundschwingung]")
    ax.set_xticks(orders[::2])
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")

def plot_harmonics_timeseries(df):
    key_orders = [3, 5, 7, 11, 13]
    cols = [f"H{o}_current_L1_pct" for o in key_orders if f"H{o}_current_L1_pct" in df.columns]
    if not cols:
        print("[INFO] Keine Harmonics-Zeitreihendaten vorhanden.")
        return
    fig, ax = plt.subplots(figsize=(14, 5))
    palette = ["#01696f", "#e05c2a", "#4a90d9", "#8e44ad", "#d4a017"]
    for col, color in zip(cols, palette):
        order = col.replace("H","").replace("_current_L1_pct","")
        smooth_col = f"{col}_smooth"
        series = df[smooth_col] if smooth_col in df.columns else df[col]
        ax.plot(df.index, series, color=color, linewidth=1.5, label=f"H{order}")
    ax.set_title("Harmonics Zeitverlauf (H3, H5, H7, H11, H13)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Amplitude [% Grundschwingung]")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=20, ha="right")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "nilm_harmonics_timeseries.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[OK] Harmonics-Zeitreihe gespeichert: {path}")
    plt.show()

def plot_dashboard(df, events_df):
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle("NILM Milestone 1 – Messdaten Dashboard",
                 fontsize=16, fontweight="bold", y=0.98)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.3)
    ax1 = fig.add_subplot(gs[0, :])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])
    plot_overall_power(df, events_df, ax1)
    plot_appliances(df, ax2)
    plot_harmonics_spectrum(df, ax3)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "nilm_dashboard.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[OK] Dashboard gespeichert: {path}")
    plt.show()

def main():
    print("=" * 50)
    print("  NILM Visualization - Milestone 1")
    print("=" * 50)
    df, events_df = load_data()
    print("[1/2] Erstelle Dashboard...")
    plot_dashboard(df, events_df)
    print("[2/2] Erstelle Harmonics-Zeitreihe...")
    plot_harmonics_timeseries(df)
    print(f"\n[OK] Alle Plots gespeichert in: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
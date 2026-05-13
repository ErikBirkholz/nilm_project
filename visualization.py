"""
visualization.py
NILM Projekt - Milestone 1.5
Visualisierung:
  - Zeitreihenplot mit Ground-Truth-Overlay (farbige Geräte-Balken)
  - P-Q-Diagramm (Fingerabdruck pro Gerät)
  - Harmonics-Spektrum pro Gerät
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import os

# ─────────────────────────────────────────────
# KONFIGURATION
# ─────────────────────────────────────────────
PREPROCESSED_CSV = "data/preprocessed_measurements.csv"
GROUND_TRUTH_CSV = "data/ground_truth.csv"
EVENTS_CSV       = "data/detected_events.csv"
OUTPUT_DIR       = "plots"

DEVICE_COLORS = {
    "fridge":          "#4a90d9",
    "pc":              "#01696f",
    "resistive_load":  "#e05c2a",
    "hairdryer":       "#e74c3c",
    "washing_machine": "#8e44ad",
    "ev_charger":      "#27ae60",
    "pv_inverter":     "#f39c12",
    "sync_machine":    "#c0392b",
    "none":            "#cccccc",
}


# ─────────────────────────────────────────────
# DATEN LADEN
# ─────────────────────────────────────────────
def load_all():
    if not os.path.exists(PREPROCESSED_CSV):
        raise FileNotFoundError(
            "preprocessed_measurements.csv nicht gefunden!\n"
            "Bitte zuerst ausführen:\n"
            "  python data_generator.py\n"
            "  python preprocessing.py"
        )
    df = pd.read_csv(PREPROCESSED_CSV, parse_dates=["timestamp"], index_col="timestamp")

    gt = pd.DataFrame()
    if os.path.exists(GROUND_TRUTH_CSV):
        gt = pd.read_csv(GROUND_TRUTH_CSV, parse_dates=["t_on", "t_off"])

    ev = pd.DataFrame()
    if os.path.exists(EVENTS_CSV):
        ev = pd.read_csv(EVENTS_CSV, parse_dates=["timestamp"], index_col="timestamp")

    print(f"[OK] {len(df)} Samples | {len(gt)} Ground-Truth-Events | {len(ev)} erkannte Events")
    return df, gt, ev


# ─────────────────────────────────────────────
# PLOT 1: ZEITREIHE + GROUND TRUTH OVERLAY
# ─────────────────────────────────────────────
def plot_timeseries_with_groundtruth(df, gt, ev):
    fig, axes = plt.subplots(3, 1, figsize=(16, 12),
                             gridspec_kw={"height_ratios": [3, 1.2, 1]})
    fig.suptitle("NILM Milestone 1 – Zeitreihe mit Ground-Truth-Overlay",
                 fontsize=14, fontweight="bold", y=0.98)

    # ── Subplot 1: Gesamtleistung + Ground Truth Balken ──
    ax1 = axes[0]
    col = "total_active_power_W_smooth" if "total_active_power_W_smooth" in df.columns \
          else "total_active_power_W"

    ax1.plot(df.index, df["total_active_power_W"],
             color="#cccccc", linewidth=0.7, alpha=0.5, label="Rohsignal P")
    ax1.plot(df.index, df[col],
             color="#1a1a2e", linewidth=1.8, label="Geglättet P")

    if "total_reactive_power_VAR" in df.columns:
        ax1.plot(df.index, df["total_reactive_power_VAR"],
                 color="#4a90d9", linewidth=1.2, alpha=0.7,
                 linestyle="--", label="Q (Blindleistung)")

    # Events
    if not ev.empty:
        on_ev  = ev[ev["event_type"] == "ON"]
        off_ev = ev[ev["event_type"] == "OFF"]
        ax1.scatter(on_ev.index,  on_ev["power_after_W"],
                    marker="^", color="#27ae60", s=70, zorder=5, label="Event ON")
        ax1.scatter(off_ev.index, off_ev["power_after_W"],
                    marker="v", color="#e74c3c", s=70, zorder=5, label="Event OFF")

    # Ground Truth farbige Spans
    if not gt.empty:
        y_max = df["total_active_power_W"].max() * 1.1
        for _, row in gt.iterrows():
            color = DEVICE_COLORS.get(row["device"], "#aaaaaa")
            ax1.axvspan(row["t_on"], row["t_off"],
                        alpha=0.15, color=color, linewidth=0)
            mid = row["t_on"] + (row["t_off"] - row["t_on"]) / 2
            ax1.text(mid, y_max * 0.92, row["device"].replace("_", "\n"),
                     ha="center", va="top", fontsize=6.5,
                     color=color, fontweight="bold")

    ax1.set_ylabel("Leistung [W / VAR]")
    ax1.set_title("Gesamtleistung (Overall Power) + Ground Truth", fontsize=11)
    ax1.legend(loc="upper right", fontsize=8, ncol=3)
    ax1.grid(True, alpha=0.3, linestyle="--")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=8)

    # ── Subplot 2: Leistungsfaktor ──
    ax2 = axes[1]
    if "power_factor_calc" in df.columns:
        ax2.plot(df.index, df["power_factor_calc"],
                 color="#01696f", linewidth=1.5, label="cos φ (berechnet)")
    if "power_factor" in df.columns:
        ax2.plot(df.index, df["power_factor"],
                 color="#e05c2a", linewidth=1.0, alpha=0.6,
                 linestyle="--", label="cos φ (gemessen)")
    if not gt.empty:
        for _, row in gt.iterrows():
            color = DEVICE_COLORS.get(row["device"], "#aaaaaa")
            ax2.axvspan(row["t_on"], row["t_off"], alpha=0.10, color=color)
    ax2.set_ylabel("cos φ [ ]")
    ax2.set_ylim(0, 1.05)
    ax2.set_title("Leistungsfaktor", fontsize=10)
    ax2.legend(loc="lower right", fontsize=8)
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=8)

    # ── Subplot 3: THD ──
    ax3 = axes[2]
    if "THD_estimated_pct" in df.columns:
        ax3.fill_between(df.index, df["THD_estimated_pct"],
                         color="#8e44ad", alpha=0.4, label="THD [%]")
        ax3.plot(df.index, df["THD_estimated_pct"],
                 color="#8e44ad", linewidth=1.2)
    if not gt.empty:
        for _, row in gt.iterrows():
            color = DEVICE_COLORS.get(row["device"], "#aaaaaa")
            ax3.axvspan(row["t_on"], row["t_off"], alpha=0.10, color=color)
    ax3.set_ylabel("THD [%]")
    ax3.set_xlabel("Zeit")
    ax3.set_title("THD-Verlauf", fontsize=10)
    ax3.legend(loc="upper right", fontsize=8)
    ax3.grid(True, alpha=0.3, linestyle="--")
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=8)

    # Geräte-Farblegende unten
    patches = [mpatches.Patch(color=DEVICE_COLORS.get(d, "#aaa"),
                               label=d.replace("_", " "), alpha=0.6)
               for d in DEVICE_COLORS if d != "none"]
    fig.legend(handles=patches, loc="lower center", ncol=len(patches),
               fontsize=8, title="Geräte (Ground Truth)", title_fontsize=8,
               bbox_to_anchor=(0.5, 0.01))

    plt.tight_layout(rect=[0, 0.05, 1, 0.97])
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "nilm_timeseries_groundtruth.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[OK] Gespeichert: {path}")
    plt.show()


# ─────────────────────────────────────────────
# PLOT 2: P-Q DIAGRAMM
# ─────────────────────────────────────────────
def plot_pq_diagram(df, gt):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("P-Q Diagramm – Geräte-Fingerabdruck",
                 fontsize=14, fontweight="bold")

    ax1 = axes[0]
    if "appliance_active_device" in df.columns:
        for device in df["appliance_active_device"].unique():
            mask  = df["appliance_active_device"] == device
            color = DEVICE_COLORS.get(device, "#aaaaaa")
            ax1.scatter(df.loc[mask, "total_active_power_W"],
                        df.loc[mask, "total_reactive_power_VAR"],
                        c=color, s=15, alpha=0.5, label=device.replace("_", " "))
    else:
        ax1.scatter(df["total_active_power_W"],
                    df["total_reactive_power_VAR"],
                    c="#01696f", s=10, alpha=0.4)
    ax1.set_xlabel("Wirkleistung P [W]")
    ax1.set_ylabel("Blindleistung Q [VAR]")
    ax1.set_title("Alle Messpunkte (eingefärbt nach Gerät)")
    ax1.legend(loc="upper left", fontsize=7, markerscale=2)
    ax1.grid(True, alpha=0.3, linestyle="--")
    ax1.axhline(0, color="black", linewidth=0.5)
    ax1.axvline(0, color="black", linewidth=0.5)

    ax2 = axes[1]
    if not gt.empty:
        for _, row in gt.drop_duplicates("device").iterrows():
            color = DEVICE_COLORS.get(row["device"], "#aaaaaa")
            ax2.scatter(row["P_W"], row["Q_VAR"],
                        c=color, s=200, zorder=5,
                        edgecolors="black", linewidths=0.8)
            ax2.annotate(row["device"].replace("_", "\n"),
                         (row["P_W"], row["Q_VAR"]),
                         textcoords="offset points", xytext=(8, 4),
                         fontsize=8, color=color, fontweight="bold")

        r_max = max(gt["P_W"].abs().max(), gt["Q_VAR"].abs().max()) * 1.2
        for pf, ls in [(0.8, "--"), (0.9, ":"), (0.95, "-.")]:
            phi = np.arccos(pf)
            ax2.plot([0, r_max * np.cos(phi)], [0, r_max * np.sin(phi)],
                     color="gray", linewidth=0.8, linestyle=ls,
                     label=f"cos φ = {pf}")

    ax2.set_xlabel("Wirkleistung P [W]")
    ax2.set_ylabel("Blindleistung Q [VAR]")
    ax2.set_title("Geräte-Mittelpunkte (aus Profilen)")
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.axvline(0, color="black", linewidth=0.5)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "nilm_pq_diagram.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[OK] Gespeichert: {path}")
    plt.show()


# ─────────────────────────────────────────────
# PLOT 3: HARMONICS HEATMAP PRO GERÄT
# ─────────────────────────────────────────────
def plot_harmonics_spectrum(df):
    h_cols = [c for c in df.columns
              if c.startswith("H") and "_current_L1_pct" in c and "_smooth" not in c]
    if not h_cols:
        print("[INFO] Keine Harmonics-Daten vorhanden.")
        return

    orders  = [int(c.replace("H", "").replace("_current_L1_pct", "")) for c in h_cols]
    devices = []
    if "appliance_active_device" in df.columns:
        devices = [d for d in df["appliance_active_device"].unique() if d != "none"]

    if not devices:
        print("[INFO] Keine Gerätezuordnung vorhanden.")
        return

    # Matrix aufbauen: Zeilen = Geräte, Spalten = Harmonics
    matrix = []
    for device in devices:
        mask = df["appliance_active_device"] == device
        row  = [df.loc[mask, c].mean() if mask.sum() > 0 else 0.0 for c in h_cols]
        matrix.append(row)

    import numpy as np
    data = np.array(matrix)

    fig, ax = plt.subplots(figsize=(18, max(4, len(devices) * 0.8)))
    fig.suptitle("Harmonics-Fingerabdruck pro Gerät (Heatmap)",
                 fontsize=13, fontweight="bold")

    im = ax.imshow(data, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    # Achsenbeschriftung
    ax.set_xticks(range(len(orders)))
    ax.set_xticklabels([f"H{o}" for o in orders], fontsize=8, rotation=45, ha="right")
    ax.set_yticks(range(len(devices)))
    ax.set_yticklabels([d.replace("_", " ") for d in devices], fontsize=10)

    # Werte in Zellen schreiben
    for i in range(len(devices)):
        for j in range(len(orders)):
            val = data[i, j]
            text_color = "white" if val > data.max() * 0.6 else "black"
            ax.text(j, i, f"{val:.1f}",
                    ha="center", va="center",
                    fontsize=7, color=text_color)

    # Wichtige Ordnungen markieren (H3, H5, H7, H11, H13)
    key_orders = [3, 5, 7, 11, 13]
    for ko in key_orders:
        if ko in orders:
            j = orders.index(ko)
            ax.axvline(j - 0.5, color="#01696f", linewidth=1.5, alpha=0.6)
            ax.axvline(j + 0.5, color="#01696f", linewidth=1.5, alpha=0.6)

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Amplitude [% Grundschwingung]", fontsize=9)

    ax.set_xlabel("Harmonische Ordnung", fontsize=10)
    ax.set_ylabel("Gerät", fontsize=10)

    # Legende für markierte Ordnungen
    from matplotlib.lines import Line2D
    legend = [Line2D([0], [0], color="#01696f", linewidth=2,
                     label="Charakteristische Ordnungen (H3,H5,H7,H11,H13)")]
    ax.legend(handles=legend, loc="upper right", fontsize=8)

    plt.tight_layout()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "nilm_harmonics_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[OK] Gespeichert: {path}")
    plt.show()

    # ─────────────────────────────────────────────
# PLOT 4: TIMELINE + CHARAKTERISTIKEN
# ─────────────────────────────────────────────
def plot_timeline(df, gt):
    if gt.empty:
        print("[INFO] Keine Ground-Truth-Daten für Timeline.")
        return

    from device_profiles import DEVICE_PROFILES

    # Eindeutige Geräte aus Ground Truth
    devices = gt["device"].unique().tolist()
    n       = len(devices)

    fig, axes = plt.subplots(2, 1, figsize=(18, 4 + n * 0.7 + 4),
                             gridspec_kw={"height_ratios": [n, 3]})
    fig.suptitle("NILM – Geräte-Timeline mit Charakteristiken",
                 fontsize=14, fontweight="bold", y=0.99)

    # ── Subplot 1: Timeline-Balken ──
    ax1 = axes[0]
    ax1.set_xlim(gt["t_on"].min(), gt["t_off"].max())
    ax1.set_ylim(-0.5, n - 0.5)
    ax1.set_yticks(range(n))
    ax1.set_yticklabels([d.replace("_", " ") for d in devices], fontsize=10)
    ax1.set_title("Geräte-Timeline (Ground Truth)", fontsize=11)
    ax1.grid(True, axis="x", alpha=0.3, linestyle="--")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=8)

    for _, row in gt.iterrows():
        y     = devices.index(row["device"])
        color = DEVICE_COLORS.get(row["device"], "#aaaaaa")
        dur   = (row["t_off"] - row["t_on"]).total_seconds()

        # Balken
        ax1.barh(y, width=row["t_off"] - row["t_on"],
                 left=row["t_on"], height=0.6,
                 color=color, alpha=0.85, edgecolor="white", linewidth=0.8)

        # Charakteristiken als Text im Balken
        profile = DEVICE_PROFILES[row["device"]]["states"][row["state"]]
        label = (f"{row['state']}\n"
                 f"P={profile['P_W']}W  Q={profile['Q_VAR']}VAR\n"
                 f"cosφ={profile['cos_phi']}  THD={profile['THD_pct']}%")
        mid = row["t_on"] + (row["t_off"] - row["t_on"]) / 2
        ax1.text(mid, y, label,
                 ha="center", va="center", fontsize=6.5,
                 color="white" if color not in ["#f39c12", "#e05c2a"] else "black",
                 fontweight="bold", linespacing=1.4)

    # ── Subplot 2: Gesamtleistung darunter (synchron) ──
    ax2 = axes[1]
    col = "total_active_power_W_smooth" if "total_active_power_W_smooth" in df.columns \
          else "total_active_power_W"

    ax2.plot(df.index, df["total_active_power_W"],
             color="#cccccc", linewidth=0.7, alpha=0.5, label="Rohsignal P")
    ax2.plot(df.index, df[col],
             color="#1a1a2e", linewidth=1.8, label="Geglättet P")
    ax2.plot(df.index, df["total_reactive_power_VAR"],
             color="#4a90d9", linewidth=1.2, alpha=0.6,
             linestyle="--", label="Q Blindleistung")

    # Gleiche farbige Spans wie Timeline
    for _, row in gt.iterrows():
        color = DEVICE_COLORS.get(row["device"], "#aaaaaa")
        ax2.axvspan(row["t_on"], row["t_off"], alpha=0.12, color=color)

    ax2.set_xlim(gt["t_on"].min(), gt["t_off"].max())
    ax2.set_ylabel("Leistung [W / VAR]")
    ax2.set_xlabel("Zeit")
    ax2.set_title("Gesamtleistung (synchron zur Timeline)", fontsize=10)
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=8)

    plt.tight_layout()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "nilm_timeline.png")
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"[OK] Gespeichert: {path}")
    plt.show()


# ─────────────────────────────────────────────
# HAUPTPROGRAMM
# ─────────────────────────────────────────────
def main():
    # ... bestehender Code ...
    df, gt, ev = load_all()

    print("\n[1/4] Zeitreihe + Ground-Truth-Overlay...")
    plot_timeseries_with_groundtruth(df, gt, ev)

    print("[2/4] P-Q Diagramm...")
    plot_pq_diagram(df, gt)

    print("[3/4] Harmonics Heatmap...")
    plot_harmonics_spectrum(df)

    print("[4/4] Timeline mit Charakteristiken...")  # ← NEU
    plot_timeline(df, gt)                             # ← NEU

if __name__ == "__main__":
    main()
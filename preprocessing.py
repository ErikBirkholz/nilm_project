"""
preprocessing.py
NILM Projekt - Milestone 1
Vorverarbeitung der Rohdaten:
  - Laden der CSV
  - Bereinigung (fehlende Werte, Ausreißer)
  - Resampling auf einheitlichen Zeittakt
  - Filterung (gleitender Mittelwert)
  - Event-Erkennung (Ein-/Ausschalten von Geräten)
  - Speicherung der verarbeiteten Daten
"""

import pandas as pd
import numpy as np
import os

# ─────────────────────────────────────────────
# KONFIGURATION
# ─────────────────────────────────────────────
INPUT_FILE        = "data/raw_measurements.csv"
OUTPUT_FILE       = "data/preprocessed_measurements.csv"
EVENTS_FILE       = "data/detected_events.csv"

RESAMPLE_INTERVAL = "1s"
WINDOW_SIZE       = 5
EVENT_THRESHOLD_W = 30
OUTLIER_FACTOR    = 3.0

POWER_COLS = [
    "total_active_power_W",
    "total_apparent_power_VA",
    "total_reactive_power_VAR",
]
APPLIANCE_COLS = [
    "appliance_kettle_W",
    "appliance_fridge_W",
    "appliance_laptop_W",
]
HARMONIC_COLS = [f"H{o}_current_L1_pct" for o in range(2, 32)]


# ─────────────────────────────────────────────
# 1. DATEN LADEN
# ─────────────────────────────────────────────
def load_data(filepath):
    print(f"[1/5] Lade Daten aus: {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Datei nicht gefunden: {filepath}\n"
            "Bitte zuerst acquisition.py ausführen!"
        )
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    print(f"      {len(df)} Messwerte geladen | "
          f"Zeitraum: {df.index[0]} → {df.index[-1]}")
    return df


# ─────────────────────────────────────────────
# 2. BEREINIGUNG
# ─────────────────────────────────────────────
def clean_data(df):
    print("[2/5] Bereinigung...")
    original_len = len(df)

    df = df[~df.index.duplicated(keep="first")]

    for col in POWER_COLS + APPLIANCE_COLS:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    for col in POWER_COLS:
        if col in df.columns:
            mean = df[col].mean()
            std  = df[col].std()
            upper = mean + OUTLIER_FACTOR * std
            outliers = df[col] > upper
            df.loc[outliers, col] = np.nan
            if outliers.sum() > 0:
                print(f"      Ausreißer entfernt in {col}: {outliers.sum()} Werte")

    df.interpolate(method="time", inplace=True)
    df.ffill(inplace=True)
    df.bfill(inplace=True)

    print(f"      {original_len - len(df)} Duplikate entfernt | "
          f"{df.isnull().sum().sum()} verbleibende NaN-Werte")
    return df


# ─────────────────────────────────────────────
# 3. RESAMPLING
# ─────────────────────────────────────────────
def resample_data(df):
    print(f"[3/5] Resampling auf {RESAMPLE_INTERVAL}-Takt...")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df_resampled = df[numeric_cols].resample(RESAMPLE_INTERVAL).mean()
    df_resampled.interpolate(method="time", inplace=True)
    print(f"      {len(df_resampled)} Datenpunkte nach Resampling")
    return df_resampled


# ─────────────────────────────────────────────
# 4. FILTERUNG
# ─────────────────────────────────────────────
def filter_data(df):
    print(f"[4/5] Filterung (gleitender Mittelwert, Fenster={WINDOW_SIZE}s)...")

    for col in POWER_COLS:
        if col in df.columns:
            df[f"{col}_smooth"] = (
                df[col]
                .rolling(window=WINDOW_SIZE, center=True, min_periods=1)
                .mean()
                .round(3)
            )

    harmonic_cols_present = [c for c in HARMONIC_COLS if c in df.columns]
    for col in harmonic_cols_present:
        df[f"{col}_smooth"] = (
            df[col]
            .rolling(window=WINDOW_SIZE * 2, center=True, min_periods=1)
            .mean()
            .round(4)
        )

    if "total_active_power_W" in df.columns and "total_apparent_power_VA" in df.columns:
        df["power_factor_calc"] = (
            df["total_active_power_W"] / df["total_apparent_power_VA"]
        ).clip(0, 1).round(4)

    print(f"      Geglättete Spalten erstellt für: {POWER_COLS}")
    return df


# ─────────────────────────────────────────────
# 5. EVENT-ERKENNUNG
# ─────────────────────────────────────────────
def detect_events(df):
    print(f"[5/5] Event-Erkennung (Schwellwert: ±{EVENT_THRESHOLD_W}W)...")
    events = []

    power_col = "total_active_power_W_smooth" if "total_active_power_W_smooth" in df.columns \
                else "total_active_power_W"

    if power_col not in df.columns:
        print("      Keine Leistungsdaten gefunden.")
        return pd.DataFrame()

    diff = df[power_col].diff()

    for ts, delta in diff.items():
        if abs(delta) >= EVENT_THRESHOLD_W:
            event_type = "ON" if delta > 0 else "OFF"
            events.append({
                "timestamp":     ts,
                "event_type":    event_type,
                "power_delta_W": round(delta, 2),
                "power_after_W": round(df.loc[ts, power_col], 2),
            })

    events_df = pd.DataFrame(events)
    if not events_df.empty:
        events_df.set_index("timestamp", inplace=True)

    print(f"      {len(events_df)} Events erkannt "
          f"({(events_df['event_type']=='ON').sum() if not events_df.empty else 0} ON, "
          f"{(events_df['event_type']=='OFF').sum() if not events_df.empty else 0} OFF)")
    return events_df


# ─────────────────────────────────────────────
# SPEICHERUNG
# ─────────────────────────────────────────────
def save_results(df, events_df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_FILE)
    print(f"\n[OK] Vorverarbeitete Daten: {OUTPUT_FILE}")

    if not events_df.empty:
        events_df.to_csv(EVENTS_FILE)
        print(f"[OK] Events gespeichert:   {EVENTS_FILE}")

    print("\n── Zusammenfassung ──────────────────────────")
    print(f"  Datenpunkte:       {len(df)}")
    print(f"  Zeitraum:          {df.index[0]} → {df.index[-1]}")
    if "total_active_power_W" in df.columns:
        print(f"  Ø Gesamtleistung:  {df['total_active_power_W'].mean():.1f} W")
        print(f"  Max Leistung:      {df['total_active_power_W'].max():.1f} W")
    print(f"  Events erkannt:    {len(events_df)}")
    print("─────────────────────────────────────────────")


# ─────────────────────────────────────────────
# HAUPTPROGRAMM
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  NILM Preprocessing - Milestone 1")
    print("=" * 50)

    df = load_data(INPUT_FILE)
    df = clean_data(df)
    df = resample_data(df)
    df = filter_data(df)
    events_df = detect_events(df)
    save_results(df, events_df)

if __name__ == "__main__":
    main()
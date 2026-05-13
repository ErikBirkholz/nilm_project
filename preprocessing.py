"""
preprocessing.py
NILM Projekt - Milestone 1.3 + 1.4
Einheitliche load_data()-Schnittstelle + Preprocessing Pipeline
"""

import pandas as pd
import numpy as np
import os

# ─────────────────────────────────────────────
# KONFIGURATION
# ─────────────────────────────────────────────
RAW_CSV            = "data/raw_measurements.csv"
PREPROCESSED_CSV   = "data/preprocessed_measurements.csv"
EVENTS_CSV         = "data/detected_events.csv"

RESAMPLE_RATE      = "1s"
SMOOTH_WINDOW      = 5
EVENT_THRESHOLD_W  = 30
EVENT_THRESHOLD_VA = 40

NORMALIZE_COLS = [
    "total_active_power_W",
    "total_apparent_power_VA",
    "total_reactive_power_VAR",
    "current_L1_A",
    "power_factor",
]


# ─────────────────────────────────────────────
# 1.3 EINHEITLICHE LOAD_DATA() SCHNITTSTELLE
# ─────────────────────────────────────────────
def load_data(filepath: str = RAW_CSV) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Datei nicht gefunden: {filepath}\n"
            "Bitte zuerst data_generator.py oder acquisition.py ausführen!"
        )
    df = pd.read_csv(filepath, parse_dates=["timestamp"], index_col="timestamp")
    print(f"[OK] {len(df)} Zeilen geladen aus: {filepath}")
    print(f"     Zeitraum: {df.index[0]} → {df.index[-1]}")
    print(f"     Spalten:  {len(df.columns)}")
    df = df.sort_index()
    return df


# ─────────────────────────────────────────────
# 1.4 PREPROCESSING PIPELINE
# ─────────────────────────────────────────────
def resample(df: pd.DataFrame, rate: str = RESAMPLE_RATE) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    df_num = df[num_cols].resample(rate).mean()
    if cat_cols:
        df_cat = df[cat_cols].resample(rate).last()
        df_resampled = pd.concat([df_num, df_cat], axis=1)
    else:
        df_resampled = df_num

    gaps = df_resampled[num_cols].isna().sum().sum()
    print(f"[OK] Resampling auf {rate} → {len(df_resampled)} Samples | Lücken: {gaps}")
    return df_resampled


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    before = df[num_cols].isna().sum().sum()

    df[num_cols] = df[num_cols].interpolate(method="time", limit=5)
    df[num_cols] = df[num_cols].ffill().bfill()

    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    df[cat_cols] = df[cat_cols].ffill().bfill().fillna("unknown")

    after = df[num_cols].isna().sum().sum()
    print(f"[OK] Fehlende Werte: {before} → {after} (interpoliert/gefüllt)")
    return df


def smooth(df: pd.DataFrame, window: int = SMOOTH_WINDOW) -> pd.DataFrame:
    smooth_cols = [
        "total_active_power_W",
        "total_apparent_power_VA",
        "total_reactive_power_VAR",
        "current_L1_A",
    ]
    for col in smooth_cols:
        if col in df.columns:
            df[f"{col}_smooth"] = (
                df[col].rolling(window=window, center=True, min_periods=1).mean()
            )
    print(f"[OK] Glättung: Fenster={window}s auf {len(smooth_cols)} Spalten")
    return df


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    for col in NORMALIZE_COLS:
        if col in df.columns:
            col_min = df[col].min()
            col_max = df[col].max()
            denom = col_max - col_min
            if denom > 0:
                df[f"{col}_norm"] = (df[col] - col_min) / denom
            else:
                df[f"{col}_norm"] = 0.0
    print(f"[OK] Normalisierung: {len(NORMALIZE_COLS)} Spalten → *_norm")
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    P = df["total_active_power_W"]
    S = df["total_apparent_power_VA"]
    Q = df["total_reactive_power_VAR"]

    df["power_factor_calc"] = (P / S.replace(0, np.nan)).clip(0, 1).fillna(1.0)
    df["phi_deg"] = np.degrees(np.arctan2(Q.abs(), P.abs()))

    h_cols = [c for c in df.columns if c.startswith("H")
              and "_current_L1_pct" in c and "_smooth" not in c]
    if h_cols:
        df["THD_estimated_pct"] = df[h_cols].pow(2).sum(axis=1).pow(0.5)

    print(f"[OK] Features: power_factor_calc, phi_deg"
          + (", THD_estimated_pct" if h_cols else ""))
    return df


def detect_events(df: pd.DataFrame) -> pd.DataFrame:
    col_p = "total_active_power_W_smooth" if "total_active_power_W_smooth" in df.columns \
            else "total_active_power_W"
    col_s = "total_apparent_power_VA_smooth" if "total_apparent_power_VA_smooth" in df.columns \
            else "total_apparent_power_VA"

    diff_p = df[col_p].diff().abs()
    diff_s = df[col_s].diff().abs()

    event_mask = (diff_p > EVENT_THRESHOLD_W) | (diff_s > EVENT_THRESHOLD_VA)
    event_idx  = df.index[event_mask]

    events = []
    for ts in event_idx:
        dp = df[col_p].diff().loc[ts]
        events.append({
            "timestamp":     ts,
            "event_type":    "ON" if dp > 0 else "OFF",
            "delta_P_W":     round(dp, 2),
            "delta_S_VA":    round(diff_s.loc[ts], 2),
            "power_after_W": round(df[col_p].loc[ts], 2),
        })

    events_df = pd.DataFrame(events)
    if not events_df.empty:
        events_df = events_df.set_index("timestamp")

    print(f"[OK] Events erkannt: {len(events_df)} "
          f"(ON: {(events_df['event_type']=='ON').sum() if not events_df.empty else 0}, "
          f"OFF: {(events_df['event_type']=='OFF').sum() if not events_df.empty else 0})")
    return events_df


# ─────────────────────────────────────────────
# VOLLSTÄNDIGE PIPELINE
# ─────────────────────────────────────────────
def run_pipeline(input_csv: str = RAW_CSV) -> tuple:
    print("=" * 55)
    print("  NILM Preprocessing – Milestone 1.3 + 1.4")
    print("=" * 55)

    df = load_data(input_csv)
    df = resample(df)
    df = handle_missing(df)
    df = smooth(df)
    df = normalize(df)
    df = add_features(df)
    events_df = detect_events(df)

    os.makedirs("data", exist_ok=True)
    df.to_csv(PREPROCESSED_CSV)
    print(f"\n[OK] Preprocessed: {PREPROCESSED_CSV}  ({len(df)} Zeilen, {len(df.columns)} Spalten)")

    if not events_df.empty:
        events_df.to_csv(EVENTS_CSV)
        print(f"[OK] Events:       {EVENTS_CSV}  ({len(events_df)} Events)")

    return df, events_df


if __name__ == "__main__":
    df, events = run_pipeline()
    print("\n── Feature-Übersicht ────────────────────────────────")
    print(df[["total_active_power_W", "total_reactive_power_VAR",
              "power_factor_calc", "phi_deg"]].describe().round(2))
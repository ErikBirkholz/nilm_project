"""
preprocessing.py
NILM Projekt - Milestone 1
Funktioniert im TEST- und LIVE-Modus via config.py
"""

import pandas as pd
import numpy as np
import os
from config import PREPROCESSED_CSV, MODE
from storage import load_data

SMOOTHING_WINDOW = 5

def preprocess():
    print("=" * 55)
    print(f"  NILM Preprocessing – Modus: {MODE}")
    print("=" * 55)

    df = load_data()
    print(f"  Geladen  : load_data()  ({len(df)} Samples)")
    print(f"  Spalten  : {list(df.columns)}")

    # ── Fehlende Werte ─────────────────────────────────────────────────────────
    df = df.ffill().bfill()

    # ── Glättung (nur numerische Spalten außer Zeitachse) ─────────────────────
    smooth_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    df[smooth_cols] = (
        df[smooth_cols]
        .rolling(window=SMOOTHING_WINDOW, center=True, min_periods=1)
        .mean()
    )
    print(f"  Glättung : rolling mean, window={SMOOTHING_WINDOW}")

    # ── 3σ-Ausreißer-Clipping auf aggregierte Signale ─────────────────────────
    for col in ["total_active_power_W", "total_reactive_power_VAR"]:
        if col in df.columns:
            mu, sigma = df[col].mean(), df[col].std()
            n = ((df[col] < mu - 3*sigma) | (df[col] > mu + 3*sigma)).sum()
            df[col] = df[col].clip(mu - 3*sigma, mu + 3*sigma)
            print(f"  Clipping : {col} → {n} Ausreißer entfernt")

    # ── Speichern ──────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(PREPROCESSED_CSV), exist_ok=True)
    df.to_csv(PREPROCESSED_CSV, float_format="%.4f")
    print(f"  Gespeichert : {PREPROCESSED_CSV}")
    print("=" * 55)

if __name__ == "__main__":
    preprocess()
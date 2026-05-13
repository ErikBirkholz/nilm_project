"""
preprocessing.py
NILM Projekt - Milestone 1.1
"""

import pandas as pd
import numpy as np
import os

INPUT_FILE  = "data/nilm_raw.csv"
OUTPUT_FILE = "data/nilm_preprocessed.csv"
SMOOTHING_WINDOW = 5

def preprocess():
    print("=" * 55)
    print("  NILM Preprocessing – Milestone 1.1")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)
    print(f"  Geladen  : {INPUT_FILE}  ({len(df)} Samples)")
    print(f"  Spalten  : {list(df.columns)}")

    # Fehlende Werte
    df = df.ffill().bfill()

    # Glättung auf alle Spalten außer time_s
    smooth_cols = [c for c in df.columns if c != "time_s"]
    df[smooth_cols] = (
        df[smooth_cols]
        .rolling(window=SMOOTHING_WINDOW, center=True, min_periods=1)
        .mean()
    )
    print(f"  Glättung : rolling mean, window={SMOOTHING_WINDOW}")

    # 3σ-Ausreißer-Clipping nur auf aggregierte Signale
    for col in ["P_total_W", "Q_total_VAR"]:
        if col in df.columns:
            mu, sigma = df[col].mean(), df[col].std()
            n = ((df[col] < mu - 3*sigma) | (df[col] > mu + 3*sigma)).sum()
            df[col] = df[col].clip(mu - 3*sigma, mu + 3*sigma)
            print(f"  Clipping : {col} → {n} Ausreißer entfernt")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, float_format="%.4f")

    print(f"  Gespeichert : {OUTPUT_FILE}")
    print("=" * 55)

if __name__ == "__main__":
    preprocess()
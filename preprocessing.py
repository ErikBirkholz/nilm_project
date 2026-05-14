"""
preprocessing.py
NILM Projekt - Milestone 1

Drei-Stufen-Preprocessing-Pipeline für PAC4200-Messdaten (TEST- und LIVE-Modus):
  1. Forward-Fill / Backward-Fill  — Lückenschluss bei Modbus-Verbindungsabbrüchen
  2. Rolling-Mean-Glättung         — Reduktion von 1-Hz-Abtastrauschen
  3. 3-Sigma-Clipping              — Statistische Ausreißerunterdrückung auf P und Q

Bewusste Vereinfachungen:
  - Keine Normalisierung: Absolutwerte (P, Q) sind das identifizierende Merkmal
    für NILM-Klassifikation; Normalisierung würde die Gerätesignaturen verwischen.
  - Kein Bandpassfilter: 1-Hz-Polling des PAC4200 liefert kein auswertbares
    Frequenzspektrum; Rolling Mean ist ausreichend für diese Abtastrate.
  - TEST-Modus: Forward-Fill und 3-Sigma-Clipping sind bei synthetischen Daten
    ohne Lücken und ohne echte Ausreißer wirkungslos — bleiben aber in der
    Pipeline, damit TEST- und LIVE-Modus denselben Code-Pfad durchlaufen.
"""

import pandas as pd
import numpy as np
import os
from config import PREPROCESSED_CSV, MODE
from storage import load_data

SMOOTHING_WINDOW = 5

def preprocess():
    """
    Lädt Rohdaten via load_data(), wendet die drei Preprocessing-Stufen an
    und speichert das Ergebnis nach PREPROCESSED_CSV.

    Forward-Fill: Im LIVE-Modus mit Modbus TCP sind kurze Verbindungsabbrüche
    (<5 s) normal; ffill() propagiert den letzten validen Messwert.
    bfill() als Fallback für fehlende Werte am Zeitreihen-Anfang.

    Rolling Mean (window=SMOOTHING_WINDOW): Glättet 1-Hz-Abtastrauschen (~2%
    auf P/Q). Zentriert (center=True) vermeidet Phasenverzug. min_periods=1
    verhindert NaN an den Rändern.

    3-Sigma-Clipping: Statistische Ausreißerunterdrückung auf P und Q.
    Bewusst nicht auf Harmonics-Kanäle angewendet, da deren Verteilungen
    typischerweise schief sind und das 3-Sigma-Kriterium (Gauß-Annahme)
    dort nicht zutrifft.

    Keine Normalisierung: Absolutwerte sind das NILM-Identifikationsmerkmal.
    """
    print("=" * 55)
    print(f"  NILM Preprocessing – Modus: {MODE}")
    print("=" * 55)

    df = load_data()
    print(f"  Geladen  : load_data()  ({len(df)} Samples)")
    print(f"  Spalten  : {list(df.columns)}")

    # ── Fehlende Werte ─────────────────────────────────────────────────────────
    # Forward-Fill: Modbus-Drops im LIVE-Modus; im TEST-Modus wirkungslos
    # (synthetische Daten lückenfrei), aber Pipeline-konsistent mit LIVE.
    # Geeignet für kurze Drops (<5 s). Längere Lücken sollten in
    # Milestone 3 als expliziter Datenausfall markiert werden, statt propagiert zu werden.
    df = df.ffill().bfill()

    # ── Glättung (nur numerische Spalten außer Zeitachse) ─────────────────────
    # Rolling Mean auf allen numerischen Kanälen: 1-Hz-Polling erzeugt ~2%
    # Rauschen auf P/Q; window=5 s ist klein genug, um typische Geräteschaltvorgänge
    # nicht zu verschmieren, aber groß genug für effektive Rauschreduktion.
    smooth_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    df[smooth_cols] = (
        df[smooth_cols]
        .rolling(window=SMOOTHING_WINDOW, center=True, min_periods=1)
        .mean()
    )
    print(f"  Glättung : rolling mean, window={SMOOTHING_WINDOW}")

    # ── 3-Sigma-Ausreißer-Clipping auf aggregierte Signale ────────────────────
    # Nur auf P und Q: Harmonics-Kanäle haben typischerweise schiefe Verteilungen;
    # das 3-Sigma-Kriterium (Gauß-Annahme) trifft dort nicht zu.
    for col in ["total_active_power_W", "total_reactive_power_VAR"]:
        if col in df.columns:
            mu, sigma = df[col].mean(), df[col].std()
            n = ((df[col] < mu - 3*sigma) | (df[col] > mu + 3*sigma)).sum()
            df[col] = df[col].clip(mu - 3*sigma, mu + 3*sigma)
            print(f"  Clipping : {col} -> {n} Ausreißer entfernt")

    # ── Speichern ──────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(PREPROCESSED_CSV), exist_ok=True)
    df.to_csv(PREPROCESSED_CSV, float_format="%.4f")
    print(f"  Gespeichert : {PREPROCESSED_CSV}")
    print("=" * 55)

if __name__ == "__main__":
    preprocess()

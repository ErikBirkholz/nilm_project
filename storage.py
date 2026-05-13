"""
storage.py
NILM Projekt - Milestone 1
Datenspeicherung in SQLite-Datenbank:
  - Messdaten (preprocessed)
  - Events
  - Abfrage-Funktionen für spätere Auswertung
"""

import sqlite3
import pandas as pd
import os

# ─────────────────────────────────────────────
# KONFIGURATION
# ─────────────────────────────────────────────
DB_FILE             = "data/nilm.db"
PREPROCESSED_CSV    = "data/preprocessed_measurements.csv"
EVENTS_CSV          = "data/detected_events.csv"


# ─────────────────────────────────────────────
# DATENBANKVERBINDUNG
# ─────────────────────────────────────────────
def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ─────────────────────────────────────────────
# TABELLEN ERSTELLEN
# ─────────────────────────────────────────────
def create_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            timestamp                TEXT PRIMARY KEY,
            total_active_power_W     REAL,
            total_apparent_power_VA  REAL,
            total_reactive_power_VAR REAL,
            voltage_L1_V             REAL,
            voltage_L2_V             REAL,
            voltage_L3_V             REAL,
            current_L1_A             REAL,
            current_L2_A             REAL,
            current_L3_A             REAL,
            frequency_Hz             REAL,
            power_factor             REAL,
            power_factor_calc        REAL,
            appliance_kettle_W       REAL,
            appliance_fridge_W       REAL,
            appliance_laptop_W       REAL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS harmonics (
            timestamp       TEXT,
            harmonic_order  INTEGER,
            value_pct       REAL,
            value_smooth    REAL,
            PRIMARY KEY (timestamp, harmonic_order),
            FOREIGN KEY (timestamp) REFERENCES measurements(timestamp)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            timestamp     TEXT PRIMARY KEY,
            event_type    TEXT,
            power_delta_W REAL,
            power_after_W REAL
        )
    """)

    conn.commit()
    print("[OK] Tabellen erstellt/geprüft: measurements, harmonics, events")


# ─────────────────────────────────────────────
# MESSDATEN SPEICHERN
# ─────────────────────────────────────────────
def store_measurements(conn, df):
    print("[1/3] Speichere Messdaten...")

    base_cols = [
        "total_active_power_W", "total_apparent_power_VA", "total_reactive_power_VAR",
        "voltage_L1_V", "voltage_L2_V", "voltage_L3_V",
        "current_L1_A", "current_L2_A", "current_L3_A",
        "frequency_Hz", "power_factor", "power_factor_calc",
        "appliance_kettle_W", "appliance_fridge_W", "appliance_laptop_W",
    ]
    available_cols = [c for c in base_cols if c in df.columns]
    df_base = df[available_cols].copy()
    df_base.index.name = "timestamp"
    df_base.to_sql("measurements", conn, if_exists="append", index=True)

    # Harmonics separat speichern
    harmonic_cols = [c for c in df.columns if c.startswith("H") and "_smooth" not in c
                     and "current_L1_pct" in c]

    if harmonic_cols:
        harmonic_rows = []
        for col in harmonic_cols:
            order = int(col.replace("H", "").replace("_current_L1_pct", ""))
            smooth_col = f"{col}_smooth"
            
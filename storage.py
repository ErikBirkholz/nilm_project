"""
storage.py
NILM Projekt - Milestone 1
Funktioniert im TEST- und LIVE-Modus via config.py
"""

import sqlite3
import pandas as pd
import os
from config import RAW_CSV, DB_FILE, MODE

HARMONICS_ORDERS = list(range(2, 32))

def load_data(mode: str = None) -> pd.DataFrame:
    """
    Lädt Messdaten unabhängig von der Quelle (TEST/LIVE).
    
    Returns: DataFrame mit PAC4200-Schema, indexiert nach timestamp.
    """
    if mode is None:
        mode = MODE
    
    if mode == "TEST":
        csv_file = "data/raw_measurements.csv"  # Nach Generierung
    else:  # LIVE
        csv_file = "data/raw_measurements.csv"  # Gleicher Name
    
    df = pd.read_csv(csv_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df

def load_ground_truth() -> pd.DataFrame:
    """
    Lädt Ground-Truth-Daten (nur für TEST-Modus verfügbar).
    
    Returns: DataFrame mit timestamp, active_device, active_state oder leerer DataFrame für LIVE.
    """
    if MODE == "TEST":
        df = pd.read_csv("data/ground_truth.csv")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df
    else:
        return pd.DataFrame()  # Leer für LIVE

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def create_tables(conn):
    # TEST-Modus Tabelle
    conn.execute("""
        CREATE TABLE IF NOT EXISTS measurements_test (
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
            power_factor             REAL
        )
    """)

    # LIVE-Modus Tabelle
    conn.execute("""
        CREATE TABLE IF NOT EXISTS measurements_live (
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
            power_factor             REAL
        )
    """)

    # Harmonics (nur LIVE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS harmonics (
            timestamp      TEXT,
            harmonic_order INTEGER,
            value_pct      REAL,
            PRIMARY KEY (timestamp, harmonic_order)
        )
    """)

    # Events (beide Modi)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT,
            event_type    TEXT,
            device        TEXT,
            power_delta_W REAL,
            power_after_W REAL
        )
    """)

    conn.commit()
    print(f"[OK] Tabellen erstellt/geprüft (Modus: {MODE})")

def store_from_csv(conn):
    print(f"[1/2] Lade: {RAW_CSV}")
    df = pd.read_csv(RAW_CSV)
    print(f"      {len(df)} Zeilen, {len(df.columns)} Spalten")

    measurement_cols = [
        "timestamp",
        "total_active_power_W", "total_apparent_power_VA",
        "total_reactive_power_VAR",
        "voltage_L1_V", "voltage_L2_V", "voltage_L3_V",
        "current_L1_A", "current_L2_A", "current_L3_A",
        "frequency_Hz", "power_factor",
    ]

    available = [c for c in measurement_cols if c in df.columns]
    # TEST-Modus überschreibt — bei jedem Aufruf wird die DB mit aktuellen
    # synthetischen Daten neu gefüllt. DELETE behält Tabellenstruktur und Constraints.
    if MODE == "TEST":
        conn.execute("DELETE FROM measurements_test")
        conn.execute("DELETE FROM harmonics")
        conn.commit()
        df[available].drop_duplicates(subset="timestamp").to_sql(
            "measurements_test", conn, if_exists="append", index=False
        )
        print(f"[OK] {len(df)} Zeilen -> measurements_test")
    else:  # LIVE
        conn.execute("DELETE FROM measurements_live")
        conn.execute("DELETE FROM harmonics")
        conn.commit()
        df[available].drop_duplicates(subset="timestamp").to_sql(
            "measurements_live", conn, if_exists="append", index=False
        )
        print(f"[OK] {len(df)} Zeilen -> measurements_live")

    # Harmonics
    harm_cols = [c for c in df.columns if c.endswith("_current_L1_pct")]
    if harm_cols:
        rows = []
        for _, row in df.iterrows():
            for col in harm_cols:
                order = int(col.replace("H", "").replace("_current_L1_pct", ""))
                rows.append({
                    "timestamp":      row["timestamp"],
                    "harmonic_order": order,
                    "value_pct":      row[col],
                })
        pd.DataFrame(rows).to_sql("harmonics", conn,
                                  if_exists="append", index=False)
        print(f"[OK] {len(rows)} Harmonics-Zeilen gespeichert")

def insert_measurement(conn, data: dict):
    """Live-Einfügen eines Einzelmesswerts (für acquisition.py)."""
    if MODE != "LIVE":
        return
    base_cols = [
        "timestamp",
        "total_active_power_W", "total_apparent_power_VA",
        "total_reactive_power_VAR",
        "voltage_L1_V", "voltage_L2_V", "voltage_L3_V",
        "current_L1_A", "current_L2_A", "current_L3_A",
        "frequency_Hz", "power_factor",
    ]
    base = {k: data.get(k) for k in base_cols}
    cols = ", ".join(base.keys())
    vals = ", ".join(["?"] * len(base))
    conn.execute(
        f"INSERT OR IGNORE INTO measurements_live ({cols}) VALUES ({vals})",
        list(base.values())
    )
    for order in HARMONICS_ORDERS:
        key = f"H{order}_current_L1_pct"
        if key in data and data[key] is not None:
            conn.execute(
                "INSERT OR IGNORE INTO harmonics VALUES (?,?,?)",
                (data["timestamp"], order, data[key])
            )
    conn.commit()

def print_summary(conn):
    print("=" * 55)
    print(f"  NILM Storage – Übersicht (Modus: {MODE})")
    print("=" * 55)
    if MODE == "TEST":
        n = conn.execute("SELECT COUNT(*) FROM measurements_test").fetchone()[0]
        print(f"  measurements_test : {n} Einträge")
    else:
        n = conn.execute("SELECT COUNT(*) FROM measurements_live").fetchone()[0]
        h = conn.execute("SELECT COUNT(*) FROM harmonics").fetchone()[0]
        print(f"  measurements_live : {n} Einträge")
        print(f"  harmonics         : {h} Einträge")
    e = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"  events            : {e} Einträge")
    print(f"  Datei             : {DB_FILE}")
    print("=" * 55)

def main():
    conn = get_connection()
    create_tables(conn)
    store_from_csv(conn)
    print_summary(conn)
    conn.close()

if __name__ == "__main__":
    main()
"""
config.py
NILM Projekt - Zentraler Pipeline-Schalter
"""

# ── Hier umschalten: "TEST" oder "LIVE" ───────────────────────────────────────
MODE = "LIVE"   # "TEST" = data_generator | "LIVE" = acquisition.py

# ── Pfade ──────────────────────────────────────────────────────────────────────
if MODE == "TEST":
    RAW_CSV          = "data/nilm_raw.csv"
    PREPROCESSED_CSV = "data/nilm_preprocessed.csv"
    COL_P_TOTAL      = "P_total_W"
    COL_Q_TOTAL      = "Q_total_VAR"
    COL_TIME         = "time_s"
else:  # LIVE
    RAW_CSV          = "data/raw_measurements.csv"
    PREPROCESSED_CSV = "data/nilm_preprocessed_live.csv"
    COL_P_TOTAL      = "total_active_power_W"
    COL_Q_TOTAL      = "total_reactive_power_VAR"
    COL_TIME         = "timestamp"

DB_FILE = "data/nilm.db"
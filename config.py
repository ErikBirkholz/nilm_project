"""
config.py
NILM Projekt - Zentraler Pipeline-Schalter
"""

# ── Hier umschalten: "TEST" oder "LIVE" ───────────────────────────────────────
MODE = "TEST"   # "TEST" = data_generator | "LIVE" = acquisition.py

# ── Pfade ──────────────────────────────────────────────────────────────────────
if MODE == "TEST":
    RAW_CSV          = "data/raw_measurements.csv"
    PREPROCESSED_CSV = "data/nilm_preprocessed.csv"
else:  # LIVE
    RAW_CSV          = "data/raw_measurements.csv"
    PREPROCESSED_CSV = "data/nilm_preprocessed_live.csv"

DB_FILE = "data/nilm.db"
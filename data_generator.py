"""
data_generator.py
NILM Projekt - Milestone 1.1
"""

import numpy as np
import pandas as pd
import os
from device_profiles import DEVICE_PROFILES

OUTPUT_FILE = "data/nilm_raw.csv"
SAMPLE_RATE = 1       # Hz
DURATION    = 1200    # Sekunden
NOISE_PCT   = 0.02
RANDOM_SEED = 42

SCHEDULE = [
    (   0, 1200, "fridge",          "COMPRESSOR_ON"),
    ( 120,  900, "pc",              "NORMAL"),
    ( 200,  700, "washing_machine", "WASH"),
    ( 700,  950, "washing_machine", "SPIN"),
    ( 300,  600, "hairdryer",       "HOT"),
    ( 450,  750, "ev_charger",      "MODE2_16A"),
    ( 600,  900, "sync_machine",    "MOTOR_HALF"),
    ( 700, 1000, "resistive_load",  "100PCT"),
    ( 800, 1100, "pv_inverter",     "MEDIUM"),
]

def add_noise(value, pct, rng):
    sigma = abs(value) * pct if value != 0 else 1.0
    return value + rng.normal(0, sigma)

def generate():
    print("=" * 55)
    print("  NILM Data Generator – Milestone 1.1")
    print("=" * 55)

    rng       = np.random.default_rng(RANDOM_SEED)
    t_array   = np.arange(0, DURATION, 1.0 / SAMPLE_RATE)
    n_samples = len(t_array)

    P_agg = np.zeros(n_samples)
    Q_agg = np.zeros(n_samples)

    df = pd.DataFrame({"time_s": t_array})

    devices_in_schedule = list({d for _, _, d, _ in SCHEDULE})
    for dev in devices_in_schedule:
        df[f"{dev}_P"] = 0.0
        df[f"{dev}_Q"] = 0.0

    for start, end, device, state in SCHEDULE:
        mask    = (t_array >= start) & (t_array < end)
        profile = DEVICE_PROFILES[device]["states"][state]
        p_val   = float(profile["P_W"])
        q_val   = float(profile["Q_VAR"])

        df.loc[mask, f"{device}_P"] += p_val
        df.loc[mask, f"{device}_Q"] += q_val
        P_agg[mask] += p_val
        Q_agg[mask] += q_val

        print(f"  [{start:4d}s–{end:4d}s]  {device:<18} {state:<14} "
              f"P={p_val:>7.0f} W")

    P_noisy = np.array([add_noise(v, NOISE_PCT, rng) for v in P_agg])
    Q_noisy = np.array([add_noise(v, NOISE_PCT, rng) for v in Q_agg])

    df.insert(1, "P_total_W",   P_noisy)
    df.insert(2, "Q_total_VAR", Q_noisy)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, float_format="%.4f")

    print(f"\n  Samples : {n_samples}")
    print(f"  Datei   : {OUTPUT_FILE}")
    print("=" * 55)

if __name__ == "__main__":
    generate()
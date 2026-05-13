"""
data_generator.py
NILM Projekt - Milestone 1.2
Synthetischer Datengenerator:
  - Zeitplanbasiertes Ein-/Ausschalten der Laborgeräte
  - Aggregiertes Zeitsignal (Overall Power)
  - Realistisches Messrauschen
  - Ground-Truth-Tabelle (welches Gerät wann aktiv)
  - Kein gleichzeitiges Schalten (Concurrent Events ausgeschlossen)
  - CSV-Export identisch zum PAC4200-Format
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from device_profiles import DEVICE_PROFILES, get_profile

# ─────────────────────────────────────────────
# KONFIGURATION
# ─────────────────────────────────────────────
OUTPUT_CSV       = "data/raw_measurements.csv"
GROUND_TRUTH_CSV = "data/ground_truth.csv"
START_TIME       = datetime(2026, 5, 14, 8, 0, 0)
SAMPLE_INTERVAL  = 1        # Sekunden
NOISE_FACTOR     = 0.02     # 2% Rauschen
HARMONICS_ORDER  = list(range(2, 32))

# ─────────────────────────────────────────────
# ZEITPLAN
# (t_on_sec, t_off_sec, device, state)
# Kein überlappender Zeitraum → kein Concurrent Switching!
# ─────────────────────────────────────────────
SCHEDULE = [
    (   10,   60,  "fridge",          "COMPRESSOR_ON"),
    (   70,  130,  "pc",              "IDLE"),
    (  140,  200,  "pc",              "NORMAL"),
    (  210,  270,  "resistive_load",  "50PCT"),
    (  280,  340,  "hairdryer",       "WARM"),
    (  350,  410,  "washing_machine", "WASH"),
    (  420,  480,  "washing_machine", "SPIN"),
    (  490,  550,  "ev_charger",      "MODE2_16A"),
    (  560,  620,  "pv_inverter",     "MEDIUM"),
    (  630,  690,  "sync_machine",    "MOTOR_HALF"),
    (  700,  760,  "fridge",          "COMPRESSOR_ON"),
    (  770,  830,  "pc",              "FULL"),
    (  840,  900,  "hairdryer",       "HOT"),
    (  910,  970,  "washing_machine", "HEAT"),
    (  980, 1040,  "ev_charger",      "TAPER"),
    ( 1050, 1110,  "resistive_load",  "100PCT"),
    ( 1120, 1180,  "sync_machine",    "MOTOR_FULL"),
    ( 1190, 1250,  "pv_inverter",     "HIGH"),
]

TOTAL_DURATION = 1300  # Sekunden


# ─────────────────────────────────────────────
# HILFSFUNKTIONEN
# ─────────────────────────────────────────────
def add_noise(value, factor=NOISE_FACTOR):
    sigma = abs(value) * factor + 0.5
    return value + np.random.normal(0, sigma)

def get_active_state(t_sec):
    for t_on, t_off, device, state in SCHEDULE:
        if t_on <= t_sec < t_off:
            return device, state
    return None, "OFF"

def get_harmonics(profile: dict) -> dict:
    thd = profile["THD_pct"]
    h3  = profile["H3_pct"]
    h5  = profile["H5_pct"]
    h7  = profile["H7_pct"]
    harmonics = {}
    for order in HARMONICS_ORDER:
        if order == 3:
            val = h3
        elif order == 5:
            val = h5
        elif order == 7:
            val = h7
        else:
            val = thd * (1.0 / order) * 0.5
        harmonics[order] = round(max(0, add_noise(val, 0.05)), 3)
    return harmonics


# ─────────────────────────────────────────────
# MESSWERT ERZEUGEN
# ─────────────────────────────────────────────
def generate_sample(t_sec: int, timestamp: datetime) -> dict:
    device, state = get_active_state(t_sec)

    if device is not None:
        profile = get_profile(device, state)
    else:
        profile = {"P_W": 5, "Q_VAR": 2, "cos_phi": 0.99,
                   "THD_pct": 0.5, "H3_pct": 0.1, "H5_pct": 0.1, "H7_pct": 0.1}

    P  = add_noise(profile["P_W"])
    Q  = add_noise(profile["Q_VAR"])
    S  = np.sqrt(P**2 + Q**2)
    pf = abs(P) / S if S > 0 else 1.0
    I  = S / 230.0 if S > 0 else 0.0

    sample = {
        "timestamp":                timestamp.isoformat(),
        "total_active_power_W":     round(P, 2),
        "total_apparent_power_VA":  round(S, 2),
        "total_reactive_power_VAR": round(Q, 2),
        "voltage_L1_V":             round(add_noise(230.0, 0.005), 2),
        "voltage_L2_V":             round(add_noise(230.0, 0.005), 2),
        "voltage_L3_V":             round(add_noise(230.0, 0.005), 2),
        "current_L1_A":             round(max(0, add_noise(I, 0.02)), 3),
        "current_L2_A":             round(max(0, add_noise(I * 0.99, 0.02)), 3),
        "current_L3_A":             round(max(0, add_noise(I * 1.01, 0.02)), 3),
        "frequency_Hz":             round(add_noise(50.0, 0.001), 3),
        "power_factor":             round(min(1.0, max(0.0, add_noise(pf, 0.005))), 4),
        "appliance_active_device":  device if device else "none",
        "appliance_active_state":   state,
        "appliance_active_P_W":     round(P, 2) if device else 0.0,
    }

    harmonics = get_harmonics(profile)
    for order, val in harmonics.items():
        sample[f"H{order}_current_L1_pct"] = val

    return sample


# ─────────────────────────────────────────────
# GROUND TRUTH TABELLE
# ─────────────────────────────────────────────
def build_ground_truth() -> pd.DataFrame:
    rows = []
    for t_on, t_off, device, state in SCHEDULE:
        ts_on  = START_TIME + timedelta(seconds=t_on)
        ts_off = START_TIME + timedelta(seconds=t_off)
        profile = get_profile(device, state)
        rows.append({
            "t_on":    ts_on.isoformat(),
            "t_off":   ts_off.isoformat(),
            "device":  device,
            "state":   state,
            "P_W":     profile["P_W"],
            "Q_VAR":   profile["Q_VAR"],
            "cos_phi": profile["cos_phi"],
            "THD_pct": profile["THD_pct"],
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# HAUPTPROGRAMM
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  NILM Datengenerator – Milestone 1.2")
    print(f"  Startzeit:  {START_TIME}")
    print(f"  Dauer:      {TOTAL_DURATION}s ({TOTAL_DURATION//60} min)")
    print(f"  Abtastrate: {SAMPLE_INTERVAL}s → {TOTAL_DURATION} Samples")
    print("=" * 60)

    os.makedirs("data", exist_ok=True)

    samples = []
    for t in range(TOTAL_DURATION):
        ts = START_TIME + timedelta(seconds=t)
        sample = generate_sample(t, ts)
        samples.append(sample)
        if t % 100 == 0:
            dev, state = get_active_state(t)
            print(f"  t={t:4d}s | {dev or 'NONE':<20} {state:<15} | "
                  f"P={sample['total_active_power_W']:8.1f}W")

    df = pd.DataFrame(samples)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n[OK] Messdaten:   {OUTPUT_CSV}  ({len(df)} Zeilen)")

    gt = build_ground_truth()
    gt.to_csv(GROUND_TRUTH_CSV, index=False)
    print(f"[OK] Ground Truth: {GROUND_TRUTH_CSV}  ({len(gt)} Events)")

if __name__ == "__main__":
    main()
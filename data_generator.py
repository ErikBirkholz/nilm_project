"""
data_generator.py
NILM Projekt - Milestone 1.2
Generiert synthetische Daten im exakten PAC4200-Schema für TEST-Modus.

Annahmen für die Simulation:
- Netzspannung: U_L-N = 230 V nominal ±0.5% Rauschen, U_L-L = 400 V (sqrt(3)*230 ≈ 398.4)
- Frequenz: 50 Hz ±0.05 Hz Rauschen
- Phasenverteilung: Einphasige Geräte (PC, resistive_load, hairdryer, washing_machine, fridge, ev_charger, pv_inverter) laufen ausschließlich auf L1 (I_L2 = I_L3 = 0, U_L2/L3 nominal)
- Dreiphasige Geräte: Synchronmaschine läuft symmetrisch dreiphasig (I_L1 = I_L2 = I_L3, U_L1 = U_L2 = U_L3)
- cos_phi: Aus Geräteprofil übernommen, gilt für die aktive Phase(n)
- THD_U: Realistisch klein (1-2%), da Labornetz sauber; Geräte beeinflussen primär THD_I
- THD_I und Harmonics H3/H5/H7: Gewichtet aus aktiven Geräteprofilen nach Stromanteil (I_L1 als Gewicht)
- Wenn mehrere Geräte aktiv (Concurrent Events ausgeschlossen in Phase 1), gewichtete Mittelung
- Rauschen: 2% auf P/Q, 0.5% auf U/f, 10% auf THD/Harmonics
"""

import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
from device_profiles import DEVICE_PROFILES

OUTPUT_FILE = "data/raw_measurements.csv"
GROUND_TRUTH_FILE = "data/ground_truth.csv"
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
    print("  NILM Data Generator – Milestone 1.2")
    print("=" * 55)

    rng       = np.random.default_rng(RANDOM_SEED)
    start_time = datetime(2026, 5, 13, 18, 0, 0)  # Beispiel-Startzeit
    t_array   = [start_time + timedelta(seconds=i) for i in range(DURATION)]
    n_samples = len(t_array)

    # Grundsignale
    U_LN_nominal = 230.0
    U_LL_nominal = 400.0  # sqrt(3)*230 ≈ 398.4, gerundet
    f_nominal = 50.0

    # DataFrames initialisieren
    df = pd.DataFrame()
    df_gt = pd.DataFrame()

    P_agg = np.zeros(n_samples)
    Q_agg = np.zeros(n_samples)
    cos_phi_agg = np.ones(n_samples)  # Default 1.0
    thd_agg = np.zeros(n_samples)
    h3_agg = np.zeros(n_samples)
    h5_agg = np.zeros(n_samples)
    h7_agg = np.zeros(n_samples)
    active_devices = [None] * n_samples
    active_states = [None] * n_samples

    for start, end, device, state in SCHEDULE:
        mask = [(t >= start_time + timedelta(seconds=start) and t < start_time + timedelta(seconds=end)) for t in t_array]
        profile = DEVICE_PROFILES[device]["states"][state]
        p_val = float(profile["P_W"])
        q_val = float(profile["Q_VAR"])
        cos_phi_val = float(profile["cos_phi"])
        thd_val = float(profile["THD_pct"]) / 100.0  # in %
        h3_val = float(profile["H3_pct"]) / 100.0
        h5_val = float(profile["H5_pct"]) / 100.0
        h7_val = float(profile["H7_pct"]) / 100.0

        for i in range(n_samples):
            if mask[i]:
                P_agg[i] += p_val
                Q_agg[i] += q_val
                # Gewichtete cos_phi (nach P)
                cos_phi_agg[i] = (cos_phi_agg[i] * P_agg[i] + cos_phi_val * p_val) / (P_agg[i] + p_val) if P_agg[i] + p_val > 0 else cos_phi_val
                # Gewichtete Harmonics (nach Stromanteil, approx P/U)
                weight = p_val / (U_LN_nominal * cos_phi_val) if cos_phi_val > 0 else 0
                total_weight = thd_agg[i] + weight
                if total_weight > 0:
                    thd_agg[i] = (thd_agg[i] * thd_agg[i] + thd_val * weight) / total_weight  # Approximation
                    h3_agg[i] = (h3_agg[i] * h3_agg[i] + h3_val * weight) / total_weight
                    h5_agg[i] = (h5_agg[i] * h5_agg[i] + h5_val * weight) / total_weight
                    h7_agg[i] = (h7_agg[i] * h7_agg[i] + h7_val * weight) / total_weight
                else:
                    thd_agg[i] = thd_val
                    h3_agg[i] = h3_val
                    h5_agg[i] = h5_val
                    h7_agg[i] = h7_val
                active_devices[i] = device
                active_states[i] = state

        print(f"  [{start:4d}s–{end:4d}s]  {device:<18} {state:<14} "
              f"P={p_val:>7.0f} W")

    # Rauschen hinzufügen
    P_noisy = np.array([add_noise(v, NOISE_PCT, rng) for v in P_agg])
    Q_noisy = np.array([add_noise(v, NOISE_PCT, rng) for v in Q_agg])
    cos_phi_noisy = np.array([add_noise(v, 0.01, rng) for v in cos_phi_agg])  # 1% Rauschen auf cos_phi

    # Berechne abgeleitete Werte
    S_total = np.sqrt(P_noisy**2 + Q_noisy**2)
    PF_total = np.where(S_total > 0, P_noisy / S_total, 1.0)

    # Spannungen
    U_L1 = np.array([add_noise(U_LN_nominal, 0.005, rng) for _ in range(n_samples)])
    U_L2 = np.array([add_noise(U_LN_nominal, 0.005, rng) for _ in range(n_samples)])
    U_L3 = np.array([add_noise(U_LN_nominal, 0.005, rng) for _ in range(n_samples)])
    U_LL1 = np.array([add_noise(U_LL_nominal, 0.005, rng) for _ in range(n_samples)])
    U_LL2 = np.array([add_noise(U_LL_nominal, 0.005, rng) for _ in range(n_samples)])
    U_LL3 = np.array([add_noise(U_LL_nominal, 0.005, rng) for _ in range(n_samples)])

    # Frequenz
    freq = np.array([add_noise(f_nominal, 0.001, rng) for _ in range(n_samples)])  # 0.05 Hz Rauschen

    # Ströme: Annahme einphasig auf L1 für meisten, dreiphasig für sync_machine
    I_L1 = np.zeros(n_samples)
    I_L2 = np.zeros(n_samples)
    I_L3 = np.zeros(n_samples)
    for i in range(n_samples):
        if active_devices[i] == "sync_machine":
            # Dreiphasig symmetrisch: S_total ist die gesamte Scheinleistung über alle drei Phasen
            I_phase = S_total[i] / (3 * U_L1[i]) if U_L1[i] > 0 else 0
            I_L1[i] = I_L2[i] = I_L3[i] = I_phase
        else:
            # Einphasig auf L1: Strom aus der scheinbaren Leistung der aktiven Phase
            I_L1[i] = S_total[i] / U_L1[i] if U_L1[i] > 0 else 0

    # THD_U klein
    THD_U_L1 = np.array([add_noise(0.015, 0.1, rng) for _ in range(n_samples)])  # 1.5% ±10%
    H3_U_L1 = THD_U_L1 * 0.3
    H5_U_L1 = THD_U_L1 * 0.2
    H7_U_L1 = THD_U_L1 * 0.1

    # THD_I aus Aggregation
    THD_I_L1 = np.array([add_noise(v, 0.1, rng) for v in thd_agg])
    H3_I_L1 = np.array([add_noise(v, 0.1, rng) for v in h3_agg])
    H5_I_L1 = np.array([add_noise(v, 0.1, rng) for v in h5_agg])
    H7_I_L1 = np.array([add_noise(v, 0.1, rng) for v in h7_agg])

    # Harmonics H2 bis H31: Für Strom L1, andere 0
    harmonics_I = {}
    for h in range(2, 32):
        if h == 3:
            harmonics_I[f"H{h}_current_L1_pct"] = H3_I_L1 * 100
        elif h == 5:
            harmonics_I[f"H{h}_current_L1_pct"] = H5_I_L1 * 100
        elif h == 7:
            harmonics_I[f"H{h}_current_L1_pct"] = H7_I_L1 * 100
        else:
            harmonics_I[f"H{h}_current_L1_pct"] = np.zeros(n_samples)

    # DataFrame aufbauen
    df['timestamp'] = t_array
    df['total_active_power_W'] = P_noisy
    df['total_apparent_power_VA'] = S_total
    df['total_reactive_power_VAR'] = Q_noisy
    df['voltage_L1_V'] = U_L1
    df['voltage_L2_V'] = U_L2
    df['voltage_L3_V'] = U_L3
    df['current_L1_A'] = I_L1
    df['current_L2_A'] = I_L2
    df['current_L3_A'] = I_L3
    df['frequency_Hz'] = freq
    df['power_factor'] = PF_total
    # Keine appliance-Spalten für TEST
    for h in range(2, 32):
        df[f"H{h}_current_L1_pct"] = harmonics_I[f"H{h}_current_L1_pct"]

    # Ground Truth
    df_gt['timestamp'] = t_array
    df_gt['active_device'] = active_devices
    df_gt['active_state'] = active_states

    # Speichern
    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, float_format="%.4f")
    df_gt.to_csv(GROUND_TRUTH_FILE, index=False)

    print(f"\n  Samples : {n_samples}")
    print(f"  Datei   : {OUTPUT_FILE}")
    print(f"  Ground Truth: {GROUND_TRUTH_FILE}")
    print("=" * 55)

if __name__ == "__main__":
    generate()
"""
device_profiles.py
NILM Projekt - Milestone 1.1
Geräteprofile für alle Laborgeräte

Quellen-Klassifikation der Parameterwerte:
  [NORMATIV]  Wert direkt aus einer Norm oder Spezifikation abgeleitet
  [REFERENZ]  Wert durch Messdatensatz oder Fachliteratur plausibilisiert
  [ANNAHME]   Physikalisch motivierte Engineering Assumption ohne direkten Messbeleg
"""

DEVICE_PROFILES = {

    # Office-PC mit aktivem PFC-Schaltnetzteil (Standard-Bürorechner, mittlere Leistung)
    # cos_phi > 0.9: IEC 61000-3-2 Klasse D schreibt PFC-Pflicht vor [NORMATIV]
    # Effizienz-Charakteristik konsistent mit 80 PLUS Zertifizierung (plugloadsolutions.com) [REFERENZ]
    # P-Werte (80/200/400 W) für typischen Office-PC [ANNAHME]; THD 4.5-5.0% bei PFC-Boost-Topologie [ANNAHME]
    "pc_office": {
        "type": "II",
        "description": "Office-PC mit Schaltnetzteil (PFC aktiv, ~400 W-Klasse)",
        "states": {
            "OFF":    {"P_W":   0, "Q_VAR":  0,  "cos_phi": 1.00, "THD_pct":  0.0, "H3_pct": 0.0, "H5_pct": 0.0, "H7_pct": 0.0},
            "IDLE":   {"P_W":  80, "Q_VAR": 15,  "cos_phi": 0.98, "THD_pct":  4.5, "H3_pct": 3.5, "H5_pct": 2.5, "H7_pct": 1.0},
            "NORMAL": {"P_W": 200, "Q_VAR": 25,  "cos_phi": 0.99, "THD_pct":  4.7, "H3_pct": 3.8, "H5_pct": 2.7, "H7_pct": 1.2},
            "FULL":   {"P_W": 400, "Q_VAR": 40,  "cos_phi": 0.99, "THD_pct":  5.0, "H3_pct": 4.0, "H5_pct": 3.0, "H7_pct": 1.5},
        }
    },

    # Workstation / Gaming-PC mit 750-W-Netzteil (PFC aktiv, höhere Leistungsklasse)
    # cos_phi > 0.9: IEC 61000-3-2 Klasse D (PFC-Pflicht > 75 W) [NORMATIV]
    # 80 PLUS Gold/Platinum Effizienzanforderungen für Hochleistungsnetzteile [REFERENZ]
    # Erhöhtes THD im IDLE: 750-W-Netzteil bei ~16% Nennlast — PFC-Regler im ungünstigen Arbeitspunkt [ANNAHME]
    # P-Werte (120/380/700 W), Q-Werte, THD-Absolutwerte: [ANNAHME]
    "pc_workstation": {
        "type": "II",
        "description": "Workstation / Gaming-PC mit 750-W-Netzteil (PFC aktiv)",
        "states": {
            "OFF":    {"P_W":   0, "Q_VAR":  0,  "cos_phi": 1.00, "THD_pct":  0.0, "H3_pct": 0.0, "H5_pct": 0.0, "H7_pct": 0.0},
            "IDLE":   {"P_W": 120, "Q_VAR": 20,  "cos_phi": 0.98, "THD_pct":  5.5, "H3_pct": 4.2, "H5_pct": 3.2, "H7_pct": 1.5},
            "NORMAL": {"P_W": 380, "Q_VAR": 40,  "cos_phi": 0.99, "THD_pct":  4.8, "H3_pct": 3.8, "H5_pct": 2.8, "H7_pct": 1.3},
            "FULL":   {"P_W": 700, "Q_VAR": 65,  "cos_phi": 0.99, "THD_pct":  5.2, "H3_pct": 4.2, "H5_pct": 3.1, "H7_pct": 1.6},
        }
    },

    # Thin Client / Mini-PC (externes Kleinnetzteil, keine aktive PFC)
    # Gerät < 75 W: IEC 61000-3-2 Klasse A — keine Pflicht zur aktiven PFC [NORMATIV]
    # Ohne aktive PFC: niedrigeres cos_phi (0.93-0.95) und höheres THD (8-9%) [ANNAHME]
    # P-Werte (8/14 W), Q-Werte, THD-Absolutwerte: [ANNAHME]
    # Kein FULL-Zustand: Thin Clients haben keinen nennenswerten Hochlastzustand
    "pc_thinclient": {
        "type": "II",
        "description": "Thin Client / Mini-PC (kein aktives PFC, < 75 W)",
        "states": {
            "OFF":    {"P_W":  0, "Q_VAR": 0,  "cos_phi": 1.00, "THD_pct": 0.0, "H3_pct": 0.0, "H5_pct": 0.0, "H7_pct": 0.0},
            "IDLE":   {"P_W":  8, "Q_VAR": 3,  "cos_phi": 0.93, "THD_pct": 8.5, "H3_pct": 5.5, "H5_pct": 4.0, "H7_pct": 2.5},
            "NORMAL": {"P_W": 14, "Q_VAR": 5,  "cos_phi": 0.94, "THD_pct": 8.0, "H3_pct": 5.2, "H5_pct": 3.8, "H7_pct": 2.2},
        }
    },

    # Ohmsche Widerstandslast
    # cos_phi = 1.00 exakt aus Ohm'schem Gesetz ableitbar — keine externe Quelle erforderlich
    # THD-Residual 0.5%: konservative Annahme für Bauteilnichtidealitäten (Temperaturgang, Kontaktwiderstand) [ANNAHME]
    # H3/H5/H7-Residual: [ANNAHME]
    "resistive_load": {
        "type": "II",
        "description": "Variable Widerstandslast (ohmsch)",
        "states": {
            "OFF":   {"P_W":    0, "Q_VAR": 0, "cos_phi": 1.00, "THD_pct": 0.0, "H3_pct": 0.0, "H5_pct": 0.0, "H7_pct": 0.0},
            "25PCT": {"P_W":  500, "Q_VAR": 0, "cos_phi": 1.00, "THD_pct": 0.5, "H3_pct": 0.2, "H5_pct": 0.1, "H7_pct": 0.1},
            "50PCT": {"P_W": 1000, "Q_VAR": 0, "cos_phi": 1.00, "THD_pct": 0.5, "H3_pct": 0.2, "H5_pct": 0.1, "H7_pct": 0.1},
            "75PCT": {"P_W": 1500, "Q_VAR": 0, "cos_phi": 1.00, "THD_pct": 0.5, "H3_pct": 0.2, "H5_pct": 0.1, "H7_pct": 0.1},
            "100PCT":{"P_W": 2000, "Q_VAR": 0, "cos_phi": 1.00, "THD_pct": 0.5, "H3_pct": 0.2, "H5_pct": 0.1, "H7_pct": 0.1},
        }
    },

    # Haartrockner (dominante Widerstandsheizung + kleiner Gebläsemotor)
    # Keine Leistungsqualitäts-Norm verfügbar (IEC 60335-2-23 deckt nur Gerätesicherheit ab)
    # Alle Werte physikalisch motiviert: Heizwiderstand dominant → hoher cos_phi; Motor-Anteil → geringe Harmonics [ANNAHME]
    "hairdryer": {
        "type": "II",
        "description": "Haartrockner (Heizung + Gebläsemotor)",
        "states": {
            "OFF":  {"P_W":    0, "Q_VAR":  0,  "cos_phi": 1.00, "THD_pct": 0.0, "H3_pct": 0.0, "H5_pct": 0.0, "H7_pct": 0.0},
            "COLD": {"P_W":  200, "Q_VAR": 30,  "cos_phi": 0.99, "THD_pct": 3.0, "H3_pct": 2.0, "H5_pct": 1.5, "H7_pct": 0.8},
            "WARM": {"P_W":  900, "Q_VAR": 60,  "cos_phi": 0.998,"THD_pct": 4.0, "H3_pct": 2.5, "H5_pct": 2.0, "H7_pct": 1.0},
            "HOT":  {"P_W": 1800, "Q_VAR": 80,  "cos_phi": 0.999,"THD_pct": 5.0, "H3_pct": 3.0, "H5_pct": 2.5, "H7_pct": 1.2},
        }
    },

    # Waschmaschine (Motor + Heizwiderstand, mehrere Betriebszustände)
    # P-Größenordnungen plausibilisiert durch:
    #   REDD: Kolter & Johnson, 2011, SustKDD Workshop at KDD [REFERENZ]
    #   UK-DALE: Kelly & Knottenbelt, 2015, Scientific Data, DOI: 10.1038/sdata.2015.7 [REFERENZ]
    # Q, THD, H3/H5/H7 aller Zustände: [ANNAHME]
    # SPIN: hohe Blindleistung (Q=400 VAR) und THD (25%) durch Inverter-Motor bei variabler Drehzahl [ANNAHME]
    "washing_machine": {
        "type": "II",
        "description": "Waschmaschine (Motor + Heizwiderstand)",
        "states": {
            "OFF":      {"P_W":    0, "Q_VAR":   0,  "cos_phi": 1.00, "THD_pct":  0.0, "H3_pct":  0.0, "H5_pct":  0.0, "H7_pct": 0.0},
            "STANDBY":  {"P_W":    5, "Q_VAR":   2,  "cos_phi": 0.93, "THD_pct":  8.0, "H3_pct":  5.0, "H5_pct":  3.0, "H7_pct": 2.0},
            "WASH":     {"P_W":  500, "Q_VAR": 300,  "cos_phi": 0.86, "THD_pct": 15.0, "H3_pct":  8.0, "H5_pct":  7.0, "H7_pct": 5.0},
            "HEAT":     {"P_W": 2000, "Q_VAR": 150,  "cos_phi": 0.997,"THD_pct":  6.0, "H3_pct":  4.0, "H5_pct":  2.0, "H7_pct": 1.0},
            "SPIN":     {"P_W":  300, "Q_VAR": 400,  "cos_phi": 0.60, "THD_pct": 25.0, "H3_pct": 12.0, "H5_pct": 10.0, "H7_pct": 8.0},
        }
    },

    # Kühlschrank (einphasiger Kompressormotor, zyklisch)
    # P_COMPRESSOR_ON ≈ 150 W: plausibilisiert durch REDD- und BLUED-Datensatz [REFERENZ]
    # cos_phi ≈ 0.78: typisch für einphasigen Induktionsmotor (Maschinenlehre) [REFERENZ]
    # H3 > H5: typisches Oberschwingungsmuster einphasiger Last [ANNAHME]
    # THD = 12%, Q, H3/H5/H7-Absolutwerte: [ANNAHME]
    "fridge": {
        "type": "I",
        "description": "Kühlschrank (Kompressormotor, zyklisch)",
        "states": {
            "OFF":           {"P_W":   0, "Q_VAR":   0,  "cos_phi": 1.00, "THD_pct":  0.0, "H3_pct": 0.0, "H5_pct": 0.0, "H7_pct": 0.0},
            "STANDBY":       {"P_W":   5, "Q_VAR":   3,  "cos_phi": 0.86, "THD_pct":  8.0, "H3_pct": 4.0, "H5_pct": 3.0, "H7_pct": 2.0},
            "COMPRESSOR_ON": {"P_W": 150, "Q_VAR": 120,  "cos_phi": 0.78, "THD_pct": 12.0, "H3_pct": 7.0, "H5_pct": 5.0, "H7_pct": 5.0},
        }
    },

    # EV-Lader (einphasiges AC-Laden, Onboard-Charger)
    # P-Werte EXAKT nach IEC 61851-1: P = 230 V × I [NORMATIV]
    #   MODE1_10A: 230 V × 10 A = 2300 W; MODE2_16A: 230 V × 16 A = 3680 W; MODE3_32A: 230 V × 32 A = 7360 W
    # THD-Grenzwerte: IEC 61000-3-2 Klasse A (Modi ≤ 16 A); IEC 61000-3-12 (MODE3_32A, > 16 A) [NORMATIV]
    # TAPER: hoher THD (28%) durch ungünstige PFC-Arbeitspunkte bei minimaler Ladeleistung [ANNAHME]
    # Q-Werte, exakte THD-Typwerte, H3/H5/H7: [ANNAHME]
    "ev_charger": {
        "type": "II",
        "description": "E-Auto AC-Laden (Onboard-Charger)",
        "states": {
            "OFF":       {"P_W":    0, "Q_VAR":   0,  "cos_phi": 1.00, "THD_pct":  0.0, "H3_pct":  0.0, "H5_pct":  0.0, "H7_pct": 0.0},
            "MODE1_10A": {"P_W": 2300, "Q_VAR": 200,  "cos_phi": 0.996,"THD_pct":  5.0, "H3_pct":  3.0, "H5_pct":  2.5, "H7_pct": 1.5},
            "MODE2_16A": {"P_W": 3680, "Q_VAR": 300,  "cos_phi": 0.997,"THD_pct":  8.0, "H3_pct":  5.0, "H5_pct":  4.0, "H7_pct": 2.0},
            "MODE3_32A": {"P_W": 7360, "Q_VAR": 500,  "cos_phi": 0.998,"THD_pct": 12.0, "H3_pct":  7.0, "H5_pct":  5.0, "H7_pct": 3.0},
            "TAPER":     {"P_W":  500, "Q_VAR": 100,  "cos_phi": 0.980,"THD_pct": 28.0, "H3_pct": 15.0, "H5_pct": 10.0, "H7_pct": 7.0},
        }
    },

    # PV-Wechselrichter (Einspeisung AC, negativer P-Wert = Verbraucherzählpfeil-Konvention)
    # THD < 5%: normativ vorgeschrieben durch IEC 61727 und VDE-AR-N 4105 [NORMATIV]
    # Typwerte 2-3% und THD-Abnahme bei steigender Last: konsistent mit Hersteller-Whitepapern (SMA, Fronius) [REFERENZ]
    # P-Absolutwerte, Q-Werte, H3/H5/H7: [ANNAHME]
    "pv_inverter": {
        "type": "II",
        "description": "PV-Einspeisung AC (hinter Wechselrichter)",
        "states": {
            "OFF":    {"P_W":     0, "Q_VAR":  0,  "cos_phi": 1.00, "THD_pct": 0.0, "H3_pct": 0.0, "H5_pct": 0.0, "H7_pct": 0.0},
            "LOW":    {"P_W":  -500, "Q_VAR": 20,  "cos_phi": 0.999,"THD_pct": 3.0, "H3_pct": 1.5, "H5_pct": 1.0, "H7_pct": 0.8},
            "MEDIUM": {"P_W": -1500, "Q_VAR": 30,  "cos_phi": 0.999,"THD_pct": 2.5, "H3_pct": 1.2, "H5_pct": 0.8, "H7_pct": 0.5},
            "HIGH":   {"P_W": -3000, "Q_VAR": 50,  "cos_phi": 0.999,"THD_pct": 2.0, "H3_pct": 1.0, "H5_pct": 0.6, "H7_pct": 0.4},
        }
    },

    # Synchronmaschine (Motor- und Generatorbetrieb, Direktanlauf angenommen)
    # P/Q/cos_phi-Charakteristik nach Maschinenlehre: Chapman, "Electric Machinery Fundamentals", McGraw-Hill [REFERENZ]
    # cos_phi ≈ 0.20 im Leerlauf: typisch für unbelasteten Synchronmotor (kapazitive/induktive Blindleistungsaufnahme) [REFERENZ]
    # THD/H3/H5/H7: [ANNAHME]; Oberschwingungen abhängig von Antriebstopologie — hier Direktanlauf ohne Umrichter
    "sync_machine": {
        "type": "II",
        "description": "Synchronmaschine (Motor-/Generatorbetrieb)",
        "states": {
            "OFF":        {"P_W":    0, "Q_VAR":    0,  "cos_phi": 1.00, "THD_pct":  0.0, "H3_pct": 0.0, "H5_pct": 0.0, "H7_pct": 0.0},
            "IDLE":       {"P_W":  100, "Q_VAR":  500,  "cos_phi": 0.20, "THD_pct":  8.0, "H3_pct": 3.0, "H5_pct": 5.0, "H7_pct": 4.0},
            "MOTOR_HALF": {"P_W":  800, "Q_VAR":  600,  "cos_phi": 0.80, "THD_pct": 12.0, "H3_pct": 5.0, "H5_pct": 8.0, "H7_pct": 6.0},
            "MOTOR_FULL": {"P_W": 1500, "Q_VAR":  700,  "cos_phi": 0.91, "THD_pct": 10.0, "H3_pct": 4.0, "H5_pct": 7.0, "H7_pct": 5.0},
            "GENERATOR":  {"P_W":-1200, "Q_VAR": -400,  "cos_phi": 0.95, "THD_pct":  6.0, "H3_pct": 2.0, "H5_pct": 4.0, "H7_pct": 3.0},
        }
    },
}

def get_profile(device_name, state):
    return DEVICE_PROFILES[device_name]["states"][state]

def list_devices():
    return list(DEVICE_PROFILES.keys())

def list_states(device_name):
    return list(DEVICE_PROFILES[device_name]["states"].keys())

def print_summary():
    print("=" * 70)
    print("  NILM Geräteprofile – Milestone 1.1")
    print("=" * 70)
    for name, dev in DEVICE_PROFILES.items():
        print(f"\n  [{dev['type']}] {name.upper()} — {dev['description']}")
        print(f"  {'Zustand':<18} {'P [W]':>8} {'Q [VAR]':>9} {'cos φ':>7} {'THD%':>6} {'H3%':>5} {'H5%':>5} {'H7%':>5}")
        print(f"  {'-'*66}")
        for state, vals in dev["states"].items():
            print(f"  {state:<18} {vals['P_W']:>8.0f} {vals['Q_VAR']:>9.0f} "
                  f"{vals['cos_phi']:>7.3f} {vals['THD_pct']:>6.1f} "
                  f"{vals['H3_pct']:>5.1f} {vals['H5_pct']:>5.1f} {vals['H7_pct']:>5.1f}")

if __name__ == "__main__":
    print_summary()

"""
acquisition.py
NILM Projekt - Milestone 1
Signalerfassung vom Siemens SENTRON PAC4200 via Modbus TCP
Inkl. Harmonics bis zur 31. Ordnung (Strom L1)
"""

import time
import random
import struct
import csv
import os
import math
from datetime import datetime

# ─────────────────────────────────────────────
# KONFIGURATION – hier anpassen
# ─────────────────────────────────────────────
SIMULATION_MODE  = True             # True = Simulation | False = echter PAC4200
PAC4200_IP       = "192.168.0.100"  # IP-Adresse des PAC4200
PAC4200_PORT     = 502
SLAVE_ID         = 1
SAMPLE_INTERVAL  = 1
OUTPUT_FILE      = "data/raw_measurements.csv"
ENABLE_HARMONICS = True             # Harmonics H2–H31 mitmessen

# ─────────────────────────────────────────────
# MODBUS REGISTER-ADRESSEN (0-basiert)
# ─────────────────────────────────────────────
REGISTERS_BASE = {
    "total_active_power_W":     400065 - 1,
    "total_apparent_power_VA":  400063 - 1,
    "total_reactive_power_VAR": 400067 - 1,
    "voltage_L1_V":             400001 - 1,
    "voltage_L2_V":             400003 - 1,
    "voltage_L3_V":             400005 - 1,
    "current_L1_A":             400013 - 1,
    "current_L2_A":             400015 - 1,
    "current_L3_A":             400017 - 1,
    "frequency_Hz":             400055 - 1,
    "power_factor":             400069 - 1,
}

HARMONICS_START_REGISTER = 400801 - 1  # Bitte mit PAC4200-Handbuch abgleichen!
HARMONICS_ORDER = list(range(2, 32))   # H2 bis H31

# Simulierte Geräte mit typischen Harmonics-Profilen
APPLIANCES = {
    "kettle": {
        "base_W": 0, "on_W": 2000, "prob_on": 0.05, "prob_off": 0.10,
        "harmonics": {2:0.5, 3:0.8, 4:0.3, 5:0.5, 7:0.3}   # Ohmssch → kaum Harmonics
    },
    "fridge": {
        "base_W": 80, "on_W": 150, "prob_on": 0.30, "prob_off": 0.30,
        "harmonics": {2:1.0, 3:2.5, 5:8.0, 7:5.0, 11:2.0, 13:1.5}  # Motor → H5, H7
    },
    "laptop": {
        "base_W": 0, "on_W": 45, "prob_on": 0.02, "prob_off": 0.01,
        "harmonics": {2:2.0, 3:18.0, 4:1.5, 5:12.0, 7:8.0, 9:4.0, 11:3.0, 13:2.5}  # Schaltnetzteil
    },
}


# ─────────────────────────────────────────────
# MODBUS ECHTGERÄT
# ─────────────────────────────────────────────
def connect_pac4200():
    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient(PAC4200_IP, port=PAC4200_PORT)
    if client.connect():
        print(f"[OK] Verbunden mit PAC4200 @ {PAC4200_IP}:{PAC4200_PORT}")
        return client
    raise ConnectionError(f"Verbindung zu {PAC4200_IP}:{PAC4200_PORT} fehlgeschlagen!")

def read_float(client, register):
    result = client.read_holding_registers(register, 2, slave=SLAVE_ID)
    if result.isError():
        return None
    raw = struct.pack(">HH", result.registers[0], result.registers[1])
    return round(struct.unpack(">f", raw)[0], 4)

def read_pac4200(client):
    data = {"timestamp": datetime.now().isoformat()}
    for name, reg in REGISTERS_BASE.items():
        data[name] = read_float(client, reg)
    if ENABLE_HARMONICS:
        for order in HARMONICS_ORDER:
            reg = HARMONICS_START_REGISTER + (order - 2) * 2
            data[f"H{order}_current_L1_pct"] = read_float(client, reg)
    data["appliance_kettle_W"] = None
    data["appliance_fridge_W"] = None
    data["appliance_laptop_W"] = None
    return data


# ─────────────────────────────────────────────
# SIMULATIONS-MODUS
# ─────────────────────────────────────────────
appliance_states = {name: False for name in APPLIANCES}

def simulate_measurement():
    global appliance_states
    appliance_power = {}
    combined_harmonics = {order: 0.0 for order in HARMONICS_ORDER}

    for name, cfg in APPLIANCES.items():
        if appliance_states[name]:
            if random.random() < cfg["prob_off"]:
                appliance_states[name] = False
        else:
            if random.random() < cfg["prob_on"]:
                appliance_states[name] = True

        power = cfg["on_W"] if appliance_states[name] else cfg["base_W"]
        power += random.gauss(0, max(power * 0.02, 1))
        appliance_power[name] = max(0, power)

        if appliance_states[name] or cfg["base_W"] > 0:
            weight = appliance_power[name] / max(cfg["on_W"], 1)
            for order, amplitude in cfg["harmonics"].items():
                if order in combined_harmonics:
                    combined_harmonics[order] += amplitude * weight + random.gauss(0, 0.1)

    total_active   = sum(appliance_power.values()) + random.gauss(0, 5)
    total_apparent = total_active * random.uniform(1.0, 1.15)
    total_reactive = math.sqrt(max(0, total_apparent**2 - total_active**2))
    pf             = total_active / total_apparent if total_apparent > 0 else 1.0

    data = {
        "timestamp":                datetime.now().isoformat(),
        "total_active_power_W":     round(max(0, total_active), 2),
        "total_apparent_power_VA":  round(max(0, total_apparent), 2),
        "total_reactive_power_VAR": round(max(0, total_reactive), 2),
        "voltage_L1_V":             round(random.gauss(230, 1.5), 2),
        "voltage_L2_V":             round(random.gauss(230, 1.5), 2),
        "voltage_L3_V":             round(random.gauss(230, 1.5), 2),
        "current_L1_A":             round(max(0, total_active / 230), 3),
        "current_L2_A":             round(max(0, total_active / 230 * 0.98), 3),
        "current_L3_A":             round(max(0, total_active / 230 * 1.01), 3),
        "frequency_Hz":             round(random.gauss(50.0, 0.02), 3),
        "power_factor":             round(min(1.0, max(0.0, pf)), 4),
        "appliance_kettle_W":       round(appliance_power["kettle"], 2),
        "appliance_fridge_W":       round(appliance_power["fridge"], 2),
        "appliance_laptop_W":       round(appliance_power["laptop"], 2),
    }

    if ENABLE_HARMONICS:
        for order in HARMONICS_ORDER:
            val = combined_harmonics.get(order, 0.0)
            data[f"H{order}_current_L1_pct"] = round(max(0, val + random.gauss(0, 0.05)), 3)

    return data


# ─────────────────────────────────────────────
# CSV SPEICHERUNG
# ─────────────────────────────────────────────
def get_fieldnames():
    fields = ["timestamp"] + list(REGISTERS_BASE.keys())
    fields += ["appliance_kettle_W", "appliance_fridge_W", "appliance_laptop_W"]
    if ENABLE_HARMONICS:
        fields += [f"H{o}_current_L1_pct" for o in HARMONICS_ORDER]
    return fields

def init_csv():
    os.makedirs("data", exist_ok=True)
    write_header = not os.path.exists(OUTPUT_FILE)
    f = open(OUTPUT_FILE, "a", newline="")
    writer = csv.DictWriter(f, fieldnames=get_fieldnames())
    if write_header:
        writer.writeheader()
        print(f"[OK] CSV erstellt: {OUTPUT_FILE}")
    return f, writer


# ─────────────────────────────────────────────
# HAUPTPROGRAMM
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  NILM Acquisition - Milestone 1")
    print(f"  Modus:     {'SIMULATION' if SIMULATION_MODE else 'PAC4200 LIVE'}")
    print(f"  Harmonics: {'AN (H2-H31)' if ENABLE_HARMONICS else 'AUS'}")
    print("  Stoppen mit Strg+C")
    print("=" * 60)

    client = None
    if not SIMULATION_MODE:
        client = connect_pac4200()

    csv_file, writer = init_csv()

    try:
        while True:
            data = simulate_measurement() if SIMULATION_MODE else read_pac4200(client)
            writer.writerow(data)
            csv_file.flush()

            print(f"[{data['timestamp']}] "
                  f"P={data['total_active_power_W']:7.1f}W | "
                  f"PF={data['power_factor']:.3f} | "
                  f"H3={data.get('H3_current_L1_pct','--')}% "
                  f"H5={data.get('H5_current_L1_pct','--')}% "
                  f"H7={data.get('H7_current_L1_pct','--')}% | "
                  f"Kettle={data['appliance_kettle_W']}W "
                  f"Fridge={data['appliance_fridge_W']}W "
                  f"Laptop={data['appliance_laptop_W']}W")

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("\n[STOP] Messung beendet.")
    finally:
        csv_file.close()
        if client:
            client.close()
        print(f"[OK] Daten gespeichert: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
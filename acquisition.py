"""
acquisition.py
NILM Projekt - Milestone 1
Signalerfassung vom Siemens SENTRON PAC4200 via Modbus TCP
Mit Simulations-Modus als Fallback (solange kein Gerät angeschlossen)
"""

import time
import random
import struct
import csv
import os
from datetime import datetime


# ─────────────────────────────────────────────
# KONFIGURATION – hier anpassen
# ─────────────────────────────────────────────
SIMULATION_MODE = True             # True = Simulation, False = echter PAC4200
PAC4200_IP      = "192.168.0.100"  # IP-Adresse des PAC4200
PAC4200_PORT    = 502              # Modbus TCP Port (Standard)
SLAVE_ID        = 1                # Modbus Slave-ID
SAMPLE_INTERVAL = 1                # Sekunden zwischen Messungen
OUTPUT_FILE     = "data/raw_measurements.csv"

# Modbus Register-Adressen PAC4200
REGISTERS = {
    "total_active_power_W":     400065 - 1,
    "total_apparent_power_VA":  400063 - 1,
    "total_reactive_power_VAR": 400067 - 1,
    "voltage_L1_V":             400001 - 1,
    "current_L1_A":             400013 - 1,
    "frequency_Hz":             400055 - 1,
}

# Simulierte Geräte (Single Appliances)
APPLIANCES = {
    "kettle_W": {"base": 0,  "on": 2000, "prob_on": 0.05, "prob_off": 0.1},
    "fridge_W": {"base": 80, "on": 150,  "prob_on": 0.3,  "prob_off": 0.3},
    "laptop_W": {"base": 0,  "on": 45,   "prob_on": 0.02, "prob_off": 0.01},
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
    else:
        raise ConnectionError(f"Verbindung zu {PAC4200_IP}:{PAC4200_PORT} fehlgeschlagen!")

def read_float_register(client, register):
    result = client.read_holding_registers(register, 2, slave=SLAVE_ID)
    if result.isError():
        return None
    raw = struct.pack(">HH", result.registers[0], result.registers[1])
    return round(struct.unpack(">f", raw)[0], 3)

def read_pac4200(client):
    data = {"timestamp": datetime.now().isoformat()}
    for name, reg in REGISTERS.items():
        data[name] = read_float_register(client, reg)
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
    for name, cfg in APPLIANCES.items():
        state = appliance_states[name]
        if state:
            if random.random() < cfg["prob_off"]:
                appliance_states[name] = False
        else:
            if random.random() < cfg["prob_on"]:
                appliance_states[name] = True
        power = cfg["on"] if appliance_states[name] else cfg["base"]
        appliance_power[name] = power + random.gauss(0, power * 0.02 + 1)

    total_active   = sum(appliance_power.values()) + random.gauss(0, 5)
    total_apparent = total_active * random.uniform(1.0, 1.1)
    total_reactive = (total_apparent**2 - total_active**2) ** 0.5

    return {
        "timestamp":                datetime.now().isoformat(),
        "total_active_power_W":     round(max(0, total_active), 2),
        "total_apparent_power_VA":  round(max(0, total_apparent), 2),
        "total_reactive_power_VAR": round(max(0, total_reactive), 2),
        "voltage_L1_V":             round(random.gauss(230, 1.5), 2),
        "current_L1_A":             round(max(0, total_active / 230), 3),
        "frequency_Hz":             round(random.gauss(50.0, 0.02), 3),
        "appliance_kettle_W":       round(appliance_power["kettle_W"], 2),
        "appliance_fridge_W":       round(appliance_power["fridge_W"], 2),
        "appliance_laptop_W":       round(appliance_power["laptop_W"], 2),
    }


# ─────────────────────────────────────────────
# CSV SPEICHERUNG
# ─────────────────────────────────────────────
FIELDNAMES = [
    "timestamp",
    "total_active_power_W", "total_apparent_power_VA", "total_reactive_power_VAR",
    "voltage_L1_V", "current_L1_A", "frequency_Hz",
    "appliance_kettle_W", "appliance_fridge_W", "appliance_laptop_W",
]

def init_csv():
    os.makedirs("data", exist_ok=True)
    write_header = not os.path.exists(OUTPUT_FILE)
    f = open(OUTPUT_FILE, "a", newline="")
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    if write_header:
        writer.writeheader()
        print(f"[OK] CSV erstellt: {OUTPUT_FILE}")
    return f, writer


# ─────────────────────────────────────────────
# HAUPTPROGRAMM
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  NILM Acquisition - Milestone 1")
    print(f"  Modus: {'SIMULATION' if SIMULATION_MODE else 'PAC4200 LIVE'}")
    print("  Stoppen mit Strg+C")
    print("=" * 50)

    client = None
    if not SIMULATION_MODE:
        client = connect_pac4200()

    csv_file, writer = init_csv()

    try:
        while True:
            if SIMULATION_MODE:
                data = simulate_measurement()
            else:
                data = read_pac4200(client)

            writer.writerow(data)
            csv_file.flush()

            print(f"[{data['timestamp']}] "
                  f"P={data['total_active_power_W']:7.1f}W | "
                  f"U={data['voltage_L1_V']}V | "
                  f"f={data['frequency_Hz']}Hz | "
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
        print(f"[OK] Daten gespeichert in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
# Milestone 1 — Signal Acquisition, Preprocessing, Storage, Visualization

## 1. Why — Problemstellung
NILM (Non-Intrusive Load Monitoring) zielt darauf ab, aus dem aggregierten Stromsignal eines Labors einzelne Verbraucher zu identifizieren und deren Leistungsaufnahme zu rekonstruieren, ohne Sub-Metering. Dies ermöglicht kostengünstige Energieanalyse und Optimierung in intelligenten Gebäuden. Synthetische Daten sind zunächst notwendig, da echte Labordaten erst in späteren Milestones verfügbar sind, und erlauben die Validierung von Algorithmen ohne Hardware-Abhängigkeiten.

## 2. How — Konzept

### 2.1 Geräteprofile
Die Wissensbasis des NILM-Systems bilden realistische Leistungsprofile für 8 Laborgeräte (PC, resistive_load, hairdryer, washing_machine, fridge, ev_charger, pv_inverter, sync_machine). Jedes Profil enthält pro Betriebszustand: Wirkleistung P [W], Blindleistung Q [var], Leistungsfaktor cos(φ), THD [%], Oberschwingungen H3/H5/H7 [%]. Typ-I-Geräte (ON/OFF) haben zwei Zustände, Typ-II-Geräte (Multi-State) mehrere Leistungsstufen. Diese Profile basieren auf typischen Messwerten aus der Literatur und Vorlesung.

### 2.2 Datengenerator
Ein Python-Modul erzeugt aus den Geräteprofilen ein aggregiertes Zeitsignal im exakten PAC4200-Schema. Geräte schalten sequenziell nach definiertem Zeitplan (keine Concurrent Events in Phase 1). Rauschen (2% auf P/Q) wird hinzugefügt. Abgeleitete Werte wie S_total, PF_total, Ströme, Spannungen und Harmonics werden konsistent berechnet. Annahmen: Einphasige Geräte auf L1, dreiphasige symmetrisch; U_LN=230V ±0.5%, f=50Hz ±0.05Hz; THD_U klein (1-2%), THD_I aus Profilen gewichtet.

### 2.3 Datenformat & Speicherung
Das CSV-Schema entspricht exakt dem PAC Sentron 4200-Export: timestamp, total_active_power_W, total_apparent_power_VA, total_reactive_power_VAR, voltage_L1_V etc., current_L1_A etc., frequency_Hz, power_factor, H2_current_L1_pct bis H31. Eine einheitliche `load_data()`-Funktion lädt Daten unabhängig von TEST/LIVE-Modus. Ground Truth (aktives Gerät pro Sample) ist separat gespeichert, da sie in echten Daten nicht verfügbar ist.

### 2.4 Preprocessing
Resampling auf 1 Hz (implizit durch Generierung), Behandlung fehlender Werte (ffill/bfill), Glättung (rolling mean, window=5), 3σ-Ausreißer-Clipping auf P/Q. Keine Normalisierung, da absolute Leistungswerte das identifizierende Merkmal für NILM sind.

### 2.5 Visualisierung
- Aggregat-Plot: P und Q über Zeit mit zwei Y-Achsen.
- Ground-Truth-Overlay: Aggregiertes P mit farbigen Bändern für aktive Geräte.
- P-Q-Fingerprints: Scatter-Plot pro Gerät im P-Q-Raum, mit Linien für Multi-State-Geräte.

## 3. What — Ergebnisse
- Generierte Daten: 1200 Samples (20 Minuten) mit realistischen Schwankungen.
- Plots: `plots/nilm_visualization.png` (3 Subplots), `plots/pq_fingerprints.png`.
- Beispiel: Fridge läuft kontinuierlich, PC von 120-900s, etc. — Sprünge im Aggregatsignal korrespondieren mit Ground Truth.

## 4. Bewusste Vereinfachungen für Milestone 1
- Keine Concurrent Events (Thema Milestone 2)
- Ein PC-Profil als Repräsentant (Erweiterung mit echten Labor-PCs in Milestone 3)
- Statische Harmonics-Werte aus Profilen (dynamische Modellierung Milestone 2/3)
- Keine Normalisierung (Absolutwerte sind das identifizierende Feature für NILM)

## 5. Übergang zu Milestone 2 & 3
Der Code ist modular und erweiterbar: `load_data()` abstrahiert die Datenquelle, PAC4200-Schema funktioniert für synthetische und echte Daten. Preprocessing und Visualisierung sind modus-unabhängig. Für Milestone 2: Event Detection auf P/Q-Sprüngen; für Milestone 3: Modbus-Integration und echte Daten.
# NILM Milestone 1 — Signal Acquisition, Preprocessing, Speicherung, Visualisierung

**Kurs:** Modeling, Simulation and Automation of Electrical Energy Systems  
**Betreuer:** Prof. Dr.-Ing. M. Freiburg, TH Köln  
**Semester:** Sommersemester 2026  
**Team:** [Name 1], [Name 2], [Name 3]  
**Abgabe:** 14. Mai 2026

---

## 1. Why — Problemstellung

Non-Intrusive Load Monitoring (NILM) bezeichnet die rechnergestützte Disaggregation eines aggregierten Energiemesssignals in die Beiträge einzelner Geräte — ohne physische Sensoren an jedem Gerät. Die zentrale Motivation: ein einziger Messpunkt am Netzanschluss eines Gebäudes oder Labors genügt, um den Energieverbrauch einzelner Lasten zu rekonstruieren. Das reduziert den Sensoraufwand erheblich und eröffnet Möglichkeiten für Lastmanagement, Anomalieerkennung und Effizienzoptimierung.

Im Kontext dieses Projekts ist das Zielobjekt ein Hochschullabor mit heterogenem Gerätebestand: Personal Computer unterschiedlicher Leistungsklassen, elektrische Maschinen, einen EV-Ladepunkt, eine PV-Einspeisung und konventionelle Haushaltsgeräte. Das Messgerät ist ein Siemens PAC Sentron 4200 mit Modbus-TCP-Schnittstelle und 1-Hz-Abtastrate.

Milestone 1 deckt die Grundlage des Gesamtsystems ab: synthetische Datengenerierung, Speicherung, Preprocessing und Visualisierung. Synthetische statt realer Messdaten werden in dieser Phase eingesetzt, weil (a) das Messgerät für Milestone 3 vorgesehen ist, (b) Ground-Truth-Labels für reale Daten aufwendig zu erheben sind, und (c) kontrollierte synthetische Daten die Validierung der Pipeline ohne Laborzugang erlauben.

Die didaktische Zielsetzung von Milestone 1 im Gesamtprojekt: eine stabile, modusagnostische Datenpipeline schaffen, auf der Milestone 2 (Event Detection, Feature Extraction, Clustering) und Milestone 3 (Live-Anbindung via Modbus TCP) aufbauen. Jede Designentscheidung in Milestone 1 ist darauf ausgelegt, den Übergang zu Milestone 3 ohne Schema- oder Interface-Änderungen zu ermöglichen.

---

## 2. How — Konzept und Designentscheidungen

### 2.1 Geräteprofile als Wissensbasis

Jedes Gerät wird durch ein 7-dimensionales Feature-Profil pro Betriebszustand beschrieben:

| Feature | Einheit | Bedeutung |
|---|---|---|
| P | W | Wirkleistung |
| Q | VAR | Blindleistung |
| cos φ | — | Leistungsfaktor |
| THD | % | Gesamtoberschwingungsgehalt des Stroms |
| H3 | % | 3. Oberschwingung (150 Hz) |
| H5 | % | 5. Oberschwingung (250 Hz) |
| H7 | % | 7. Oberschwingung (350 Hz) |

Das Profil verwendet Absolutwerte (statt normierter Werte): P und Q sind die primären Identifikationsmerkmale für NILM-Klassifikation. Normierte Werte würden den Informationsgehalt des Leistungsniveaus zerstören.

Die Parameterwerte im Projekt folgen einem dreistufigen Quellen-Klassifikationssystem:

- **[NORMATIV]** Wert direkt aus einer Norm oder Spezifikation abgeleitet
- **[REFERENZ]** Wert durch Messdatensatz oder Fachliteratur plausibilisiert
- **[ANNAHME]** Physikalisch motivierte Engineering Assumption ohne direkten Messbeleg

Beispiel: EV-Ladepunkt, Zustand `MODE2_16A`:

```python
# P-Werte EXAKT nach IEC 61851-1: P = 230 V × I [NORMATIV]
#   MODE2_16A: 230 V × 16 A = 3680 W
# THD-Grenzwerte nach IEC 61000-3-2 (Klasse A) [NORMATIV]; Typwerte und Q: [ANNAHME]
"MODE2_16A": {"P_W": 3680, "Q_VAR": 300, "cos_phi": 0.997,
              "THD_pct": 8.0, "H3_pct": 5.0, "H5_pct": 4.0, "H7_pct": 2.0},
```

Das Projekt modelliert 10 Gerätekategorien mit insgesamt 42 Betriebszuständen:

| Gerät | Typ | Zustände |
|---|---|---|
| `pc_office` | Einphasig | OFF, IDLE, NORMAL, FULL |
| `pc_workstation` | Einphasig | OFF, IDLE, NORMAL, FULL |
| `pc_thinclient` | Einphasig | OFF, IDLE, NORMAL |
| `resistive_load` | Einphasig | OFF, 25PCT, 50PCT, 75PCT, 100PCT |
| `hairdryer` | Einphasig | OFF, COLD, WARM, HOT |
| `washing_machine` | Einphasig | OFF, STANDBY, WASH, HEAT, SPIN |
| `fridge` | Einphasig | OFF, STANDBY, COMPRESSOR_ON |
| `ev_charger` | Einphasig | OFF, MODE1_10A, MODE2_16A, MODE3_32A, TAPER |
| `pv_inverter` | Einphasig | OFF, LOW, MEDIUM, HIGH |
| `sync_machine` | Dreiphasig | OFF, IDLE, MOTOR_HALF, MOTOR_FULL, GENERATOR |

Die drei PC-Profile decken den im Laborkontext relevanten Leistungsbereich von 8 W bis 700 W ab und unterscheiden sich nicht nur im Leistungsniveau, sondern auch in der Netzteil-Topologie: `pc_office` und `pc_workstation` verwenden aktive PFC (IEC 61000-3-2 Klasse D, cos φ > 0,9), während `pc_thinclient` mit einem Kleinnetzteil unter 75 W ohne PFC-Pflicht arbeitet (Klasse A, cos φ ≈ 0,93–0,95, THD ≈ 8 %).

### 2.2 Synthetischer Datengenerator

Der Datengenerator (`data_generator.py`) erzeugt synthetische PAC4200-konforme Messdaten in drei Schritten:

1. **Schedule-Abarbeitung:** Ein fester Zeitplan weist jedem Zeitschritt das aktive Gerät und seinen Zustand zu. Die Leistungswerte (P, Q) und Oberschwingungen (THD, H3, H5, H7) werden aus dem Geräteprofil übernommen und über alle aktiven Geräte aufsummiert.

2. **Abgeleitete Größen:** Scheinleistung S = √(P² + Q²), Leistungsfaktor PF = P/S, Strom I_L1 = S/U_L1 (einphasig) bzw. I_L1 = S/(3·U_L1) (dreiphasig symmetrisch für `sync_machine`), Spannungen und Frequenz.

3. **Rauschüberlagerung:** Gauß'sches Rauschen auf allen Größen: 2 % auf P/Q, 0,5 % auf U/f, 10 % auf THD/Harmonics.

Bewusste Einschränkung in Milestone 1: keine gleichzeitigen Schaltevents (Concurrent Events). Alle Geräte laufen in nicht-überlappenden Zeitfenstern, was die Ground-Truth-Etikettierung vereinfacht. Concurrent Events sind Thema von Milestone 2.

### 2.3 PAC4200-Schema als architektonischer Anker

Der zentrale Designentscheid: CSV-Datei und SQLite-Datenbank folgen exakt dem Ausgabeschema des Siemens PAC Sentron 4200. Das Schema umfasst 42 Spalten:

```
timestamp
total_active_power_W, total_apparent_power_VA, total_reactive_power_VAR
voltage_L1_V, voltage_L2_V, voltage_L3_V
current_L1_A, current_L2_A, current_L3_A
frequency_Hz, power_factor
H2_current_L1_pct … H31_current_L1_pct   (30 Oberschwingungskanäle)
```

Diese Schema-Konsistenz hat eine direkte Konsequenz für Milestone 3: Die `acquisition.py`-Schicht, die Modbus-Register in dieses Schema übersetzt, kann `data_generator.py` vollständig ersetzen, ohne dass `preprocessing.py`, `visualization.py` oder `storage.py` angepasst werden müssen.

### 2.4 load_data() als Quellenabstraktion

Die Funktion `load_data()` in `storage.py` kapselt die Datenquelle vollständig:

```python
def load_data(mode: str = None) -> pd.DataFrame:
    """
    Lädt Messdaten unabhängig von der Quelle (TEST/LIVE).
    Returns: DataFrame mit PAC4200-Schema, indexiert nach timestamp.
    """
```

Im TEST-Modus liest sie die synthetisch generierte CSV. Im LIVE-Modus (Milestone 3) liest sie dieselbe CSV — befüllt durch `acquisition.py` statt `data_generator.py`. Alle nachgelagerten Module rufen ausschließlich `load_data()` auf und sind damit quellenunabhängig.

### 2.5 Modellierungsannahmen

**Spannung:** 230 V Nennspannung (Phase-Neutral), simuliert mit Gauß'schem Rauschen σ = 1,15 V (0,5 % von U_N). Gemessene Werte: 226,4–234,0 V (±1,7 % von U_N), innerhalb der EN-50160-Toleranz von ±10 %.

**Frequenz:** 50 Hz Nennfrequenz, σ = 0,050 Hz. Über die Simulationsdauer liegen alle Werte im Bereich 49,85–50,21 Hz. Das ENTSO-E Continental Europe Operation Handbook definiert den Normalbetrieb als ±0,2 Hz um 50 Hz; einzelne Samples des modellierten Rauschens überschreiten dieses Band geringfügig — das ist konsistent mit dem ungeclippten Gauß-Modell und bildet ab, dass reale Netzfrequenzen das Toleranzband statistisch selten überschreiten.

**Strom:** Konsistenz zur Scheinleistung per Konstruktion: I_L1 = S/U_L1 für einphasige Geräte. Für die dreiphasig symmetrische Synchronmaschine gilt I_L1 = S/(3·U_L1), sodass jede Phase ein Drittel der Gesamtscheinleistung trägt.

### 2.6 Preprocessing-Philosophie

Das Preprocessing (`preprocessing.py`) wendet drei Stufen an:

1. **Forward-Fill / Backward-Fill:** Lückenschluss für fehlende Messwerte. Im LIVE-Modus mit Modbus TCP sind kurze Verbindungsabbrüche (<5 s) normal; `ffill()` propagiert den letzten validen Wert. Im TEST-Modus wirkungslos (synthetische Daten lückenfrei), bleibt aber pipeline-konsistent mit dem LIVE-Pfad. Geeignet nur für kurze Drops; längere Lücken werden in Milestone 3 als expliziter Datenausfall markiert.

2. **Rolling-Mean-Glättung:** Zentrierter gleitender Mittelwert, Fensterbreite 5 s, auf allen numerischen Kanälen. Reduziert das ~2 %-Abtastrauschen auf P/Q. Die Fenstergröße ist klein genug, um typische Geräteschaltvorgänge nicht zu verschmieren, aber groß genug für effektive Rauschreduktion.

3. **3σ-Clipping:** Statistische Ausreißerunterdrückung auf P und Q. Bewusst nicht auf Harmonics-Kanäle angewendet: deren Verteilungen sind typischerweise schief, das 3σ-Kriterium (Gauß-Annahme) trifft dort nicht zu.

Bewusste Vereinfachungen:

- **Keine Normalisierung:** Absolutwerte von P und Q sind das primäre NILM-Identifikationsmerkmal. Normalisierung würde Gerätesignaturen auf eine gemeinsame Skala projizieren und damit das Leistungsniveau als Trennmerkmal zerstören.
- **Kein Bandpassfilter:** Das 1-Hz-Polling des PAC4200 liefert kein auswertbares Frequenzspektrum für zeitbereichsbasierte Filter. Rolling Mean ist für diese Abtastrate ausreichend.

---

## 3. What — Konkrete Umsetzung und Ergebnisse

### 3.1 Modularchitektur

| Modul | Modus | Aufgabe |
|---|---|---|
| `config.py` | TEST/LIVE | Zentraler Modus-Schalter und Pfaddefinitionen |
| `device_profiles.py` | — | Wissensbasis: 10 Geräte, 42 Zustände, 7 Features mit Quellen-Tags |
| `data_generator.py` | TEST | Synthetische Datenerzeugung im PAC4200-Schema |
| `acquisition.py` | LIVE | Modbus-TCP-Polling (vorbereitet, aktiv ab Milestone 3) |
| `storage.py` | TEST/LIVE | `load_data()`-Abstraktion + SQLite-Persistenz |
| `preprocessing.py` | TEST/LIVE | Forward-Fill, Rolling-Mean, 3σ-Clipping |
| `visualization.py` | TEST/LIVE | Zeitreihen-Plot + P-Q-Fingerprint-Plot |

### 3.2 Generierte Daten

| Größe | Wert |
|---|---|
| Sampling-Rate | 1 Hz |
| Simulationsdauer | 1199 s (~20 min) |
| Anzahl Samples | 1200 |
| Zeitspanne | 2026-05-13 18:00:00 bis 18:19:59 |
| Gerätekategorien | 10 |
| Betriebszustände gesamt | 42 |

**Aggregierte Wirkleistung P:**

| Statistik | Wert |
|---|---|
| Minimum | −1400,5 W |
| Maximum | 7904,3 W |
| Mittelwert | 2361,9 W |
| Standardabweichung | 2699,1 W |

Das Minimum liegt im negativen Bereich, weil der PV-Wechselrichter während aktiver Einspeisung die gleichzeitig laufenden Verbraucher teilweise kompensiert (Verbraucherzählpfeil-Konvention). Das Maximum entsteht durch die Überlagerung mehrerer Großverbraucher im selben Zeitfenster.

**Netzspannung U_L1:**

| Statistik | Wert |
|---|---|
| Minimum | 226,4 V |
| Maximum | 234,0 V |
| Mittelwert | 230,0 V |
| Standardabweichung | 1,15 V (0,5 % von U_N) |

Alle Spannungswerte liegen im Bereich ±1,7 % von U_N — innerhalb der EN-50160-Toleranz.

**Netzfrequenz:**

| Statistik | Wert |
|---|---|
| Minimum | 49,846 Hz |
| Maximum | 50,208 Hz |
| Mittelwert | 49,999 Hz |
| Standardabweichung | 0,050 Hz |

**Strom-Spannungs-Konsistenz:** Für alle einphasigen Geräte gilt I_L1 = S/U_L1 per Konstruktion (Abweichung nur durch Gleitkomma-Arithmetik). Für die dreiphasig symmetrische Synchronmaschine gilt I_L1 = S/(3·U_L1) — der Vergleich I_L1·U_L1 mit S_total ergibt dort planmäßig eine Abweichung von 2/3·S, was das korrekte Dreiphasen-Modell widerspiegelt.

### 3.3 Visualisierungen

**Zeitreihen-Plot mit Ground-Truth-Overlay:**

![NILM Pipeline](plots/nilm_visualization.png)

Die Figur besteht aus zwei Subplots: oben die aggregierte Wirk- und Blindleistung über die Zeit, unten dasselbe P-Signal mit überlagerten Ground-Truth-Aktivitätsbändern der einzelnen Geräte.

Der obere Subplot zeigt die aggregierte Wirkleistung P (weiß) und Blindleistung Q (gelb, rechte Achse) über die gesamte Simulationsdauer. Die starke Varianz von P (−1400 W bis +7900 W) spiegelt die unterschiedlichen Lastprofile und die PV-Einspeisung wider. Der untere Subplot überlagert dasselbe P-Signal mit eingefärbten Aktivitätsbändern der einzelnen Geräte aus der Ground-Truth-Datei. Die Überlagerung zeigt, welche Geräte zu welchen Zeitabschnitten zum Aggregat beitragen.

**P-Q-Fingerprint-Plot:**

![P-Q-Fingerprints](plots/pq_fingerprints.png)

Jedes Gerät bildet im P-Q-Raum eine charakteristische Trajektorie über seine Betriebszustände. Wichtige Muster: Alle drei PC-Varianten liegen nahe der P-Achse (niedriges Q/P-Verhältnis durch aktive PFC bzw. dominante Widerstandslast), aber in klar unterschiedlichen Leistungsbereichen (8–22 W, 80–400 W, 120–700 W). Die Waschmaschine zeigt den weitesten Streubereich — HEAT nahe der P-Achse (Widerstandsheizung), SPIN bei hohem Q und niedrigem P (Inverter-Motor). Der PV-Wechselrichter liegt im negativen P-Bereich (Einspeisung). Die Synchronmaschine deckt alle vier P-Q-Quadranten ab (Motor- und Generatorbetrieb).

### 3.4 Datenpersistenz

**CSV-Outputs:**

| Datei | Zeilen | Größe | Inhalt |
|---|---|---|---|
| `data/raw_measurements.csv` | 1200 | 388,3 KB | PAC4200-Schema, 42 Spalten, Rohdaten |
| `data/ground_truth.csv` | 1200 | 48,9 KB | Timestamp, aktives Gerät, Zustand |
| `data/nilm_preprocessed.csv` | 1200 | 388,3 KB | Nach Forward-Fill, Rolling-Mean, 3σ-Clipping |

**SQLite-Datenbank `nilm.db` (2,51 MB):**

| Tabelle | Zeilen | Inhalt |
|---|---|---|
| `measurements_test` | 1200 | PAC4200-Kernspalten (ohne Harmonics) |
| `harmonics` | 36 000 | Oberschwingungen H2–H31 je Timestamp |
| `events` | 0 | Schaltereignisse (ab Milestone 2) |
| `measurements_live` | — | Schema bereit für Milestone 3 |

Ground Truth und Messdaten sind bewusst getrennt: Ground-Truth-Labels existieren nur im TEST-Modus und werden nicht in die DB geschrieben. Im LIVE-Modus gibt es keine Ground Truth.

---

## 4. Bewusste Vereinfachungen für Milestone 1

| Vereinfachung | Begründung |
|---|---|
| Keine Concurrent Events | Ground-Truth-Etikettierung bei Lastüberlagerung mehrdeutig; Disaggregation gleichzeitiger Lasten ist Thema Milestone 2 |
| Statische Harmonics-Profile | THD und H3/H5/H7 konstant pro Gerätezustand; dynamische Modellierung erfordert Zeitbereichs-Simulation |
| Ground Truth: ein Label pro Timestep | Bei Schedule-Überlappungen trägt der zuletzt im Ablaufplan aktive Eintrag das Label; vollständige Multi-Label-Annotation ab Milestone 2 |
| Forward-Fill nur für kurze Drops | Geeignet für Modbus-Ausfall <5 s; längere Lücken werden in Milestone 3 explizit als Datenausfall markiert |
| Keine Normalisierung | Absolutwerte P/Q sind das NILM-Identifikationsmerkmal; Normalisierung würde das Leistungsniveau als Trennmerkmal zerstören |
| PV-Einspeisung im Aggregat | Im Aggregat überlagert PV die Verbraucherlast; ohne Ground Truth im LIVE-Modus nicht direkt separierbar |

---

## 5. Übergang zu Milestone 2 und 3

**Milestone 3 (Live-Anbindung via Modbus TCP):**

- `load_data()` abstrahiert die Datenquelle vollständig — `acquisition.py` ersetzt `data_generator.py`, ohne dass andere Module angepasst werden.
- Die SQLite-Tabellen `measurements_live` und `harmonics` sind im Schema bereits definiert.
- `insert_measurement(conn, data)` in `storage.py` bietet eine direkte Schnittstelle für Modbus-Streaming einzelner Messwerte.
- Das PAC4200-Schema in CSV und DB ist mit dem Modbus-Registerformat des Siemens PAC Sentron 4200 kompatibel — kein Schema-Mapping beim Umschalten auf LIVE nötig.

**Milestone 2 (Event Detection, Klassifikation):**

- Der 7-dimensionale Feature-Raum (P, Q, cos φ, THD, H3, H5, H7) ist als Input für Clustering- und Klassifikationsalgorithmen vorbereitet.
- Der P-Q-Fingerprint-Plot zeigt, dass die 10 Geräteklassen im P-Q-Raum unterscheidbare Cluster bilden — Grundvoraussetzung für erfolgreiche Disaggregation.
- Die `events`-Tabelle in der DB ist strukturell bereit; Schalteventerkennung (Leistungssprünge zwischen aufeinanderfolgenden Samples) implementiert Milestone 2.

---

## 6. Quellenverzeichnis

**Normen:**

- IEC 61000-3-2: *Electromagnetic compatibility — Limits for harmonic current emissions (equipment input current ≤ 16 A per phase)*. Internationale Elektrotechnische Kommission. Klassen A (allgemein) und D (PCs, Monitore) für Oberschwingungsgrenzwerte.
- IEC 61000-3-12: *Electromagnetic compatibility — Limits for harmonic currents produced by equipment connected to public low-voltage systems with input current > 16 A and ≤ 75 A per phase*. Internationale Elektrotechnische Kommission.
- IEC 61727: *Photovoltaic (PV) systems — Characteristics of the utility interface*. Internationale Elektrotechnische Kommission. THD-Grenzwerte für netzgekoppelte Wechselrichter.
- IEC 61851-1: *Electric vehicle conductive charging system — Part 1: General requirements*. Internationale Elektrotechnische Kommission. Definition der Lademodi (Mode 1/2/3) und Nennströme (10 A / 16 A / 32 A).
- EN 50160: *Voltage characteristics of electricity supplied by public electricity networks*. CENELEC. Spannungstoleranzband ±10 % von U_N.
- VDE-AR-N 4105: *Erzeugungsanlagen am Niederspannungsnetz — Technische Mindestanforderungen für Anschluss und Parallelbetrieb von Erzeugungsanlagen am Niederspannungsnetz*. VDE, 2018. THD-Anforderungen für PV-Wechselrichter.

**Messdatensätze:**

- Kolter, J. Z.; Johnson, M. J.: *REDD: A Public Data Set for Energy Disaggregation Research*. Workshop on Data Mining Applications in Sustainability (SustKDD), at KDD, San Diego, 2011. Basis zur Plausibilisierung von P-Werten für Waschmaschine und Kühlschrank.
- Kelly, J.; Knottenbelt, W.: *The UK-DALE dataset, domestic appliance-level electricity demand and whole-house demand from five UK homes*. Scientific Data, 2015. DOI: 10.1038/sdata.2015.7. Basis zur Plausibilisierung von P-Werten für Waschmaschine und Kühlschrank.

**Bücher:**

- Chapman, S. J.: *Electric Machinery Fundamentals*. McGraw-Hill, 5. Aufl. ISBN 978-0073366791. Grundlage für P/Q/cos-φ-Charakteristik der Synchronmaschine.

**Hersteller-Spezifikationen:**

- 80 PLUS Certification Program: *Efficiency and power factor specifications for certified power supplies*. Plug Load Solutions. URL: plugloadsolutions.com. Basis für cos-φ-Anforderungen bei PFC-Netzteilen (> 0,9 bei Nennlast).

**Betriebshandbuch:**

- ENTSO-E: *Continental Europe Operation Handbook — Policy 1: Load-Frequency Control and Performance*. Europäisches Netz der Übertragungsnetzbetreiber. Frequenztoleranzen im Normalbetrieb: ±200 mHz (49,8–50,2 Hz).

---

## Anhang A — Generierte Outputs

| Datei | Größe | Beschreibung |
|---|---|---|
| `data/raw_measurements.csv` | 388,3 KB | Synthetische Rohmessdaten, PAC4200-Schema, 1200 Samples |
| `data/ground_truth.csv` | 48,9 KB | Geräteetiketten pro Timestep (TEST-Modus) |
| `data/nilm_preprocessed.csv` | 388,3 KB | Preprocessed (Forward-Fill, Rolling-Mean, 3σ-Clipping) |
| `data/nilm.db` | 2,51 MB | SQLite-DB: measurements_test (1200 Zeilen), harmonics (36 000 Zeilen) |
| `plots/nilm_visualization.png` | 241,9 KB | Zeitreihen-Plot: P/Q aggregiert + Ground-Truth-Overlay |
| `plots/pq_fingerprints.png` | 120,8 KB | P-Q-Fingerprint aller 10 Geräteklassen |

---

## Anhang B — Ausführung der Pipeline

```bash
# Schritt 1: Synthetische Daten generieren
python data_generator.py

# Schritt 2: Preprocessing anwenden
python preprocessing.py

# Schritt 3: Visualisierungen erzeugen
python visualization.py

# Schritt 4: In SQLite-DB speichern
python storage.py
```

Alle Skripte lesen den Betriebsmodus aus `config.py` (`MODE = "TEST"`). Für den LIVE-Betrieb (Milestone 3) genügt die Umstellung auf `MODE = "LIVE"` — die restliche Pipeline bleibt unverändert.

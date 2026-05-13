# NILM-Projekt — Schrittplan

---

## Milestone 1 — Signal Acquisition, Preprocessing, Datenspeicherung, Visualisierung
*Deadline: 14.05.2026*

**1.1 Geräteprofile definieren**
Für jedes Laborgerät realistische Signalwerte festlegen: P, Q, cos(φ), THD, H3/H5/H7 — für jeden Zustand (ON/OFF bei Typ I; alle Leistungsstufen bei Typ II). Dies ist die Wissensbasis des gesamten Systems.

Geräte laut Vorlesung:
- 2–3 PCs
- Variable Widerstandslast
- Haartrockner
- Waschmaschine
- Kühlschrank
- E-Auto (verschiedene Lademodi)
- PV-Einspeisung (AC, hinter Wechselrichter)
- Synchronmaschine (verschiedene Lastkonfigurationen)

**1.2 Synthetischer Datengenerator**
Python-Modul, das auf Basis der Geräteprofile ein aggregiertes Zeitsignal erzeugt. Geräte schalten nach definierten Zeitplänen; realistisches Messrauschen wird hinzugefügt. Gleichzeitiges Schalten mehrerer Geräte (Concurrent Events) wird in Phase 1 bewusst ausgeschlossen.

**1.3 Datenformat & Speicherung**
CSV-Schema identisch zum PAC Sentron 4200-Export definieren. Einheitliche `load_data()`-Schnittstelle, die für synthetische und echte Daten gleich funktioniert.

**1.4 Preprocessing**
Resampling auf feste Abtastrate, Behandlung fehlender Werte, Normalisierung.

**1.5 Visualisierung**
Zeitreihenplot des Aggregatsignals mit Ground-Truth-Overlay (welches Gerät war wann aktiv); P-Q-Diagramm pro Gerät zur Fingerprint-Darstellung.

---

## Milestone 2 — Event Detection, Feature Extraction, Explorative Analyse
*Deadline: 04.06.2026*

**2.1 Event Detection**
Sprünge in P (und Q) per gleitendem Differenzenfilter mit definiertem Schwellenwert erkennen.

**2.2 Feature Extraction**
Pro erkanntem Event: ΔP, ΔQ, Δcos(φ), ΔTHD, ΔH3, ΔH5, ΔH7 extrahieren (Differenz zwischen Pre- und Post-Event-Fenster). Das ergibt den Feature-Vektor pro Event.

**2.3 Explorative Clusteranalyse**
Unüberwachtes Clustering (K-Means / DBSCAN) der Feature-Vektoren — zur Validierung, ob sich Geräte im Feature-Raum klar voneinander trennen lassen.

---

## Milestone 3 — Power Disaggregation & Laboranwendung
*Deadline: 09.07.2026*

**3.1 Supervised Classification**
Random Forest (Baseline) auf gelabelten Events aus synthetischen Daten trainieren. Train/Test-Split: 80/20. Evaluation pro Gerät: Precision, Recall, F1-Score; Confusion Matrix.

**3.2 Power Disaggregation**
Erkannte Events den klassifizierten Geräten zuweisen → Leistungskurve pro Gerät rekonstruieren. Energiegenauigkeit quantifizieren: Normalized Disaggregation Error (NDE).

**3.3 Übergang auf Labordaten**
Modbus-TCP-Modul für PAC Sentron 4200 implementieren (Polling-Rate: 1 Hz). Trainiertes Modell auf echten Labordaten testen; Geräteprofile bei Bedarf kalibrieren.

---

## Prüfungsleistungen & Präsentation

Jede Teilleistung folgt dem Why–How–What-Prinzip aus der Vorlesung:
- **Why** — Problemstellung und Stand der Technik
- **How** — Konzept und gewählter Ansatz
- **What** — Konkrete Umsetzung und Ergebnisse

| Leistung | Gewichtung | Deadline |
|---|---|---|
| Projektarbeit / Laborarbeit | 25 % | [TBD] |
| Scientific Paper (IEEE, max. 5 Seiten) | 25 % | [TBD] |
| Poster-Präsentation | 25 % | [TBD] |
| Live Lab Challenge | 25 % | [TBD] |

---

## Offene Fragen an Prof. Freiburg

1. **Labordaten:** Ab welchem Milestone sollen wir mit echten Messungen beginnen, und wie viel Laborzeit steht uns zur Verfügung?
2. **Lab Challenge:** Nach welchen Kriterien wird bewertet, wenn mehrere Teams alle Geräte korrekt identifizieren — z. B. Energiegenauigkeit, Robustheit, Latenz, Code-Qualität?
3. **Sampling-Rate:** Wir planen eine Modbus-Polling-Rate von 1 Hz. Ist das aus Ihrer Sicht vertretbar?

# VoiceBridge Clinical Validation Document

**Version:** 1.0  
**Date:** April 2026  
**Project:** VoiceBridge — Offline Multilingual Clinical Intake AI  
**Hackathon:** Gemma 4 Good Hackathon (Kaggle + Google DeepMind)

---

## Disclaimer

VoiceBridge is **not a medical device**. It is a clinical decision-support tool intended
for use by trained healthcare workers only. It does not replace clinical judgment,
diagnosis, or treatment decisions. All triage output must be reviewed by a qualified
clinician before clinical action is taken. Accuracy figures in this document are based
on synthetic test cases and have not been validated in live clinical settings.

---

## 1. Overview

VoiceBridge maps its triage output to two internationally recognised frameworks:

1. **South African Triage Scale (SATS)** — Wallis, Gottschalk et al., South African
   Medical Journal, 2006; updated by the South African Triage Group (SATG) under the
   Emergency Medicine Society of South Africa (EMSSA). Licensed under Creative Commons
   Attribution-NonCommercial-ShareAlike 3.0.

2. **WHO Emergency Triage Assessment and Treatment (ETAT)** — World Health Organization,
   2016. Public domain reference document.

SATS was selected as the primary framework because it was designed specifically for
low-resource African emergency settings, has been validated across multiple African
countries including Ghana, Rwanda, Ethiopia, Pakistan, and Somalia, and achieves
sensitivity/specificity of 70–75% and 91–97% respectively in in-hospital settings
(systematic review, 2018). It requires minimal equipment — a blood pressure cuff and
a thermometer — making it deployable by community health workers with basic training.

---

## 2. SATS Structure

SATS consists of three sequential components applied in order:

**Part 1 — Clinical Discriminator List:** A list of specific high-risk presentations
that immediately assign a triage colour regardless of vital signs. If any discriminator
is present, skip Part 2 and assign the colour directly.

**Part 2 — Triage Early Warning Score (TEWS):** A composite physiological score
calculated from seven parameters. Total range: 0–17. The TEWS colour is then assigned
from the total score.

**Part 3 — Additional Investigations:** SpO2 and blood glucose results that can upgrade
(but not downgrade) the TEWS-assigned colour.

The adult version applies to patients older than 12 years or taller than 150 cm.
Paediatric versions use different vital sign ranges and are not covered in this document.

---

## 3. Adult TEWS Scoring Table

Each parameter is scored 0–3. Grey cells in the original poster cannot be assigned a
score (e.g. temperature can only score 0 or 2, not 1 or 3). The total is the TEWS.

### 3.1 Respiratory Rate (breaths/min)

| Score | Range |
|---|---|
| 3 | ≤ 8 |
| 2 | 9–14 or ≥ 30 |
| 1 | 25–29 |
| 0 | 15–24 (normal) |

### 3.2 Heart Rate (beats/min)

| Score | Range |
|---|---|
| 3 | ≤ 40 or ≥ 130 |
| 2 | 41–50 or 111–129 |
| 1 | 100–110 (confirmed in Ghana validation, Rominski et al. 2014) |
| 0 | 51–99 (normal) |

### 3.3 Systolic Blood Pressure (mmHg)

| Score | Range |
|---|---|
| 3 | ≤ 70 |
| 2 | 71–80 |
| 1 | 81–100 |
| 0 | ≥ 101 (normal) |

*Note: SATS uses SBP only, not diastolic. High BP does not score points in TEWS.*

### 3.4 Temperature (°C)

| Score | Range |
|---|---|
| 2 | < 35.0 or > 38.5 |
| 0 | 35.0–38.5 (normal) |

*Temperature can only score 0 or 2. Scores of 1 and 3 are not possible for this parameter.*

### 3.5 AVPU (Consciousness)

| Score | Level |
|---|---|
| 3 | U — Unresponsive |
| 2 | P — Responds to Pain only |
| 1 | V — Responds to Voice only |
| 0 | A — Alert |

### 3.6 Mobility

| Score | Observation |
|---|---|
| 2 | Carried/bedridden — cannot walk at all |
| 1 | Assisted — requires support to walk |
| 0 | Normal — walks independently |

*Patients in a wheelchair due to permanent paralysis score 2 (they are at higher risk).*

### 3.7 Trauma

| Score | Condition |
|---|---|
| 1 | Any injury within the past 48 hours |
| 0 | No injury |

### 3.8 TEWS Total → SATS Colour

| TEWS Total | SATS Colour | Urgency |
|---|---|---|
| 0–2 | GREEN | Non-urgent |
| 3–4 | YELLOW | Urgent |
| 5–6 | ORANGE | Very urgent |
| ≥ 7 | RED | Emergency |
| — | BLUE | No signs of life |

*Source: confirmed across Wallis et al. 2006, Dixon et al. 2021, Rominski et al. 2014,
and the EMSSA SATS Training Manual 2012.*

---

## 4. Part 3 — Additional Investigations (SpO2 and Blood Glucose)

These results are checked after TEWS and can only upgrade the triage colour, never
downgrade it.

### 4.1 Oxygen Saturation (SpO2)

| SpO2 | Action |
|---|---|
| < 90% | Upgrade to RED regardless of TEWS |
| 90–94% | Upgrade to at least ORANGE |
| ≥ 95% | No change |

### 4.2 Blood Glucose

| Blood glucose | Action |
|---|---|
| < 3.0 mmol/L with altered consciousness | Upgrade to RED |
| < 3.0 mmol/L without altered consciousness | Upgrade to at least ORANGE |
| > 20 mmol/L | Upgrade to at least ORANGE |

---

## 5. Part 1 — SATS Clinical Discriminator List

Discriminators are checked before TEWS. If present, assign the colour immediately.
The full SATS discriminator list contains 32 conditions. Key discriminators by colour:

### 5.1 RED Discriminators (Emergency Signs)

These assign RED immediately — do not calculate TEWS:

- Airway obstruction or apnoea
- Severe respiratory distress (cannot speak in full sentences, accessory muscle use)
- Active uncontrolled haemorrhage
- Active generalised seizure / convulsion
- AVPU = P or U (responds to pain only, or unresponsive)
- Suspected spinal injury with neurological deficit
- High-energy mechanism of injury (vehicle rollover, ejection, fall > 3m, penetrating
  trunk injury)
- Stab or gunshot to neck, chest, or abdomen
- Acute limb ischaemia (cold, pale, pulseless limb)
- Suspected eclampsia (seizure in pregnancy)
- Anaphylaxis with stridor, wheeze, or haemodynamic compromise
- Burns > 20% body surface area, or any airway burn
- Submersion / near-drowning

### 5.2 ORANGE Discriminators (Very Urgent Signs)

These assign at least ORANGE — TEWS may independently give a higher colour:

- Mechanism of injury — high energy transfer (even if physiology currently normal)
- Stab to neck (even if currently haemodynamically stable)
- Pregnancy with bleeding > 20 weeks gestation
- Chest pain — suspected STEMI or aortic dissection
- Altered conscious level (GCS 9–13, or AVPU = V)
- Severe pain (unresponsive to simple analgesia)
- Acute stroke symptoms (facial droop, arm weakness, speech disturbance)
- Diabetic ketoacidosis (hyperglycaemia + rapid breathing)

### 5.3 YELLOW Discriminators (Urgent Signs)

These assign at least YELLOW:

- Moderate pain
- Vomiting blood (haematemesis)
- Head injury with any loss of consciousness
- Suspected fracture (deformity, point tenderness, inability to weight-bear)
- Pregnancy with mild bleeding < 20 weeks
- Psychiatric emergency (active suicidal ideation, acute psychosis)
- Fever in an infant < 3 months

### 5.4 BLUE — Deceased / Expectant

Assigned when ALL of the following are present in a resource-limited setting:

- Apnoea (no spontaneous breathing)
- No palpable pulse
- Fixed, dilated pupils

Or:

- Rigor mortis present
- Unsurvivable injuries (decapitation, evisceration of thoracic contents)

*BLUE should not be assigned without senior clinician review where possible.*

---

## 6. WHO ETAT Alignment

The WHO Emergency Triage Assessment and Treatment (ETAT) framework uses an ABC-c-c-DO
mnemonic: **Airway, Breathing, Circulation, Coma, Convulsion, Dehydration, Other**.

### 6.1 SATS ↔ ETAT Mapping

| SATS Colour | WHO ETAT Category | Clinical Basis |
|---|---|---|
| RED | Emergency Signs | Airway obstruction, absent breathing, severe respiratory distress, shock (cold extremities + weak rapid pulse + altered consciousness), coma (GCS < 9), active convulsion, severe dehydration |
| ORANGE | Priority Signs — Severe | Signs of severe illness not meeting immediate emergency threshold; altered but responsive consciousness; moderate respiratory distress; suspected sepsis |
| YELLOW | Priority Signs — Moderate | Any condition requiring urgent but not immediate attention; moderate pain; moderate dehydration |
| GREEN | Non-urgent | Stable vital signs; no emergency or priority signs; can safely wait |
| BLUE | Dead on Arrival | No signs of life; not applicable for ETAT intervention |

### 6.2 WHO ETAT Emergency Signs (→ RED in SATS)

- **Airway:** Obstructed or absent
- **Breathing:** Absent, gasping, or severe distress (central cyanosis, severe recession)
- **Circulation:** Shock — cold hands + capillary refill > 3 seconds + weak fast pulse
- **Coma:** Any coma or convulsion (GCS < 9 in adult)
- **Convulsion:** Active seizure at time of triage
- **Dehydration:** Severe — sunken eyes, very slow skin pinch, unable to drink

---

## 7. VoiceBridge Schema Mapping

The `TriageOutput` Pydantic model fields map to SATS as follows:

| Field | Clinical Basis | Notes |
|---|---|---|
| `triage_level` | SATS colour code (RED/ORANGE/YELLOW/GREEN/BLUE) | Primary output |
| `red_flag_indicators` | SATS emergency and very urgent discriminators | List of matched discriminators |
| `vital_signs_reported` | TEWS parameters extracted from transcript | RR, HR, SBP, SpO2, temp, AVPU, glucose |
| `tews_score` | Calculated TEWS total | 0–17; may be None if vitals not reported |
| `recommended_action` | SATS time-to-treatment targets | See Section 8 |
| `confidence_score` | LLM output certainty | Not a clinical certainty score — see Section 10 |
| `language_detected` | ISO 639-1 code | Used for multilingual red flag keyword lookup |
| `transcript_original` | Raw transcript in source language | For clinical review |
| `transcript_english` | English translation | Used for triage classification |

---

## 8. SATS Time-to-Treatment Targets

| Colour | Target Time to First Assessment | Clinical Disposition |
|---|---|---|
| RED | Immediate — within 0 minutes | Resuscitation area; physician called immediately |
| ORANGE | Within 10 minutes | High-acuity zone; senior nurse assessment |
| YELLOW | Within 60 minutes | Urgent area; nurse assessment |
| GREEN | Within 240 minutes (4 hours) | Waiting area; may be redirected to primary care |
| BLUE | N/A | Managed per local deceased protocol |

---

## 9. Dual-Layer Safety Architecture

VoiceBridge uses two independent layers to determine triage output. The rule-based
validator acts as a hard safety net against LLM under-triage.

```
Audio Input
    ↓
Gemma 4 E4B transcription (multilingual → English)
    ↓
Layer 1: LLM Triage Classifier (Gemma 4 26B MoE)
    - Full SATS 2023 criteria in system prompt
    - Returns TriageOutput with triage_level + red_flag_indicators
    ↓
Layer 2: Rule-Based SATS Validator (_rule_based_sats)
    - Hard-coded TEWS thresholds (Section 3)
    - Hard-coded SpO2 and glucose upgrade rules (Section 4)
    - Keyword-based discriminator detection (Section 5)
    ↓
Conflict Resolution:
    - If rule-based level == LLM level: output directly
    - If rule-based level is MORE urgent: override + display warning to clinician
    - If rule-based level is LESS urgent: keep LLM output (LLM may have detected
      discriminators from narrative that rule-based logic cannot parse)
    ↓
PDF Triage Form + Dashboard Display
```

The rule-based layer never downgrades. It can only upgrade or confirm.
Conflict warnings are displayed prominently in the UI and printed on the PDF form.

---

## 10. Multilingual Red Flag Keywords

The following terms in the transcript trigger immediate RED flag detection in the
rule-based layer, independent of LLM output. These are high-specificity terms for
life-threatening presentations sourced from clinical terminology in each language.

| Language | Code | Keywords (RED triggers) |
|---|---|---|
| English | en | not breathing, stopped breathing, no pulse, unconscious, fitting, seizure, convulsing, unresponsive, choking, airway blocked, heavy bleeding, uncontrolled bleeding |
| Swahili | sw | hapumui, anapumua vibaya sana, hana mapigo ya moyo, hana fahamu, mshtuko, kutoka damu nyingi, kizuizi cha njia ya hewa |
| Tagalog | tl | hindi humihinga, walang tibok ng puso, walang malay, nagse-seizure, nanghihina ng todo, matinding pagdurugo |
| Hausa | ha | baya numfashi, babu bugun zuciya, baya sani, farfadiya, zubar da jini mai yawa |
| Bengali | bn | শ্বাস নিচ্ছে না, নাড়ি নেই, অজ্ঞান, খিঁচুনি, অনেক রক্ত পড়ছে |
| Hindi | hi | सांस नहीं ले रहा, नब्ज नहीं है, बेहोश, दौरा पड़ रहा है, बहुत खून बह रहा है |
| Amharic | am | አይተነፍስም, ምት የለም, ንቃተ ህሊና የለም, የሚያናውጥ, ብዙ ደም እየፈሰሰ |
| French | fr | ne respire pas, pas de pouls, inconscient, convulsions, saignement abondant |

---

## 11. Known Limitations

These limitations must be understood before any clinical deployment:

**11.1 Synthetic Validation Only**
Triage accuracy figures in benchmark results are based on 500 synthetic training cases
and 20 synthetic test cases. The model has not been validated on real patient encounters.
Any deployment in clinical settings requires prospective validation with real patient data.

**11.2 Error Direction — Over-Triage Only**
All 5 misclassifications in the Phase 3.3 benchmark were over-triage errors (system
assigned higher urgency than ground truth). In a clinical context over-triage is the
preferred failure mode — it results in a patient receiving more attention than strictly
necessary rather than being under-served.

**11.3 Vital Signs May Not Be Reported**
VoiceBridge extracts vital signs from spoken narrative. If the nurse does not state a
vital sign, it will not appear in the output. The rule-based validator cannot calculate
a TEWS without reported values. The LLM classifier may still infer triage level from
clinical narrative alone.

**11.4 Chronic Illness Caveat**
Patients with TB, HIV/AIDS, or other chronic conditions may have chronically abnormal
baseline vital signs. A patient with pulmonary TB may have a high RR at rest not
indicating acute emergency. The SATS training manual explicitly notes these patients
may be over-triaged by TEWS alone. Senior clinician review is required for known
chronically unwell patients.

**11.5 LLM Confidence Score Is Not a Clinical Certainty Score**
The `confidence_score` field reflects the LLM's output token probability distribution,
not clinical certainty. A high confidence score does not mean the triage assignment is
clinically correct. The field should be treated as an internal quality indicator only.

**11.6 Paediatric Patients**
This implementation uses the adult TEWS only (patients > 12 years or > 150 cm). The
paediatric SATS uses different vital sign ranges. VoiceBridge should not be used to
triage infants or young children without a paediatric TEWS extension.

**11.7 Audio Quality**
Transcription accuracy degrades with background noise, strong accents, and poor
microphone quality. Audio quality below a signal-to-noise ratio of approximately 15dB
may produce unreliable transcripts and therefore unreliable triage output.

---

## 12. References

1. Wallis LA, Gottschalk SB, Wood D, Bruijns S, de Vries S, Balfour C, on behalf of the
   Cape Triage Group. The Cape Triage Score — a triage system for South Africa. *South
   African Medical Journal.* 2006;96(1):53–56.

2. Gottschalk SB, Wood D, DeVries S, Wallis LA, Bruijns S. The Cape Triage Score: a new
   triage system South Africa. Proposal from the Cape Triage Group. *Emergency Medicine
   Journal.* 2006;23(2):149–153.

3. Rominski S, Bell SA, Oduro G, Ampong P, Oteng R, Donkor P. The implementation of the
   South African Triage Score (SATS) in an urban teaching hospital, Ghana. *African
   Journal of Emergency Medicine.* 2014;4(2):71–75.

4. Dixon J, Burkholder T, Pigoga J, Lee M, Moodley K, de Vries S, Wallis L,
   Mould-Millman NK. Validity and reliability of the South African Triage Scale in
   prehospital providers. *BMC Emergency Medicine.* 2021;21:8.

5. Rosedale K, Smith ZA, Davies H, Wood D. The effectiveness of the South African Triage
   Score (SATS) in a rural emergency department. *South African Medical Journal.*
   2011;101(8):537–540.

6. Twomey M, Wallis LA, Thompson ML, Myers JE. The South African triage scale (adult
   version) provides reliable acuity ratings. *International Emergency Nursing.*
   2012;20(3):142–150.

7. Emergency Medicine Society of South Africa (EMSSA). *South African Triage Scale
   Training Manual.* 2012. Licensed under Creative Commons Attribution-NonCommercial-
   ShareAlike 3.0. Available at: emssa.org.za

8. World Health Organization. *Emergency Triage Assessment and Treatment (ETAT):
   Manual for Participants.* WHO Press, Geneva, 2005 (updated 2016).
   Available at: apps.who.int/iris

9. Sunyoto T, Van den Bergh R, Valles P, et al. Providing emergency care and assessing
   a patient triage system in a referral hospital in Somaliland. *BMC Health Services
   Research.* 2014;14:531.

10. Dalwai MK, Twomey M, Maikere J, et al. Reliability and accuracy of the South African
    Triage Scale when used by nurses in the emergency department of Timergara Hospital,
    Pakistan. *South African Medical Journal.* 2014;104(5):372–375.

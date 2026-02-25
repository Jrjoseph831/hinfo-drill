"""
synthea_integration.py - Import Synthea-generated CSV data into the
Health Informatics Learning Platform database.

Synthea (https://github.com/synthetichealth/synthea) generates realistic
synthetic patient records in CSV format. This module parses those CSVs
and maps them into the platform's 16-table schema.

Supported Synthea CSV files (all optional — missing files are skipped):
  patients.csv, encounters.csv, conditions.csv, medications.csv,
  observations.csv, procedures.csv, allergies.csv, careplans.csv,
  organizations.csv, providers.csv, payers.csv, claims.csv

If no Synthea directory is provided, a built-in sample dataset of ~50
patients is generated programmatically (no Java/Synthea install needed).

Public API
----------
    load_synthea_csv(db_path, synthea_dir)  -- import from CSV directory
    generate_synthea_sample(db_path)        -- generate built-in sample
"""

import csv
import os
import random
import sqlite3
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

# Map Synthea SNOMED condition codes to ICD-10 (common subset)
SNOMED_TO_ICD10 = {
    "44054006": ("I10", "Essential (primary) hypertension"),
    "15777000": ("E78.5", "Hyperlipidemia, unspecified"),
    "73211009": ("E11.9", "Type 2 diabetes mellitus without complications"),
    "53741008": ("I25.10", "Atherosclerotic heart disease"),
    "84114007": ("I50.9", "Heart failure, unspecified"),
    "185086009": ("J06.9", "Acute upper respiratory infection"),
    "195662009": ("J18.9", "Pneumonia, unspecified organism"),
    "40055000": ("J44.1", "COPD with acute exacerbation"),
    "431855005": ("J44.1", "COPD"),
    "233604007": ("J18.9", "Pneumonia"),
    "38341003": ("I10", "Hypertension"),
    "59621000": ("I10", "Essential hypertension"),
    "162864005": ("M54.5", "Low back pain"),
    "10509002": ("M54.5", "Low back pain"),
    "36971009": ("E11.9", "Type 2 diabetes mellitus"),
    "44054006": ("I10", "Essential hypertension"),
    "698754002": ("J44.1", "COPD"),
    "449868002": ("F32.9", "Major depressive disorder"),
    "87433001": ("E78.5", "Hyperlipidemia"),
    "230690007": ("I63.9", "Cerebral infarction"),
    "22298006": ("I21.9", "Acute myocardial infarction"),
    "399211009": ("I48.91", "Atrial fibrillation"),
    "65966004": ("R50.9", "Fever"),
    "386661006": ("R50.9", "Fever, unspecified"),
    "36955009": ("N17.9", "Acute kidney failure"),
    "431856006": ("K21.0", "GERD"),
    "235595009": ("K21.0", "GERD with esophagitis"),
    "68496003": ("N39.0", "Urinary tract infection"),
    "301011002": ("R07.9", "Chest pain"),
    "267036007": ("R06.02", "Shortness of breath"),
    "49727002": ("R11.2", "Nausea with vomiting"),
    "25064002": ("R42", "Dizziness"),
    "62106007": ("R55", "Syncope"),
    "128613002": ("A41.9", "Sepsis"),
    "91302008": ("A41.9", "Sepsis, unspecified"),
    "424393004": ("E86.0", "Dehydration"),
    "271737000": ("D64.9", "Anemia, unspecified"),
    "126906006": ("C34.90", "Malignant neoplasm of lung"),
    "254837009": ("C50.919", "Malignant neoplasm of breast"),
    "399068003": ("C61", "Malignant neoplasm of prostate"),
    "56265001": ("I50.9", "Heart disease"),
    "46635009": ("E11.9", "Diabetes mellitus type 1"),
    "190905008": ("E11.9", "Diabetes mellitus"),
    "40275004": ("I24.0", "Acute coronary syndrome"),
    "230265002": ("G45.9", "Transient ischemic attack"),
}

# Map Synthea encounter classes to our encounter_type values
ENCOUNTER_CLASS_MAP = {
    "inpatient": "inpatient",
    "emergency": "ED",
    "outpatient": "outpatient",
    "ambulatory": "outpatient",
    "urgentcare": "ED",
    "wellness": "outpatient",
    "snf": "inpatient",
    "home": "telehealth",
    "virtual": "telehealth",
}

# Departments by encounter type (for random assignment)
DEPT_MAP_BY_TYPE = {
    "inpatient": [2, 4, 5, 6, 7, 8],   # ICU, Med-Surg, Cardiology, Oncology, Ortho, Neuro
    "ED": [1],                            # Emergency Department
    "outpatient": [9, 10, 11, 12, 13, 15],  # Radiology, Lab, Pharmacy, OB, Peds, Rehab
    "observation": [2, 4],                # ICU, Med-Surg
    "telehealth": [4, 13, 14],            # Med-Surg, Peds, Behavioral Health
}

# Synthea observation codes we map to lab_results
LOINC_TO_LAB = {
    "6690-2":  ("WBC", "10^3/uL", 4.5, 11.0),
    "789-8":   ("RBC", "10^6/uL", 4.2, 5.9),
    "718-7":   ("Hemoglobin", "g/dL", 12.0, 17.5),
    "4544-3":  ("Hematocrit", "%", 36.0, 51.0),
    "777-3":   ("Platelets", "10^3/uL", 150.0, 400.0),
    "2951-2":  ("Sodium", "mEq/L", 136.0, 145.0),
    "2823-3":  ("Potassium", "mEq/L", 3.5, 5.0),
    "2075-0":  ("Chloride", "mEq/L", 98.0, 106.0),
    "2028-9":  ("CO2", "mEq/L", 23.0, 29.0),
    "3094-0":  ("BUN", "mg/dL", 7.0, 20.0),
    "2160-0":  ("Creatinine", "mg/dL", 0.7, 1.3),
    "2345-7":  ("Glucose", "mg/dL", 70.0, 100.0),
    "17861-6": ("Calcium", "mg/dL", 8.5, 10.5),
    "1751-7":  ("Albumin", "g/dL", 3.5, 5.5),
    "1975-2":  ("Total Bilirubin", "mg/dL", 0.1, 1.2),
    "1742-6":  ("ALT", "U/L", 7.0, 56.0),
    "1920-8":  ("AST", "U/L", 10.0, 40.0),
    "4548-4":  ("HbA1c", "%", 4.0, 5.6),
    "2093-3":  ("Total Cholesterol", "mg/dL", 0.0, 200.0),
    "2571-8":  ("Triglycerides", "mg/dL", 0.0, 150.0),
    "2085-9":  ("HDL", "mg/dL", 40.0, 60.0),
    "18262-6": ("LDL", "mg/dL", 0.0, 100.0),
    "2089-1":  ("LDL", "mg/dL", 0.0, 100.0),
}

# Synthea observation codes that are vitals
VITAL_CODES = {
    "8310-5":  "temperature",
    "8867-4":  "heart_rate",
    "8480-6":  "systolic_bp",
    "8462-4":  "diastolic_bp",
    "9279-1":  "respiratory_rate",
    "2708-6":  "spo2",
    "59576-9": "bmi",
    "8302-2":  "height_cm",
    "29463-7": "weight_kg",
}


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _parse_dt(s):
    """Parse a Synthea datetime string (ISO-ish format)."""
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def _abnormal_flag(val, ref_low, ref_high):
    try:
        v = float(val)
    except (ValueError, TypeError):
        return "N"
    if v < ref_low:
        return "C" if v < ref_low * 0.7 else "L"
    if v > ref_high:
        return "C" if v > ref_high * 1.5 else "H"
    return "N"


# ---------------------------------------------------------------------------
# CSV import (for users who run Synthea externally)
# ---------------------------------------------------------------------------

def load_synthea_csv(db_path, synthea_dir):
    """Import Synthea CSV output into the database.

    Expects *synthea_dir* to contain standard Synthea CSV files.
    The database schema must already exist (call init_db first with
    schema_only=True if needed).
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Track ID mappings (Synthea UUIDs -> our integer IDs)
    patient_map = {}   # synthea_id -> mrn
    encounter_map = {} # synthea_id -> encounter_id
    provider_map = {}  # synthea_id -> provider_id

    mrn_counter = [0]
    def next_mrn():
        mrn_counter[0] += 1
        return f"MRN-{mrn_counter[0]:07d}"

    # --- Patients ---
    patients_csv = os.path.join(synthea_dir, "patients.csv")
    if os.path.exists(patients_csv):
        with open(patients_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mrn = next_mrn()
                sid = row.get("Id", "")
                patient_map[sid] = mrn
                gender_map = {"M": "Male", "F": "Female"}
                cur.execute(
                    "INSERT INTO patients (mrn, first_name, last_name, dob, gender, race, "
                    "ethnicity, address, city, state, zip, phone, email, primary_language, "
                    "insurance_plan, insurance_id, created_at, status) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (mrn,
                     row.get("FIRST", ""),
                     row.get("LAST", ""),
                     row.get("BIRTHDATE", ""),
                     gender_map.get(row.get("GENDER", ""), "Unknown"),
                     row.get("RACE", "Unknown"),
                     row.get("ETHNICITY", "Unknown"),
                     row.get("ADDRESS", ""),
                     row.get("CITY", ""),
                     row.get("STATE", ""),
                     row.get("ZIP", ""),
                     row.get("Id", "")[:15],  # placeholder phone
                     f"{row.get('FIRST','').lower()}.{row.get('LAST','').lower()}@email.com",
                     "English",
                     "Blue Cross Blue Shield PPO",
                     f"BCBS{random.randint(100000000, 999999999)}",
                     _fmt(datetime.now()),
                     "active" if not row.get("DEATHDATE") else "deceased"),
                )

    # --- Providers ---
    providers_csv = os.path.join(synthea_dir, "providers.csv")
    if os.path.exists(providers_csv):
        with open(providers_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                sid = row.get("Id", "")
                npi = f"{1000000000 + i}"
                dept_id = (i % 15) + 1
                cur.execute(
                    "INSERT INTO providers (npi, first_name, last_name, credential, "
                    "specialty, department_id, email, phone, active) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (npi,
                     row.get("NAME", "Provider").split()[0] if row.get("NAME") else f"Provider{i}",
                     row.get("NAME", "Last").split()[-1] if row.get("NAME") else f"Last{i}",
                     "MD",
                     row.get("SPECIALITY", row.get("SPECIALTY", "General")),
                     dept_id,
                     f"provider{i}@merithealth.org",
                     f"(555) 200-{i:04d}",
                     1),
                )
                provider_map[sid] = cur.lastrowid

    # Ensure we have at least one provider
    if not provider_map:
        cur.execute(
            "INSERT INTO providers (npi, first_name, last_name, credential, specialty, "
            "department_id, email, phone, active) VALUES (?,?,?,?,?,?,?,?,?)",
            ("1000000000", "Default", "Provider", "MD", "General", 1,
             "default@merithealth.org", "(555) 200-0000", 1))
        provider_map["default"] = cur.lastrowid

    default_prov = list(provider_map.values())[0]

    # --- Encounters ---
    encounters_csv = os.path.join(synthea_dir, "encounters.csv")
    enc_meta = []
    if os.path.exists(encounters_csv):
        with open(encounters_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("Id", "")
                patient_sid = row.get("PATIENT", "")
                mrn = patient_map.get(patient_sid)
                if not mrn:
                    continue
                enc_class = row.get("ENCOUNTERCLASS", "outpatient").lower()
                enc_type = ENCOUNTER_CLASS_MAP.get(enc_class, "outpatient")
                admit_dt = _parse_dt(row.get("START"))
                discharge_dt = _parse_dt(row.get("STOP"))
                if not admit_dt:
                    continue
                is_open = discharge_dt is None
                los_days = 0
                if discharge_dt:
                    los_days = round((discharge_dt - admit_dt).total_seconds() / 86400, 1)
                prov_id = provider_map.get(row.get("PROVIDER"), default_prov)
                dept_id = random.choice(DEPT_MAP_BY_TYPE.get(enc_type, [4]))
                complaint = row.get("REASONDESCRIPTION", "") or row.get("DESCRIPTION", "")

                cur.execute(
                    "INSERT INTO encounters (patient_mrn, encounter_type, admission_date, "
                    "discharge_date, attending_provider_id, department_id, chief_complaint, "
                    "disposition, status, los_days) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (mrn, enc_type, _fmt(admit_dt),
                     _fmt(discharge_dt) if discharge_dt else None,
                     prov_id, dept_id, complaint[:200] if complaint else None,
                     "Discharged home" if discharge_dt else None,
                     "closed" if discharge_dt else "open",
                     los_days),
                )
                enc_id = cur.lastrowid
                encounter_map[sid] = enc_id
                enc_meta.append((enc_id, mrn, admit_dt, discharge_dt or admit_dt))

    # --- Conditions -> diagnoses ---
    conditions_csv = os.path.join(synthea_dir, "conditions.csv")
    if os.path.exists(conditions_csv):
        with open(conditions_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                enc_sid = row.get("ENCOUNTER", "")
                enc_id = encounter_map.get(enc_sid)
                mrn = patient_map.get(row.get("PATIENT", ""))
                if not enc_id or not mrn:
                    continue
                snomed = row.get("CODE", "")
                desc = row.get("DESCRIPTION", "")
                icd10, icd_desc = SNOMED_TO_ICD10.get(snomed, (snomed[:7], desc))
                dx_date = row.get("START", "")
                dx_dt = _parse_dt(dx_date)
                cur.execute(
                    "INSERT INTO diagnoses (encounter_id, patient_mrn, icd10_code, "
                    "description, diagnosis_type, diagnosed_date, status) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (enc_id, mrn, icd10, icd_desc or desc,
                     "primary", _fmt(dx_dt) if dx_dt else dx_date,
                     "resolved" if row.get("STOP") else "active"),
                )

    # --- Medications ---
    meds_csv = os.path.join(synthea_dir, "medications.csv")
    if os.path.exists(meds_csv):
        with open(meds_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                enc_sid = row.get("ENCOUNTER", "")
                enc_id = encounter_map.get(enc_sid)
                mrn = patient_map.get(row.get("PATIENT", ""))
                if not enc_id or not mrn:
                    continue
                prov_id = provider_map.get(row.get("PROVIDER", ""), default_prov)
                start_dt = _parse_dt(row.get("START"))
                stop_dt = _parse_dt(row.get("STOP"))
                cur.execute(
                    "INSERT INTO medications (encounter_id, patient_mrn, medication_name, "
                    "dosage, route, frequency, prescribing_provider_id, start_date, "
                    "end_date, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (enc_id, mrn,
                     row.get("DESCRIPTION", "Unknown medication"),
                     row.get("DISPENSES", ""),
                     "PO",
                     row.get("REASONDESCRIPTION", "Daily"),
                     prov_id,
                     _fmt(start_dt) if start_dt else None,
                     _fmt(stop_dt) if stop_dt else None,
                     "completed" if stop_dt else "active"),
                )

    # --- Observations -> lab_results + vital_signs ---
    obs_csv = os.path.join(synthea_dir, "observations.csv")
    if os.path.exists(obs_csv):
        with open(obs_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                enc_sid = row.get("ENCOUNTER", "")
                enc_id = encounter_map.get(enc_sid)
                mrn = patient_map.get(row.get("PATIENT", ""))
                if not enc_id or not mrn:
                    continue
                code = row.get("CODE", "")
                value = row.get("VALUE", "")
                obs_dt = _parse_dt(row.get("DATE"))
                obs_dt_str = _fmt(obs_dt) if obs_dt else None
                result_dt_str = _fmt(obs_dt + timedelta(minutes=random.randint(30, 180))) if obs_dt else None

                if code in LOINC_TO_LAB:
                    name, unit, ref_low, ref_high = LOINC_TO_LAB[code]
                    flag = _abnormal_flag(value, ref_low, ref_high)
                    cur.execute(
                        "INSERT INTO lab_results (encounter_id, patient_mrn, test_name, "
                        "test_code, result_value, result_unit, reference_range_low, "
                        "reference_range_high, abnormal_flag, collected_datetime, "
                        "resulted_datetime, ordering_provider_id, status) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (enc_id, mrn, name, code, str(value), unit,
                         ref_low, ref_high, flag,
                         obs_dt_str, result_dt_str, default_prov, "final"),
                    )

                elif code in VITAL_CODES:
                    vital_col = VITAL_CODES[code]
                    # We need to batch vitals by encounter+datetime
                    # Simpler: insert one row per vital reading
                    try:
                        v = float(value)
                    except (ValueError, TypeError):
                        continue
                    vals = {
                        "temperature": None, "heart_rate": None,
                        "systolic_bp": None, "diastolic_bp": None,
                        "respiratory_rate": None, "spo2": None,
                        "height_cm": None, "weight_kg": None, "bmi": None,
                    }
                    vals[vital_col] = v
                    cur.execute(
                        "INSERT INTO vital_signs (encounter_id, patient_mrn, "
                        "recorded_datetime, temperature, heart_rate, systolic_bp, "
                        "diastolic_bp, respiratory_rate, spo2, height_cm, weight_kg, "
                        "bmi, recorded_by_provider_id) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (enc_id, mrn, obs_dt_str,
                         vals["temperature"], vals["heart_rate"],
                         vals["systolic_bp"], vals["diastolic_bp"],
                         vals["respiratory_rate"], vals["spo2"],
                         vals["height_cm"], vals["weight_kg"],
                         vals["bmi"], default_prov),
                    )

    # --- Procedures ---
    procs_csv = os.path.join(synthea_dir, "procedures.csv")
    if os.path.exists(procs_csv):
        with open(procs_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                enc_sid = row.get("ENCOUNTER", "")
                enc_id = encounter_map.get(enc_sid)
                mrn = patient_map.get(row.get("PATIENT", ""))
                if not enc_id or not mrn:
                    continue
                proc_dt = _parse_dt(row.get("DATE") or row.get("START"))
                cur.execute(
                    "INSERT INTO procedures (encounter_id, patient_mrn, cpt_code, "
                    "description, performing_provider_id, procedure_date, "
                    "department_id, status) VALUES (?,?,?,?,?,?,?,?)",
                    (enc_id, mrn,
                     row.get("CODE", "99999"),
                     row.get("DESCRIPTION", "Procedure"),
                     default_prov,
                     _fmt(proc_dt) if proc_dt else None,
                     random.randint(1, 15),
                     "completed"),
                )

    # --- Allergies ---
    allergies_csv = os.path.join(synthea_dir, "allergies.csv")
    if os.path.exists(allergies_csv):
        with open(allergies_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mrn = patient_map.get(row.get("PATIENT", ""))
                if not mrn:
                    continue
                cur.execute(
                    "INSERT INTO allergies (patient_mrn, allergen, allergy_type, "
                    "reaction, severity, reported_date, status) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (mrn,
                     row.get("DESCRIPTION", "Unknown"),
                     row.get("TYPE", "drug").lower() if row.get("TYPE") else "drug",
                     row.get("REACTION1", "") or row.get("DESCRIPTION", ""),
                     row.get("SEVERITY1", "moderate") or "moderate",
                     row.get("START", ""),
                     "active" if not row.get("STOP") else "inactive"),
                )

    # --- Claims -> insurance_claims ---
    claims_csv = os.path.join(synthea_dir, "claims.csv")
    if os.path.exists(claims_csv):
        with open(claims_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mrn = patient_map.get(row.get("PATIENTID", row.get("PATIENT", "")))
                enc_id = encounter_map.get(row.get("ENCOUNTER", ""))
                if not mrn or not enc_id:
                    continue
                try:
                    amount = float(row.get("TOTAL_CLAIM_COST", row.get("AMOUNT", 0)))
                except (ValueError, TypeError):
                    amount = 0
                paid = amount * random.uniform(0.6, 1.0) if random.random() > 0.15 else 0
                denied = amount - paid if paid < amount * 0.99 else 0
                status = "paid" if paid > 0 else "denied"
                cur.execute(
                    "INSERT INTO insurance_claims (encounter_id, patient_mrn, "
                    "insurance_plan, claim_amount, paid_amount, denied_amount, "
                    "claim_status, submitted_date, resolved_date, denial_reason) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (enc_id, mrn, "Synthea Payer",
                     round(amount, 2), round(paid, 2), round(denied, 2),
                     status, row.get("FROMDATE", ""),
                     row.get("TODATE", ""), None),
                )

    conn.commit()
    conn.close()
    return {
        "patients": len(patient_map),
        "encounters": len(encounter_map),
        "providers": len(provider_map),
    }


# ---------------------------------------------------------------------------
# Built-in Synthea-style sample generator (no Java needed)
#
# Generates ~50 patients with clinically coherent histories:
#   - A diabetic patient has metformin, HbA1c labs, endocrinology visits
#   - A cardiac patient has troponin, ECG, cardiology encounters
#   - Conditions drive medications, labs, and procedures realistically
# ---------------------------------------------------------------------------

# Patient archetypes: each defines a clinical profile
ARCHETYPES = [
    {
        "name": "Diabetic",
        "weight": 20,
        "conditions": [
            ("E11.9", "Type 2 diabetes mellitus without complications"),
            ("E78.5", "Hyperlipidemia, unspecified"),
            ("I10", "Essential (primary) hypertension"),
        ],
        "medications": [
            ("Metformin", "500 mg", "PO", "BID"),
            ("Atorvastatin", "40 mg", "PO", "Daily"),
            ("Lisinopril", "10 mg", "PO", "Daily"),
        ],
        "labs": [
            ("HbA1c", "4548-4", "%", 4.0, 5.6, 7.2, 1.5),
            ("Glucose", "2345-7", "mg/dL", 70.0, 100.0, 145.0, 40.0),
            ("Creatinine", "2160-0", "mg/dL", 0.7, 1.3, 1.1, 0.3),
            ("Total Cholesterol", "2093-3", "mg/dL", 0.0, 200.0, 220.0, 30.0),
            ("BUN", "3094-0", "mg/dL", 7.0, 20.0, 16.0, 5.0),
        ],
        "encounter_types": ["outpatient", "outpatient", "outpatient", "inpatient"],
        "departments": [4, 4, 11],  # Med-Surg, Pharmacy
        "complaints": ["Routine diabetes follow-up", "Elevated blood sugar", "Foot numbness"],
    },
    {
        "name": "Cardiac",
        "weight": 18,
        "conditions": [
            ("I50.9", "Heart failure, unspecified"),
            ("I48.91", "Unspecified atrial fibrillation"),
            ("I10", "Essential (primary) hypertension"),
            ("I25.10", "Atherosclerotic heart disease"),
        ],
        "medications": [
            ("Carvedilol", "12.5 mg", "PO", "BID"),
            ("Furosemide", "40 mg", "IV", "BID"),
            ("Warfarin", "5 mg", "PO", "Daily"),
            ("Spironolactone", "25 mg", "PO", "Daily"),
            ("Digoxin", "0.125 mg", "PO", "Daily"),
        ],
        "labs": [
            ("Troponin I", "10839-9", "ng/mL", 0.0, 0.04, 0.08, 0.1),
            ("BNP", "30934-4", "pg/mL", 0.0, 100.0, 350.0, 200.0),
            ("INR", "6301-6", "", 0.8, 1.1, 2.3, 0.5),
            ("Sodium", "2951-2", "mEq/L", 136.0, 145.0, 138.0, 3.0),
            ("Potassium", "2823-3", "mEq/L", 3.5, 5.0, 4.5, 0.5),
        ],
        "encounter_types": ["inpatient", "ED", "outpatient", "inpatient"],
        "departments": [5, 1, 5, 2],  # Cardiology, ED, Cardiology, ICU
        "complaints": ["Chest pain", "Shortness of breath", "Palpitations", "Leg swelling"],
    },
    {
        "name": "Respiratory",
        "weight": 15,
        "conditions": [
            ("J44.1", "COPD with acute exacerbation"),
            ("J18.9", "Pneumonia, unspecified organism"),
        ],
        "medications": [
            ("Albuterol", "2.5 mg", "INH", "Q4H PRN"),
            ("Prednisone", "40 mg", "PO", "Daily"),
            ("Azithromycin", "250 mg", "PO", "Daily"),
            ("Ceftriaxone", "1 g", "IV", "Daily"),
        ],
        "labs": [
            ("WBC", "6690-2", "10^3/uL", 4.5, 11.0, 14.0, 3.0),
            ("Procalcitonin", "75241-0", "ng/mL", 0.0, 0.1, 0.8, 0.5),
            ("CRP", "1988-5", "mg/L", 0.0, 3.0, 15.0, 8.0),
            ("Lactate", "2524-7", "mmol/L", 0.5, 2.2, 1.8, 0.6),
        ],
        "encounter_types": ["inpatient", "ED", "inpatient"],
        "departments": [4, 1, 2],  # Med-Surg, ED, ICU
        "complaints": ["Cough", "Shortness of breath", "Fever", "Difficulty breathing"],
    },
    {
        "name": "Renal",
        "weight": 10,
        "conditions": [
            ("N17.9", "Acute kidney failure, unspecified"),
            ("E87.1", "Hypo-osmolality and hyponatremia"),
            ("E87.6", "Hypokalemia"),
        ],
        "medications": [
            ("Potassium Chloride", "20 mEq", "PO", "BID"),
            ("Furosemide", "40 mg", "IV", "BID"),
            ("Pantoprazole", "40 mg", "IV", "Daily"),
        ],
        "labs": [
            ("Creatinine", "2160-0", "mg/dL", 0.7, 1.3, 3.2, 1.5),
            ("BUN", "3094-0", "mg/dL", 7.0, 20.0, 45.0, 15.0),
            ("Potassium", "2823-3", "mEq/L", 3.5, 5.0, 3.1, 0.4),
            ("Sodium", "2951-2", "mEq/L", 136.0, 145.0, 131.0, 3.0),
            ("Phosphorus", "2777-1", "mg/dL", 2.5, 4.5, 5.2, 1.0),
        ],
        "encounter_types": ["inpatient", "ED", "inpatient"],
        "departments": [4, 1, 2],
        "complaints": ["Weakness", "Nausea/vomiting", "Decreased urine output", "Confusion"],
    },
    {
        "name": "Sepsis",
        "weight": 8,
        "conditions": [
            ("A41.9", "Sepsis, unspecified organism"),
            ("R65.20", "Severe sepsis without septic shock"),
            ("N39.0", "Urinary tract infection"),
        ],
        "medications": [
            ("Vancomycin", "1 g", "IV", "Q12H"),
            ("Piperacillin-Tazobactam", "4.5 g", "IV", "Q6H"),
            ("Heparin", "5000 units", "SubQ", "Q8H"),
            ("Ondansetron", "4 mg", "IV", "Q6H PRN"),
        ],
        "labs": [
            ("WBC", "6690-2", "10^3/uL", 4.5, 11.0, 18.0, 5.0),
            ("Lactate", "2524-7", "mmol/L", 0.5, 2.2, 4.5, 2.0),
            ("Procalcitonin", "75241-0", "ng/mL", 0.0, 0.1, 5.0, 3.0),
            ("CRP", "1988-5", "mg/L", 0.0, 3.0, 45.0, 20.0),
            ("Creatinine", "2160-0", "mg/dL", 0.7, 1.3, 2.1, 0.8),
        ],
        "encounter_types": ["ED", "inpatient"],
        "departments": [1, 2],  # ED, ICU
        "complaints": ["Fever", "Altered mental status", "Weakness", "Confusion"],
    },
    {
        "name": "Orthopedic",
        "weight": 10,
        "conditions": [
            ("M17.11", "Primary osteoarthritis, right knee"),
            ("S72.001A", "Fracture of neck of right femur"),
            ("M54.5", "Low back pain"),
        ],
        "medications": [
            ("Acetaminophen", "650 mg", "PO", "Q6H PRN"),
            ("Morphine", "2 mg", "IV", "Q4H PRN"),
            ("Enoxaparin", "40 mg", "SubQ", "Daily"),
            ("Cephalexin", "500 mg", "PO", "QID"),
        ],
        "labs": [
            ("Hemoglobin", "718-7", "g/dL", 12.0, 17.5, 11.5, 1.5),
            ("Hematocrit", "4544-3", "%", 36.0, 51.0, 34.0, 4.0),
            ("PT", "5902-2", "sec", 11.0, 13.5, 12.5, 1.0),
            ("Calcium", "17861-6", "mg/dL", 8.5, 10.5, 9.2, 0.5),
        ],
        "encounter_types": ["ED", "inpatient", "outpatient"],
        "departments": [1, 7, 15],  # ED, Ortho, Rehab
        "complaints": ["Hip pain", "Fall", "Back pain", "Joint pain"],
    },
    {
        "name": "Oncology",
        "weight": 7,
        "conditions": [
            ("C34.90", "Malignant neoplasm of unspecified part of unspecified bronchus or lung"),
            ("D64.9", "Anemia, unspecified"),
        ],
        "medications": [
            ("Ondansetron", "4 mg", "IV", "Q6H PRN"),
            ("Dexamethasone", "4 mg", "IV", "Q6H"),
            ("Morphine", "2 mg", "IV", "Q4H PRN"),
        ],
        "labs": [
            ("WBC", "6690-2", "10^3/uL", 4.5, 11.0, 3.2, 1.5),
            ("Hemoglobin", "718-7", "g/dL", 12.0, 17.5, 9.5, 1.5),
            ("Platelets", "777-3", "10^3/uL", 150.0, 400.0, 95.0, 40.0),
            ("Albumin", "1751-7", "g/dL", 3.5, 5.5, 2.8, 0.5),
        ],
        "encounter_types": ["inpatient", "outpatient", "inpatient"],
        "departments": [6, 6, 2],  # Oncology, Oncology, ICU
        "complaints": ["Fatigue", "Shortness of breath", "Weight loss", "Chest tightness"],
    },
    {
        "name": "Behavioral",
        "weight": 7,
        "conditions": [
            ("F32.9", "Major depressive disorder, single episode, unspecified"),
            ("F41.1", "Generalized anxiety disorder"),
        ],
        "medications": [
            ("Sertraline", "50 mg", "PO", "Daily"),
            ("Lorazepam", "1 mg", "PO", "Q8H PRN"),
        ],
        "labs": [
            ("TSH", "3016-3", "mIU/L", 0.27, 4.20, 2.5, 1.0),
            ("Vitamin D", "1989-3", "ng/mL", 30.0, 100.0, 22.0, 10.0),
            ("CBC with Differential", "6690-2", "10^3/uL", 4.5, 11.0, 7.0, 2.0),
        ],
        "encounter_types": ["outpatient", "outpatient", "ED"],
        "departments": [14, 14, 1],  # Behavioral Health, Behavioral Health, ED
        "complaints": ["Anxiety", "Fatigue", "Altered mental status"],
    },
    {
        "name": "Healthy",
        "weight": 5,
        "conditions": [],
        "medications": [],
        "labs": [
            ("WBC", "6690-2", "10^3/uL", 4.5, 11.0, 7.0, 1.5),
            ("Hemoglobin", "718-7", "g/dL", 12.0, 17.5, 14.5, 1.0),
            ("Glucose", "2345-7", "mg/dL", 70.0, 100.0, 88.0, 8.0),
        ],
        "encounter_types": ["outpatient"],
        "departments": [4],
        "complaints": ["Annual physical", "Routine check-up"],
    },
]


def generate_synthea_sample(db_path, num_patients=50):
    """Generate a built-in Synthea-style dataset with clinically coherent
    patient histories. No external Synthea installation required.

    Returns a dict of table row counts.
    """
    random.seed(42)

    try:
        from faker import Faker
        fake = Faker()
        Faker.seed(42)
        has_faker = True
    except ImportError:
        has_faker = False

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    now = datetime(2026, 2, 25, 12, 0, 0)
    year_ago = now - timedelta(days=365)

    from database import (
        DEPARTMENTS_DATA, INSURANCE_PLANS, CREDENTIALS,
        ALLERGENS, SENDING_SYSTEMS, RECEIVING_SYSTEMS,
        HL7_MESSAGE_TYPES, CHIEF_COMPLAINTS,
    )

    # --- Departments (reuse from database.py) ---
    for d in DEPARTMENTS_DATA:
        cur.execute(
            "INSERT OR IGNORE INTO departments (dept_name, dept_code, floor, building, "
            "manager_name, phone, active) VALUES (?,?,?,?,?,?,1)", d)

    # --- Providers (80, same structure) ---
    from database import SPECIALTIES_BY_DEPT
    providers = []
    for i in range(80):
        dept_id = (i % 15) + 1
        specs = SPECIALTIES_BY_DEPT.get(dept_id, ["General"])
        specialty = random.choice(specs)
        cred = random.choices(CREDENTIALS, weights=[35, 15, 20, 12, 10, 8])[0]
        fn = fake.first_name() if has_faker else f"Provider{i}First"
        ln = fake.last_name() if has_faker else f"Provider{i}Last"
        npi = str(1000000000 + i)
        email = f"{fn.lower()}.{ln.lower()}@merithealth.org"
        phone = fake.phone_number() if has_faker else f"(555) 200-{i:04d}"
        active = 1 if random.random() < 0.95 else 0
        providers.append((npi, fn, ln, cred, specialty, dept_id, email, phone, active))
    cur.executemany(
        "INSERT INTO providers (npi, first_name, last_name, credential, specialty, "
        "department_id, email, phone, active) VALUES (?,?,?,?,?,?,?,?,?)", providers)
    num_providers = 80

    # --- Patients with archetypes ---
    genders = ["Male", "Female"]
    races = ["White", "Black or African American", "Asian",
             "American Indian or Alaska Native", "Two or More Races", "Unknown"]
    ethnicities = ["Hispanic or Latino", "Not Hispanic or Latino", "Unknown"]
    states_list = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI",
                   "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI"]

    archetype_weights = [a["weight"] for a in ARCHETYPES]
    mrn_list = []
    patient_archetypes = {}  # mrn -> archetype
    mrn_counter = 0

    for i in range(num_patients):
        mrn_counter += 1
        mrn = f"MRN-{mrn_counter:07d}"
        mrn_list.append(mrn)
        archetype = random.choices(ARCHETYPES, weights=archetype_weights)[0]
        patient_archetypes[mrn] = archetype

        gender = random.choice(genders)
        fn = fake.first_name_male() if gender == "Male" and has_faker else (
            fake.first_name_female() if has_faker else f"Patient{i}")
        ln = fake.last_name() if has_faker else f"Last{i}"
        dob = (now - timedelta(days=random.randint(20 * 365, 90 * 365))).strftime("%Y-%m-%d")
        race = random.choice(races)
        ethnicity = random.choice(ethnicities)
        addr = fake.street_address() if has_faker else f"{random.randint(100, 9999)} Main St"
        city = fake.city() if has_faker else "Springfield"
        state = random.choice(states_list)
        zipcode = fake.zipcode() if has_faker else f"{random.randint(10000, 99999)}"
        phone = fake.phone_number() if has_faker else f"(555) 300-{i:04d}"
        email = f"{fn.lower()}.{ln.lower()}{random.randint(1, 999)}@email.com"
        ins_plan = random.choice(INSURANCE_PLANS)
        ins_id = f"{ins_plan[:3].upper()}{random.randint(100000000, 999999999)}"
        pcp_id = random.randint(1, num_providers)
        created = _fmt(now - timedelta(days=random.randint(30, 3 * 365)))

        cur.execute(
            "INSERT INTO patients (mrn, first_name, last_name, dob, gender, race, "
            "ethnicity, address, city, state, zip, phone, email, primary_language, "
            "insurance_plan, insurance_id, pcp_id, created_at, status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (mrn, fn, ln, dob, gender, race, ethnicity, addr, city, state,
             zipcode, phone, email, "English", ins_plan, ins_id, pcp_id,
             created, "active"))

    # --- Encounters (driven by archetype) ---
    enc_meta = []
    dispositions = ["Discharged home", "Discharged to SNF", "Discharged to rehab",
                    "Discharged with home health", None]

    for mrn in mrn_list:
        arch = patient_archetypes[mrn]
        num_encounters = random.randint(1, len(arch["encounter_types"]))
        for j in range(num_encounters):
            enc_type = arch["encounter_types"][j % len(arch["encounter_types"])]
            dept_id = arch["departments"][j % len(arch["departments"])]
            complaint = random.choice(arch["complaints"]) if arch["complaints"] else random.choice(CHIEF_COMPLAINTS)

            admit_dt = year_ago + timedelta(days=random.randint(0, 360),
                                            hours=random.randint(0, 23))
            if enc_type == "ED":
                los_hours = random.choice([2, 4, 6, 8, 12])
            elif enc_type in ("outpatient", "telehealth"):
                los_hours = random.choice([0.5, 1, 2])
            elif enc_type == "observation":
                los_hours = random.choice([12, 24, 36])
            else:
                los_hours = random.choice([24, 48, 72, 96, 120, 168])
            discharge_dt = admit_dt + timedelta(hours=los_hours)
            is_open = discharge_dt > now
            los_days = round(los_hours / 24.0, 1)
            prov_id = random.randint(1, num_providers)

            cur.execute(
                "INSERT INTO encounters (patient_mrn, encounter_type, admission_date, "
                "discharge_date, attending_provider_id, department_id, chief_complaint, "
                "disposition, status, los_days) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (mrn, enc_type, _fmt(admit_dt),
                 _fmt(discharge_dt) if not is_open else None,
                 prov_id, dept_id, complaint,
                 random.choice(dispositions) if not is_open else None,
                 "open" if is_open else "closed",
                 los_days))
            enc_id = cur.lastrowid
            enc_meta.append((enc_id, mrn, admit_dt, discharge_dt))

    # --- Diagnoses (archetype-driven: coherent conditions) ---
    for mrn in mrn_list:
        arch = patient_archetypes[mrn]
        # Get this patient's encounters
        patient_encs = [(eid, m, a, d) for eid, m, a, d in enc_meta if m == mrn]
        if not patient_encs or not arch["conditions"]:
            continue
        for k, (icd10, desc) in enumerate(arch["conditions"]):
            enc_id, _, admit_dt, _ = patient_encs[k % len(patient_encs)]
            dx_type = "primary" if k == 0 else "secondary"
            dx_date = _fmt(admit_dt + timedelta(hours=random.randint(0, 6)))
            prov_id = random.randint(1, num_providers)
            cur.execute(
                "INSERT INTO diagnoses (encounter_id, patient_mrn, icd10_code, "
                "description, diagnosis_type, diagnosed_by_provider_id, "
                "diagnosed_date, status) VALUES (?,?,?,?,?,?,?,?)",
                (enc_id, mrn, icd10, desc, dx_type, prov_id, dx_date, "active"))

    # --- Medications (archetype-driven: conditions match meds) ---
    for mrn in mrn_list:
        arch = patient_archetypes[mrn]
        patient_encs = [(eid, m, a, d) for eid, m, a, d in enc_meta if m == mrn]
        if not patient_encs:
            continue
        for med_name, dosage, route, freq in arch["medications"]:
            enc_id, _, admit_dt, discharge_dt = random.choice(patient_encs)
            prov_id = random.randint(1, num_providers)
            start = admit_dt + timedelta(hours=random.randint(0, 4))
            duration = random.randint(3, 30)
            end = start + timedelta(days=duration)
            ndc = f"00{random.randint(100, 999)}-{random.randint(1000, 9999)}-01"
            cur.execute(
                "INSERT INTO medications (encounter_id, patient_mrn, medication_name, "
                "dosage, route, frequency, prescribing_provider_id, start_date, "
                "end_date, status, ndc_code) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (enc_id, mrn, med_name, dosage, route, freq, prov_id,
                 _fmt(start), _fmt(end),
                 "completed" if end < now else "active", ndc))

    # --- Lab results (archetype-driven: disease-appropriate values) ---
    for mrn in mrn_list:
        arch = patient_archetypes[mrn]
        patient_encs = [(eid, m, a, d) for eid, m, a, d in enc_meta if m == mrn]
        if not patient_encs:
            continue
        for test_name, test_code, unit, ref_low, ref_high, mean, std in arch["labs"]:
            # Multiple lab draws per encounter
            for enc_id, _, admit_dt, _ in patient_encs:
                num_draws = random.randint(1, 3)
                for draw in range(num_draws):
                    val = round(random.gauss(mean, std), 2)
                    if ref_low is not None and val < ref_low * 0.3:
                        val = round(ref_low * 0.3, 2)
                    if ref_high is not None and val > ref_high * 2.5:
                        val = round(ref_high * 2.5, 2)
                    flag = _abnormal_flag(val, ref_low, ref_high)
                    collected = admit_dt + timedelta(hours=draw * 8 + random.randint(0, 4))
                    resulted = collected + timedelta(minutes=random.randint(30, 240))
                    prov_id = random.randint(1, num_providers)
                    cur.execute(
                        "INSERT INTO lab_results (encounter_id, patient_mrn, test_name, "
                        "test_code, result_value, result_unit, reference_range_low, "
                        "reference_range_high, abnormal_flag, collected_datetime, "
                        "resulted_datetime, ordering_provider_id, status) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (enc_id, mrn, test_name, test_code, str(val), unit,
                         ref_low, ref_high, flag, _fmt(collected), _fmt(resulted),
                         prov_id, "final"))

    # --- Vital signs ---
    for enc_id, mrn, admit_dt, discharge_dt in enc_meta:
        num_vitals = random.randint(1, 4)
        for v in range(num_vitals):
            recorded = admit_dt + timedelta(hours=v * 6 + random.randint(0, 3))
            temp = round(random.gauss(98.6, 0.8), 1)
            hr = random.randint(55, 120)
            sbp = random.randint(90, 180)
            dbp = random.randint(55, 100)
            rr = random.randint(12, 26)
            spo2 = round(min(100.0, random.gauss(96.5, 2.0)), 1)
            height = round(random.gauss(170, 10), 1)
            weight = round(random.gauss(80, 18), 1)
            bmi = round(weight / ((height / 100) ** 2), 1) if height > 0 else None
            prov_id = random.randint(1, num_providers)
            cur.execute(
                "INSERT INTO vital_signs (encounter_id, patient_mrn, recorded_datetime, "
                "temperature, heart_rate, systolic_bp, diastolic_bp, respiratory_rate, "
                "spo2, height_cm, weight_kg, bmi, recorded_by_provider_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (enc_id, mrn, _fmt(recorded), temp, hr, sbp, dbp, rr, spo2,
                 height, weight, bmi, prov_id))

    # --- Orders ---
    order_types = ["lab", "imaging", "medication", "consult", "diet", "nursing"]
    order_descs = {
        "lab": ["CBC with Differential", "BMP", "CMP", "Lipid Panel", "HbA1c", "Troponin I", "Blood Culture x2"],
        "imaging": ["Chest X-ray 2 views", "CT Head without contrast", "CT Chest with contrast", "Echocardiogram"],
        "medication": ["Start IV Normal Saline 125 mL/hr", "Morphine 2mg IV Q4H PRN", "Heparin drip per protocol"],
        "consult": ["Cardiology consult", "Pulmonology consult", "Infectious Disease consult", "Social Work consult"],
        "diet": ["NPO", "Clear liquid diet", "Regular diet", "Cardiac diet"],
        "nursing": ["Fall precautions", "Telemetry monitoring", "Strict I&O", "DVT prophylaxis"],
    }
    for enc_id, mrn, admit_dt, _ in enc_meta:
        num_orders = random.randint(1, 5)
        for _ in range(num_orders):
            otype = random.choice(order_types)
            desc = random.choice(order_descs[otype])
            prov_id = random.randint(1, num_providers)
            order_dt = _fmt(admit_dt + timedelta(hours=random.randint(0, 12)))
            status = random.choices(["ordered", "completed", "cancelled"], weights=[20, 70, 10])[0]
            priority = random.choices(["routine", "stat", "urgent"], weights=[60, 20, 20])[0]
            cur.execute(
                "INSERT INTO orders (encounter_id, patient_mrn, order_type, "
                "order_description, ordering_provider_id, order_datetime, status, "
                "priority) VALUES (?,?,?,?,?,?,?,?)",
                (enc_id, mrn, otype, desc, prov_id, order_dt, status, priority))

    # --- Procedures ---
    from database import CPT_CODES
    for enc_id, mrn, admit_dt, _ in enc_meta:
        if random.random() < 0.4:  # 40% of encounters have procedures
            num_procs = random.randint(1, 3)
            for _ in range(num_procs):
                cpt, desc = random.choice(CPT_CODES)
                prov_id = random.randint(1, num_providers)
                proc_date = _fmt(admit_dt + timedelta(hours=random.randint(1, 48)))
                dept_id = random.randint(1, 15)
                cur.execute(
                    "INSERT INTO procedures (encounter_id, patient_mrn, cpt_code, "
                    "description, performing_provider_id, procedure_date, "
                    "department_id, status) VALUES (?,?,?,?,?,?,?,?)",
                    (enc_id, mrn, cpt, desc, prov_id, proc_date, dept_id, "completed"))

    # --- Allergies ---
    for mrn in mrn_list:
        if random.random() < 0.5:
            num_allergies = random.randint(1, 4)
            selected = random.sample(ALLERGENS, k=min(num_allergies, len(ALLERGENS)))
            for allergen, atype, reaction, severity in selected:
                reported = (now - timedelta(days=random.randint(30, 5 * 365))).strftime("%Y-%m-%d")
                cur.execute(
                    "INSERT INTO allergies (patient_mrn, allergen, allergy_type, "
                    "reaction, severity, reported_date, status) VALUES (?,?,?,?,?,?,?)",
                    (mrn, allergen, atype, reaction, severity, reported, "active"))

    # --- Insurance claims ---
    for enc_id, mrn, admit_dt, discharge_dt in enc_meta:
        plan = random.choice(INSURANCE_PLANS)
        amount = round(random.uniform(200, 80000), 2)
        claim_status = random.choices(
            ["submitted", "pending", "paid", "denied", "appealed"],
            weights=[15, 20, 40, 15, 10])[0]
        if claim_status == "paid":
            paid = round(amount * random.uniform(0.5, 1.0), 2)
            denied_amt = round(amount - paid, 2)
        elif claim_status == "denied":
            paid = 0.0
            denied_amt = amount
        else:
            paid = 0.0
            denied_amt = 0.0
        from database import DENIAL_REASONS
        submitted = _fmt(discharge_dt + timedelta(days=random.randint(0, 14)))
        resolved = None
        denial_reason = None
        if claim_status in ("paid", "denied"):
            resolved = _fmt(discharge_dt + timedelta(days=random.randint(15, 90)))
        if claim_status in ("denied", "appealed"):
            denial_reason = random.choice(DENIAL_REASONS)
        cur.execute(
            "INSERT INTO insurance_claims (encounter_id, patient_mrn, insurance_plan, "
            "claim_amount, paid_amount, denied_amount, claim_status, submitted_date, "
            "resolved_date, denial_reason) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (enc_id, mrn, plan, amount, round(paid, 2), round(denied_amt, 2),
             claim_status, submitted, resolved, denial_reason))

    # --- Users ---
    roles = ["physician", "nurse", "admin", "analyst", "pharmacist"]
    for i in range(40):
        fn = fake.first_name() if has_faker else f"User{i}"
        ln = fake.last_name() if has_faker else f"Last{i}"
        username = f"{fn[0].lower()}{ln.lower()}{random.randint(1, 99)}"
        full_name = f"{fn} {ln}"
        role = random.choice(roles)
        dept_id = random.randint(1, 15)
        last_login = _fmt(now - timedelta(days=random.randint(0, 30)))
        active = 1 if random.random() < 0.90 else 0
        access_level = {"physician": 4, "nurse": 3, "admin": 5,
                        "analyst": 4, "pharmacist": 3}[role]
        cur.execute(
            "INSERT INTO users (username, full_name, role, department_id, "
            "last_login, active, access_level) VALUES (?,?,?,?,?,?,?)",
            (username, full_name, role, dept_id, last_login, active, access_level))

    # --- Audit log ---
    actions = ["view", "edit", "print", "export"]
    resource_types = ["patient_chart", "lab_result", "medication_order",
                      "encounter", "report", "user_account"]
    for i in range(5000):
        uid = random.randint(1, 40)
        action = random.choices(actions, weights=[60, 20, 10, 10])[0]
        rtype = random.choice(resource_types)
        rid = str(random.randint(1, len(enc_meta)))
        ts = _fmt(now - timedelta(days=random.randint(0, 30),
                                  hours=random.randint(0, 23),
                                  minutes=random.randint(0, 59)))
        ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        details = None
        if action == "export":
            details = f"Exported {rtype} #{rid} to PDF"
        elif action == "print":
            details = f"Printed {rtype} #{rid}"
        cur.execute(
            "INSERT INTO audit_log (user_id, action, resource_type, resource_id, "
            "timestamp, ip_address, details) VALUES (?,?,?,?,?,?,?)",
            (uid, action, rtype, rid, ts, ip, details))

    # --- HL7 messages ---
    for i in range(200):
        msg_info = random.choice(HL7_MESSAGE_TYPES)
        mtype, trigger, desc = msg_info
        sender = random.choice(SENDING_SYSTEMS)
        receiver = random.choice(RECEIVING_SYSTEMS)
        mrn = random.choice(mrn_list)
        enc_id = random.choice(enc_meta)[0]
        msg_dt = _fmt(now - timedelta(days=random.randint(0, 30),
                                      hours=random.randint(0, 23)))
        status = random.choices(["sent", "received", "error", "acknowledged"],
                                weights=[15, 40, 15, 30])[0]
        raw_preview = (
            f"MSH|^~\\&|{sender}|MERIT_HEALTH|{receiver}|MERIT_HEALTH|"
            f"{msg_dt.replace('-', '').replace(':', '').replace(' ', '')}||"
            f"{mtype}^{trigger}|MSG{random.randint(100000, 999999)}|P|2.5.1\r"
            f"PID|||{mrn}||...")
        cur.execute(
            "INSERT INTO hl7_messages (message_type, trigger_event, sending_system, "
            "receiving_system, patient_mrn, encounter_id, message_datetime, status, "
            "raw_message_preview) VALUES (?,?,?,?,?,?,?,?,?)",
            (mtype, trigger, sender, receiver, mrn, enc_id, msg_dt, status,
             raw_preview[:200]))

    # --- System alerts ---
    alert_types = ["interface_error", "downtime", "security", "performance"]
    severities = ["info", "warning", "critical"]
    source_systems = ["EHR_Core", "LabInterface_Engine", "RadPACS", "PharmacySystem",
                      "ADT_Interface", "BillingEngine", "HIE_Gateway", "Firewall",
                      "DatabaseServer", "ApplicationServer"]
    alert_messages = {
        "interface_error": [
            "HL7 ACK timeout from LabCorp interface after 30s",
            "Failed to parse ORU message from Quest - invalid OBX segment",
            "Connection refused by RadPACS on port 2575",
        ],
        "downtime": [
            "Scheduled maintenance window: EHR Core 02:00-04:00",
            "Unscheduled downtime: Lab Interface offline",
            "Database failover initiated - primary node unresponsive",
        ],
        "security": [
            "Multiple failed login attempts detected for user account",
            "Unusual after-hours access pattern detected",
            "PHI access from terminated employee account",
        ],
        "performance": [
            "Database query response time exceeds 5s threshold",
            "Memory utilization above 90% on application server",
            "HL7 message queue depth exceeds 500 messages",
        ],
    }
    for i in range(50):
        atype = random.choice(alert_types)
        sev = random.choice(severities)
        source = random.choice(source_systems)
        msg = random.choice(alert_messages[atype])
        created = _fmt(now - timedelta(days=random.randint(0, 7),
                                       hours=random.randint(0, 23)))
        ack = 1 if random.random() < 0.6 else 0
        ack_by = f"admin_{random.randint(1, 5)}" if ack else None
        cur.execute(
            "INSERT INTO system_alerts (alert_type, severity, source_system, message, "
            "created_at, acknowledged, acknowledged_by) VALUES (?,?,?,?,?,?,?)",
            (atype, sev, source, msg, created, ack, ack_by))

    conn.commit()

    # Count rows
    counts = {}
    for table in ["departments", "providers", "patients", "encounters", "diagnoses",
                   "procedures", "medications", "lab_results", "vital_signs", "orders",
                   "allergies", "insurance_claims", "users", "audit_log", "hl7_messages",
                   "system_alerts"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return counts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        print(f"Importing Synthea CSVs from {sys.argv[1]} ...")
        from database import SCHEMA_SQL
        db = sys.argv[2] if len(sys.argv) > 2 else "synthea_drill.db"
        if os.path.exists(db):
            os.remove(db)
        conn = sqlite3.connect(db)
        conn.executescript(SCHEMA_SQL)
        conn.close()
        stats = load_synthea_csv(db, sys.argv[1])
        print(f"Imported: {stats}")
    else:
        db = sys.argv[1] if len(sys.argv) > 1 else "synthea_drill.db"
        print(f"Generating built-in Synthea sample at {db} ...")
        if os.path.exists(db):
            os.remove(db)
        from database import SCHEMA_SQL
        conn = sqlite3.connect(db)
        conn.executescript(SCHEMA_SQL)
        conn.close()
        counts = generate_synthea_sample(db)
        print("Row counts:")
        for t, c in counts.items():
            print(f"  {t:25s} {c:>6,d}")
        print("Done.")

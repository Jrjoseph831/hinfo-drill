"""
tools_coding.py - Medical Code Mapper for the Health Informatics
Learning Platform.

Provides ICD-10, CPT, SNOMED, and DRG code lookup, mapping, validation,
and coding accuracy auditing against the platform's SQLite database.

Public API
----------
    search_icd10(query, limit=20)
    search_cpt(query, limit=20)
    validate_code(code, code_type)
    get_drg_info(drg_code)
    crosswalk_snomed_to_icd10(snomed_code)
    suggest_codes(clinical_text)
    check_coding_accuracy(db_path, encounter_id)
"""

import sqlite3
import re
from database import ICD10_CODES, CPT_CODES


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _db(db_path):
    """Return an sqlite3.Connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# DRG Reference Table
# ---------------------------------------------------------------------------

DRG_TABLE = {
    "065": {
        "description": "Intracranial hemorrhage or cerebral infarction with MCC",
        "mdc": "01 - Diseases and Disorders of the Nervous System",
        "type": "Medical",
        "weight": 1.7851,
        "gmlos": 5.1,
        "amlos": 6.7,
        "expected_reimbursement": 12550.00,
    },
    "066": {
        "description": "Intracranial hemorrhage or cerebral infarction with CC",
        "mdc": "01 - Diseases and Disorders of the Nervous System",
        "type": "Medical",
        "weight": 1.0693,
        "gmlos": 3.5,
        "amlos": 4.4,
        "expected_reimbursement": 7520.00,
    },
    "069": {
        "description": "Transient ischemia without thrombolytic",
        "mdc": "01 - Diseases and Disorders of the Nervous System",
        "type": "Medical",
        "weight": 0.7427,
        "gmlos": 2.3,
        "amlos": 2.9,
        "expected_reimbursement": 5222.00,
    },
    "177": {
        "description": "Respiratory infections and inflammations with MCC",
        "mdc": "04 - Diseases and Disorders of the Respiratory System",
        "type": "Medical",
        "weight": 2.0240,
        "gmlos": 6.2,
        "amlos": 7.9,
        "expected_reimbursement": 14230.00,
    },
    "178": {
        "description": "Respiratory infections and inflammations with CC",
        "mdc": "04 - Diseases and Disorders of the Respiratory System",
        "type": "Medical",
        "weight": 1.2768,
        "gmlos": 4.5,
        "amlos": 5.5,
        "expected_reimbursement": 8978.00,
    },
    "179": {
        "description": "Respiratory infections and inflammations without CC/MCC",
        "mdc": "04 - Diseases and Disorders of the Respiratory System",
        "type": "Medical",
        "weight": 0.8704,
        "gmlos": 3.1,
        "amlos": 3.9,
        "expected_reimbursement": 6120.00,
    },
    "190": {
        "description": "Chronic obstructive pulmonary disease with MCC",
        "mdc": "04 - Diseases and Disorders of the Respiratory System",
        "type": "Medical",
        "weight": 1.1825,
        "gmlos": 3.9,
        "amlos": 5.0,
        "expected_reimbursement": 8315.00,
    },
    "191": {
        "description": "Chronic obstructive pulmonary disease with CC",
        "mdc": "04 - Diseases and Disorders of the Respiratory System",
        "type": "Medical",
        "weight": 0.8849,
        "gmlos": 3.1,
        "amlos": 3.9,
        "expected_reimbursement": 6223.00,
    },
    "193": {
        "description": "Simple pneumonia and pleurisy with MCC",
        "mdc": "04 - Diseases and Disorders of the Respiratory System",
        "type": "Medical",
        "weight": 1.4032,
        "gmlos": 4.5,
        "amlos": 5.7,
        "expected_reimbursement": 9867.00,
    },
    "194": {
        "description": "Simple pneumonia and pleurisy with CC",
        "mdc": "04 - Diseases and Disorders of the Respiratory System",
        "type": "Medical",
        "weight": 0.9148,
        "gmlos": 3.3,
        "amlos": 4.1,
        "expected_reimbursement": 6433.00,
    },
    "195": {
        "description": "Simple pneumonia and pleurisy without CC/MCC",
        "mdc": "04 - Diseases and Disorders of the Respiratory System",
        "type": "Medical",
        "weight": 0.6502,
        "gmlos": 2.5,
        "amlos": 3.1,
        "expected_reimbursement": 4572.00,
    },
    "291": {
        "description": "Heart failure and shock with MCC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 1.4924,
        "gmlos": 4.7,
        "amlos": 6.0,
        "expected_reimbursement": 10493.00,
    },
    "292": {
        "description": "Heart failure and shock with CC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 0.9819,
        "gmlos": 3.4,
        "amlos": 4.3,
        "expected_reimbursement": 6904.00,
    },
    "293": {
        "description": "Heart failure and shock without CC/MCC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 0.6752,
        "gmlos": 2.5,
        "amlos": 3.1,
        "expected_reimbursement": 4748.00,
    },
    "300": {
        "description": "Peripheral vascular disorders with MCC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 1.3176,
        "gmlos": 4.3,
        "amlos": 5.5,
        "expected_reimbursement": 9265.00,
    },
    "301": {
        "description": "Peripheral vascular disorders with CC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 0.8483,
        "gmlos": 3.0,
        "amlos": 3.8,
        "expected_reimbursement": 5965.00,
    },
    "305": {
        "description": "Hypertension with MCC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 1.0456,
        "gmlos": 3.2,
        "amlos": 4.1,
        "expected_reimbursement": 7353.00,
    },
    "306": {
        "description": "Hypertension without MCC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 0.6231,
        "gmlos": 2.2,
        "amlos": 2.8,
        "expected_reimbursement": 4381.00,
    },
    "378": {
        "description": "GI hemorrhage with MCC",
        "mdc": "06 - Diseases and Disorders of the Digestive System",
        "type": "Medical",
        "weight": 1.7205,
        "gmlos": 4.7,
        "amlos": 6.2,
        "expected_reimbursement": 12096.00,
    },
    "379": {
        "description": "GI hemorrhage with CC",
        "mdc": "06 - Diseases and Disorders of the Digestive System",
        "type": "Medical",
        "weight": 1.0032,
        "gmlos": 3.1,
        "amlos": 3.9,
        "expected_reimbursement": 7056.00,
    },
    "392": {
        "description": "Esophagitis, gastroenteritis and misc digestive disorders with MCC",
        "mdc": "06 - Diseases and Disorders of the Digestive System",
        "type": "Medical",
        "weight": 1.1422,
        "gmlos": 3.8,
        "amlos": 4.9,
        "expected_reimbursement": 8031.00,
    },
    "470": {
        "description": "Major hip and knee joint replacement or reattachment of lower extremity without MCC",
        "mdc": "08 - Diseases and Disorders of the Musculoskeletal System",
        "type": "Surgical",
        "weight": 1.9586,
        "gmlos": 2.3,
        "amlos": 3.0,
        "expected_reimbursement": 13770.00,
    },
    "462": {
        "description": "Rehabilitation with CC/MCC",
        "mdc": "23 - Rehabilitation",
        "type": "Medical",
        "weight": 1.3975,
        "gmlos": 9.2,
        "amlos": 12.3,
        "expected_reimbursement": 9826.00,
    },
    "463": {
        "description": "Rehabilitation without CC/MCC",
        "mdc": "23 - Rehabilitation",
        "type": "Medical",
        "weight": 0.9831,
        "gmlos": 7.0,
        "amlos": 9.1,
        "expected_reimbursement": 6912.00,
    },
    "640": {
        "description": "Nutritional and miscellaneous metabolic disorders with MCC",
        "mdc": "10 - Endocrine, Nutritional and Metabolic Diseases",
        "type": "Medical",
        "weight": 1.1874,
        "gmlos": 3.7,
        "amlos": 4.8,
        "expected_reimbursement": 8350.00,
    },
    "641": {
        "description": "Nutritional and miscellaneous metabolic disorders without MCC",
        "mdc": "10 - Endocrine, Nutritional and Metabolic Diseases",
        "type": "Medical",
        "weight": 0.6648,
        "gmlos": 2.4,
        "amlos": 3.0,
        "expected_reimbursement": 4675.00,
    },
    "682": {
        "description": "Renal failure with MCC",
        "mdc": "11 - Diseases and Disorders of the Kidney and Urinary Tract",
        "type": "Medical",
        "weight": 1.5671,
        "gmlos": 4.5,
        "amlos": 5.7,
        "expected_reimbursement": 11019.00,
    },
    "683": {
        "description": "Renal failure with CC",
        "mdc": "11 - Diseases and Disorders of the Kidney and Urinary Tract",
        "type": "Medical",
        "weight": 0.9373,
        "gmlos": 3.1,
        "amlos": 3.8,
        "expected_reimbursement": 6592.00,
    },
    "689": {
        "description": "Kidney and urinary tract infections with MCC",
        "mdc": "11 - Diseases and Disorders of the Kidney and Urinary Tract",
        "type": "Medical",
        "weight": 1.1753,
        "gmlos": 4.0,
        "amlos": 5.1,
        "expected_reimbursement": 8265.00,
    },
    "690": {
        "description": "Kidney and urinary tract infections without MCC",
        "mdc": "11 - Diseases and Disorders of the Kidney and Urinary Tract",
        "type": "Medical",
        "weight": 0.7235,
        "gmlos": 2.8,
        "amlos": 3.5,
        "expected_reimbursement": 5088.00,
    },
    "871": {
        "description": "Septicemia or severe sepsis without mechanical ventilation >96 hours with MCC",
        "mdc": "18 - Infectious and Parasitic Diseases",
        "type": "Medical",
        "weight": 1.8612,
        "gmlos": 5.3,
        "amlos": 6.7,
        "expected_reimbursement": 13091.00,
    },
    "872": {
        "description": "Septicemia or severe sepsis without mechanical ventilation >96 hours without MCC",
        "mdc": "18 - Infectious and Parasitic Diseases",
        "type": "Medical",
        "weight": 1.0793,
        "gmlos": 3.6,
        "amlos": 4.5,
        "expected_reimbursement": 7590.00,
    },
    "774": {
        "description": "Vaginal delivery without complicating diagnoses",
        "mdc": "14 - Pregnancy, Childbirth and the Puerperium",
        "type": "Medical",
        "weight": 0.6907,
        "gmlos": 2.0,
        "amlos": 2.5,
        "expected_reimbursement": 4857.00,
    },
    "766": {
        "description": "Cesarean section without CC/MCC",
        "mdc": "14 - Pregnancy, Childbirth and the Puerperium",
        "type": "Surgical",
        "weight": 1.0124,
        "gmlos": 2.8,
        "amlos": 3.4,
        "expected_reimbursement": 7118.00,
    },
    "247": {
        "description": "Percutaneous cardiovascular procedures with drug-eluting stent without MCC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Surgical",
        "weight": 2.0452,
        "gmlos": 2.5,
        "amlos": 3.5,
        "expected_reimbursement": 14380.00,
    },
    "280": {
        "description": "Acute myocardial infarction, discharged alive with MCC",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 1.7245,
        "gmlos": 4.3,
        "amlos": 5.7,
        "expected_reimbursement": 12124.00,
    },
    "313": {
        "description": "Chest pain",
        "mdc": "05 - Diseases and Disorders of the Circulatory System",
        "type": "Medical",
        "weight": 0.5339,
        "gmlos": 1.6,
        "amlos": 2.1,
        "expected_reimbursement": 3754.00,
    },
    "603": {
        "description": "Cellulitis with MCC",
        "mdc": "09 - Diseases and Disorders of the Skin, Subcutaneous Tissue and Breast",
        "type": "Medical",
        "weight": 1.3682,
        "gmlos": 4.6,
        "amlos": 5.8,
        "expected_reimbursement": 9621.00,
    },
}


# ---------------------------------------------------------------------------
# SNOMED CT to ICD-10 Crosswalk reference
# ---------------------------------------------------------------------------

SNOMED_TO_ICD10 = {
    "44054006": [("I10", "Essential (primary) hypertension")],
    "73211009": [("E11.9", "Type 2 diabetes mellitus without complications"),
                 ("E11.65", "Type 2 diabetes mellitus with hyperglycemia")],
    "233604007": [("J18.9", "Pneumonia, unspecified organism")],
    "84114007": [("I50.9", "Heart failure, unspecified")],
    "22298006": [("I21.9", "Acute myocardial infarction, unspecified")],
    "195111005": [("I50.9", "Heart failure, unspecified")],
    "13645005": [("J44.1", "COPD with acute exacerbation")],
    "40055000": [("J44.1", "COPD with acute exacerbation")],
    "14669001": [("N17.9", "Acute kidney failure, unspecified")],
    "236578006": [("N18.3", "Chronic kidney disease, stage 3")],
    "230690007": [("I63.9", "Cerebral infarction, unspecified")],
    "91302008": [("A41.9", "Sepsis, unspecified organism")],
    "266257000": [("I47.1", "Supraventricular tachycardia"),
                  ("R00.0", "Tachycardia, unspecified")],
    "49436004": [("I48.91", "Unspecified atrial fibrillation")],
    "59621000": [("I10", "Essential (primary) hypertension")],
    "35489007": [("F32.9", "Major depressive disorder, single episode, unspecified")],
    "197480006": [("D64.9", "Anemia, unspecified")],
    "396275006": [("E03.9", "Hypothyroidism, unspecified")],
    "68496003": [("N39.0", "Urinary tract infection, site not specified")],
    "235595009": [("K21.0", "Gastro-esophageal reflux disease with esophagitis")],
    "267036007": [("R06.02", "Shortness of breath")],
    "29857009": [("R07.9", "Chest pain, unspecified")],
    "271807003": [("R11.2", "Nausea with vomiting, unspecified")],
    "386661006": [("R50.9", "Fever, unspecified")],
    "62315008": [("R42", "Dizziness and giddiness")],
    "25064002": [("R10.9", "Unspecified abdominal pain")],
    "161891005": [("M54.5", "Low back pain")],
    "399211009": [("G45.9", "Transient cerebral ischemic attack, unspecified")],
    "128613002": [("R65.20", "Severe sepsis without septic shock"),
                  ("R65.21", "Severe sepsis with septic shock")],
    "40930008": [("E78.5", "Hyperlipidemia, unspecified")],
    "235919008": [("K80.20", "Calculus of gallbladder without cholecystitis")],
    "47693006": [("K35.80", "Unspecified acute appendicitis")],
    "263756000": [("R55", "Syncope and collapse")],
    "428251008": [("G47.33", "Obstructive sleep apnea")],
    "301011002": [("G43.909", "Migraine, unspecified")],
    "87433001": [("J96.01", "Acute respiratory failure with hypoxia")],
    "59282003": [("I26.99", "Other pulmonary embolism without acute cor pulmonale")],
    "34000006": [("G20", "Parkinson disease")],
    "36971009": [("F41.1", "Generalized anxiety disorder")],
}


# ---------------------------------------------------------------------------
# Clinical text keyword-to-ICD-10 mapping for suggest_codes
# ---------------------------------------------------------------------------

_KEYWORD_TO_ICD10 = {
    "diabetes":         [("E11.9", "Type 2 diabetes mellitus without complications")],
    "diabetic":         [("E11.9", "Type 2 diabetes mellitus without complications")],
    "hyperglycemia":    [("E11.65", "Type 2 diabetes mellitus with hyperglycemia")],
    "hypertension":     [("I10", "Essential (primary) hypertension")],
    "high blood pressure": [("I10", "Essential (primary) hypertension")],
    "pneumonia":        [("J18.9", "Pneumonia, unspecified organism")],
    "heart failure":    [("I50.9", "Heart failure, unspecified")],
    "chf":              [("I50.9", "Heart failure, unspecified")],
    "congestive":       [("I50.9", "Heart failure, unspecified")],
    "copd":             [("J44.1", "COPD with acute exacerbation")],
    "chest pain":       [("R07.9", "Chest pain, unspecified")],
    "myocardial infarction": [("I21.9", "Acute myocardial infarction, unspecified")],
    "heart attack":     [("I21.9", "Acute myocardial infarction, unspecified")],
    "mi":               [("I21.9", "Acute myocardial infarction, unspecified")],
    "stroke":           [("I63.9", "Cerebral infarction, unspecified")],
    "cva":              [("I63.9", "Cerebral infarction, unspecified")],
    "sepsis":           [("A41.9", "Sepsis, unspecified organism")],
    "septic":           [("R65.21", "Severe sepsis with septic shock")],
    "kidney failure":   [("N17.9", "Acute kidney failure, unspecified")],
    "renal failure":    [("N17.9", "Acute kidney failure, unspecified")],
    "aki":              [("N17.9", "Acute kidney failure, unspecified")],
    "ckd":              [("N18.3", "Chronic kidney disease, stage 3")],
    "uti":              [("N39.0", "Urinary tract infection, site not specified")],
    "urinary tract":    [("N39.0", "Urinary tract infection, site not specified")],
    "atrial fibrillation": [("I48.91", "Unspecified atrial fibrillation")],
    "afib":             [("I48.91", "Unspecified atrial fibrillation")],
    "a-fib":            [("I48.91", "Unspecified atrial fibrillation")],
    "depression":       [("F32.9", "Major depressive disorder, single episode, unspecified")],
    "depressive":       [("F32.9", "Major depressive disorder, single episode, unspecified")],
    "anxiety":          [("F41.1", "Generalized anxiety disorder")],
    "back pain":        [("M54.5", "Low back pain")],
    "low back":         [("M54.5", "Low back pain")],
    "lumbar":           [("M54.5", "Low back pain")],
    "abdominal pain":   [("R10.9", "Unspecified abdominal pain")],
    "nausea":           [("R11.2", "Nausea with vomiting, unspecified")],
    "vomiting":         [("R11.2", "Nausea with vomiting, unspecified")],
    "shortness of breath": [("R06.02", "Shortness of breath")],
    "dyspnea":          [("R06.02", "Shortness of breath")],
    "sob":              [("R06.02", "Shortness of breath")],
    "fever":            [("R50.9", "Fever, unspecified")],
    "febrile":          [("R50.9", "Fever, unspecified")],
    "syncope":          [("R55", "Syncope and collapse")],
    "fainted":          [("R55", "Syncope and collapse")],
    "fainting":         [("R55", "Syncope and collapse")],
    "dizziness":        [("R42", "Dizziness and giddiness")],
    "dizzy":            [("R42", "Dizziness and giddiness")],
    "pulmonary embolism": [("I26.99", "Other pulmonary embolism without acute cor pulmonale")],
    "pe":               [("I26.99", "Other pulmonary embolism without acute cor pulmonale")],
    "dvt":              [("I80.10", "Phlebitis and thrombophlebitis of unspecified femoral vein")],
    "deep vein":        [("I80.10", "Phlebitis and thrombophlebitis of unspecified femoral vein")],
    "anemia":           [("D64.9", "Anemia, unspecified")],
    "iron deficiency":  [("D50.9", "Iron deficiency anemia, unspecified")],
    "hypothyroid":      [("E03.9", "Hypothyroidism, unspecified")],
    "thyroid":          [("E03.9", "Hypothyroidism, unspecified")],
    "hyperlipidemia":   [("E78.5", "Hyperlipidemia, unspecified")],
    "cholesterol":      [("E78.5", "Hyperlipidemia, unspecified")],
    "asthma":           [("J45.20", "Mild intermittent asthma, uncomplicated")],
    "appendicitis":     [("K35.80", "Unspecified acute appendicitis")],
    "gallstone":        [("K80.20", "Calculus of gallbladder without cholecystitis")],
    "cholelithiasis":   [("K80.20", "Calculus of gallbladder without cholecystitis")],
    "reflux":           [("K21.0", "Gastro-esophageal reflux disease with esophagitis")],
    "gerd":             [("K21.0", "Gastro-esophageal reflux disease with esophagitis")],
    "dehydration":      [("E86.0", "Dehydration")],
    "hyponatremia":     [("E87.1", "Hypo-osmolality and hyponatremia")],
    "hypokalemia":      [("E87.6", "Hypokalemia")],
    "constipation":     [("K59.00", "Constipation, unspecified")],
    "cellulitis":       [("L03.311", "Cellulitis of abdominal wall")],
    "fracture":         [("S72.001A", "Fracture of neck of right femur, initial encounter")],
    "hip fracture":     [("S72.001A", "Fracture of neck of right femur, initial encounter")],
    "knee":             [("M17.11", "Primary osteoarthritis, right knee")],
    "osteoarthritis":   [("M17.11", "Primary osteoarthritis, right knee")],
    "cancer":           [("C34.90", "Malignant neoplasm of bronchus or lung")],
    "lung cancer":      [("C34.90", "Malignant neoplasm of bronchus or lung")],
    "breast cancer":    [("C50.919", "Malignant neoplasm of unspecified site of breast")],
    "prostate cancer":  [("C61", "Malignant neoplasm of prostate")],
    "seizure":          [("G40.909", "Epilepsy, unspecified")],
    "epilepsy":         [("G40.909", "Epilepsy, unspecified")],
    "parkinson":        [("G20", "Parkinson disease")],
    "migraine":         [("G43.909", "Migraine, unspecified")],
    "headache":         [("G43.909", "Migraine, unspecified")],
    "sleep apnea":      [("G47.33", "Obstructive sleep apnea")],
    "alcohol":          [("F10.20", "Alcohol dependence, uncomplicated")],
    "bipolar":          [("F31.9", "Bipolar disorder, unspecified")],
    "respiratory failure": [("J96.01", "Acute respiratory failure with hypoxia")],
    "ards":             [("J80", "Acute respiratory distress syndrome")],
    "pleural effusion": [("J90", "Pleural effusion, not elsewhere classified")],
    "bronchitis":       [("J20.9", "Acute bronchitis, unspecified")],
    "cough":            [("J06.9", "Acute upper respiratory infection, unspecified")],
    "rhabdomyolysis":   [("M62.82", "Rhabdomyolysis")],
    "tia":              [("G45.9", "Transient cerebral ischemic attack, unspecified")],
    "kidney stone":     [("N20.0", "Calculus of kidney")],
    "renal calculus":   [("N20.0", "Calculus of kidney")],
    "intestinal obstruction": [("K56.60", "Unspecified intestinal obstruction")],
    "bowel obstruction": [("K56.60", "Unspecified intestinal obstruction")],
    "cirrhosis":        [("K74.60", "Unspecified cirrhosis of liver")],
    "liver":            [("K74.60", "Unspecified cirrhosis of liver")],
    "diverticulosis":   [("K57.30", "Diverticulosis of large intestine")],
    "concussion":       [("S06.0X0A", "Concussion without loss of consciousness, initial encounter")],
    "anaphylaxis":      [("T78.2XXA", "Anaphylactic shock, unspecified, initial encounter")],
    "delivery":         [("O80", "Encounter for full-term uncomplicated delivery")],
    "pregnancy":        [("O80", "Encounter for full-term uncomplicated delivery")],
    "chemotherapy":     [("Z51.11", "Encounter for antineoplastic chemotherapy")],
    "radiation therapy": [("Z51.0", "Encounter for antineoplastic radiation therapy")],
    "immunization":     [("Z23", "Encounter for immunization")],
    "vaccination":      [("Z23", "Encounter for immunization")],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_icd10(query, limit=20):
    """Search ICD-10 codes by code prefix or description keyword.

    Parameters
    ----------
    query : str
        Search string - matched against code and description.
    limit : int
        Maximum results to return (default 20).

    Returns
    -------
    list of dict
        Each dict has keys: code, description, match_type ('code' or 'description').
    """
    if not query or not query.strip():
        return []

    query_upper = query.strip().upper()
    query_lower = query.strip().lower()
    results = []

    # Search by code prefix
    for code, desc in ICD10_CODES:
        if code.upper().startswith(query_upper):
            results.append({
                "code": code,
                "description": desc,
                "match_type": "code",
            })

    # Search by description keyword
    for code, desc in ICD10_CODES:
        if query_lower in desc.lower() and not any(r["code"] == code for r in results):
            results.append({
                "code": code,
                "description": desc,
                "match_type": "description",
            })

    return results[:limit]


def search_cpt(query, limit=20):
    """Search CPT codes by code prefix or description keyword.

    Parameters
    ----------
    query : str
        Search string - matched against code and description.
    limit : int
        Maximum results to return (default 20).

    Returns
    -------
    list of dict
        Each dict has keys: code, description, match_type ('code' or 'description').
    """
    if not query or not query.strip():
        return []

    query_stripped = query.strip()
    query_lower = query_stripped.lower()
    results = []

    # Search by code prefix
    for code, desc in CPT_CODES:
        if code.startswith(query_stripped):
            results.append({
                "code": code,
                "description": desc,
                "match_type": "code",
            })

    # Search by description keyword
    for code, desc in CPT_CODES:
        if query_lower in desc.lower() and not any(r["code"] == code for r in results):
            results.append({
                "code": code,
                "description": desc,
                "match_type": "description",
            })

    return results[:limit]


def validate_code(code, code_type):
    """Validate a medical code and return detailed information.

    Parameters
    ----------
    code : str
        The code to validate.
    code_type : str
        One of 'icd10', 'cpt', 'drg', 'snomed'.

    Returns
    -------
    dict
        Keys: valid (bool), code, code_type, description, format_valid,
        common_issues (list of str).
    """
    if not code or not code_type:
        return {
            "valid": False,
            "code": code,
            "code_type": code_type,
            "description": None,
            "format_valid": False,
            "common_issues": ["Code and code_type are required"],
        }

    code = code.strip()
    code_type = code_type.strip().lower()
    issues = []
    description = None
    format_valid = False
    found = False

    if code_type == "icd10":
        # ICD-10-CM format: letter + digits, optional decimal
        icd10_pattern = re.compile(r"^[A-Z]\d{2}(\.\d{1,4})?[A-Z]?$", re.IGNORECASE)
        format_valid = bool(icd10_pattern.match(code))

        if not format_valid:
            issues.append(f"Code '{code}' does not match ICD-10-CM format (letter + 2 digits + optional decimal + up to 4 characters)")

        # Look up in reference
        code_upper = code.upper()
        for c, d in ICD10_CODES:
            if c.upper() == code_upper:
                found = True
                description = d
                break

        if not found:
            # Check if truncated version exists
            base_code = code_upper.split(".")[0]
            partials = [(c, d) for c, d in ICD10_CODES if c.upper().startswith(base_code)]
            if partials:
                issues.append(f"Code '{code}' not found but similar codes exist under category {base_code}")
                issues.append("Consider: " + "; ".join(f"{c} ({d})" for c, d in partials[:3]))
            else:
                issues.append(f"Code '{code}' not found in reference table (may still be valid if table is incomplete)")

        # Common ICD-10 coding issues
        if "." not in code and len(code) > 3:
            issues.append("Missing decimal point - ICD-10 codes with >3 characters should have a decimal after position 3")
        if code.upper().startswith("E11") and "diabetes" not in (description or "").lower():
            pass  # fine
        if code.upper() == code and format_valid and not found:
            issues.append("Verify laterality and extension characters for injury/external cause codes")

    elif code_type == "cpt":
        # CPT format: 5 digits (or 4 digits + letter for Category II/III)
        cpt_pattern = re.compile(r"^\d{4,5}[A-Z]?$")
        format_valid = bool(cpt_pattern.match(code))

        if not format_valid:
            issues.append(f"Code '{code}' does not match CPT format (5 digits, or 4 digits + letter)")

        for c, d in CPT_CODES:
            if c == code:
                found = True
                description = d
                break

        if not found:
            # Check category range
            if code.isdigit():
                num = int(code)
                if 99201 <= num <= 99499:
                    issues.append("E/M code range - verify documentation level supports this code")
                elif 10000 <= num <= 69999:
                    issues.append("Surgical code range - ensure operative report supports procedure code")
                elif 70000 <= num <= 79999:
                    issues.append("Radiology code range")
                elif 80000 <= num <= 89999:
                    issues.append("Pathology/Lab code range")
                elif 90000 <= num <= 99199:
                    issues.append("Medicine code range")

            issues.append(f"Code '{code}' not found in reference table")

    elif code_type == "drg":
        drg_pattern = re.compile(r"^\d{3}$")
        format_valid = bool(drg_pattern.match(code))

        if not format_valid:
            issues.append(f"DRG code '{code}' should be exactly 3 digits")

        info = DRG_TABLE.get(code)
        if info:
            found = True
            description = info["description"]
        else:
            issues.append(f"DRG '{code}' not found in reference table")

    elif code_type == "snomed":
        snomed_pattern = re.compile(r"^\d{6,18}$")
        format_valid = bool(snomed_pattern.match(code))

        if not format_valid:
            issues.append(f"SNOMED CT code '{code}' should be 6-18 digits")

        if code in SNOMED_TO_ICD10:
            found = True
            mapped = SNOMED_TO_ICD10[code]
            description = f"Maps to: {', '.join(c + ' (' + d + ')' for c, d in mapped)}"
        else:
            issues.append(f"SNOMED code '{code}' not found in crosswalk table")

    else:
        issues.append(f"Unknown code_type '{code_type}'. Supported: icd10, cpt, drg, snomed")

    return {
        "valid": found and format_valid,
        "code": code,
        "code_type": code_type,
        "description": description,
        "format_valid": format_valid,
        "in_reference_table": found,
        "common_issues": issues if issues else ["No issues found"],
    }


def get_drg_info(drg_code):
    """Return detailed DRG information for a given code.

    Parameters
    ----------
    drg_code : str
        The 3-digit DRG code.

    Returns
    -------
    dict
        Keys: drg_code, description, mdc, type, weight, gmlos, amlos,
        expected_reimbursement. Returns error key if not found.
    """
    if not drg_code:
        return {"error": "DRG code is required"}

    drg_code = drg_code.strip().zfill(3)
    info = DRG_TABLE.get(drg_code)

    if not info:
        # Try to find similar
        suggestions = []
        for k, v in DRG_TABLE.items():
            if k[0] == drg_code[0]:
                suggestions.append({"code": k, "description": v["description"]})
        return {
            "error": f"DRG code '{drg_code}' not found",
            "suggestions": suggestions[:5],
        }

    return {
        "drg_code": drg_code,
        "description": info["description"],
        "mdc": info["mdc"],
        "type": info["type"],
        "relative_weight": info["weight"],
        "geometric_mean_los": info["gmlos"],
        "arithmetic_mean_los": info["amlos"],
        "expected_reimbursement": info["expected_reimbursement"],
        "reimbursement_note": "Based on national average base rate; actual varies by facility and region",
    }


def crosswalk_snomed_to_icd10(snomed_code):
    """Map a SNOMED CT code to ICD-10-CM codes.

    Parameters
    ----------
    snomed_code : str
        The SNOMED CT concept ID.

    Returns
    -------
    list of dict
        Each dict has keys: icd10_code, description, mapping_type.
        Returns a single error dict if not found.
    """
    if not snomed_code:
        return [{"error": "SNOMED code is required"}]

    snomed_code = snomed_code.strip()
    mappings = SNOMED_TO_ICD10.get(snomed_code)

    if not mappings:
        return [{
            "error": f"No ICD-10 mapping found for SNOMED CT code '{snomed_code}'",
            "note": "This crosswalk table contains a representative subset of mappings. "
                    "A production system would use the full NLM SNOMED-to-ICD-10-CM map.",
            "available_snomed_codes": sorted(SNOMED_TO_ICD10.keys())[:20],
        }]

    results = []
    for idx, (icd10_code, desc) in enumerate(mappings):
        results.append({
            "icd10_code": icd10_code,
            "description": desc,
            "mapping_type": "primary" if idx == 0 else "alternative",
            "snomed_code": snomed_code,
        })

    return results


def suggest_codes(clinical_text):
    """Suggest ICD-10 codes based on clinical text keywords.

    Parameters
    ----------
    clinical_text : str
        Free-text clinical narrative (e.g., chief complaint, HPI).

    Returns
    -------
    list of dict
        Each dict has keys: code, description, matched_keyword, confidence.
    """
    if not clinical_text or not clinical_text.strip():
        return []

    text_lower = clinical_text.strip().lower()
    suggestions = {}

    # Match multi-word keywords first (longer = more specific)
    sorted_keywords = sorted(_KEYWORD_TO_ICD10.keys(), key=len, reverse=True)

    for keyword in sorted_keywords:
        if keyword in text_lower:
            for code, desc in _KEYWORD_TO_ICD10[keyword]:
                if code not in suggestions:
                    # Confidence heuristic: longer keyword match = higher confidence
                    word_count = len(keyword.split())
                    if word_count >= 3:
                        confidence = "high"
                    elif word_count == 2:
                        confidence = "medium"
                    else:
                        confidence = "low"

                    suggestions[code] = {
                        "code": code,
                        "description": desc,
                        "matched_keyword": keyword,
                        "confidence": confidence,
                    }

    # Sort by confidence then code
    conf_order = {"high": 0, "medium": 1, "low": 2}
    result = sorted(suggestions.values(), key=lambda x: (conf_order.get(x["confidence"], 3), x["code"]))

    return result


def check_coding_accuracy(db_path, encounter_id):
    """Audit coding accuracy for a specific encounter.

    Checks for common coding issues: missing primary diagnosis, diagnosis
    not supporting the DRG, procedure code mismatches, and more.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    encounter_id : int or str
        The encounter ID to audit.

    Returns
    -------
    dict
        Keys: encounter_id, encounter_type, findings (list of issues),
        diagnoses, procedures, drg_info, score, recommendation.
    """
    conn = _db(db_path)
    try:
        encounter_id = int(encounter_id)

        # Fetch encounter
        enc = conn.execute(
            "SELECT e.*, d.dept_name "
            "FROM encounters e "
            "LEFT JOIN departments d ON e.department_id = d.dept_id "
            "WHERE e.encounter_id = ?", (encounter_id,)
        ).fetchone()

        if not enc:
            return {"error": f"Encounter {encounter_id} not found"}

        findings = []
        score = 100  # Start at 100, deduct for each finding

        # Fetch diagnoses
        diagnoses = conn.execute(
            "SELECT * FROM diagnoses WHERE encounter_id = ? ORDER BY diagnosis_type",
            (encounter_id,)
        ).fetchall()
        dx_list = [dict(d) for d in diagnoses]

        # Fetch procedures
        procedures = conn.execute(
            "SELECT * FROM procedures WHERE encounter_id = ?",
            (encounter_id,)
        ).fetchall()
        proc_list = [dict(p) for p in procedures]

        # Check 1: Primary diagnosis
        has_primary = any(d["diagnosis_type"] == "primary" for d in dx_list)
        if not has_primary and dx_list:
            findings.append({
                "severity": "error",
                "category": "Diagnosis",
                "message": "No primary diagnosis assigned. Every encounter requires a principal/primary diagnosis.",
                "recommendation": "Review diagnoses and designate one as primary."
            })
            score -= 15
        if not dx_list:
            findings.append({
                "severity": "error",
                "category": "Diagnosis",
                "message": "No diagnoses found for this encounter.",
                "recommendation": "All encounters should have at least one diagnosis code."
            })
            score -= 25

        # Check 2: Validate ICD-10 codes
        known_icd10 = {c.upper() for c, _ in ICD10_CODES}
        for dx in dx_list:
            code = dx.get("icd10_code", "").upper()
            if code not in known_icd10:
                findings.append({
                    "severity": "warning",
                    "category": "Diagnosis",
                    "message": f"ICD-10 code '{dx.get('icd10_code', '')}' not found in reference table.",
                    "recommendation": "Verify code validity in the official ICD-10-CM code set."
                })
                score -= 5

        # Check 3: Validate CPT codes
        known_cpt = {c for c, _ in CPT_CODES}
        for proc in proc_list:
            code = proc.get("cpt_code", "")
            if code not in known_cpt:
                findings.append({
                    "severity": "warning",
                    "category": "Procedure",
                    "message": f"CPT code '{code}' not found in reference table.",
                    "recommendation": "Verify code validity."
                })
                score -= 5

        # Check 4: DRG validation for inpatient encounters
        drg_info = None
        if enc["encounter_type"] == "inpatient":
            drg_code = enc["drg_code"]
            if not drg_code:
                findings.append({
                    "severity": "error",
                    "category": "DRG",
                    "message": "Inpatient encounter is missing a DRG code.",
                    "recommendation": "Assign an appropriate MS-DRG based on principal diagnosis and procedures."
                })
                score -= 20
            else:
                drg_info = DRG_TABLE.get(drg_code)
                if drg_info:
                    # Check LOS vs expected
                    los = enc["los_days"] or 0
                    gmlos = drg_info.get("gmlos", 0)
                    if los > 0 and gmlos > 0:
                        if los > gmlos * 2:
                            findings.append({
                                "severity": "warning",
                                "category": "DRG",
                                "message": f"Length of stay ({los} days) significantly exceeds geometric mean LOS ({gmlos} days) for DRG {drg_code}.",
                                "recommendation": "Review for potential DRG optimization or documentation improvement."
                            })
                            score -= 5
                        elif los < gmlos * 0.3:
                            findings.append({
                                "severity": "info",
                                "category": "DRG",
                                "message": f"Length of stay ({los} days) is well below expected ({gmlos} days) for DRG {drg_code}.",
                                "recommendation": "Ensure discharge criteria were met and documentation supports the DRG."
                            })
                else:
                    findings.append({
                        "severity": "warning",
                        "category": "DRG",
                        "message": f"DRG code '{drg_code}' not found in reference table.",
                        "recommendation": "Verify DRG code assignment."
                    })
                    score -= 5
        elif enc["encounter_type"] == "outpatient":
            if enc.get("drg_code"):
                findings.append({
                    "severity": "warning",
                    "category": "DRG",
                    "message": "Outpatient encounter has a DRG code assigned. DRGs are typically used for inpatient only.",
                    "recommendation": "Review encounter type classification."
                })
                score -= 5

        # Check 5: E/M code level consistency
        em_procs = [p for p in proc_list if p.get("cpt_code", "").startswith("992")]
        if em_procs:
            for em in em_procs:
                cpt = em.get("cpt_code", "")
                # High-complexity E/M with few diagnoses
                if cpt in ("99215", "99223", "99233", "99285", "99291") and len(dx_list) < 2:
                    findings.append({
                        "severity": "warning",
                        "category": "E/M Coding",
                        "message": f"High-complexity E/M code {cpt} with only {len(dx_list)} diagnosis code(s).",
                        "recommendation": "Ensure medical decision-making documentation supports the E/M level."
                    })
                    score -= 5

        # Check 6: Missing procedures for certain encounter types
        if enc["encounter_type"] == "inpatient" and not proc_list:
            findings.append({
                "severity": "info",
                "category": "Procedure",
                "message": "No procedures recorded for inpatient encounter.",
                "recommendation": "Verify all performed procedures have been coded."
            })

        # Check 7: Diagnosis-procedure consistency
        dx_codes = {d.get("icd10_code", "").upper() for d in dx_list}
        surgical_procs = [p for p in proc_list if p.get("cpt_code", "") and
                          p["cpt_code"].isdigit() and 10000 <= int(p["cpt_code"]) <= 69999]
        if surgical_procs and not dx_list:
            findings.append({
                "severity": "error",
                "category": "Consistency",
                "message": "Surgical procedures recorded but no diagnoses to support them.",
                "recommendation": "Add diagnosis codes that justify the surgical procedures."
            })
            score -= 15

        # Check 8: Duplicate diagnoses
        seen_codes = set()
        for dx in dx_list:
            code = dx.get("icd10_code", "")
            if code in seen_codes:
                findings.append({
                    "severity": "warning",
                    "category": "Diagnosis",
                    "message": f"Duplicate diagnosis code '{code}' found on this encounter.",
                    "recommendation": "Remove duplicate diagnosis entries."
                })
                score -= 3
            seen_codes.add(code)

        # Ensure score stays in 0-100 range
        score = max(0, min(100, score))

        # Rating
        if score >= 90:
            rating = "Excellent"
        elif score >= 75:
            rating = "Good"
        elif score >= 60:
            rating = "Fair"
        elif score >= 40:
            rating = "Needs Improvement"
        else:
            rating = "Poor"

        return {
            "encounter_id": encounter_id,
            "encounter_type": enc["encounter_type"],
            "patient_mrn": enc["patient_mrn"],
            "department": enc["dept_name"],
            "admission_date": enc["admission_date"],
            "discharge_date": enc["discharge_date"],
            "drg_code": enc["drg_code"],
            "drg_info": drg_info,
            "diagnoses": dx_list,
            "diagnosis_count": len(dx_list),
            "procedures": proc_list,
            "procedure_count": len(proc_list),
            "findings": findings,
            "finding_count": len(findings),
            "accuracy_score": score,
            "rating": rating,
        }
    finally:
        conn.close()

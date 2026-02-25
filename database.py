"""
Health Informatics Learning Platform - Database Schema & Seed Data Generator

Creates a comprehensive SQLite database modelling a hospital EHR system
with realistic clinical, administrative, quality, and integration data.

Usage:
    python database.py              # Creates hinfo.db in the current directory
    python database.py <path.db>    # Creates database at the specified path

Programmatic:
    from database import init_db, seed_data
    init_db('hinfo.db')
    seed_data('hinfo.db')
"""

import sqlite3
import random
import string
import sys
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# ---------------------------------------------------------------------------
# Constants - realistic medical reference data
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    ("Emergency Department", "ED", 1, "Main", "(555) 100-0001", 40),
    ("Intensive Care Unit", "ICU", 3, "Main", "(555) 100-0002", 24),
    ("Medical/Surgical", "MEDSURG", 4, "Main", "(555) 100-0003", 60),
    ("Pediatrics", "PEDS", 2, "East Wing", "(555) 100-0004", 30),
    ("OB/GYN", "OBGYN", 2, "East Wing", "(555) 100-0005", 25),
    ("Cardiology", "CARD", 5, "Heart Center", "(555) 100-0006", 20),
    ("Oncology", "ONC", 6, "Cancer Center", "(555) 100-0007", 18),
    ("Orthopedics", "ORTHO", 4, "Main", "(555) 100-0008", 22),
    ("Neurology", "NEURO", 5, "Main", "(555) 100-0009", 16),
    ("Radiology", "RAD", 1, "Main", "(555) 100-0010", None),
    ("Laboratory", "LAB", 1, "Main", "(555) 100-0011", None),
    ("Pharmacy", "PHARM", 1, "Main", "(555) 100-0012", None),
    ("Respiratory Therapy", "RESP", 3, "Main", "(555) 100-0013", None),
    ("Rehabilitation", "REHAB", 2, "West Wing", "(555) 100-0014", 12),
    ("Psychiatry", "PSYCH", 6, "West Wing", "(555) 100-0015", 20),
]

SPECIALTIES = [
    "Emergency Medicine", "Internal Medicine", "Family Medicine",
    "Cardiology", "Pulmonology", "Neurology", "Oncology",
    "Orthopedic Surgery", "General Surgery", "Pediatrics",
    "Obstetrics and Gynecology", "Psychiatry", "Radiology",
    "Anesthesiology", "Pathology", "Critical Care Medicine",
    "Endocrinology", "Gastroenterology", "Nephrology",
    "Infectious Disease",
]

CREDENTIALS = ["MD", "MD", "MD", "DO", "DO", "NP", "PA", "RN", "RN", "MD"]

# 90 ICD-10 codes with descriptions
ICD10_CODES = [
    ("I10", "Essential (primary) hypertension"),
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("E11.65", "Type 2 diabetes mellitus with hyperglycemia"),
    ("J18.9", "Pneumonia, unspecified organism"),
    ("N39.0", "Urinary tract infection, site not specified"),
    ("K21.0", "Gastro-esophageal reflux disease with esophagitis"),
    ("M54.5", "Low back pain"),
    ("J44.1", "Chronic obstructive pulmonary disease with acute exacerbation"),
    ("I25.10", "Atherosclerotic heart disease of native coronary artery"),
    ("E78.5", "Hyperlipidemia, unspecified"),
    ("F32.9", "Major depressive disorder, single episode, unspecified"),
    ("J06.9", "Acute upper respiratory infection, unspecified"),
    ("I50.9", "Heart failure, unspecified"),
    ("I48.91", "Unspecified atrial fibrillation"),
    ("E87.1", "Hypo-osmolality and hyponatremia"),
    ("N17.9", "Acute kidney failure, unspecified"),
    ("D64.9", "Anemia, unspecified"),
    ("I63.9", "Cerebral infarction, unspecified"),
    ("J96.01", "Acute respiratory failure with hypoxia"),
    ("A41.9", "Sepsis, unspecified organism"),
    ("K92.1", "Melena"),
    ("R07.9", "Chest pain, unspecified"),
    ("K59.00", "Constipation, unspecified"),
    ("J45.20", "Mild intermittent asthma, uncomplicated"),
    ("J45.41", "Moderate persistent asthma with acute exacerbation"),
    ("E11.22", "Type 2 diabetes mellitus with diabetic chronic kidney disease"),
    ("G47.33", "Obstructive sleep apnea"),
    ("I21.9", "Acute myocardial infarction, unspecified"),
    ("K80.20", "Calculus of gallbladder without cholecystitis without obstruction"),
    ("N18.3", "Chronic kidney disease, stage 3"),
    ("N18.6", "End stage renal disease"),
    ("F41.1", "Generalized anxiety disorder"),
    ("G40.909", "Epilepsy, unspecified, not intractable, without status epilepticus"),
    ("M79.3", "Panniculitis, unspecified"),
    ("L03.311", "Cellulitis of abdominal wall"),
    ("T78.40XA", "Allergy, unspecified, initial encounter"),
    ("E03.9", "Hypothyroidism, unspecified"),
    ("B96.20", "Unspecified Escherichia coli as cause of diseases classified elsewhere"),
    ("R11.2", "Nausea with vomiting, unspecified"),
    ("M17.11", "Primary osteoarthritis, right knee"),
    ("M17.12", "Primary osteoarthritis, left knee"),
    ("I26.99", "Other pulmonary embolism without acute cor pulmonale"),
    ("G43.909", "Migraine, unspecified, not intractable, without status migrainosus"),
    ("J20.9", "Acute bronchitis, unspecified"),
    ("I73.9", "Peripheral vascular disease, unspecified"),
    ("K57.32", "Diverticulitis of large intestine without perforation or abscess without bleeding"),
    ("R10.9", "Unspecified abdominal pain"),
    ("S72.001A", "Fracture of unspecified part of neck of right femur, initial encounter"),
    ("S82.001A", "Unspecified fracture of right patella, initial encounter"),
    ("E55.9", "Vitamin D deficiency, unspecified"),
    ("Z87.891", "Personal history of nicotine dependence"),
    ("Z79.4", "Long term (current) use of insulin"),
    ("G20", "Parkinson disease"),
    ("F10.20", "Alcohol dependence, uncomplicated"),
    ("B37.0", "Candidal stomatitis"),
    ("J15.9", "Unspecified bacterial pneumonia"),
    ("M48.06", "Spinal stenosis, lumbar region"),
    ("K76.0", "Fatty (change of) liver, not elsewhere classified"),
    ("E66.01", "Morbid (severe) obesity due to excess calories"),
    ("R06.02", "Shortness of breath"),
    ("I70.0", "Atherosclerosis of aorta"),
    ("N40.0", "Benign prostatic hyperplasia without lower urinary tract symptoms"),
    ("D50.9", "Iron deficiency anemia, unspecified"),
    ("R55", "Syncope and collapse"),
    ("Z23", "Encounter for immunization"),
    ("J02.9", "Acute pharyngitis, unspecified"),
    ("M25.561", "Pain in right knee"),
    ("M25.562", "Pain in left knee"),
    ("H26.9", "Unspecified cataract"),
    ("E87.6", "Hypokalemia"),
    ("R50.9", "Fever, unspecified"),
    ("I47.1", "Supraventricular tachycardia"),
    ("J90", "Pleural effusion, not elsewhere classified"),
    ("C34.90", "Malignant neoplasm of unspecified part of unspecified bronchus or lung"),
    ("C50.919", "Malignant neoplasm of unspecified site of unspecified female breast"),
    ("C18.9", "Malignant neoplasm of colon, unspecified"),
    ("C61", "Malignant neoplasm of prostate"),
    ("Z51.11", "Encounter for antineoplastic chemotherapy"),
    ("Z51.0", "Encounter for antineoplastic radiation therapy"),
    ("F17.210", "Nicotine dependence, cigarettes, uncomplicated"),
    ("G89.29", "Other chronic pain"),
    ("M62.830", "Muscle spasm of back"),
    ("R05.9", "Cough, unspecified"),
    ("T14.91XA", "Suicide attempt, initial encounter"),
    ("L97.529", "Non-pressure chronic ulcer of other part of left foot with unspecified severity"),
    ("E11.40", "Type 2 diabetes mellitus with diabetic neuropathy, unspecified"),
    ("I69.354", "Hemiplegia and hemiparesis following cerebral infarction affecting left non-dominant side"),
    ("Z96.641", "Presence of right artificial hip joint"),
    ("Z95.1", "Presence of aortocoronary bypass graft"),
    ("Z66", "Do not resuscitate"),
]

# 50 CPT codes with descriptions
CPT_CODES = [
    ("99213", "Office/outpatient visit, established patient, low complexity"),
    ("99214", "Office/outpatient visit, established patient, moderate complexity"),
    ("99215", "Office/outpatient visit, established patient, high complexity"),
    ("99223", "Initial hospital care, high complexity"),
    ("99232", "Subsequent hospital care, moderate complexity"),
    ("99233", "Subsequent hospital care, high complexity"),
    ("99281", "Emergency department visit, straightforward"),
    ("99283", "Emergency department visit, moderate complexity"),
    ("99284", "Emergency department visit, moderately high complexity"),
    ("99285", "Emergency department visit, high complexity"),
    ("36415", "Venipuncture"),
    ("71046", "Chest X-ray, 2 views"),
    ("71045", "Chest X-ray, single view"),
    ("93000", "Electrocardiogram, 12-lead, with interpretation"),
    ("85025", "Complete blood count with differential"),
    ("80053", "Comprehensive metabolic panel"),
    ("80048", "Basic metabolic panel"),
    ("80061", "Lipid panel"),
    ("81001", "Urinalysis, automated with microscopy"),
    ("84443", "Thyroid stimulating hormone"),
    ("83036", "Hemoglobin A1c"),
    ("82947", "Glucose, blood"),
    ("74177", "CT abdomen and pelvis with contrast"),
    ("70553", "MRI brain with and without contrast"),
    ("73721", "MRI lower extremity joint without contrast"),
    ("27447", "Total knee arthroplasty"),
    ("27130", "Total hip arthroplasty"),
    ("43239", "Upper GI endoscopy with biopsy"),
    ("45380", "Colonoscopy with biopsy"),
    ("33533", "Coronary artery bypass, single graft"),
    ("92928", "Percutaneous coronary stent placement"),
    ("43846", "Gastric bypass for morbid obesity"),
    ("47562", "Laparoscopic cholecystectomy"),
    ("49505", "Inguinal hernia repair"),
    ("59400", "Routine obstetric care, vaginal delivery"),
    ("59510", "Routine obstetric care, cesarean delivery"),
    ("11042", "Debridement, subcutaneous tissue"),
    ("20610", "Arthrocentesis, major joint"),
    ("62322", "Lumbar epidural injection"),
    ("90837", "Psychotherapy, 60 minutes"),
    ("96372", "Therapeutic injection, subcutaneous or intramuscular"),
    ("97110", "Therapeutic exercises"),
    ("97140", "Manual therapy techniques"),
    ("94640", "Nebulizer treatment"),
    ("31500", "Intubation, endotracheal"),
    ("32551", "Chest tube insertion"),
    ("93306", "Echocardiography, transthoracic, complete"),
    ("76856", "Pelvic ultrasound, complete"),
    ("77067", "Screening mammography, bilateral"),
    ("90471", "Immunization administration"),
]

MEDICATIONS = [
    ("Metformin", "Metformin HCl", "Biguanide", "oral", "tablet"),
    ("Lisinopril", "Lisinopril", "ACE Inhibitor", "oral", "tablet"),
    ("Atorvastatin", "Atorvastatin Calcium", "HMG-CoA Reductase Inhibitor", "oral", "tablet"),
    ("Metoprolol Succinate", "Metoprolol Succinate", "Beta Blocker", "oral", "tablet"),
    ("Omeprazole", "Omeprazole", "Proton Pump Inhibitor", "oral", "capsule"),
    ("Amlodipine", "Amlodipine Besylate", "Calcium Channel Blocker", "oral", "tablet"),
    ("Losartan", "Losartan Potassium", "Angiotensin II Receptor Blocker", "oral", "tablet"),
    ("Levothyroxine", "Levothyroxine Sodium", "Thyroid Hormone", "oral", "tablet"),
    ("Gabapentin", "Gabapentin", "Anticonvulsant / Neuropathic Pain", "oral", "capsule"),
    ("Sertraline", "Sertraline HCl", "SSRI", "oral", "tablet"),
    ("Furosemide", "Furosemide", "Loop Diuretic", "oral", "tablet"),
    ("Hydrochlorothiazide", "Hydrochlorothiazide", "Thiazide Diuretic", "oral", "tablet"),
    ("Prednisone", "Prednisone", "Corticosteroid", "oral", "tablet"),
    ("Albuterol", "Albuterol Sulfate", "Beta-2 Agonist", "inhalation", "nebulizer solution"),
    ("Insulin Glargine", "Insulin Glargine", "Long-Acting Insulin", "subcutaneous", "injection"),
    ("Warfarin", "Warfarin Sodium", "Anticoagulant", "oral", "tablet"),
    ("Heparin", "Heparin Sodium", "Anticoagulant", "intravenous", "injection"),
    ("Enoxaparin", "Enoxaparin Sodium", "Low Molecular Weight Heparin", "subcutaneous", "injection"),
    ("Ceftriaxone", "Ceftriaxone Sodium", "Cephalosporin Antibiotic", "intravenous", "injection"),
    ("Vancomycin", "Vancomycin HCl", "Glycopeptide Antibiotic", "intravenous", "injection"),
    ("Piperacillin-Tazobactam", "Piperacillin/Tazobactam", "Penicillin/Beta-Lactamase Inhibitor", "intravenous", "injection"),
    ("Morphine", "Morphine Sulfate", "Opioid Analgesic", "intravenous", "injection"),
    ("Acetaminophen", "Acetaminophen", "Analgesic/Antipyretic", "oral", "tablet"),
    ("Ibuprofen", "Ibuprofen", "NSAID", "oral", "tablet"),
    ("Ondansetron", "Ondansetron HCl", "Antiemetic", "intravenous", "injection"),
    ("Pantoprazole", "Pantoprazole Sodium", "Proton Pump Inhibitor", "intravenous", "injection"),
    ("Normal Saline", "Sodium Chloride 0.9%", "IV Fluid", "intravenous", "solution"),
    ("Lactated Ringers", "Lactated Ringers Solution", "IV Fluid", "intravenous", "solution"),
    ("Potassium Chloride", "Potassium Chloride", "Electrolyte Replacement", "oral", "tablet"),
    ("Aspirin", "Acetylsalicylic Acid", "Antiplatelet / NSAID", "oral", "tablet"),
]

# Lab tests with realistic reference ranges and units
LAB_TESTS = [
    # CBC
    ("WBC", "6690-2", "x10^3/uL", 4.5, 11.0, lambda: round(random.gauss(7.5, 3.0), 1)),
    ("RBC", "789-8", "x10^6/uL", 4.0, 5.5, lambda: round(random.gauss(4.7, 0.6), 2)),
    ("Hemoglobin", "718-7", "g/dL", 12.0, 17.5, lambda: round(random.gauss(14.0, 2.0), 1)),
    ("Hematocrit", "4544-3", "%", 36.0, 50.0, lambda: round(random.gauss(42.0, 5.0), 1)),
    ("Platelet Count", "777-3", "x10^3/uL", 150.0, 400.0, lambda: round(random.gauss(250.0, 70.0))),
    ("MCV", "787-2", "fL", 80.0, 100.0, lambda: round(random.gauss(90.0, 6.0), 1)),
    # BMP
    ("Sodium", "2951-2", "mEq/L", 136.0, 145.0, lambda: round(random.gauss(140.0, 3.0))),
    ("Potassium", "2823-3", "mEq/L", 3.5, 5.0, lambda: round(random.gauss(4.2, 0.5), 1)),
    ("Chloride", "2075-0", "mEq/L", 98.0, 106.0, lambda: round(random.gauss(102.0, 3.0))),
    ("CO2", "2028-9", "mEq/L", 22.0, 29.0, lambda: round(random.gauss(25.0, 3.0))),
    ("BUN", "3094-0", "mg/dL", 7.0, 20.0, lambda: round(random.gauss(15.0, 6.0))),
    ("Creatinine", "2160-0", "mg/dL", 0.6, 1.2, lambda: round(random.gauss(1.0, 0.4), 2)),
    ("Glucose", "2345-7", "mg/dL", 70.0, 100.0, lambda: round(random.gauss(105.0, 35.0))),
    # CMP additional
    ("Calcium", "17861-6", "mg/dL", 8.5, 10.5, lambda: round(random.gauss(9.5, 0.5), 1)),
    ("Total Protein", "2885-2", "g/dL", 6.0, 8.3, lambda: round(random.gauss(7.0, 0.6), 1)),
    ("Albumin", "1751-7", "g/dL", 3.5, 5.0, lambda: round(random.gauss(4.0, 0.5), 1)),
    ("Bilirubin Total", "1975-2", "mg/dL", 0.1, 1.2, lambda: round(random.gauss(0.7, 0.4), 1)),
    ("ALT", "1742-6", "U/L", 7.0, 56.0, lambda: round(random.gauss(28.0, 15.0))),
    ("AST", "1920-8", "U/L", 10.0, 40.0, lambda: round(random.gauss(25.0, 12.0))),
    ("ALP", "6768-6", "U/L", 44.0, 147.0, lambda: round(random.gauss(80.0, 30.0))),
    # Lipid panel
    ("Total Cholesterol", "2093-3", "mg/dL", 0.0, 200.0, lambda: round(random.gauss(195.0, 40.0))),
    ("LDL Cholesterol", "2089-1", "mg/dL", 0.0, 100.0, lambda: round(random.gauss(110.0, 35.0))),
    ("HDL Cholesterol", "2085-9", "mg/dL", 40.0, 60.0, lambda: round(random.gauss(52.0, 14.0))),
    ("Triglycerides", "2571-8", "mg/dL", 0.0, 150.0, lambda: round(random.gauss(140.0, 60.0))),
    # Coag
    ("PT", "5902-2", "seconds", 11.0, 13.5, lambda: round(random.gauss(12.5, 2.0), 1)),
    ("INR", "6301-6", "", 0.8, 1.1, lambda: round(random.gauss(1.1, 0.4), 1)),
    ("PTT", "3173-2", "seconds", 25.0, 35.0, lambda: round(random.gauss(30.0, 5.0), 1)),
    # UA
    ("Urinalysis pH", "2756-5", "", 5.0, 8.0, lambda: round(random.gauss(6.0, 0.8), 1)),
    ("Urinalysis Specific Gravity", "2965-2", "", 1.005, 1.030, lambda: round(random.gauss(1.020, 0.008), 3)),
    # Special
    ("Troponin I", "10839-9", "ng/mL", 0.0, 0.04, lambda: round(random.expovariate(10.0), 3)),
    ("BNP", "30934-4", "pg/mL", 0.0, 100.0, lambda: round(random.expovariate(0.005), 1)),
    ("HbA1c", "4548-4", "%", 4.0, 5.6, lambda: round(random.gauss(6.2, 1.5), 1)),
    ("TSH", "3016-3", "mIU/L", 0.4, 4.0, lambda: round(random.gauss(2.5, 1.5), 2)),
    ("Procalcitonin", "75241-0", "ng/mL", 0.0, 0.1, lambda: round(random.expovariate(5.0), 2)),
    ("Lactate", "2524-7", "mmol/L", 0.5, 2.0, lambda: round(random.gauss(1.5, 1.0), 1)),
    ("Magnesium", "19123-9", "mg/dL", 1.7, 2.2, lambda: round(random.gauss(2.0, 0.3), 1)),
    ("Phosphorus", "2777-1", "mg/dL", 2.5, 4.5, lambda: round(random.gauss(3.5, 0.7), 1)),
]

ALLERGENS = [
    ("Penicillin", "drug"), ("Sulfa drugs", "drug"), ("Aspirin", "drug"),
    ("Codeine", "drug"), ("NSAIDs", "drug"), ("Morphine", "drug"),
    ("Latex", "environmental"), ("Iodine contrast dye", "drug"),
    ("Cephalosporins", "drug"), ("Fluoroquinolones", "drug"),
    ("ACE Inhibitors", "drug"), ("Erythromycin", "drug"),
    ("Peanuts", "food"), ("Shellfish", "food"), ("Eggs", "food"),
    ("Tree nuts", "food"), ("Milk", "food"), ("Soy", "food"),
    ("Wheat", "food"), ("Bee stings", "environmental"),
    ("Dust mites", "environmental"), ("Pollen", "environmental"),
    ("Mold", "environmental"), ("Pet dander", "environmental"),
    ("Tetracycline", "drug"), ("Metformin", "drug"),
    ("Lisinopril", "drug"), ("Hydrocodone", "drug"),
]

ALLERGY_REACTIONS = [
    "Rash", "Hives", "Anaphylaxis", "Swelling", "Nausea",
    "Shortness of breath", "Itching", "Throat tightness",
    "Gastrointestinal upset", "Dizziness", "Angioedema",
    "Bronchospasm", "Hypotension", "Stevens-Johnson Syndrome",
]

CHIEF_COMPLAINTS = [
    "Chest pain", "Shortness of breath", "Abdominal pain",
    "Headache", "Back pain", "Fever", "Cough", "Nausea and vomiting",
    "Dizziness", "Weakness", "Fall", "Altered mental status",
    "Leg pain", "Difficulty breathing", "Palpitations",
    "Urinary symptoms", "Wound evaluation", "Anxiety",
    "Suicidal ideation", "Syncope", "Seizure", "Chest tightness",
    "Right arm pain", "Left leg swelling", "Rectal bleeding",
    "Flank pain", "Sore throat", "Hip pain", "Knee pain",
]

INSURANCE_PLANS = [
    ("Blue Cross Blue Shield PPO", "PPO", "Blue Cross Blue Shield", "GRP-100234"),
    ("Aetna HMO", "HMO", "Aetna", "GRP-200567"),
    ("UnitedHealthcare Choice Plus", "PPO", "UnitedHealthcare", "GRP-300891"),
    ("Cigna Open Access Plus", "PPO", "Cigna", "GRP-400123"),
    ("Medicare Part A", "Medicare", "CMS", "MCARE-A"),
    ("Medicare Part B", "Medicare", "CMS", "MCARE-B"),
    ("Medicaid", "Medicaid", "State Medicaid", "MCAID-001"),
    ("Humana Gold Plus", "HMO", "Humana", "GRP-500456"),
    ("Kaiser Permanente", "HMO", "Kaiser", "GRP-600789"),
    ("Tricare Prime", "Commercial", "Department of Defense", "TRI-001"),
]

SYSTEMS = [
    ("Epic EHR", "operational"), ("Cerner Lab Interface", "operational"),
    ("PACS Imaging", "operational"), ("Pharmacy Dispensing", "operational"),
    ("Patient Portal", "operational"), ("HL7 Interface Engine", "operational"),
    ("Bed Management System", "operational"), ("Billing System", "operational"),
]

QUALITY_MEASURES = [
    ("SEP-1", "QM-SEP1", "Severe Sepsis and Septic Shock Management Bundle"),
    ("VTE-1", "QM-VTE1", "Venous Thromboembolism Prophylaxis"),
    ("VTE-2", "QM-VTE2", "ICU Venous Thromboembolism Prophylaxis"),
    ("STK-4", "QM-STK4", "Thrombolytic Therapy"),
    ("EDTC-1", "QM-EDTC1", "Emergency Department Transfer Communication"),
    ("PC-01", "QM-PC01", "Elective Delivery < 39 Weeks"),
    ("IMM-2", "QM-IMM2", "Influenza Immunization"),
    ("HF-1", "QM-HF1", "Heart Failure: Discharge Instructions"),
    ("PN-6", "QM-PN6", "Initial Antibiotic Selection for Community-Acquired Pneumonia"),
    ("CAUTI", "QM-CAUTI", "Catheter-Associated Urinary Tract Infection Rate"),
    ("CLABSI", "QM-CLABSI", "Central Line-Associated Bloodstream Infection Rate"),
    ("MRSA", "QM-MRSA", "MRSA Bacteremia Rate"),
    ("CDI", "QM-CDI", "C. difficile Infection Rate"),
    ("SSI", "QM-SSI", "Surgical Site Infection Rate"),
    ("PSI-90", "QM-PSI90", "Patient Safety and Adverse Events Composite"),
    ("HCAHPS", "QM-HCAHPS", "Hospital Consumer Assessment of Healthcare Providers"),
    ("MORT-30-AMI", "QM-MAMI", "30-Day Mortality Rate for Acute Myocardial Infarction"),
    ("MORT-30-HF", "QM-MHF", "30-Day Mortality Rate for Heart Failure"),
    ("READM-30-HF", "QM-RHF", "30-Day Readmission Rate for Heart Failure"),
    ("ED-2b", "QM-ED2B", "ED Admit Decision Time to ED Departure for Admitted Patients"),
]


# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS departments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    code            TEXT NOT NULL UNIQUE,
    floor           INTEGER,
    building        TEXT,
    phone           TEXT,
    manager_name    TEXT,
    bed_count       INTEGER
);

CREATE TABLE IF NOT EXISTS insurance_plans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name       TEXT NOT NULL,
    plan_type       TEXT NOT NULL CHECK (plan_type IN ('HMO','PPO','Medicare','Medicaid','Commercial')),
    payer_name      TEXT NOT NULL,
    group_number    TEXT
);

CREATE TABLE IF NOT EXISTS providers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    npi             TEXT NOT NULL UNIQUE,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    credentials     TEXT NOT NULL,
    specialty       TEXT NOT NULL,
    department_id   INTEGER NOT NULL REFERENCES departments(id),
    email           TEXT,
    phone           TEXT,
    active          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS patients (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    mrn                     TEXT NOT NULL UNIQUE,
    first_name              TEXT NOT NULL,
    last_name               TEXT NOT NULL,
    dob                     TEXT NOT NULL,
    gender                  TEXT NOT NULL,
    race                    TEXT,
    ethnicity               TEXT,
    ssn_last4               TEXT,
    address                 TEXT,
    city                    TEXT,
    state                   TEXT,
    zip                     TEXT,
    phone                   TEXT,
    email                   TEXT,
    insurance_id            INTEGER REFERENCES insurance_plans(id),
    primary_care_provider_id INTEGER REFERENCES providers(id),
    created_at              TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active','inactive','deceased'))
);

CREATE TABLE IF NOT EXISTS encounters (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id              INTEGER NOT NULL REFERENCES patients(id),
    provider_id             INTEGER NOT NULL REFERENCES providers(id),
    department_id           INTEGER NOT NULL REFERENCES departments(id),
    encounter_type          TEXT NOT NULL
                            CHECK (encounter_type IN ('inpatient','outpatient','emergency','observation')),
    admit_date              TEXT NOT NULL,
    discharge_date          TEXT,
    status                  TEXT NOT NULL
                            CHECK (status IN ('active','discharged','transferred')),
    chief_complaint         TEXT,
    admission_source        TEXT,
    discharge_disposition   TEXT
);

CREATE TABLE IF NOT EXISTS diagnoses (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id            INTEGER NOT NULL REFERENCES encounters(id),
    patient_id              INTEGER NOT NULL REFERENCES patients(id),
    icd10_code              TEXT NOT NULL,
    description             TEXT NOT NULL,
    diagnosis_type          TEXT NOT NULL
                            CHECK (diagnosis_type IN ('primary','secondary','admitting')),
    diagnosed_by_provider_id INTEGER NOT NULL REFERENCES providers(id),
    diagnosis_date          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS procedures (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id            INTEGER NOT NULL REFERENCES encounters(id),
    patient_id              INTEGER NOT NULL REFERENCES patients(id),
    cpt_code                TEXT NOT NULL,
    description             TEXT NOT NULL,
    performing_provider_id  INTEGER NOT NULL REFERENCES providers(id),
    procedure_date          TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS medications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    generic_name    TEXT NOT NULL,
    drug_class      TEXT NOT NULL,
    route           TEXT NOT NULL,
    form            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medication_orders (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id            INTEGER NOT NULL REFERENCES encounters(id),
    patient_id              INTEGER NOT NULL REFERENCES patients(id),
    medication_id           INTEGER NOT NULL REFERENCES medications(id),
    ordering_provider_id    INTEGER NOT NULL REFERENCES providers(id),
    dose                    TEXT NOT NULL,
    unit                    TEXT NOT NULL,
    frequency               TEXT NOT NULL,
    route                   TEXT NOT NULL,
    start_date              TEXT NOT NULL,
    end_date                TEXT,
    status                  TEXT NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active','completed','discontinued','held'))
);

CREATE TABLE IF NOT EXISTS lab_results (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id            INTEGER NOT NULL REFERENCES encounters(id),
    patient_id              INTEGER NOT NULL REFERENCES patients(id),
    ordering_provider_id    INTEGER NOT NULL REFERENCES providers(id),
    test_name               TEXT NOT NULL,
    test_code               TEXT NOT NULL,
    value                   TEXT NOT NULL,
    unit                    TEXT NOT NULL,
    reference_range_low     REAL,
    reference_range_high    REAL,
    abnormal_flag           TEXT DEFAULT 'N'
                            CHECK (abnormal_flag IN ('N','L','H','C')),
    result_date             TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'final'
                            CHECK (status IN ('final','preliminary','corrected'))
);

CREATE TABLE IF NOT EXISTS vital_signs (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id            INTEGER NOT NULL REFERENCES encounters(id),
    patient_id              INTEGER NOT NULL REFERENCES patients(id),
    recorded_by_provider_id INTEGER NOT NULL REFERENCES providers(id),
    temperature             REAL,
    heart_rate              INTEGER,
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    respiratory_rate        INTEGER,
    spo2                    REAL,
    pain_scale              INTEGER,
    recorded_at             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS allergies (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id              INTEGER NOT NULL REFERENCES patients(id),
    allergen                TEXT NOT NULL,
    reaction                TEXT,
    severity                TEXT NOT NULL
                            CHECK (severity IN ('mild','moderate','severe')),
    allergy_type            TEXT NOT NULL
                            CHECK (allergy_type IN ('drug','food','environmental')),
    documented_date         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id            INTEGER NOT NULL REFERENCES encounters(id),
    patient_id              INTEGER NOT NULL REFERENCES patients(id),
    ordering_provider_id    INTEGER NOT NULL REFERENCES providers(id),
    order_type              TEXT NOT NULL
                            CHECK (order_type IN ('lab','imaging','consult','diet','activity')),
    order_text              TEXT NOT NULL,
    priority                TEXT NOT NULL DEFAULT 'routine'
                            CHECK (priority IN ('routine','urgent','stat')),
    status                  TEXT NOT NULL DEFAULT 'ordered'
                            CHECK (status IN ('ordered','in_progress','completed','cancelled')),
    ordered_at              TEXT NOT NULL,
    completed_at            TEXT
);

CREATE TABLE IF NOT EXISTS beds (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id           INTEGER NOT NULL REFERENCES departments(id),
    bed_number              TEXT NOT NULL,
    room_number             TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'available'
                            CHECK (status IN ('available','occupied','cleaning','maintenance')),
    current_patient_id      INTEGER REFERENCES patients(id)
);

CREATE TABLE IF NOT EXISTS staff_schedule (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id     INTEGER NOT NULL REFERENCES providers(id),
    shift_date      TEXT NOT NULL,
    shift_start     TEXT NOT NULL,
    shift_end       TEXT NOT NULL,
    department_id   INTEGER NOT NULL REFERENCES departments(id),
    role            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    action          TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    record_id       INTEGER,
    old_value       TEXT,
    new_value       TEXT,
    timestamp       TEXT NOT NULL,
    ip_address      TEXT
);

CREATE TABLE IF NOT EXISTS clinical_alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL REFERENCES patients(id),
    encounter_id    INTEGER REFERENCES encounters(id),
    alert_type      TEXT NOT NULL
                    CHECK (alert_type IN ('drug_interaction','allergy','critical_lab','fall_risk')),
    severity        TEXT NOT NULL,
    message         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active','acknowledged','resolved')),
    created_at      TEXT NOT NULL,
    acknowledged_by INTEGER REFERENCES providers(id),
    acknowledged_at TEXT
);

CREATE TABLE IF NOT EXISTS quality_measures (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    measure_name        TEXT NOT NULL,
    measure_code        TEXT NOT NULL,
    numerator           INTEGER NOT NULL,
    denominator         INTEGER NOT NULL,
    rate                REAL NOT NULL,
    reporting_period    TEXT NOT NULL,
    department_id       INTEGER REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS hl7_messages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    message_type        TEXT NOT NULL
                        CHECK (message_type IN ('ADT','ORM','ORU','DFT')),
    direction           TEXT NOT NULL
                        CHECK (direction IN ('inbound','outbound')),
    sending_facility    TEXT NOT NULL,
    receiving_facility  TEXT NOT NULL,
    message_content     TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'received'
                        CHECK (status IN ('received','processed','error')),
    created_at          TEXT NOT NULL,
    processed_at        TEXT,
    error_message       TEXT
);

CREATE TABLE IF NOT EXISTS system_status (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    system_name     TEXT NOT NULL,
    status          TEXT NOT NULL
                    CHECK (status IN ('operational','degraded','down')),
    last_check      TEXT NOT NULL,
    response_time_ms INTEGER,
    notes           TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients(mrn);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id);
CREATE INDEX IF NOT EXISTS idx_encounters_dates ON encounters(admit_date, discharge_date);
CREATE INDEX IF NOT EXISTS idx_diagnoses_encounter ON diagnoses(encounter_id);
CREATE INDEX IF NOT EXISTS idx_diagnoses_icd10 ON diagnoses(icd10_code);
CREATE INDEX IF NOT EXISTS idx_lab_results_encounter ON lab_results(encounter_id);
CREATE INDEX IF NOT EXISTS idx_lab_results_patient ON lab_results(patient_id);
CREATE INDEX IF NOT EXISTS idx_medication_orders_encounter ON medication_orders(encounter_id);
CREATE INDEX IF NOT EXISTS idx_vital_signs_encounter ON vital_signs(encounter_id);
CREATE INDEX IF NOT EXISTS idx_orders_encounter ON orders(encounter_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_clinical_alerts_patient ON clinical_alerts(patient_id);
CREATE INDEX IF NOT EXISTS idx_beds_department ON beds(department_id);
CREATE INDEX IF NOT EXISTS idx_providers_npi ON providers(npi);
"""


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _random_dt(start, end):
    """Return a random datetime between *start* and *end*."""
    delta = end - start
    seconds = random.randint(0, max(0, int(delta.total_seconds())))
    return start + timedelta(seconds=seconds)


def _fmt(dt):
    """Format a datetime as ISO-8601 string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _fmt_date(dt):
    """Format a datetime as a date-only string."""
    return dt.strftime("%Y-%m-%d")


def _generate_npi():
    """Generate a realistic-looking 10-digit NPI."""
    return "".join([str(random.randint(0, 9)) for _ in range(10)])


def _generate_mrn(idx):
    """Generate an MRN like MRN-000001."""
    return f"MRN-{idx:06d}"


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def init_db(db_path="hinfo.db"):
    """Create the SQLite database with the full EHR schema.

    Drops existing tables first for a clean start, then creates all 20
    tables with foreign-key constraints and indexes.
    """
    conn = sqlite3.connect(db_path)
    # Drop tables in reverse dependency order for a clean reinitialisation
    conn.executescript("""
        DROP TABLE IF EXISTS system_status;
        DROP TABLE IF EXISTS hl7_messages;
        DROP TABLE IF EXISTS quality_measures;
        DROP TABLE IF EXISTS clinical_alerts;
        DROP TABLE IF EXISTS audit_log;
        DROP TABLE IF EXISTS staff_schedule;
        DROP TABLE IF EXISTS beds;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS vital_signs;
        DROP TABLE IF EXISTS lab_results;
        DROP TABLE IF EXISTS medication_orders;
        DROP TABLE IF EXISTS medications;
        DROP TABLE IF EXISTS procedures;
        DROP TABLE IF EXISTS diagnoses;
        DROP TABLE IF EXISTS encounters;
        DROP TABLE IF EXISTS patients;
        DROP TABLE IF EXISTS providers;
        DROP TABLE IF EXISTS insurance_plans;
        DROP TABLE IF EXISTS departments;
    """)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    print(f"[init_db] Schema created at {db_path}")


# ---------------------------------------------------------------------------
# seed_data
# ---------------------------------------------------------------------------

def seed_data(db_path="hinfo.db"):
    """Populate the database with realistic fake healthcare data.

    Generates:
      - 500 patients, 50 providers, 15 departments, 10 insurance plans
      - 1200 encounters, 2500 diagnoses, 800 procedures, 30 medications
      - 1500 medication orders, 3000 lab results, 4000 vital signs
      - 300 allergies, 1000 orders, 200 beds, 500 staff schedules
      - 500 audit log entries, 150 clinical alerts, 20 quality measures
      - 100 HL7 messages, 8 system-status rows
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    cur = conn.cursor()

    now = datetime.now()
    ninety_days_ago = now - timedelta(days=90)

    # ==================================================================
    # Insurance Plans (10)
    # ==================================================================
    print("[seed] Inserting insurance plans ...")
    for plan_name, plan_type, payer_name, group_number in INSURANCE_PLANS:
        cur.execute(
            "INSERT INTO insurance_plans (plan_name, plan_type, payer_name, group_number) "
            "VALUES (?,?,?,?)",
            (plan_name, plan_type, payer_name, group_number),
        )
    conn.commit()
    insurance_ids = list(range(1, len(INSURANCE_PLANS) + 1))

    # ==================================================================
    # Departments (15)
    # ==================================================================
    print("[seed] Inserting departments ...")
    for name, code, floor, building, phone, bed_count in DEPARTMENTS:
        manager = fake.name()
        cur.execute(
            "INSERT INTO departments (name, code, floor, building, phone, manager_name, bed_count) "
            "VALUES (?,?,?,?,?,?,?)",
            (name, code, floor, building, phone, manager, bed_count),
        )
    conn.commit()
    dept_ids = list(range(1, len(DEPARTMENTS) + 1))

    # Build a map of departments that have beds
    dept_bed_map = {}
    for idx, (_, _, _, _, _, bed_count) in enumerate(DEPARTMENTS, 1):
        if bed_count:
            dept_bed_map[idx] = bed_count

    # ==================================================================
    # Providers (50)
    # ==================================================================
    print("[seed] Inserting providers ...")
    provider_ids = []
    used_npis = set()
    for _ in range(50):
        npi = _generate_npi()
        while npi in used_npis:
            npi = _generate_npi()
        used_npis.add(npi)
        first = fake.first_name()
        last = fake.last_name()
        cred = random.choice(CREDENTIALS)
        spec = random.choice(SPECIALTIES)
        dept = random.choice(dept_ids)
        email = f"{first.lower()}.{last.lower()}@hospital.org"
        phone = fake.phone_number()
        active = 1 if random.random() < 0.95 else 0
        cur.execute(
            "INSERT INTO providers (npi, first_name, last_name, credentials, specialty, "
            "department_id, email, phone, active) VALUES (?,?,?,?,?,?,?,?,?)",
            (npi, first, last, cred, spec, dept, email, phone, active),
        )
        provider_ids.append(cur.lastrowid)
    conn.commit()

    # ==================================================================
    # Patients (500)
    # ==================================================================
    print("[seed] Inserting patients ...")
    genders = ["Male", "Female", "Other", "Unknown"]
    gender_weights = [0.48, 0.48, 0.02, 0.02]
    races = [
        "White", "Black or African American", "Asian",
        "American Indian or Alaska Native",
        "Native Hawaiian or Other Pacific Islander",
        "Two or More Races", "Unknown",
    ]
    ethnicities = ["Hispanic or Latino", "Not Hispanic or Latino", "Unknown"]
    statuses = ["active", "inactive", "deceased"]
    status_weights = [0.85, 0.10, 0.05]

    patient_ids = []
    for i in range(1, 501):
        mrn = _generate_mrn(i)
        first = fake.first_name()
        last = fake.last_name()
        dob = fake.date_of_birth(minimum_age=1, maximum_age=95)
        gender = random.choices(genders, gender_weights)[0]
        race = random.choice(races)
        ethnicity = random.choice(ethnicities)
        ssn4 = f"{random.randint(0, 9999):04d}"
        address = fake.street_address()
        city = fake.city()
        state = fake.state_abbr()
        zipcode = fake.zipcode()
        phone = fake.phone_number()
        email = f"{first.lower()}.{last.lower()}{random.randint(1, 999)}@{fake.free_email_domain()}"
        ins_id = random.choice(insurance_ids)
        pcp_id = random.choice(provider_ids)
        created = _fmt(_random_dt(now - timedelta(days=365 * 3), now))
        status = random.choices(statuses, status_weights)[0]
        cur.execute(
            "INSERT INTO patients "
            "(mrn, first_name, last_name, dob, gender, race, ethnicity, "
            " ssn_last4, address, city, state, zip, phone, email, "
            " insurance_id, primary_care_provider_id, created_at, status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (mrn, first, last, str(dob), gender, race, ethnicity,
             ssn4, address, city, state, zipcode, phone, email,
             ins_id, pcp_id, created, status),
        )
        patient_ids.append(cur.lastrowid)
    conn.commit()

    # ==================================================================
    # Encounters (1200)
    # ==================================================================
    print("[seed] Inserting encounters ...")
    encounter_types = ["inpatient", "outpatient", "emergency", "observation"]
    enc_weights = [0.30, 0.35, 0.25, 0.10]
    admission_sources = [
        "Emergency Room", "Physician Referral", "Transfer",
        "Walk-in", "Direct Admit", "Clinic",
    ]
    discharge_dispositions = [
        "Home", "Home with Home Health", "Skilled Nursing Facility",
        "Rehabilitation Facility", "Transfer to Another Hospital",
        "Against Medical Advice", "Expired", "Hospice",
    ]
    encounter_ids = []
    # Parallel list for fast lookups during child-row generation
    encounter_data = []  # (id, patient_id, provider_id, dept_id, admit_dt, discharge_dt, status, enc_type)

    for _ in range(1200):
        pat_id = random.choice(patient_ids)
        prov_id = random.choice(provider_ids)
        dept_id = random.choice(dept_ids)
        enc_type = random.choices(encounter_types, enc_weights)[0]
        admit_dt = _random_dt(ninety_days_ago, now - timedelta(hours=2))

        if enc_type == "outpatient":
            discharge_dt = admit_dt + timedelta(hours=random.randint(1, 4))
            status = "discharged"
        elif enc_type == "emergency":
            hours = random.randint(2, 24)
            discharge_dt = admit_dt + timedelta(hours=hours)
            status = random.choices(["discharged", "active"], [0.85, 0.15])[0]
            if status == "active":
                discharge_dt = None
        elif enc_type == "observation":
            hours = random.randint(6, 48)
            discharge_dt = admit_dt + timedelta(hours=hours)
            status = random.choices(["discharged", "active"], [0.80, 0.20])[0]
            if status == "active":
                discharge_dt = None
        else:  # inpatient
            days = random.randint(1, 14)
            discharge_dt = admit_dt + timedelta(days=days, hours=random.randint(0, 12))
            status = random.choices(
                ["discharged", "active", "transferred"], [0.75, 0.15, 0.10]
            )[0]
            if status == "active":
                discharge_dt = None

        cc = random.choice(CHIEF_COMPLAINTS)
        adm_src = random.choice(admission_sources)
        disp = random.choice(discharge_dispositions) if discharge_dt else None

        cur.execute(
            "INSERT INTO encounters "
            "(patient_id, provider_id, department_id, encounter_type, "
            " admit_date, discharge_date, status, chief_complaint, "
            " admission_source, discharge_disposition) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pat_id, prov_id, dept_id, enc_type,
             _fmt(admit_dt),
             _fmt(discharge_dt) if discharge_dt else None,
             status, cc, adm_src, disp),
        )
        eid = cur.lastrowid
        encounter_ids.append(eid)
        encounter_data.append(
            (eid, pat_id, prov_id, dept_id, admit_dt, discharge_dt, status, enc_type)
        )
    conn.commit()

    # Helper: get a safe end datetime for an encounter (discharge or now)
    def _enc_end(enc):
        return enc[5] if enc[5] else now

    # ==================================================================
    # Diagnoses (2500)
    # ==================================================================
    print("[seed] Inserting diagnoses ...")
    dx_types = ["primary", "secondary", "admitting"]
    dx_type_weights = [0.30, 0.55, 0.15]
    for _ in range(2500):
        enc = random.choice(encounter_data)
        eid, pat_id = enc[0], enc[1]
        code, desc = random.choice(ICD10_CODES)
        dx_type = random.choices(dx_types, dx_type_weights)[0]
        diag_prov = random.choice(provider_ids)
        dx_date = _random_dt(enc[4], _enc_end(enc))
        cur.execute(
            "INSERT INTO diagnoses "
            "(encounter_id, patient_id, icd10_code, description, "
            " diagnosis_type, diagnosed_by_provider_id, diagnosis_date) "
            "VALUES (?,?,?,?,?,?,?)",
            (eid, pat_id, code, desc, dx_type, diag_prov, _fmt(dx_date)),
        )
    conn.commit()

    # ==================================================================
    # Procedures (800)
    # ==================================================================
    print("[seed] Inserting procedures ...")
    proc_statuses = ["completed", "scheduled", "in_progress", "cancelled"]
    proc_status_weights = [0.75, 0.10, 0.10, 0.05]
    for _ in range(800):
        enc = random.choice(encounter_data)
        eid, pat_id = enc[0], enc[1]
        code, desc = random.choice(CPT_CODES)
        perf_prov = random.choice(provider_ids)
        proc_date = _random_dt(enc[4], _enc_end(enc))
        pstatus = random.choices(proc_statuses, proc_status_weights)[0]
        cur.execute(
            "INSERT INTO procedures "
            "(encounter_id, patient_id, cpt_code, description, "
            " performing_provider_id, procedure_date, status) "
            "VALUES (?,?,?,?,?,?,?)",
            (eid, pat_id, code, desc, perf_prov, _fmt(proc_date), pstatus),
        )
    conn.commit()

    # ==================================================================
    # Medications (30)
    # ==================================================================
    print("[seed] Inserting medications ...")
    med_ids = []
    for name, generic, drug_class, route, form in MEDICATIONS:
        cur.execute(
            "INSERT INTO medications (name, generic_name, drug_class, route, form) "
            "VALUES (?,?,?,?,?)",
            (name, generic, drug_class, route, form),
        )
        med_ids.append(cur.lastrowid)
    conn.commit()

    # ==================================================================
    # Medication Orders (1500)
    # ==================================================================
    print("[seed] Inserting medication orders ...")
    frequencies = [
        "once", "BID", "TID", "QID", "Q4H", "Q6H",
        "Q8H", "Q12H", "daily", "PRN", "continuous",
    ]
    dose_units = ["mg", "mcg", "mL", "units", "mEq", "g"]
    med_order_statuses = ["active", "completed", "discontinued", "held"]
    med_order_weights = [0.35, 0.45, 0.15, 0.05]

    for _ in range(1500):
        enc = random.choice(encounter_data)
        eid, pat_id = enc[0], enc[1]
        med_idx = random.randint(0, len(MEDICATIONS) - 1)
        med_id = med_ids[med_idx]
        med_info = MEDICATIONS[med_idx]
        ord_prov = random.choice(provider_ids)

        # Realistic dose based on route
        if med_info[3] == "intravenous":
            dose = str(random.choice([250, 500, 1000, 100, 50, 25, 1, 2, 4]))
        elif med_info[3] == "oral":
            dose = str(random.choice([5, 10, 20, 25, 40, 50, 81, 100, 200, 325, 500, 650, 1000]))
        elif med_info[3] == "subcutaneous":
            dose = str(random.choice([10, 20, 30, 40, 50, 60, 80, 100]))
        else:
            dose = str(random.choice([2.5, 5, 10]))

        unit = random.choice(dose_units[:3])  # mg, mcg, mL are most common
        if "Insulin" in med_info[0]:
            unit = "units"
        elif "Potassium" in med_info[0]:
            unit = "mEq"

        freq = random.choice(frequencies)
        route = med_info[3]

        start = _random_dt(enc[4], _enc_end(enc))
        mo_status = random.choices(med_order_statuses, med_order_weights)[0]
        if mo_status in ("completed", "discontinued"):
            end = start + timedelta(days=random.randint(1, 14))
        else:
            end = None

        cur.execute(
            "INSERT INTO medication_orders "
            "(encounter_id, patient_id, medication_id, ordering_provider_id, "
            " dose, unit, frequency, route, start_date, end_date, status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (eid, pat_id, med_id, ord_prov,
             dose, unit, freq, route,
             _fmt(start), _fmt(end) if end else None, mo_status),
        )
    conn.commit()

    # ==================================================================
    # Lab Results (3000)
    # ==================================================================
    print("[seed] Inserting lab results ...")
    lab_statuses = ["final", "preliminary", "corrected"]
    lab_status_weights = [0.85, 0.10, 0.05]

    for _ in range(3000):
        enc = random.choice(encounter_data)
        eid, pat_id = enc[0], enc[1]
        test = random.choice(LAB_TESTS)
        test_name, test_code, unit, ref_low, ref_high, value_fn = test
        value = value_fn()
        # Ensure non-negative for most labs
        if value < 0:
            value = abs(value)
        # Determine abnormal flag
        if ref_low is not None and ref_high is not None:
            if value < ref_low:
                flag = "L"
            elif value > ref_high:
                flag = "H"
            else:
                flag = "N"
        else:
            flag = "N"
        # Occasionally mark critical
        if flag in ("L", "H") and random.random() < 0.08:
            flag = "C"

        ord_prov = random.choice(provider_ids)
        result_date = _random_dt(enc[4], _enc_end(enc))
        lstatus = random.choices(lab_statuses, lab_status_weights)[0]
        cur.execute(
            "INSERT INTO lab_results "
            "(encounter_id, patient_id, ordering_provider_id, "
            " test_name, test_code, value, unit, "
            " reference_range_low, reference_range_high, "
            " abnormal_flag, result_date, status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (eid, pat_id, ord_prov,
             test_name, test_code, str(value), unit,
             ref_low, ref_high, flag,
             _fmt(result_date), lstatus),
        )
    conn.commit()

    # ==================================================================
    # Vital Signs (4000)
    # ==================================================================
    print("[seed] Inserting vital signs ...")
    for _ in range(4000):
        enc = random.choice(encounter_data)
        eid, pat_id = enc[0], enc[1]
        rec_prov = random.choice(provider_ids)
        recorded_at = _random_dt(enc[4], _enc_end(enc))

        temp = round(random.gauss(98.6, 0.8), 1)
        hr = max(40, min(180, int(random.gauss(80, 15))))
        sbp = max(70, min(220, int(random.gauss(125, 20))))
        dbp = max(40, min(130, int(random.gauss(75, 12))))
        rr = max(8, min(40, int(random.gauss(16, 4))))
        spo2 = round(min(100.0, max(80.0, random.gauss(97.0, 2.0))), 1)
        pain = random.choices(
            range(11),
            weights=[30, 10, 8, 8, 7, 7, 6, 6, 6, 6, 6],
        )[0]

        cur.execute(
            "INSERT INTO vital_signs "
            "(encounter_id, patient_id, recorded_by_provider_id, "
            " temperature, heart_rate, blood_pressure_systolic, "
            " blood_pressure_diastolic, respiratory_rate, spo2, "
            " pain_scale, recorded_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (eid, pat_id, rec_prov,
             temp, hr, sbp, dbp, rr, spo2, pain,
             _fmt(recorded_at)),
        )
    conn.commit()

    # ==================================================================
    # Allergies (300)
    # ==================================================================
    print("[seed] Inserting allergies ...")
    severities = ["mild", "moderate", "severe"]
    sev_weights = [0.40, 0.40, 0.20]
    for _ in range(300):
        pat_id = random.choice(patient_ids)
        allergen, a_type = random.choice(ALLERGENS)
        reaction = random.choice(ALLERGY_REACTIONS)
        severity = random.choices(severities, sev_weights)[0]
        doc_date = _fmt_date(_random_dt(now - timedelta(days=365 * 5), now))
        cur.execute(
            "INSERT INTO allergies "
            "(patient_id, allergen, reaction, severity, allergy_type, documented_date) "
            "VALUES (?,?,?,?,?,?)",
            (pat_id, allergen, reaction, severity, a_type, doc_date),
        )
    conn.commit()

    # ==================================================================
    # Orders (1000)
    # ==================================================================
    print("[seed] Inserting orders ...")
    order_types = ["lab", "imaging", "consult", "diet", "activity"]
    order_type_weights = [0.35, 0.25, 0.15, 0.15, 0.10]
    priorities = ["routine", "urgent", "stat"]
    priority_weights = [0.60, 0.25, 0.15]
    order_statuses = ["ordered", "in_progress", "completed", "cancelled"]
    order_status_weights = [0.15, 0.10, 0.65, 0.10]

    order_text_map = {
        "lab": [
            "CBC with Differential", "BMP", "CMP", "Lipid Panel",
            "Coagulation Panel (PT/INR/PTT)", "Urinalysis",
            "Troponin I", "BNP", "HbA1c", "TSH",
            "Blood Culture x2", "Procalcitonin", "Lactate Level",
            "Type and Screen", "Magnesium Level",
        ],
        "imaging": [
            "Chest X-ray PA and Lateral", "CT Abdomen Pelvis with Contrast",
            "MRI Brain with and without Contrast", "CT Head without Contrast",
            "Portable Chest X-ray", "Abdominal Ultrasound",
            "CT Angiogram Chest", "MRI Lumbar Spine without Contrast",
            "Bilateral Lower Extremity Doppler Ultrasound",
            "Echocardiogram Transthoracic",
        ],
        "consult": [
            "Cardiology Consult", "Pulmonology Consult", "GI Consult",
            "Nephrology Consult", "Infectious Disease Consult",
            "Surgery Consult", "Neurology Consult", "Psychiatry Consult",
            "Palliative Care Consult", "Wound Care Consult",
        ],
        "diet": [
            "Regular Diet", "Cardiac Diet", "Diabetic Diet", "NPO",
            "Clear Liquids", "Renal Diet", "Low Sodium Diet",
            "Mechanical Soft Diet",
        ],
        "activity": [
            "Bedrest", "Up Ad Lib", "Ambulate TID", "Fall Precautions",
            "Physical Therapy Evaluation", "OT Evaluation",
            "Wheelchair Only", "Weight Bearing as Tolerated",
        ],
    }

    for _ in range(1000):
        enc = random.choice(encounter_data)
        eid, pat_id = enc[0], enc[1]
        otype = random.choices(order_types, order_type_weights)[0]
        otext = random.choice(order_text_map[otype])
        priority = random.choices(priorities, priority_weights)[0]
        ostatus = random.choices(order_statuses, order_status_weights)[0]
        ordered_at = _random_dt(enc[4], _enc_end(enc))
        completed_at = None
        if ostatus == "completed":
            completed_at = ordered_at + timedelta(hours=random.randint(1, 48))
        ord_prov = random.choice(provider_ids)
        cur.execute(
            "INSERT INTO orders "
            "(encounter_id, patient_id, ordering_provider_id, "
            " order_type, order_text, priority, status, "
            " ordered_at, completed_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (eid, pat_id, ord_prov,
             otype, otext, priority, ostatus,
             _fmt(ordered_at), _fmt(completed_at) if completed_at else None),
        )
    conn.commit()

    # ==================================================================
    # Beds (200)
    # ==================================================================
    print("[seed] Inserting beds ...")
    beds_per_dept = dict(dept_bed_map)  # copy
    total_planned = sum(beds_per_dept.values())
    if total_planned < 200:
        extra = 200 - total_planned
        expandable = [3, 1, 2, 6, 4, 5]  # MEDSURG, ED, ICU, CARD, PEDS, OBGYN
        i = 0
        while extra > 0:
            d = expandable[i % len(expandable)]
            beds_per_dept[d] = beds_per_dept.get(d, 0) + 1
            extra -= 1
            i += 1

    # Pool of patients in active encounters for bed assignment
    active_patient_pool = [e[1] for e in encounter_data if e[6] == "active"]
    random.shuffle(active_patient_pool)

    for dept_id, num_beds in sorted(beds_per_dept.items()):
        for b in range(1, num_beds + 1):
            room = f"{dept_id * 100 + (b - 1) // 2 + 1}"
            bed_letter = "A" if b % 2 == 1 else "B"
            bed_num = f"{room}-{bed_letter}"

            r = random.random()
            if r < 0.25 and active_patient_pool:
                bstatus = "occupied"
                cpat = active_patient_pool.pop()
            elif r < 0.30:
                bstatus = "cleaning"
                cpat = None
            elif r < 0.33:
                bstatus = "maintenance"
                cpat = None
            else:
                bstatus = "available"
                cpat = None

            cur.execute(
                "INSERT INTO beds (department_id, bed_number, room_number, status, current_patient_id) "
                "VALUES (?,?,?,?,?)",
                (dept_id, bed_num, room, bstatus, cpat),
            )
    conn.commit()

    # ==================================================================
    # Staff Schedule (~500 entries over last 7 days)
    # ==================================================================
    print("[seed] Inserting staff schedules ...")
    roles = ["Attending", "Resident", "Nurse", "Charge Nurse", "CNA", "RT", "Pharmacist"]
    shift_templates = [
        ("07:00", "19:00"),
        ("19:00", "07:00"),
        ("07:00", "15:00"),
        ("15:00", "23:00"),
        ("23:00", "07:00"),
    ]
    for _ in range(500):
        prov = random.choice(provider_ids)
        dept = random.choice(dept_ids)
        shift_date = _fmt_date(now - timedelta(days=random.randint(0, 7)))
        shift_start, shift_end = random.choice(shift_templates)
        role = random.choice(roles)
        cur.execute(
            "INSERT INTO staff_schedule "
            "(provider_id, shift_date, shift_start, shift_end, department_id, role) "
            "VALUES (?,?,?,?,?,?)",
            (prov, shift_date, shift_start, shift_end, dept, role),
        )
    conn.commit()

    # ==================================================================
    # Audit Log (500)
    # ==================================================================
    print("[seed] Inserting audit log entries ...")
    actions = [
        "CREATE", "READ", "UPDATE", "DELETE",
        "LOGIN", "LOGOUT", "PRINT", "EXPORT", "VIEW",
    ]
    table_names = [
        "patients", "encounters", "medication_orders", "lab_results",
        "vital_signs", "orders", "diagnoses", "procedures", "providers",
    ]
    for _ in range(500):
        user_id = random.choice(provider_ids)
        action = random.choice(actions)
        table = random.choice(table_names)
        record_id = random.randint(1, 1000)
        old_val = None
        new_val = None
        if action == "UPDATE":
            old_val = f'{{"status": "{random.choice(["active", "completed"])}"}}'
            new_val = f'{{"status": "{random.choice(["discharged", "discontinued"])}"}}'
        ts = _fmt(_random_dt(ninety_days_ago, now))
        ip = fake.ipv4()
        cur.execute(
            "INSERT INTO audit_log "
            "(user_id, action, table_name, record_id, old_value, new_value, timestamp, ip_address) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (user_id, action, table, record_id, old_val, new_val, ts, ip),
        )
    conn.commit()

    # ==================================================================
    # Clinical Alerts (150)
    # ==================================================================
    print("[seed] Inserting clinical alerts ...")
    alert_types = ["drug_interaction", "allergy", "critical_lab", "fall_risk"]
    alert_type_weights = [0.25, 0.25, 0.30, 0.20]
    alert_severities = ["low", "medium", "high", "critical"]
    alert_sev_weights = [0.20, 0.35, 0.30, 0.15]
    alert_messages = {
        "drug_interaction": [
            "Potential interaction between Warfarin and Aspirin",
            "Concomitant use of ACE Inhibitor and Potassium supplement may increase risk of hyperkalemia",
            "Duplicate therapy alert: Two beta-blockers ordered",
            "NSAID may reduce effectiveness of antihypertensive therapy",
            "Serotonin syndrome risk: concurrent SSRI and Tramadol",
        ],
        "allergy": [
            "Patient has documented allergy to Penicillin - Cephalosporin ordered (cross-reactivity risk)",
            "Patient allergic to Sulfa drugs - Trimethoprim-Sulfamethoxazole ordered",
            "Contrast dye allergy - CT with contrast ordered, pre-medication required",
            "NSAID allergy documented - Ibuprofen ordered",
            "Latex allergy alert for upcoming procedure",
        ],
        "critical_lab": [
            "CRITICAL: Potassium 6.2 mEq/L (ref: 3.5-5.0)",
            "CRITICAL: Troponin I 2.45 ng/mL (ref: <0.04)",
            "CRITICAL: Hemoglobin 6.1 g/dL (ref: 12.0-17.5)",
            "CRITICAL: Glucose 42 mg/dL (ref: 70-100)",
            "CRITICAL: INR 5.8 (ref: 0.8-1.1)",
            "CRITICAL: Sodium 118 mEq/L (ref: 136-145)",
            "CRITICAL: Platelet Count 22 x10^3/uL (ref: 150-400)",
        ],
        "fall_risk": [
            "High fall risk: Morse Fall Scale score 55",
            "Fall risk: Patient on multiple sedating medications",
            "Fall risk reassessment due: previous fall during admission",
            "Elevated fall risk: age >65, gait instability, psychoactive medications",
        ],
    }
    alert_statuses = ["active", "acknowledged", "resolved"]
    alert_status_weights = [0.30, 0.35, 0.35]

    for _ in range(150):
        enc = random.choice(encounter_data)
        eid, pat_id = enc[0], enc[1]
        atype = random.choices(alert_types, alert_type_weights)[0]
        sev = random.choices(alert_severities, alert_sev_weights)[0]
        msg = random.choice(alert_messages[atype])
        astatus = random.choices(alert_statuses, alert_status_weights)[0]
        created = _random_dt(enc[4], _enc_end(enc))
        ack_by = None
        ack_at = None
        if astatus in ("acknowledged", "resolved"):
            ack_by = random.choice(provider_ids)
            ack_at = _fmt(created + timedelta(minutes=random.randint(1, 120)))
        cur.execute(
            "INSERT INTO clinical_alerts "
            "(patient_id, encounter_id, alert_type, severity, message, "
            " status, created_at, acknowledged_by, acknowledged_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (pat_id, eid, atype, sev, msg, astatus,
             _fmt(created), ack_by, ack_at),
        )
    conn.commit()

    # ==================================================================
    # Quality Measures (20)
    # ==================================================================
    print("[seed] Inserting quality measures ...")
    reporting_periods = ["2025-Q3", "2025-Q4", "2026-Q1"]
    for measure_name, measure_code, _ in QUALITY_MEASURES:
        denom = random.randint(50, 500)
        rate = round(random.uniform(0.50, 0.99), 4)
        numer = int(denom * rate)
        period = random.choice(reporting_periods)
        dept = random.choice(dept_ids)
        cur.execute(
            "INSERT INTO quality_measures "
            "(measure_name, measure_code, numerator, denominator, rate, "
            " reporting_period, department_id) "
            "VALUES (?,?,?,?,?,?,?)",
            (measure_name, measure_code, numer, denom, rate, period, dept),
        )
    conn.commit()

    # ==================================================================
    # HL7 Messages (100)
    # ==================================================================
    print("[seed] Inserting HL7 messages ...")
    hl7_types = ["ADT", "ORM", "ORU", "DFT"]
    hl7_type_weights = [0.35, 0.25, 0.30, 0.10]
    directions = ["inbound", "outbound"]
    facilities = [
        "MAIN_HOSP", "LAB_SYSTEM", "RAD_SYSTEM", "BILLING",
        "PHARMACY", "EXTERNAL_LAB", "HIE_NETWORK", "PACS",
    ]
    hl7_statuses = ["received", "processed", "error"]
    hl7_status_weights = [0.10, 0.82, 0.08]

    for _ in range(100):
        mtype = random.choices(hl7_types, hl7_type_weights)[0]
        direction = random.choice(directions)
        sending = random.choice(facilities)
        receiving = random.choice([f for f in facilities if f != sending])
        ts = _random_dt(ninety_days_ago, now)
        msg_ctrl_id = "".join(random.choices(string.digits, k=10))
        content = (
            f"MSH|^~\\&|{sending}|{sending}|{receiving}|{receiving}|"
            f"{ts.strftime('%Y%m%d%H%M%S')}||{mtype}^A01|{msg_ctrl_id}|P|2.5.1\r"
            f"EVN|A01|{ts.strftime('%Y%m%d%H%M%S')}\r"
            f"PID|1||{random.randint(100000, 999999)}||DOE^JOHN||19800101|M\r"
        )
        hstatus = random.choices(hl7_statuses, hl7_status_weights)[0]
        processed_at = None
        error_msg = None
        if hstatus == "processed":
            processed_at = _fmt(ts + timedelta(seconds=random.randint(1, 30)))
        elif hstatus == "error":
            processed_at = _fmt(ts + timedelta(seconds=random.randint(1, 30)))
            error_msg = random.choice([
                "Invalid patient identifier",
                "Duplicate message control ID",
                "Required field PID-3 missing",
                "Unknown sending facility",
                "Message validation failed: segment order",
                "Acknowledgment timeout",
            ])
        cur.execute(
            "INSERT INTO hl7_messages "
            "(message_type, direction, sending_facility, receiving_facility, "
            " message_content, status, created_at, processed_at, error_message) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (mtype, direction, sending, receiving, content,
             hstatus, _fmt(ts), processed_at, error_msg),
        )
    conn.commit()

    # ==================================================================
    # System Status (8)
    # ==================================================================
    print("[seed] Inserting system status ...")
    for sys_name, sys_status in SYSTEMS:
        # Occasionally degrade a system
        if random.random() < 0.1:
            sys_status = "degraded"
        resp_time = (
            random.randint(5, 250)
            if sys_status == "operational"
            else random.randint(500, 5000)
        )
        notes = None
        if sys_status == "degraded":
            notes = random.choice([
                "Elevated response times observed",
                "Intermittent connectivity issues",
                "Scheduled maintenance window approaching",
            ])
        cur.execute(
            "INSERT INTO system_status "
            "(system_name, status, last_check, response_time_ms, notes) "
            "VALUES (?,?,?,?,?)",
            (sys_name, sys_status, _fmt(now), resp_time, notes),
        )
    conn.commit()
    conn.close()
    print(f"[seed] Seeding complete for {db_path}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "hinfo.db"
    init_db(db_file)
    seed_data(db_file)
    print("Database created and seeded successfully!")

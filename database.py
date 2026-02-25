"""
database.py - SQLite database initialization and seeding for the
Health Informatics Learning Platform.

Simulates a hospital EHR system with 16 comprehensive tables and
realistic fake data generated via the Faker library (seed=42).

Public API
----------
    init_db(db_path)  -- create schema + seed data, return nothing
    get_db(db_path)   -- return an sqlite3.Connection
"""

import sqlite3
import os
import random
import math
from datetime import datetime, timedelta

try:
    from faker import Faker
    fake = Faker()
    Faker.seed(42)
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False

random.seed(42)

DEFAULT_DB_PATH = "hinfo.db"


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

ICD10_CODES = [
    ("E11.9",  "Type 2 diabetes mellitus without complications"),
    ("I10",    "Essential (primary) hypertension"),
    ("J18.9",  "Pneumonia, unspecified organism"),
    ("I25.10", "Atherosclerotic heart disease of native coronary artery without angina pectoris"),
    ("E78.5",  "Hyperlipidemia, unspecified"),
    ("N17.9",  "Acute kidney failure, unspecified"),
    ("J44.1",  "Chronic obstructive pulmonary disease with acute exacerbation"),
    ("I50.9",  "Heart failure, unspecified"),
    ("K21.0",  "Gastro-esophageal reflux disease with esophagitis"),
    ("M54.5",  "Low back pain"),
    ("F32.9",  "Major depressive disorder, single episode, unspecified"),
    ("J06.9",  "Acute upper respiratory infection, unspecified"),
    ("N39.0",  "Urinary tract infection, site not specified"),
    ("I63.9",  "Cerebral infarction, unspecified"),
    ("K80.20", "Calculus of gallbladder without cholecystitis"),
    ("E87.1",  "Hypo-osmolality and hyponatremia"),
    ("D64.9",  "Anemia, unspecified"),
    ("G47.33", "Obstructive sleep apnea"),
    ("I48.91", "Unspecified atrial fibrillation"),
    ("J96.01", "Acute respiratory failure with hypoxia"),
    ("I21.9",  "Acute myocardial infarction, unspecified"),
    ("E11.65", "Type 2 diabetes mellitus with hyperglycemia"),
    ("J45.20", "Mild intermittent asthma, uncomplicated"),
    ("K59.00", "Constipation, unspecified"),
    ("R07.9",  "Chest pain, unspecified"),
    ("G43.909","Migraine, unspecified, not intractable, without status migrainosus"),
    ("M79.3",  "Panniculitis, unspecified"),
    ("I26.99", "Other pulmonary embolism without acute cor pulmonale"),
    ("A41.9",  "Sepsis, unspecified organism"),
    ("K92.1",  "Melena"),
    ("L03.311","Cellulitis of abdominal wall"),
    ("R10.9",  "Unspecified abdominal pain"),
    ("E87.6",  "Hypokalemia"),
    ("J20.9",  "Acute bronchitis, unspecified"),
    ("N18.3",  "Chronic kidney disease, stage 3"),
    ("G40.909","Epilepsy, unspecified, not intractable, without status epilepticus"),
    ("R50.9",  "Fever, unspecified"),
    ("M17.11", "Primary osteoarthritis, right knee"),
    ("I25.5",  "Ischemic cardiomyopathy"),
    ("J15.9",  "Unspecified bacterial pneumonia"),
    ("E03.9",  "Hypothyroidism, unspecified"),
    ("G20",    "Parkinson disease"),
    ("I70.0",  "Atherosclerosis of aorta"),
    ("K74.60", "Unspecified cirrhosis of liver"),
    ("J84.10", "Pulmonary fibrosis, unspecified"),
    ("C34.90", "Malignant neoplasm of unspecified part of unspecified bronchus or lung"),
    ("C50.919","Malignant neoplasm of unspecified site of unspecified female breast"),
    ("C61",    "Malignant neoplasm of prostate"),
    ("D50.9",  "Iron deficiency anemia, unspecified"),
    ("F41.1",  "Generalized anxiety disorder"),
    ("F10.20", "Alcohol dependence, uncomplicated"),
    ("F17.210","Nicotine dependence, cigarettes, uncomplicated"),
    ("B34.9",  "Viral infection, unspecified"),
    ("R11.2",  "Nausea with vomiting, unspecified"),
    ("R00.0",  "Tachycardia, unspecified"),
    ("S72.001A","Fracture of unspecified part of neck of right femur, initial encounter"),
    ("S82.001A","Unspecified fracture of right patella, initial encounter"),
    ("T81.4XXA","Infection following a procedure, initial encounter"),
    ("Z87.891","Personal history of nicotine dependence"),
    ("Z96.641","Presence of right artificial hip joint"),
    ("J69.0",  "Pneumonitis due to inhalation of food and vomit"),
    ("R06.02", "Shortness of breath"),
    ("R55",    "Syncope and collapse"),
    ("K35.80", "Unspecified acute appendicitis"),
    ("O80",    "Encounter for full-term uncomplicated delivery"),
    ("F31.9",  "Bipolar disorder, unspecified"),
    ("R42",    "Dizziness and giddiness"),
    ("M48.06", "Spinal stenosis, lumbar region"),
    ("S06.0X0A","Concussion without loss of consciousness, initial encounter"),
    ("I71.4",  "Abdominal aortic aneurysm, without rupture"),
    ("J38.00", "Paralysis of vocal cords and larynx, unspecified"),
    ("T78.2XXA","Anaphylactic shock, unspecified, initial encounter"),
    ("K25.9",  "Gastric ulcer, unspecified, without hemorrhage or perforation"),
    ("N20.0",  "Calculus of kidney"),
    ("R40.20", "Unspecified coma"),
    ("E86.0",  "Dehydration"),
    ("E11.22", "Type 2 diabetes mellitus with diabetic chronic kidney disease"),
    ("I47.1",  "Supraventricular tachycardia"),
    ("K56.60", "Unspecified intestinal obstruction"),
    ("G45.9",  "Transient cerebral ischemic attack, unspecified"),
    ("B96.20", "Unspecified Escherichia coli as the cause of diseases classified elsewhere"),
    ("J90",    "Pleural effusion, not elsewhere classified"),
    ("M62.82", "Rhabdomyolysis"),
    ("N13.30", "Unspecified hydronephrosis"),
    ("E87.0",  "Hyperosmolality and hypernatremia"),
    ("I42.9",  "Cardiomyopathy, unspecified"),
    ("R04.2",  "Hemoptysis"),
    ("K57.30", "Diverticulosis of large intestine without perforation or abscess without bleeding"),
    ("Z51.11", "Encounter for antineoplastic chemotherapy"),
    ("Z51.0",  "Encounter for antineoplastic radiation therapy"),
    ("I80.10", "Phlebitis and thrombophlebitis of unspecified femoral vein"),
    ("M86.9",  "Osteomyelitis, unspecified"),
    ("K83.0",  "Cholangitis"),
    ("T50.901A","Poisoning by unspecified drugs, accidental, initial encounter"),
    ("G93.1",  "Anoxic brain damage, not elsewhere classified"),
    ("R65.20", "Severe sepsis without septic shock"),
    ("R65.21", "Severe sepsis with septic shock"),
    ("I24.0",  "Acute coronary thrombosis not resulting in myocardial infarction"),
    ("J80",    "Acute respiratory distress syndrome"),
    ("N40.0",  "Benign prostatic hyperplasia without lower urinary tract symptoms"),
    ("Z23",    "Encounter for immunization"),
]

CPT_CODES = [
    ("99213", "Office visit, established patient, low complexity"),
    ("99214", "Office visit, established patient, moderate complexity"),
    ("99215", "Office visit, established patient, high complexity"),
    ("99221", "Initial hospital care, low complexity"),
    ("99222", "Initial hospital care, moderate complexity"),
    ("99223", "Initial hospital care, high complexity"),
    ("99231", "Subsequent hospital care, low complexity"),
    ("99232", "Subsequent hospital care, moderate complexity"),
    ("99233", "Subsequent hospital care, high complexity"),
    ("99238", "Hospital discharge day management, 30 min or less"),
    ("99281", "ED visit, self-limited/minor"),
    ("99282", "ED visit, low to moderate severity"),
    ("99283", "ED visit, moderate severity"),
    ("99284", "ED visit, high severity"),
    ("99285", "ED visit, high severity with threat to life"),
    ("99291", "Critical care, first 30-74 minutes"),
    ("99292", "Critical care, each additional 30 minutes"),
    ("36415", "Collection of venous blood by venipuncture"),
    ("71046", "Chest X-ray, 2 views"),
    ("71250", "CT chest without contrast"),
    ("71260", "CT chest with contrast"),
    ("74176", "CT abdomen and pelvis without contrast"),
    ("74177", "CT abdomen and pelvis with contrast"),
    ("70553", "MRI brain with and without contrast"),
    ("93000", "Electrocardiogram, 12-lead"),
    ("93306", "Transthoracic echocardiography"),
    ("93458", "Left heart catheterization"),
    ("43239", "Esophagogastroduodenoscopy with biopsy"),
    ("45378", "Colonoscopy, diagnostic"),
    ("45380", "Colonoscopy with biopsy"),
    ("47562", "Laparoscopic cholecystectomy"),
    ("27447", "Total knee arthroplasty"),
    ("27130", "Total hip arthroplasty"),
    ("49505", "Inguinal hernia repair"),
    ("44970", "Laparoscopic appendectomy"),
    ("33533", "Coronary artery bypass graft, single"),
    ("92928", "Percutaneous coronary stent placement"),
    ("31624", "Bronchoscopy with lavage"),
    ("62322", "Lumbar epidural injection"),
    ("20610", "Arthrocentesis, major joint"),
    ("51702", "Insertion of temporary indwelling bladder catheter"),
    ("36556", "Insertion of central venous catheter"),
    ("32405", "Thoracentesis"),
    ("49083", "Paracentesis"),
    ("59400", "Routine obstetric care, vaginal delivery"),
    ("59510", "Routine obstetric care, cesarean delivery"),
    ("90837", "Psychotherapy, 60 minutes"),
    ("97110", "Therapeutic exercises"),
    ("96365", "IV infusion, initial, up to 1 hour"),
    ("85025", "Complete blood count with differential"),
    ("80053", "Comprehensive metabolic panel"),
    ("80048", "Basic metabolic panel"),
    ("84443", "Thyroid stimulating hormone"),
    ("83036", "Hemoglobin A1c"),
    ("82607", "Vitamin B-12"),
    ("81001", "Urinalysis, automated, with microscopy"),
    ("87086", "Urine culture"),
    ("87070", "Bacterial culture, any source"),
    ("86900", "Blood typing, ABO"),
    ("86901", "Blood typing, Rh"),
]

MEDICATION_LIST = [
    ("Metformin",              "500 mg",  "PO",   "BID",      "00378-0234-01"),
    ("Lisinopril",             "10 mg",   "PO",   "Daily",    "00378-0512-01"),
    ("Atorvastatin",           "40 mg",   "PO",   "Daily",    "00378-3951-01"),
    ("Amlodipine",             "5 mg",    "PO",   "Daily",    "00378-0045-01"),
    ("Metoprolol Tartrate",    "25 mg",   "PO",   "BID",      "00378-0086-01"),
    ("Omeprazole",             "20 mg",   "PO",   "Daily",    "00378-6120-01"),
    ("Levothyroxine",          "50 mcg",  "PO",   "Daily",    "00378-1805-01"),
    ("Albuterol",              "2.5 mg",  "INH",  "Q4H PRN",  "00487-9801-01"),
    ("Furosemide",             "40 mg",   "IV",   "BID",      "00409-6102-01"),
    ("Warfarin",               "5 mg",    "PO",   "Daily",    "00378-2085-01"),
    ("Insulin Glargine",       "20 units","SubQ", "Daily",    "00088-2220-33"),
    ("Clopidogrel",            "75 mg",   "PO",   "Daily",    "00378-1153-01"),
    ("Gabapentin",             "300 mg",  "PO",   "TID",      "00378-1523-01"),
    ("Sertraline",             "50 mg",   "PO",   "Daily",    "00378-4187-01"),
    ("Hydrochlorothiazide",    "25 mg",   "PO",   "Daily",    "00378-0085-01"),
    ("Pantoprazole",           "40 mg",   "IV",   "Daily",    "00143-9283-01"),
    ("Losartan",               "50 mg",   "PO",   "Daily",    "00378-0185-01"),
    ("Acetaminophen",          "650 mg",  "PO",   "Q6H PRN",  "00904-1982-60"),
    ("Ibuprofen",              "400 mg",  "PO",   "Q6H PRN",  "00904-7915-60"),
    ("Aspirin",                "81 mg",   "PO",   "Daily",    "00904-2013-60"),
    ("Ceftriaxone",            "1 g",     "IV",   "Daily",    "00409-7337-01"),
    ("Vancomycin",             "1 g",     "IV",   "Q12H",     "00409-6509-01"),
    ("Piperacillin-Tazobactam","4.5 g",   "IV",   "Q6H",      "00206-8921-02"),
    ("Heparin",                "5000 units","SubQ","Q8H",      "00409-2720-01"),
    ("Enoxaparin",             "40 mg",   "SubQ", "Daily",    "00075-0621-01"),
    ("Morphine",               "2 mg",    "IV",   "Q4H PRN",  "00409-1712-01"),
    ("Hydromorphone",          "0.5 mg",  "IV",   "Q3H PRN",  "00409-1302-01"),
    ("Ondansetron",            "4 mg",    "IV",   "Q6H PRN",  "00409-4715-01"),
    ("Famotidine",             "20 mg",   "IV",   "BID",      "00409-3375-01"),
    ("Dexamethasone",          "4 mg",    "IV",   "Q6H",      "00409-0619-01"),
    ("Prednisone",             "40 mg",   "PO",   "Daily",    "00378-0145-01"),
    ("Amoxicillin",            "500 mg",  "PO",   "TID",      "00093-4150-01"),
    ("Azithromycin",           "250 mg",  "PO",   "Daily",    "00093-7169-01"),
    ("Ciprofloxacin",          "500 mg",  "PO",   "BID",      "00093-0862-01"),
    ("Fluconazole",            "200 mg",  "PO",   "Daily",    "00093-7238-01"),
    ("Potassium Chloride",     "20 mEq",  "PO",   "BID",      "00904-5688-60"),
    ("Magnesium Oxide",        "400 mg",  "PO",   "Daily",    "00904-5700-60"),
    ("Docusate Sodium",        "100 mg",  "PO",   "BID",      "00536-3755-01"),
    ("Senna",                  "8.6 mg",  "PO",   "Daily PRN","00904-5200-60"),
    ("Lorazepam",              "1 mg",    "PO",   "Q8H PRN",  "00378-2321-01"),
    ("Diazepam",               "5 mg",    "PO",   "Q8H PRN",  "00378-0345-01"),
    ("Carvedilol",             "12.5 mg", "PO",   "BID",      "00378-0937-01"),
    ("Spironolactone",         "25 mg",   "PO",   "Daily",    "00378-0039-01"),
    ("Digoxin",                "0.125 mg","PO",   "Daily",    "00378-0171-01"),
    ("Diltiazem",              "30 mg",   "PO",   "QID",      "00378-0195-01"),
    ("Amiodarone",             "200 mg",  "PO",   "Daily",    "00378-6140-01"),
    ("Nitroglycerin",          "0.4 mg",  "SL",   "Q5min PRN","00591-3615-01"),
    ("Cephalexin",             "500 mg",  "PO",   "QID",      "00093-3145-01"),
    ("Trimethoprim-Sulfa",     "160/800 mg","PO", "BID",      "00093-0359-01"),
    ("Levofloxacin",           "750 mg",  "IV",   "Daily",    "00409-3476-01"),
]

LAB_TESTS = [
    # (test_name, test_code, result_unit, ref_low, ref_high, mean, std)
    ("WBC",              "6690-2",  "10^3/uL",  4.5,  11.0,  7.5,  2.0),
    ("RBC",              "789-8",   "10^6/uL",  4.2,   5.9,  4.8,  0.5),
    ("Hemoglobin",       "718-7",   "g/dL",    12.0,  17.5, 14.0,  1.5),
    ("Hematocrit",       "4544-3",  "%",       36.0,  51.0, 42.0,  4.0),
    ("Platelets",        "777-3",   "10^3/uL",150.0, 400.0,250.0, 60.0),
    ("Sodium",           "2951-2",  "mEq/L",  136.0, 145.0,140.0,  3.0),
    ("Potassium",        "2823-3",  "mEq/L",    3.5,   5.0,  4.2,  0.4),
    ("Chloride",         "2075-0",  "mEq/L",   98.0, 106.0,102.0,  3.0),
    ("CO2",              "2028-9",  "mEq/L",   23.0,  29.0, 26.0,  2.0),
    ("BUN",              "3094-0",  "mg/dL",    7.0,  20.0, 14.0,  4.0),
    ("Creatinine",       "2160-0",  "mg/dL",    0.7,   1.3,  1.0,  0.3),
    ("Glucose",          "2345-7",  "mg/dL",   70.0, 100.0, 95.0, 25.0),
    ("Calcium",          "17861-6", "mg/dL",    8.5,  10.5,  9.5,  0.5),
    ("Total Protein",    "2885-2",  "g/dL",     6.0,   8.3,  7.0,  0.5),
    ("Albumin",          "1751-7",  "g/dL",     3.5,   5.5,  4.2,  0.5),
    ("Total Bilirubin",  "1975-2",  "mg/dL",    0.1,   1.2,  0.7,  0.4),
    ("ALT",              "1742-6",  "U/L",      7.0,  56.0, 25.0, 12.0),
    ("AST",              "1920-8",  "U/L",     10.0,  40.0, 22.0, 10.0),
    ("Alkaline Phosphatase","6768-6","U/L",    44.0, 147.0, 80.0, 25.0),
    ("HbA1c",            "4548-4",  "%",        4.0,   5.6,  5.8,  1.2),
    ("Troponin I",       "10839-9", "ng/mL",    0.00,  0.04, 0.02, 0.05),
    ("TSH",              "3016-3",  "mIU/L",    0.27,  4.20, 2.0,  1.0),
    ("Free T4",          "3024-7",  "ng/dL",    0.9,   1.7,  1.3,  0.2),
    ("INR",              "6301-6",  "",          0.8,   1.1,  1.0,  0.2),
    ("PT",               "5902-2",  "sec",     11.0,  13.5, 12.0,  1.0),
    ("PTT",              "3173-2",  "sec",     25.0,  35.0, 30.0,  4.0),
    ("D-Dimer",          "48065-7", "ng/mL FEU",0.0, 500.0,200.0,200.0),
    ("Lactate",          "2524-7",  "mmol/L",   0.5,   2.2,  1.2,  0.6),
    ("BNP",              "30934-4", "pg/mL",    0.0, 100.0, 50.0, 80.0),
    ("Procalcitonin",    "75241-0", "ng/mL",    0.0,   0.1,  0.05, 0.3),
    ("CRP",              "1988-5",  "mg/L",     0.0,   3.0,  1.5,  3.0),
    ("ESR",              "4537-7",  "mm/hr",    0.0,  20.0, 10.0, 10.0),
    ("Magnesium",        "19123-9", "mg/dL",    1.7,   2.2,  2.0,  0.2),
    ("Phosphorus",       "2777-1",  "mg/dL",    2.5,   4.5,  3.5,  0.6),
    ("Uric Acid",        "3084-1",  "mg/dL",    3.0,   7.0,  5.0,  1.2),
    ("LDH",              "2532-0",  "U/L",    140.0, 280.0,200.0, 40.0),
    ("Lipase",           "3040-3",  "U/L",     10.0,  73.0, 30.0, 20.0),
    ("Amylase",          "1798-8",  "U/L",     28.0, 100.0, 55.0, 20.0),
    ("Total Cholesterol","2093-3",  "mg/dL",    0.0, 200.0,190.0, 35.0),
    ("LDL",              "2089-1",  "mg/dL",    0.0, 100.0,110.0, 30.0),
    ("HDL",              "2085-9",  "mg/dL",   40.0,  60.0, 50.0, 12.0),
    ("Triglycerides",    "2571-8",  "mg/dL",    0.0, 150.0,130.0, 60.0),
    ("Ferritin",         "2276-4",  "ng/mL",   12.0, 300.0,100.0, 80.0),
    ("Iron",             "2498-4",  "mcg/dL",  60.0, 170.0,100.0, 30.0),
    ("TIBC",             "2500-7",  "mcg/dL", 250.0, 370.0,310.0, 30.0),
    ("Vitamin D",        "1989-3",  "ng/mL",   30.0, 100.0, 35.0, 15.0),
    ("PSA",              "2857-1",  "ng/mL",    0.0,   4.0,  1.5,  2.0),
    ("Urinalysis pH",    "2756-5",  "",          5.0,   8.0,  6.0,  0.8),
    ("Urine Specific Gravity","2965-2","",       1.005, 1.030,1.015,0.007),
]

ALLERGENS = [
    ("Penicillin",     "drug",          "Rash",              "moderate"),
    ("Sulfa Drugs",    "drug",          "Hives",             "moderate"),
    ("Aspirin",        "drug",          "GI upset",          "mild"),
    ("Codeine",        "drug",          "Nausea, vomiting",  "mild"),
    ("Morphine",       "drug",          "Itching",           "mild"),
    ("Iodine Contrast","drug",          "Anaphylaxis",       "severe"),
    ("Latex",          "environmental", "Contact dermatitis", "moderate"),
    ("Pollen",         "environmental", "Rhinitis",          "mild"),
    ("Dust Mites",     "environmental", "Asthma",            "moderate"),
    ("Peanuts",        "food",          "Anaphylaxis",       "severe"),
    ("Shellfish",      "food",          "Hives",             "moderate"),
    ("Eggs",           "food",          "Hives",             "mild"),
    ("Milk",           "food",          "GI upset",          "mild"),
    ("Soy",            "food",          "Rash",              "mild"),
    ("Tree Nuts",      "food",          "Anaphylaxis",       "severe"),
    ("Wheat",          "food",          "GI upset",          "mild"),
    ("Lisinopril",     "drug",          "Angioedema",        "severe"),
    ("Amoxicillin",    "drug",          "Rash",              "moderate"),
    ("Erythromycin",   "drug",          "Nausea",            "mild"),
    ("NSAIDs",         "drug",          "Bronchospasm",      "moderate"),
    ("ACE Inhibitors", "drug",          "Cough",             "mild"),
    ("Bee Stings",     "environmental", "Anaphylaxis",       "severe"),
    ("Mold",           "environmental", "Rhinitis",          "mild"),
    ("Cat Dander",     "environmental", "Asthma",            "moderate"),
    ("Tetracycline",   "drug",          "Photosensitivity",  "mild"),
]

DEPARTMENTS_DATA = [
    ("Emergency Department",  "ED",    "1", "Main",             "Dr. Sarah Mitchell",  "(555) 100-4100"),
    ("Intensive Care Unit",   "ICU",   "3", "Main",             "Dr. James Rodriguez", "(555) 100-4200"),
    ("NICU",                  "NICU",  "3", "Women's Pavilion", "Dr. Amy Patel",       "(555) 100-4250"),
    ("Med-Surg",              "MSURG", "4", "Main",             "Dr. Karen Liu",       "(555) 100-4300"),
    ("Cardiology",            "CARD",  "5", "Heart Center",     "Dr. Robert Kim",      "(555) 100-4400"),
    ("Oncology",              "ONC",   "6", "Cancer Center",    "Dr. Angela Foster",   "(555) 100-4500"),
    ("Orthopedics",           "ORTHO", "4", "Main",             "Dr. William Torres",  "(555) 100-4600"),
    ("Neurology",             "NEURO", "5", "Main",             "Dr. Patricia Adams",  "(555) 100-4700"),
    ("Radiology",             "RAD",   "1", "Main",             "Dr. David Nakamura",  "(555) 100-4800"),
    ("Laboratory",            "LAB",   "B1","Main",             "Dr. Jennifer Walsh",  "(555) 100-4900"),
    ("Pharmacy",              "PHARM", "1", "Main",             "Dr. Thomas Green",    "(555) 100-5000"),
    ("OB/GYN",                "OBGYN", "2", "Women's Pavilion", "Dr. Lisa Patel",      "(555) 100-5100"),
    ("Pediatrics",            "PEDS",  "2", "Main",             "Dr. Michael Chen",    "(555) 100-5200"),
    ("Behavioral Health",     "BH",    "6", "Behavioral Health","Dr. Steven Wright",   "(555) 100-5300"),
    ("Rehab",                 "REHAB", "1", "Outpatient",       "Dr. Maria Gonzalez",  "(555) 100-5400"),
]

SPECIALTIES_BY_DEPT = {
    1:  ["Emergency Medicine"],
    2:  ["Critical Care Medicine", "Pulmonary Critical Care"],
    3:  ["Neonatology"],
    4:  ["Internal Medicine", "Hospitalist Medicine", "Family Medicine"],
    5:  ["Cardiology", "Interventional Cardiology", "Electrophysiology"],
    6:  ["Medical Oncology", "Hematology-Oncology", "Radiation Oncology"],
    7:  ["Orthopedic Surgery", "Sports Medicine"],
    8:  ["Neurology", "Neurosurgery"],
    9:  ["Diagnostic Radiology", "Interventional Radiology"],
    10: ["Pathology", "Clinical Pathology"],
    11: ["Clinical Pharmacy"],
    12: ["Obstetrics & Gynecology", "Maternal-Fetal Medicine"],
    13: ["Pediatrics", "Pediatric Emergency Medicine"],
    14: ["Psychiatry", "Addiction Medicine"],
    15: ["Physical Medicine & Rehabilitation"],
}

CREDENTIALS = ["MD", "DO", "RN", "NP", "PA", "PharmD"]

ENCOUNTER_TYPES = ["inpatient", "outpatient", "ED", "observation", "telehealth"]

CHIEF_COMPLAINTS = [
    "Chest pain", "Shortness of breath", "Abdominal pain", "Headache",
    "Back pain", "Fever", "Cough", "Dizziness", "Nausea/vomiting",
    "Weakness", "Altered mental status", "Syncope", "Palpitations",
    "Leg pain", "Swelling", "Rash", "Fall", "Laceration",
    "Joint pain", "Urinary symptoms", "Sore throat", "Anxiety",
    "Bleeding", "Difficulty breathing", "Flank pain", "Hip pain",
    "Seizure", "Confusion", "Chest tightness", "Fatigue",
]

DISPOSITIONS = [
    "Discharged home", "Discharged to SNF", "Discharged to rehab",
    "Discharged with home health", "Transferred to another facility",
    "Left against medical advice", "Expired", None,
]

INSURANCE_PLANS = [
    "Blue Cross Blue Shield PPO", "Aetna HMO", "UnitedHealthcare PPO",
    "Cigna EPO", "Humana Medicare Advantage", "Kaiser Permanente HMO",
    "Medicare Part A", "Medicare Part B", "Medicaid",
    "Tricare Standard", "Anthem Blue Cross", "Molina Healthcare",
    "Centene", "Self-Pay", "WellCare", "Oscar Health",
]

DENIAL_REASONS = [
    "Missing prior authorization",
    "Service not covered under plan",
    "Incorrect coding",
    "Timely filing limit exceeded",
    "Duplicate claim",
    "Patient not eligible on date of service",
    "Non-covered diagnosis",
    "Exceeded benefit maximum",
    "Coordination of benefits required",
    "Medical necessity not established",
]

HL7_MESSAGE_TYPES = [
    ("ADT", "A01", "Admit/Visit Notification"),
    ("ADT", "A02", "Transfer a Patient"),
    ("ADT", "A03", "Discharge/End Visit"),
    ("ADT", "A04", "Register a Patient"),
    ("ADT", "A08", "Update Patient Information"),
    ("ORM", "O01", "General Order Message"),
    ("ORU", "R01", "Unsolicited Observation Result"),
    ("SIU", "S12", "Schedule Information Unsolicited"),
    ("DFT", "P03", "Post Detail Financial Transaction"),
    ("MDM", "T02", "Original Document Notification"),
]

SENDING_SYSTEMS = [
    "LabCorp_Interface", "Quest_Interface", "RadPACS_v4",
    "PharmacyRx_Pro", "BedMgmt_2000", "Registration_Portal",
    "Cardio_Monitor_Hub", "OR_Scheduling_v3", "BillingEngine_5",
    "ED_Tracker",
]

RECEIVING_SYSTEMS = [
    "MainEHR_Prod", "DataWarehouse", "ClinicalReporting",
    "HIE_Gateway", "ArchiveSystem",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_dt(start, end):
    """Return a random datetime between *start* and *end*."""
    delta = end - start
    secs = random.randint(0, max(int(delta.total_seconds()), 1))
    return start + timedelta(seconds=secs)


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _date_only(dt):
    return dt.strftime("%Y-%m-%d")


def _mrn():
    """Generate a medical record number like MRN-0000001."""
    _mrn._counter = getattr(_mrn, "_counter", 0) + 1
    return f"MRN-{_mrn._counter:07d}"


def _npi():
    """Generate a 10-digit NPI."""
    _npi._counter = getattr(_npi, "_counter", 1000000000)
    val = _npi._counter
    _npi._counter += 1
    return str(val)


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS departments (
    dept_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_name     TEXT NOT NULL,
    dept_code     TEXT UNIQUE NOT NULL,
    floor         TEXT,
    building      TEXT,
    manager_name  TEXT,
    phone         TEXT,
    active        INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS providers (
    provider_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    npi            TEXT UNIQUE NOT NULL,
    first_name     TEXT NOT NULL,
    last_name      TEXT NOT NULL,
    credential     TEXT,
    specialty      TEXT,
    department_id  INTEGER,
    email          TEXT,
    phone          TEXT,
    active         INTEGER DEFAULT 1,
    FOREIGN KEY (department_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS patients (
    mrn              TEXT PRIMARY KEY,
    first_name       TEXT NOT NULL,
    last_name        TEXT NOT NULL,
    dob              TEXT NOT NULL,
    gender           TEXT NOT NULL,
    race             TEXT,
    ethnicity        TEXT,
    address          TEXT,
    city             TEXT,
    state            TEXT,
    zip              TEXT,
    phone            TEXT,
    email            TEXT,
    primary_language TEXT DEFAULT 'English',
    insurance_plan   TEXT,
    insurance_id     TEXT,
    pcp_id           INTEGER,
    created_at       TEXT DEFAULT (datetime('now')),
    status           TEXT DEFAULT 'active',
    FOREIGN KEY (pcp_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS encounters (
    encounter_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_mrn           TEXT NOT NULL,
    encounter_type        TEXT NOT NULL,
    admission_date        TEXT NOT NULL,
    discharge_date        TEXT,
    attending_provider_id INTEGER,
    department_id         INTEGER,
    chief_complaint       TEXT,
    disposition           TEXT,
    status                TEXT DEFAULT 'open',
    drg_code              TEXT,
    los_days              REAL,
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn),
    FOREIGN KEY (attending_provider_id) REFERENCES providers(provider_id),
    FOREIGN KEY (department_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS diagnoses (
    diagnosis_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id             INTEGER NOT NULL,
    patient_mrn              TEXT NOT NULL,
    icd10_code               TEXT NOT NULL,
    description              TEXT,
    diagnosis_type           TEXT DEFAULT 'secondary',
    diagnosed_by_provider_id INTEGER,
    diagnosed_date           TEXT,
    status                   TEXT DEFAULT 'active',
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn),
    FOREIGN KEY (diagnosed_by_provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS procedures (
    procedure_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id            INTEGER NOT NULL,
    patient_mrn             TEXT NOT NULL,
    cpt_code                TEXT NOT NULL,
    description             TEXT,
    performing_provider_id  INTEGER,
    procedure_date          TEXT,
    department_id           INTEGER,
    status                  TEXT DEFAULT 'completed',
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn),
    FOREIGN KEY (performing_provider_id) REFERENCES providers(provider_id),
    FOREIGN KEY (department_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS medications (
    med_id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id             INTEGER NOT NULL,
    patient_mrn              TEXT NOT NULL,
    medication_name          TEXT NOT NULL,
    dosage                   TEXT,
    route                    TEXT,
    frequency                TEXT,
    prescribing_provider_id  INTEGER,
    start_date               TEXT,
    end_date                 TEXT,
    status                   TEXT DEFAULT 'active',
    ndc_code                 TEXT,
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn),
    FOREIGN KEY (prescribing_provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS lab_results (
    lab_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id          INTEGER NOT NULL,
    patient_mrn           TEXT NOT NULL,
    test_name             TEXT NOT NULL,
    test_code             TEXT,
    result_value          TEXT,
    result_unit           TEXT,
    reference_range_low   REAL,
    reference_range_high  REAL,
    abnormal_flag         TEXT DEFAULT 'N',
    collected_datetime    TEXT,
    resulted_datetime     TEXT,
    ordering_provider_id  INTEGER,
    status                TEXT DEFAULT 'final',
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn),
    FOREIGN KEY (ordering_provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS vital_signs (
    vital_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id            INTEGER NOT NULL,
    patient_mrn             TEXT NOT NULL,
    recorded_datetime       TEXT NOT NULL,
    temperature             REAL,
    heart_rate              INTEGER,
    systolic_bp             INTEGER,
    diastolic_bp            INTEGER,
    respiratory_rate        INTEGER,
    spo2                    REAL,
    height_cm               REAL,
    weight_kg               REAL,
    bmi                     REAL,
    recorded_by_provider_id INTEGER,
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn),
    FOREIGN KEY (recorded_by_provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id          INTEGER NOT NULL,
    patient_mrn           TEXT NOT NULL,
    order_type            TEXT NOT NULL,
    order_description     TEXT,
    ordering_provider_id  INTEGER,
    order_datetime        TEXT,
    status                TEXT DEFAULT 'ordered',
    priority              TEXT DEFAULT 'routine',
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn),
    FOREIGN KEY (ordering_provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS allergies (
    allergy_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_mrn   TEXT NOT NULL,
    allergen      TEXT NOT NULL,
    allergy_type  TEXT,
    reaction      TEXT,
    severity      TEXT,
    reported_date TEXT,
    status        TEXT DEFAULT 'active',
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn)
);

CREATE TABLE IF NOT EXISTS insurance_claims (
    claim_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id   INTEGER NOT NULL,
    patient_mrn    TEXT NOT NULL,
    insurance_plan TEXT,
    claim_amount   REAL,
    paid_amount    REAL,
    denied_amount  REAL DEFAULT 0,
    claim_status   TEXT DEFAULT 'submitted',
    submitted_date TEXT,
    resolved_date  TEXT,
    denial_reason  TEXT,
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn)
);

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL,
    department_id INTEGER,
    last_login    TEXT,
    active        INTEGER DEFAULT 1,
    access_level  INTEGER DEFAULT 1,
    FOREIGN KEY (department_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER,
    action        TEXT NOT NULL,
    resource_type TEXT,
    resource_id   TEXT,
    timestamp     TEXT NOT NULL,
    ip_address    TEXT,
    details       TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS hl7_messages (
    message_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    message_type        TEXT NOT NULL,
    trigger_event       TEXT,
    sending_system      TEXT,
    receiving_system    TEXT,
    patient_mrn         TEXT,
    encounter_id        INTEGER,
    message_datetime    TEXT,
    status              TEXT DEFAULT 'received',
    raw_message_preview TEXT,
    FOREIGN KEY (patient_mrn) REFERENCES patients(mrn),
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
);

CREATE TABLE IF NOT EXISTS system_alerts (
    alert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type      TEXT NOT NULL,
    severity        TEXT DEFAULT 'info',
    source_system   TEXT,
    message         TEXT,
    created_at      TEXT,
    acknowledged    INTEGER DEFAULT 0,
    acknowledged_by TEXT
);
"""


# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------

def _seed_departments(cur):
    for d in DEPARTMENTS_DATA:
        cur.execute(
            "INSERT INTO departments (dept_name, dept_code, floor, building, manager_name, phone, active) "
            "VALUES (?,?,?,?,?,?,1)",
            d,
        )


def _seed_providers(cur, now):
    """Generate 80 providers spread across departments."""
    providers = []
    provider_count = 80
    dept_count = len(DEPARTMENTS_DATA)
    for i in range(provider_count):
        dept_id = (i % dept_count) + 1
        specs = SPECIALTIES_BY_DEPT.get(dept_id, ["General"])
        specialty = random.choice(specs)
        cred = random.choices(CREDENTIALS, weights=[35, 15, 20, 12, 10, 8])[0]
        fn = fake.first_name() if HAS_FAKER else f"Provider{i}First"
        ln = fake.last_name() if HAS_FAKER else f"Provider{i}Last"
        npi = _npi()
        email = f"{fn.lower()}.{ln.lower()}@merithealth.org"
        phone = fake.phone_number() if HAS_FAKER else f"(555) 200-{i:04d}"
        active = 1 if random.random() < 0.95 else 0
        providers.append((npi, fn, ln, cred, specialty, dept_id, email, phone, active))
    cur.executemany(
        "INSERT INTO providers (npi, first_name, last_name, credential, specialty, department_id, email, phone, active) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        providers,
    )
    return provider_count


def _seed_patients(cur, num_providers, now):
    """Generate 500 patients."""
    patients = []
    genders = ["Male", "Female", "Non-binary"]
    races = ["White", "Black or African American", "Asian",
             "American Indian or Alaska Native", "Native Hawaiian or Other Pacific Islander",
             "Two or More Races", "Unknown"]
    ethnicities = ["Hispanic or Latino", "Not Hispanic or Latino", "Unknown"]
    languages = ["English", "Spanish", "Chinese", "Vietnamese", "Korean",
                 "Tagalog", "Arabic", "French", "Russian", "Portuguese"]
    statuses = ["active", "active", "active", "active", "inactive", "deceased"]
    states_list = [
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
        "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
        "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
        "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
        "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    ]

    mrn_list = []
    for i in range(500):
        mrn = _mrn()
        mrn_list.append(mrn)
        gender = random.choices(genders, weights=[48, 48, 4])[0]
        fn = fake.first_name_male() if gender == "Male" else fake.first_name_female() if gender == "Female" else fake.first_name()
        ln = fake.last_name()
        dob = _date_only(_random_dt(datetime(1935, 1, 1), datetime(2024, 1, 1)))
        race = random.choice(races)
        ethnicity = random.choice(ethnicities)
        addr = fake.street_address() if HAS_FAKER else f"{random.randint(100,9999)} Main St"
        city = fake.city() if HAS_FAKER else "Springfield"
        state = random.choice(states_list)
        zipcode = fake.zipcode() if HAS_FAKER else f"{random.randint(10000,99999)}"
        phone = fake.phone_number() if HAS_FAKER else f"(555) 300-{i:04d}"
        email = f"{fn.lower()}.{ln.lower()}{random.randint(1,999)}@email.com"
        lang = random.choices(languages, weights=[60, 15, 5, 3, 3, 3, 3, 3, 3, 2])[0]
        ins_plan = random.choice(INSURANCE_PLANS)
        ins_id = f"{ins_plan[:3].upper()}{random.randint(100000000, 999999999)}"
        pcp_id = random.randint(1, num_providers)
        created = _fmt(_random_dt(now - timedelta(days=3*365), now))
        status = random.choice(statuses)
        patients.append((
            mrn, fn, ln, dob, gender, race, ethnicity,
            addr, city, state, zipcode, phone, email,
            lang, ins_plan, ins_id, pcp_id, created, status,
        ))
    cur.executemany(
        "INSERT INTO patients (mrn, first_name, last_name, dob, gender, race, ethnicity, "
        "address, city, state, zip, phone, email, primary_language, insurance_plan, insurance_id, "
        "pcp_id, created_at, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        patients,
    )
    return mrn_list


def _seed_encounters(cur, mrn_list, num_providers, now):
    """Generate 1200 encounters over the last 365 days."""
    enc_meta = []  # list of (encounter_id, patient_mrn, admission_date, discharge_date)
    year_ago = now - timedelta(days=365)

    drg_codes = [
        "291", "292", "293",  # Heart failure
        "177", "178", "179",  # Respiratory infections
        "689", "690",         # Kidney & UTI
        "470",                # Major joint replacement
        "871", "872",         # Septicemia
        "065", "066",         # Intracranial hemorrhage / stroke
        "193", "194", "195",  # Pneumothorax
        "300", "301",         # Peripheral vascular disorders
        "640", "641",         # Nutritional disorders
        "378", "379",         # GI hemorrhage
        "682", "683",         # Renal failure
        "190", "191",         # COPD
        "305", "306",         # Hypertension
        "462", "463",         # Rehabilitation
    ]

    rows = []
    for i in range(1200):
        mrn = random.choice(mrn_list)
        etype = random.choices(
            ENCOUNTER_TYPES,
            weights=[30, 25, 25, 10, 10],
        )[0]
        admit_dt = _random_dt(year_ago, now - timedelta(hours=1))
        if etype == "ED":
            los_hours = random.choices([2, 4, 6, 8, 12, 24], weights=[15, 25, 25, 15, 10, 10])[0]
        elif etype == "outpatient" or etype == "telehealth":
            los_hours = random.choices([0.5, 1, 2, 4], weights=[30, 40, 20, 10])[0]
        elif etype == "observation":
            los_hours = random.choices([12, 24, 36, 48], weights=[20, 40, 25, 15])[0]
        else:  # inpatient
            los_hours = random.choices([24, 48, 72, 96, 120, 168, 240, 336], weights=[10, 15, 20, 15, 15, 10, 10, 5])[0]

        discharge_dt = admit_dt + timedelta(hours=los_hours)
        is_open = discharge_dt > now
        discharge_str = None if is_open else _fmt(discharge_dt)
        status = random.choices(["open", "closed", "cancelled"], weights=[15, 80, 5])[0]
        if is_open:
            status = "open"

        prov_id = random.randint(1, num_providers)
        dept_id = random.randint(1, 15)
        complaint = random.choice(CHIEF_COMPLAINTS)
        disposition = None if is_open else random.choice(DISPOSITIONS)
        drg = random.choice(drg_codes) if etype == "inpatient" else None
        los_days = round(los_hours / 24.0, 1)

        rows.append((
            mrn, etype, _fmt(admit_dt), discharge_str,
            prov_id, dept_id, complaint, disposition,
            status, drg, los_days,
        ))
        enc_meta.append((i + 1, mrn, admit_dt, discharge_dt))

    cur.executemany(
        "INSERT INTO encounters (patient_mrn, encounter_type, admission_date, discharge_date, "
        "attending_provider_id, department_id, chief_complaint, disposition, status, drg_code, los_days) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    return enc_meta


def _seed_diagnoses(cur, enc_meta, num_providers):
    """Generate 2500 diagnoses."""
    rows = []
    for i in range(2500):
        enc_id, mrn, admit_dt, _ = random.choice(enc_meta)
        code, desc = random.choice(ICD10_CODES)
        dx_type = random.choices(
            ["primary", "secondary", "admitting"],
            weights=[25, 60, 15],
        )[0]
        prov_id = random.randint(1, num_providers)
        dx_date = _fmt(admit_dt + timedelta(hours=random.randint(0, 12)))
        status = random.choices(["active", "resolved", "chronic"], weights=[50, 30, 20])[0]
        rows.append((enc_id, mrn, code, desc, dx_type, prov_id, dx_date, status))
    cur.executemany(
        "INSERT INTO diagnoses (encounter_id, patient_mrn, icd10_code, description, "
        "diagnosis_type, diagnosed_by_provider_id, diagnosed_date, status) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )


def _seed_procedures(cur, enc_meta, num_providers):
    """Generate 1800 procedures."""
    rows = []
    for i in range(1800):
        enc_id, mrn, admit_dt, _ = random.choice(enc_meta)
        cpt, desc = random.choice(CPT_CODES)
        prov_id = random.randint(1, num_providers)
        proc_date = _fmt(admit_dt + timedelta(hours=random.randint(0, 48)))
        dept_id = random.randint(1, 15)
        status = random.choices(
            ["completed", "scheduled", "in_progress", "cancelled"],
            weights=[70, 10, 10, 10],
        )[0]
        rows.append((enc_id, mrn, cpt, desc, prov_id, proc_date, dept_id, status))
    cur.executemany(
        "INSERT INTO procedures (encounter_id, patient_mrn, cpt_code, description, "
        "performing_provider_id, procedure_date, department_id, status) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )


def _seed_medications(cur, enc_meta, num_providers):
    """Generate 3000 medication orders."""
    rows = []
    for i in range(3000):
        enc_id, mrn, admit_dt, discharge_dt = random.choice(enc_meta)
        med = random.choice(MEDICATION_LIST)
        med_name, dosage, route, freq, ndc = med
        prov_id = random.randint(1, num_providers)
        start = admit_dt + timedelta(hours=random.randint(0, 6))
        duration_days = random.randint(1, 30)
        end = start + timedelta(days=duration_days)
        status = random.choices(
            ["active", "discontinued", "completed"],
            weights=[30, 15, 55],
        )[0]
        rows.append((
            enc_id, mrn, med_name, dosage, route, freq,
            prov_id, _fmt(start), _fmt(end), status, ndc,
        ))
    cur.executemany(
        "INSERT INTO medications (encounter_id, patient_mrn, medication_name, dosage, route, "
        "frequency, prescribing_provider_id, start_date, end_date, status, ndc_code) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )


def _seed_lab_results(cur, enc_meta, num_providers):
    """Generate 4000 lab results with realistic values."""
    rows = []
    for i in range(4000):
        enc_id, mrn, admit_dt, _ = random.choice(enc_meta)
        test = random.choice(LAB_TESTS)
        test_name, test_code, unit, ref_low, ref_high, mean, std = test

        # Generate a realistic value
        val = round(random.gauss(mean, std), 2)
        if ref_low is not None and val < ref_low * 0.3:
            val = round(ref_low * 0.3, 2)
        if ref_high is not None and val > ref_high * 2.5:
            val = round(ref_high * 2.5, 2)

        # Determine abnormal flag
        flag = "N"
        if val < ref_low:
            flag = "L"
            if val < ref_low * 0.7:
                flag = "C"  # critical low
        elif val > ref_high:
            flag = "H"
            if val > ref_high * 1.5:
                flag = "C"  # critical high

        collected = admit_dt + timedelta(hours=random.randint(0, 72))
        resulted = collected + timedelta(minutes=random.randint(30, 360))
        prov_id = random.randint(1, num_providers)
        status = random.choices(
            ["final", "preliminary", "corrected"],
            weights=[85, 10, 5],
        )[0]

        rows.append((
            enc_id, mrn, test_name, test_code, str(val), unit,
            ref_low, ref_high, flag,
            _fmt(collected), _fmt(resulted), prov_id, status,
        ))
    cur.executemany(
        "INSERT INTO lab_results (encounter_id, patient_mrn, test_name, test_code, "
        "result_value, result_unit, reference_range_low, reference_range_high, abnormal_flag, "
        "collected_datetime, resulted_datetime, ordering_provider_id, status) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )


def _seed_vital_signs(cur, enc_meta, num_providers):
    """Generate 2000 vital sign records."""
    rows = []
    for i in range(2000):
        enc_id, mrn, admit_dt, _ = random.choice(enc_meta)
        recorded = admit_dt + timedelta(hours=random.randint(0, 72))
        temp = round(random.gauss(98.6, 0.8), 1)
        hr = random.randint(50, 130)
        sbp = random.randint(85, 200)
        dbp = random.randint(50, 110)
        rr = random.randint(10, 30)
        spo2 = round(min(100.0, random.gauss(96.5, 2.5)), 1)
        height = round(random.gauss(170, 10), 1)
        weight = round(random.gauss(80, 18), 1)
        bmi = round(weight / ((height / 100) ** 2), 1) if height > 0 else None
        prov_id = random.randint(1, num_providers)
        rows.append((
            enc_id, mrn, _fmt(recorded),
            temp, hr, sbp, dbp, rr, spo2,
            height, weight, bmi, prov_id,
        ))
    cur.executemany(
        "INSERT INTO vital_signs (encounter_id, patient_mrn, recorded_datetime, "
        "temperature, heart_rate, systolic_bp, diastolic_bp, respiratory_rate, spo2, "
        "height_cm, weight_kg, bmi, recorded_by_provider_id) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )


def _seed_orders(cur, enc_meta, num_providers):
    """Generate 2500 orders."""
    order_types = ["lab", "imaging", "medication", "consult", "diet", "nursing"]
    order_type_weights = [30, 20, 25, 10, 8, 7]
    priorities = ["routine", "stat", "urgent"]
    priority_weights = [60, 20, 20]
    statuses = ["ordered", "in_progress", "completed", "cancelled"]
    status_weights = [15, 15, 60, 10]

    order_descriptions = {
        "lab": ["CBC with Differential", "BMP", "CMP", "Lipid Panel", "HbA1c",
                "Troponin I", "TSH", "Urinalysis", "Blood Culture x2", "PT/INR",
                "Type and Screen", "Lactic Acid", "BNP", "D-Dimer", "Procalcitonin"],
        "imaging": ["Chest X-ray 2 views", "CT Head without contrast", "CT Chest with contrast",
                     "CT Abdomen/Pelvis with contrast", "MRI Brain with/without contrast",
                     "Ultrasound Abdomen", "X-ray Knee 3 views", "CT Angiography Chest",
                     "MRI Lumbar Spine", "Echocardiogram"],
        "medication": ["Start IV Normal Saline 125 mL/hr", "Morphine 2mg IV Q4H PRN pain",
                        "Ceftriaxone 1g IV Daily", "Heparin drip per protocol",
                        "Insulin sliding scale", "Potassium Chloride 20mEq PO BID",
                        "Ondansetron 4mg IV Q6H PRN nausea", "Pantoprazole 40mg IV Daily"],
        "consult": ["Cardiology consult", "Pulmonology consult", "Infectious Disease consult",
                     "Nephrology consult", "GI consult", "Orthopedic Surgery consult",
                     "Neurology consult", "Palliative Care consult", "Social Work consult"],
        "diet": ["NPO", "Clear liquid diet", "Regular diet", "Cardiac diet",
                  "Renal diet", "Diabetic diet", "Mechanical soft diet"],
        "nursing": ["Fall precautions", "Telemetry monitoring", "Strict I&O",
                     "Wound care Q12H", "Foley catheter care", "DVT prophylaxis",
                     "Blood glucose monitoring Q6H", "Neuro checks Q4H"],
    }

    rows = []
    for i in range(2500):
        enc_id, mrn, admit_dt, _ = random.choice(enc_meta)
        otype = random.choices(order_types, weights=order_type_weights)[0]
        desc = random.choice(order_descriptions[otype])
        prov_id = random.randint(1, num_providers)
        order_dt = _fmt(admit_dt + timedelta(hours=random.randint(0, 24)))
        status = random.choices(statuses, weights=status_weights)[0]
        priority = random.choices(priorities, weights=priority_weights)[0]
        rows.append((enc_id, mrn, otype, desc, prov_id, order_dt, status, priority))
    cur.executemany(
        "INSERT INTO orders (encounter_id, patient_mrn, order_type, order_description, "
        "ordering_provider_id, order_datetime, status, priority) "
        "VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )


def _seed_allergies(cur, mrn_list):
    """Generate 800 allergy records."""
    rows = []
    # Give roughly 50% of patients 1-5 allergies each to reach 800+
    patients_with_allergies = random.sample(mrn_list, min(350, len(mrn_list)))
    count = 0
    for mrn in patients_with_allergies:
        num = random.randint(1, 5)
        selected = random.sample(ALLERGENS, k=min(num, len(ALLERGENS)))
        for allergen, atype, reaction, severity in selected:
            reported = _date_only(_random_dt(datetime(2000, 1, 1), datetime(2026, 2, 25)))
            status = random.choices(["active", "inactive"], weights=[90, 10])[0]
            rows.append((mrn, allergen, atype, reaction, severity, reported, status))
            count += 1
            if count >= 800:
                break
        if count >= 800:
            break
    cur.executemany(
        "INSERT INTO allergies (patient_mrn, allergen, allergy_type, reaction, severity, "
        "reported_date, status) VALUES (?,?,?,?,?,?,?)",
        rows,
    )


def _seed_insurance_claims(cur, enc_meta):
    """Generate 1500 insurance claims."""
    rows = []
    for i in range(1500):
        enc_id, mrn, admit_dt, discharge_dt = random.choice(enc_meta)
        plan = random.choice(INSURANCE_PLANS)
        amount = round(random.uniform(200, 150000), 2)
        claim_status = random.choices(
            ["submitted", "pending", "paid", "denied", "appealed"],
            weights=[15, 20, 40, 15, 10],
        )[0]
        if claim_status == "paid":
            paid = round(amount * random.uniform(0.5, 1.0), 2)
            denied_amt = round(amount - paid, 2)
        elif claim_status == "denied":
            paid = 0.0
            denied_amt = amount
        else:
            paid = 0.0
            denied_amt = 0.0
        submitted = _fmt(discharge_dt + timedelta(days=random.randint(0, 14)))
        resolved = None
        denial_reason = None
        if claim_status in ("paid", "denied"):
            resolved = _fmt(discharge_dt + timedelta(days=random.randint(15, 90)))
        if claim_status in ("denied", "appealed"):
            denial_reason = random.choice(DENIAL_REASONS)
        rows.append((
            enc_id, mrn, plan, amount, paid, denied_amt,
            claim_status, submitted, resolved, denial_reason,
        ))
    cur.executemany(
        "INSERT INTO insurance_claims (encounter_id, patient_mrn, insurance_plan, "
        "claim_amount, paid_amount, denied_amount, claim_status, submitted_date, "
        "resolved_date, denial_reason) VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows,
    )


def _seed_users(cur, now):
    """Generate 40 EHR system users."""
    roles = ["physician", "nurse", "admin", "analyst", "pharmacist"]
    role_weights = [25, 35, 15, 15, 10]
    rows = []
    for i in range(40):
        fn = fake.first_name() if HAS_FAKER else f"User{i}"
        ln = fake.last_name() if HAS_FAKER else f"Last{i}"
        username = f"{fn[0].lower()}{ln.lower()}{random.randint(1,99)}"
        full_name = f"{fn} {ln}"
        role = random.choices(roles, weights=role_weights)[0]
        dept_id = random.randint(1, 15)
        last_login = _fmt(_random_dt(now - timedelta(days=30), now))
        active = 1 if random.random() < 0.90 else 0
        access_level = {
            "physician": random.choice([3, 4, 5]),
            "nurse": random.choice([2, 3]),
            "admin": 5,
            "analyst": random.choice([3, 4]),
            "pharmacist": random.choice([3, 4]),
        }[role]
        rows.append((username, full_name, role, dept_id, last_login, active, access_level))
    cur.executemany(
        "INSERT INTO users (username, full_name, role, department_id, last_login, active, access_level) "
        "VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    return 40


def _seed_audit_log(cur, num_users, mrn_list, now):
    """Generate 5000 audit log entries."""
    actions = ["view", "edit", "print", "export"]
    action_weights = [60, 20, 10, 10]
    resource_types = ["patient_chart", "lab_result", "medication_order",
                      "encounter", "report", "user_account"]

    rows = []
    thirty_days_ago = now - timedelta(days=30)
    for i in range(5000):
        uid = random.randint(1, num_users)
        action = random.choices(actions, weights=action_weights)[0]
        rtype = random.choice(resource_types)
        rid = str(random.randint(1, 1200))
        ts = _fmt(_random_dt(thirty_days_ago, now))
        ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        details = None
        if action == "export":
            details = f"Exported {rtype} #{rid} to PDF"
        elif action == "print":
            details = f"Printed {rtype} #{rid}"
        rows.append((uid, action, rtype, rid, ts, ip, details))
    cur.executemany(
        "INSERT INTO audit_log (user_id, action, resource_type, resource_id, timestamp, "
        "ip_address, details) VALUES (?,?,?,?,?,?,?)",
        rows,
    )


def _seed_hl7_messages(cur, mrn_list, enc_meta, now):
    """Generate 200 HL7 messages."""
    rows = []
    thirty_days_ago = now - timedelta(days=30)
    for i in range(200):
        msg_type_info = random.choice(HL7_MESSAGE_TYPES)
        mtype, trigger, desc = msg_type_info
        sender = random.choice(SENDING_SYSTEMS)
        receiver = random.choice(RECEIVING_SYSTEMS)
        mrn = random.choice(mrn_list)
        enc_id = random.choice(enc_meta)[0]
        msg_dt = _fmt(_random_dt(thirty_days_ago, now))
        status = random.choices(
            ["sent", "received", "error", "acknowledged"],
            weights=[15, 40, 15, 30],
        )[0]

        # Build a mini HL7-like preview
        raw_preview = (
            f"MSH|^~\\&|{sender}|MERIT_HEALTH|{receiver}|MERIT_HEALTH|"
            f"{msg_dt.replace('-','').replace(':','').replace(' ','')}||"
            f"{mtype}^{trigger}|MSG{random.randint(100000,999999)}|P|2.5.1\r"
            f"PID|||{mrn}||..."
        )

        rows.append((
            mtype, trigger, sender, receiver, mrn, enc_id,
            msg_dt, status, raw_preview[:200],
        ))
    cur.executemany(
        "INSERT INTO hl7_messages (message_type, trigger_event, sending_system, receiving_system, "
        "patient_mrn, encounter_id, message_datetime, status, raw_message_preview) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        rows,
    )


def _seed_system_alerts(cur, now):
    """Generate 50 system alerts."""
    alert_types = ["interface_error", "downtime", "security", "performance"]
    severities = ["info", "warning", "critical"]
    source_systems = [
        "EHR_Core", "LabInterface_Engine", "RadPACS", "PharmacySystem",
        "ADT_Interface", "BillingEngine", "HIE_Gateway", "Firewall",
        "DatabaseServer", "ApplicationServer", "NetworkSwitch", "StorageArray",
    ]
    messages_by_type = {
        "interface_error": [
            "HL7 ACK timeout from LabCorp interface after 30s",
            "Failed to parse ORU message from Quest - invalid OBX segment",
            "Connection refused by RadPACS on port 2575",
            "Duplicate message control ID detected in ADT feed",
            "Character encoding mismatch in SIU message from OR Scheduling",
        ],
        "downtime": [
            "Scheduled maintenance window: EHR Core 02:00-04:00",
            "Unscheduled downtime: Lab Interface offline",
            "Database failover initiated - primary node unresponsive",
            "Pharmacy dispensing system restart required",
            "PACS image archive migration in progress - read only mode",
        ],
        "security": [
            "Multiple failed login attempts detected for user account",
            "Unusual after-hours access pattern detected",
            "VPN connection from unrecognized IP range",
            "PHI access from terminated employee account",
            "Brute force attack detected on authentication endpoint",
        ],
        "performance": [
            "Database query response time exceeds 5s threshold",
            "Memory utilization above 90% on application server",
            "Disk I/O latency spike on storage array",
            "HL7 message queue depth exceeds 500 messages",
            "CPU utilization at 95% on interface engine",
        ],
    }

    rows = []
    for i in range(50):
        atype = random.choices(alert_types, weights=[30, 20, 25, 25])[0]
        sev = random.choices(severities, weights=[40, 35, 25])[0]
        source = random.choice(source_systems)
        msg = random.choice(messages_by_type[atype])
        created = _fmt(_random_dt(now - timedelta(days=7), now))
        ack = 1 if random.random() < 0.6 else 0
        ack_by = f"admin_{random.randint(1,5)}" if ack else None
        rows.append((atype, sev, source, msg, created, ack, ack_by))
    cur.executemany(
        "INSERT INTO system_alerts (alert_type, severity, source_system, message, "
        "created_at, acknowledged, acknowledged_by) VALUES (?,?,?,?,?,?,?)",
        rows,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_db(db_path=DEFAULT_DB_PATH):
    """Return an sqlite3.Connection for the given database path."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=DEFAULT_DB_PATH, data_source="faker", synthea_dir=None):
    """Create all tables and seed with data.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.
    data_source : str
        ``"faker"``  – original Faker-based random data (default).
        ``"synthea"`` – clinically coherent Synthea-style data with
                        archetype-driven patient histories.
        ``"synthea_csv"`` – import from an external Synthea CSV directory.
    synthea_dir : str or None
        Path to a Synthea CSV output directory (only used when
        *data_source* is ``"synthea_csv"``).

    If the database file already exists, it is removed first so that
    every call yields a clean, reproducible dataset.
    """
    # Reset seeds for reproducibility
    random.seed(42)
    if HAS_FAKER:
        Faker.seed(42)
    # Reset counters
    _mrn._counter = 0
    _npi._counter = 1000000000

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Create schema
    cur.executescript(SCHEMA_SQL)

    if data_source == "synthea":
        conn.commit()
        conn.close()
        from synthea_integration import generate_synthea_sample
        generate_synthea_sample(db_path, num_patients=50)
        return
    elif data_source == "synthea_csv" and synthea_dir:
        conn.commit()
        conn.close()
        from synthea_integration import load_synthea_csv
        load_synthea_csv(db_path, synthea_dir)
        return

    # Default: original Faker-based seeding
    now = datetime(2026, 2, 25, 12, 0, 0)

    # Seed in dependency order
    _seed_departments(cur)
    num_providers = _seed_providers(cur, now)
    mrn_list = _seed_patients(cur, num_providers, now)
    enc_meta = _seed_encounters(cur, mrn_list, num_providers, now)
    _seed_diagnoses(cur, enc_meta, num_providers)
    _seed_procedures(cur, enc_meta, num_providers)
    _seed_medications(cur, enc_meta, num_providers)
    _seed_lab_results(cur, enc_meta, num_providers)
    _seed_vital_signs(cur, enc_meta, num_providers)
    _seed_orders(cur, enc_meta, num_providers)
    _seed_allergies(cur, mrn_list)
    _seed_insurance_claims(cur, enc_meta)
    num_users = _seed_users(cur, now)
    _seed_audit_log(cur, num_users, mrn_list, now)
    _seed_hl7_messages(cur, mrn_list, enc_meta, now)
    _seed_system_alerts(cur, now)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Standalone usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    print(f"Initializing database at {db} ...")
    init_db(db)
    print("Done. Verifying row counts ...")
    conn = get_db(db)
    tables = [
        "departments", "providers", "patients", "encounters", "diagnoses",
        "procedures", "medications", "lab_results", "vital_signs", "orders",
        "allergies", "insurance_claims", "users", "audit_log", "hl7_messages",
        "system_alerts",
    ]
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:25s} {count:>6,d} rows")
    conn.close()
    print("All tables seeded successfully.")

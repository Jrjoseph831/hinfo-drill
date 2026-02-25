"""scenarios_part1.py - Data Extraction, Data Quality, Compliance, EHR Navigation scenarios."""

SCENARIOS_PART1 = []


def _s(title, desc, category, tools, minutes, steps, hints, sql=None,
       difficulty="intermediate", roles=None):
    SCENARIOS_PART1.append({
        "title": title, "description": desc, "category": category,
        "tools": tools, "estimated_minutes": minutes, "steps": steps,
        "hints": hints, "sql_answer": sql, "difficulty": difficulty,
        "target_roles": roles or ["clinical_informatics_analyst"],
    })


# =========================================================================
# DATA EXTRACTION (1-25)
# =========================================================================

_s("Pull 30-Day Readmission Rate for {dept}",
   "The CMO has requested the 30-day readmission rate for {dept}. A readmission is defined as a patient with more than one encounter within 30 days of a prior discharge.",
   "Data Extraction", ["sql"], 30,
   ["Open SQL Console", "Identify encounters and departments tables", "Write a self-join for readmissions within 30 days", "Calculate the rate as a percentage"],
   ["Self-join encounters ON patient_mrn where second admission is within 30 days of first discharge",
    "Filter by dept_name = '{dept}'"],
   sql="SELECT ROUND(COUNT(DISTINCT r.patient_mrn)*100.0 / NULLIF(COUNT(DISTINCT e.patient_mrn),0), 2) AS readmission_rate FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN encounters r ON e.patient_mrn=r.patient_mrn AND r.encounter_id != e.encounter_id AND r.admission_date BETWEEN e.discharge_date AND datetime(e.discharge_date, '+30 days') WHERE d.dept_name='{dept}' AND e.discharge_date IS NOT NULL",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Extract Patients with {dx_desc} in the Last 90 Days",
   "The quality team needs all patients diagnosed with {dx_desc} ({dx_code}) in the last 90 days. Include MRN, name, encounter date, provider, and department.",
   "Data Extraction", ["sql", "ehr"], 20,
   ["Open SQL Console", "Query diagnoses table filtering on icd10_code", "Join with patients, providers, encounters, departments", "Review results in EHR viewer"],
   ["Filter diagnoses WHERE icd10_code = '{dx_code}'",
    "Add date filter: diagnosed_date >= datetime('now','-90 days')"],
   sql="SELECT p.mrn, p.first_name, p.last_name, e.admission_date, pr.first_name||' '||pr.last_name AS provider, d.dept_name FROM diagnoses dx JOIN encounters e ON dx.encounter_id=e.encounter_id JOIN patients p ON dx.patient_mrn=p.mrn JOIN providers pr ON e.attending_provider_id=pr.provider_id JOIN departments d ON e.department_id=d.dept_id WHERE dx.icd10_code='{dx_code}' AND dx.diagnosed_date >= datetime('now','-90 days')",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Generate Medication Report for Dr. {provider}",
   "The pharmacy director needs all medications prescribed by Dr. {provider} this month. Include medication name, patient, dosage, route, frequency, and start date.",
   "Data Extraction", ["sql"], 25,
   ["Open SQL Console", "Query medications joined with providers and patients", "Filter by provider and current month", "Sort by medication name"],
   ["JOIN providers ON medications.prescribing_provider_id = providers.provider_id",
    "Use strftime to filter current month"],
   sql="SELECT m.medication_name, p.first_name||' '||p.last_name AS patient, m.dosage, m.route, m.frequency, m.start_date FROM medications m JOIN providers pr ON m.prescribing_provider_id=pr.provider_id JOIN patients p ON m.patient_mrn=p.mrn WHERE pr.first_name||' '||pr.last_name='{provider}' AND strftime('%Y-%m', m.start_date)=strftime('%Y-%m','now') ORDER BY m.medication_name",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Average Length of Stay by Department",
   "Hospital administration needs the average length of stay (in days) for each department over the last quarter. Include department name, average LOS, and encounter count.",
   "Data Extraction", ["sql"], 25,
   ["Open SQL Console", "Calculate days between admission and discharge", "Group by department", "Filter to last quarter"],
   ["Use julianday(discharge_date) - julianday(admission_date) for LOS",
    "GROUP BY dept_name and filter discharge_date >= datetime('now','-90 days')"],
   sql="SELECT d.dept_name, ROUND(AVG(julianday(e.discharge_date)-julianday(e.admission_date)),1) AS avg_los, COUNT(*) AS encounters FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE e.discharge_date IS NOT NULL AND e.discharge_date >= datetime('now','-90 days') GROUP BY d.dept_name ORDER BY avg_los DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Top 10 Diagnoses by Frequency",
   "The medical director wants the top 10 most frequently assigned diagnoses across all encounters. Include the ICD-10 code, description, and total count.",
   "Data Extraction", ["sql"], 15,
   ["Open SQL Console", "Query diagnoses table", "Group by ICD-10 code and description", "Order by count descending, limit 10"],
   ["GROUP BY icd10_code, description",
    "ORDER BY COUNT(*) DESC LIMIT 10"],
   sql="SELECT icd10_code, description, COUNT(*) AS frequency FROM diagnoses GROUP BY icd10_code, description ORDER BY frequency DESC LIMIT 10",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patients with Multiple Active Medications",
   "Pharmacy wants a list of patients currently taking 5 or more active medications. Include MRN, patient name, and medication count.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console", "Query medications table for active prescriptions", "Group by patient and count medications", "Filter HAVING count >= 5"],
   ["Active medications have no end_date or end_date > current date",
    "HAVING COUNT(*) >= 5"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient_name, COUNT(*) AS med_count FROM medications m JOIN patients p ON m.patient_mrn=p.mrn WHERE m.start_date <= date('now') GROUP BY p.mrn, p.first_name, p.last_name HAVING COUNT(*) >= 5 ORDER BY med_count DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Lab Results Outside Reference Range for {dept}",
   "The lab director needs all lab results that fall outside the reference range for patients in {dept}. Include patient name, test name, result, reference range, and date.",
   "Data Extraction", ["sql"], 30,
   ["Open SQL Console", "Join lab_results with encounters and departments", "Parse reference ranges to compare values", "Filter to {dept}"],
   ["Reference ranges are stored as strings like '70-100'",
    "Cast result_value to numeric for comparison"],
   sql="SELECT p.first_name||' '||p.last_name AS patient, lr.test_name, lr.result_value, lr.unit, lr.reference_range FROM lab_results lr JOIN encounters e ON lr.encounter_id=e.encounter_id JOIN departments d ON e.department_id=d.dept_id JOIN patients p ON lr.patient_mrn=p.mrn WHERE d.dept_name='{dept}' AND (CAST(lr.result_value AS REAL) < CAST(SUBSTR(lr.reference_range,1,INSTR(lr.reference_range,'-')-1) AS REAL) OR CAST(lr.result_value AS REAL) > CAST(SUBSTR(lr.reference_range,INSTR(lr.reference_range,'-')+1) AS REAL))",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Encounter Volume This Month",
   "Administration needs to know how many encounters each provider has had this month. List provider name, credential, specialty, and encounter count.",
   "Data Extraction", ["sql"], 15,
   ["Open SQL Console", "Join encounters with providers", "Filter to current month", "Group by provider"],
   ["Use strftime('%Y-%m', admission_date) for month filter",
    "ORDER BY encounter_count DESC"],
   sql="SELECT pr.first_name||' '||pr.last_name AS provider, pr.credential, pr.specialty, COUNT(*) AS encounter_count FROM encounters e JOIN providers pr ON e.attending_provider_id=pr.provider_id WHERE strftime('%Y-%m', e.admission_date)=strftime('%Y-%m','now') GROUP BY pr.provider_id ORDER BY encounter_count DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patients Without a Discharge Date",
   "Case management needs a list of all patients who appear to still be admitted (no discharge date). Include MRN, name, admission date, department, and attending provider.",
   "Data Extraction", ["sql", "ehr"], 15,
   ["Open SQL Console", "Query encounters where discharge_date IS NULL", "Join with patients, departments, providers", "Sort by admission date ascending"],
   ["WHERE discharge_date IS NULL",
    "Oldest admissions first: ORDER BY admission_date ASC"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, e.admission_date, d.dept_name, pr.first_name||' '||pr.last_name AS attending FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn JOIN departments d ON e.department_id=d.dept_id JOIN providers pr ON e.attending_provider_id=pr.provider_id WHERE e.discharge_date IS NULL ORDER BY e.admission_date ASC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Emergency Department Visits by Day of Week",
   "The ED medical director wants to see visit volumes broken down by day of the week. Include day name and encounter count.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console", "Filter encounters to ED/Emergency type", "Extract day of week from admission_date", "Group and count by day"],
   ["Use strftime('%w', admission_date) for day number (0=Sunday)",
    "Use CASE to convert day numbers to names"],
   sql="SELECT CASE CAST(strftime('%w', e.admission_date) AS INTEGER) WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' WHEN 6 THEN 'Saturday' END AS day_name, COUNT(*) AS visits FROM encounters e WHERE e.encounter_type='Emergency' GROUP BY strftime('%w', e.admission_date) ORDER BY CAST(strftime('%w', e.admission_date) AS INTEGER)",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Vital Signs Summary for Patient {mrn}",
   "The attending physician needs a summary of all vital signs for patient {mrn}. Show each vital type with the most recent value and the date recorded.",
   "Data Extraction", ["sql", "ehr"], 20,
   ["Open SQL Console", "Query vitals for the specific patient", "Use a subquery or window function for most recent value per type", "Display results"],
   ["GROUP BY vital_type and use MAX(recorded_at)",
    "Subselect to get the value at the max timestamp"],
   sql="SELECT v.vital_type, v.value, v.recorded_at FROM vitals v WHERE v.patient_mrn='{mrn}' AND v.recorded_at = (SELECT MAX(v2.recorded_at) FROM vitals v2 WHERE v2.patient_mrn=v.patient_mrn AND v2.vital_type=v.vital_type) ORDER BY v.vital_type",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Diagnosis Frequency by Provider Specialty",
   "Quality improvement wants to understand the distribution of diagnoses by provider specialty. Show specialty, top diagnosis, and count.",
   "Data Extraction", ["sql"], 35,
   ["Open SQL Console", "Join diagnoses with encounters and providers", "Group by specialty and diagnosis", "Rank to find the top diagnosis per specialty"],
   ["Multiple JOINs: diagnoses -> encounters -> providers",
    "Use a subquery or window function to rank diagnoses within each specialty"],
   sql="SELECT pr.specialty, dx.icd10_code, dx.description, COUNT(*) AS dx_count FROM diagnoses dx JOIN encounters e ON dx.encounter_id=e.encounter_id JOIN providers pr ON e.attending_provider_id=pr.provider_id GROUP BY pr.specialty, dx.icd10_code, dx.description ORDER BY pr.specialty, dx_count DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Monthly Encounter Trend for {dept}",
   "The department head of {dept} wants to see the monthly encounter trend for the past 12 months. Include month, encounter count, and average LOS.",
   "Data Extraction", ["sql", "report"], 25,
   ["Open SQL Console", "Filter encounters to {dept}", "Group by month using strftime", "Calculate average LOS per month"],
   ["strftime('%Y-%m', admission_date) for month grouping",
    "Filter to last 12 months: admission_date >= datetime('now','-12 months')"],
   sql="SELECT strftime('%Y-%m', e.admission_date) AS month, COUNT(*) AS encounters, ROUND(AVG(julianday(e.discharge_date)-julianday(e.admission_date)),1) AS avg_los FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE d.dept_name='{dept}' AND e.admission_date >= datetime('now','-12 months') AND e.discharge_date IS NOT NULL GROUP BY month ORDER BY month",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Find All Encounters for Patient {mrn}",
   "A clinician needs the complete encounter history for patient {mrn}. Include encounter ID, dates, type, department, provider, and primary diagnosis.",
   "Data Extraction", ["sql", "ehr"], 15,
   ["Open SQL Console", "Query encounters for the specific MRN", "Left join diagnoses for primary diagnosis", "Sort by admission date"],
   ["WHERE patient_mrn = '{mrn}'",
    "LEFT JOIN to get diagnosis even if none exists"],
   sql="SELECT e.encounter_id, e.admission_date, e.discharge_date, e.encounter_type, d.dept_name, pr.first_name||' '||pr.last_name AS provider, dx.icd10_code, dx.description FROM encounters e JOIN departments d ON e.department_id=d.dept_id JOIN providers pr ON e.attending_provider_id=pr.provider_id LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.patient_mrn='{mrn}' ORDER BY e.admission_date DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("High-Risk Medication Prescribing Patterns",
   "Pharmacy and therapeutics committee wants to analyze prescribing patterns for high-risk medications (opioids, anticoagulants, insulin). Show provider, medication, and count.",
   "Data Extraction", ["sql"], 30,
   ["Open SQL Console", "Identify high-risk medication keywords", "Query medications with provider join", "Group by provider and medication"],
   ["Use LIKE for pattern matching: '%opioid%' OR medication_name LIKE '%warfarin%' etc.",
    "GROUP BY provider, medication_name ORDER BY count DESC"],
   sql="SELECT pr.first_name||' '||pr.last_name AS provider, m.medication_name, COUNT(*) AS rx_count FROM medications m JOIN providers pr ON m.prescribing_provider_id=pr.provider_id WHERE LOWER(m.medication_name) LIKE '%oxycodone%' OR LOWER(m.medication_name) LIKE '%hydrocodone%' OR LOWER(m.medication_name) LIKE '%warfarin%' OR LOWER(m.medication_name) LIKE '%heparin%' OR LOWER(m.medication_name) LIKE '%insulin%' GROUP BY pr.provider_id, m.medication_name ORDER BY rx_count DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounter Distribution by Type",
   "Operations wants to understand the mix of encounter types (Inpatient, Outpatient, Emergency, etc.). Show encounter type and percentage of total.",
   "Data Extraction", ["sql"], 15,
   ["Open SQL Console", "Count encounters grouped by type", "Calculate percentage of total", "Order by frequency"],
   ["Use COUNT(*) * 100.0 / (SELECT COUNT(*) FROM encounters) for percentage",
    "ROUND to 1 decimal place"],
   sql="SELECT encounter_type, COUNT(*) AS total, ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM encounters),1) AS pct FROM encounters GROUP BY encounter_type ORDER BY total DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patients with Both {dx_desc} and Diabetes",
   "The clinical research team needs patients diagnosed with both {dx_desc} ({dx_code}) and any diabetes diagnosis (E11.x). Include MRN, name, and both diagnosis dates.",
   "Data Extraction", ["sql"], 30,
   ["Open SQL Console", "Find patients with the target diagnosis", "Find patients with diabetes (E11%)", "Intersect or join the two sets"],
   ["Use two subqueries or a self-join on the diagnoses table",
    "Diabetes codes start with E11"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, d1.diagnosed_date AS dx1_date, d2.diagnosed_date AS diabetes_date FROM diagnoses d1 JOIN diagnoses d2 ON d1.patient_mrn=d2.patient_mrn JOIN patients p ON d1.patient_mrn=p.mrn WHERE d1.icd10_code='{dx_code}' AND d2.icd10_code LIKE 'E11%' GROUP BY p.mrn",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Department Census at a Point in Time",
   "Bed management wants today's census by department — patients admitted but not yet discharged. Show department, patient count, and list of MRNs.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console", "Find encounters where admission_date <= today and discharge_date is null or > today", "Group by department", "Count patients per department"],
   ["WHERE admission_date <= date('now') AND (discharge_date IS NULL OR discharge_date > date('now'))",
    "GROUP BY dept_name"],
   sql="SELECT d.dept_name, COUNT(*) AS census, GROUP_CONCAT(e.patient_mrn) AS mrns FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE e.admission_date <= date('now') AND (e.discharge_date IS NULL OR e.discharge_date > date('now')) GROUP BY d.dept_name ORDER BY census DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Antibiotic Utilization Report",
   "Infection control needs a report on antibiotic usage: medication name, total prescriptions, unique patients, and number of prescribing providers.",
   "Data Extraction", ["sql"], 25,
   ["Open SQL Console", "Filter medications to antibiotics using common suffixes", "Aggregate by medication", "Count distinct patients and providers"],
   ["Antibiotics often end in -cillin, -mycin, -floxacin, -cycline",
    "Use COUNT(DISTINCT ...) for unique counts"],
   sql="SELECT m.medication_name, COUNT(*) AS total_rx, COUNT(DISTINCT m.patient_mrn) AS unique_patients, COUNT(DISTINCT m.prescribing_provider_id) AS unique_prescribers FROM medications m WHERE LOWER(m.medication_name) LIKE '%cillin%' OR LOWER(m.medication_name) LIKE '%mycin%' OR LOWER(m.medication_name) LIKE '%floxacin%' OR LOWER(m.medication_name) LIKE '%cycline%' GROUP BY m.medication_name ORDER BY total_rx DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patient Demographics Summary",
   "Population health needs a demographic breakdown of the patient population: gender distribution, age ranges, and total count.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console", "Query patients table", "Calculate age from DOB", "Group by gender and age ranges"],
   ["Use (julianday('now') - julianday(dob)) / 365.25 for age",
    "Use CASE for age buckets: 0-17, 18-44, 45-64, 65+"],
   sql="SELECT gender, CASE WHEN (julianday('now')-julianday(dob))/365.25 < 18 THEN '0-17' WHEN (julianday('now')-julianday(dob))/365.25 < 45 THEN '18-44' WHEN (julianday('now')-julianday(dob))/365.25 < 65 THEN '45-64' ELSE '65+' END AS age_group, COUNT(*) AS patient_count FROM patients GROUP BY gender, age_group ORDER BY gender, age_group",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Medication Interaction Risk Assessment",
   "Pharmacy needs to find patients currently prescribed both warfarin and an NSAID, which poses a bleeding risk. List patient, both medications, and prescribing providers.",
   "Data Extraction", ["sql"], 35,
   ["Open SQL Console", "Find patients on warfarin", "Find patients on NSAIDs", "Join to find patients on both"],
   ["Self-join medications table on patient_mrn",
    "NSAIDs include ibuprofen, naproxen, aspirin, diclofenac"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, m1.medication_name AS med1, m2.medication_name AS med2, pr1.first_name||' '||pr1.last_name AS prescriber1, pr2.first_name||' '||pr2.last_name AS prescriber2 FROM medications m1 JOIN medications m2 ON m1.patient_mrn=m2.patient_mrn AND m1.medication_id != m2.medication_id JOIN patients p ON m1.patient_mrn=p.mrn JOIN providers pr1 ON m1.prescribing_provider_id=pr1.provider_id JOIN providers pr2 ON m2.prescribing_provider_id=pr2.provider_id WHERE LOWER(m1.medication_name) LIKE '%warfarin%' AND (LOWER(m2.medication_name) LIKE '%ibuprofen%' OR LOWER(m2.medication_name) LIKE '%naproxen%' OR LOWER(m2.medication_name) LIKE '%aspirin%')",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Discharge Summary for {dept} This Week",
   "The {dept} department head needs a summary of all discharges this week: patient count, average LOS, and most common diagnosis.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console", "Filter encounters by department and discharge date this week", "Calculate summary statistics", "Find most common diagnosis"],
   ["Use datetime('now','weekday 0','-7 days') for start of week",
    "Subquery for most common diagnosis"],
   sql="SELECT COUNT(*) AS discharges, ROUND(AVG(julianday(e.discharge_date)-julianday(e.admission_date)),1) AS avg_los, (SELECT dx.description FROM diagnoses dx JOIN encounters e2 ON dx.encounter_id=e2.encounter_id JOIN departments d2 ON e2.department_id=d2.dept_id WHERE d2.dept_name='{dept}' AND e2.discharge_date >= datetime('now','weekday 0','-7 days') GROUP BY dx.description ORDER BY COUNT(*) DESC LIMIT 1) AS top_diagnosis FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE d.dept_name='{dept}' AND e.discharge_date >= datetime('now','weekday 0','-7 days')",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Unmatched Lab Results",
   "The lab interface team needs to find lab results that don't link to a valid encounter. Show result ID, patient MRN, test name, and date.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console", "Left join lab_results to encounters", "Filter where encounter join fails", "List orphaned results"],
   ["LEFT JOIN encounters ON lab_results.encounter_id = encounters.encounter_id",
    "WHERE encounters.encounter_id IS NULL"],
   sql="SELECT lr.result_id, lr.patient_mrn, lr.test_name, lr.result_value, lr.unit FROM lab_results lr LEFT JOIN encounters e ON lr.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Productivity Dashboard Data",
   "Medical staff office needs provider productivity data: encounters per provider, unique patients, and average encounters per day worked.",
   "Data Extraction", ["sql", "report"], 30,
   ["Open SQL Console", "Count encounters per provider", "Count distinct patients per provider", "Calculate days with encounters and average"],
   ["COUNT(DISTINCT e.encounter_id) for encounters",
    "COUNT(DISTINCT DATE(e.admission_date)) for active days"],
   sql="SELECT pr.first_name||' '||pr.last_name AS provider, pr.specialty, COUNT(DISTINCT e.encounter_id) AS total_encounters, COUNT(DISTINCT e.patient_mrn) AS unique_patients, COUNT(DISTINCT DATE(e.admission_date)) AS active_days, ROUND(COUNT(DISTINCT e.encounter_id)*1.0/MAX(COUNT(DISTINCT DATE(e.admission_date)),1),1) AS avg_per_day FROM encounters e JOIN providers pr ON e.attending_provider_id=pr.provider_id GROUP BY pr.provider_id ORDER BY total_encounters DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])


# =========================================================================
# DATA QUALITY (26-50)
# =========================================================================

_s("Find Patients with Missing Demographics",
   "Registration quality audit requires identifying patients with incomplete demographic data — missing first name, last name, DOB, or gender.",
   "Data Quality", ["sql", "ehr"], 15,
   ["Open SQL Console", "Query patients table for NULL or empty fields", "Count missing fields per patient", "Generate a fix list"],
   ["Check for NULL and empty string: (field IS NULL OR field = '')",
    "Include MRN so registration can correct records"],
   sql="SELECT mrn, first_name, last_name, dob, gender FROM patients WHERE first_name IS NULL OR first_name='' OR last_name IS NULL OR last_name='' OR dob IS NULL OR gender IS NULL OR gender=''",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Detect Duplicate Patient Records",
   "HIM suspects duplicate patient records. Find patients that share the same first name, last name, and date of birth but have different MRNs.",
   "Data Quality", ["sql"], 30,
   ["Open SQL Console", "Self-join patients on name and DOB", "Exclude same-MRN matches", "Review potential duplicates"],
   ["Self-join: p1.first_name=p2.first_name AND p1.last_name=p2.last_name AND p1.dob=p2.dob",
    "WHERE p1.mrn < p2.mrn to avoid duplicate pairs"],
   sql="SELECT p1.mrn AS mrn1, p2.mrn AS mrn2, p1.first_name, p1.last_name, p1.dob FROM patients p1 JOIN patients p2 ON p1.first_name=p2.first_name AND p1.last_name=p2.last_name AND p1.dob=p2.dob AND p1.mrn < p2.mrn",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounters with Invalid Department References",
   "An interface upgrade may have corrupted department IDs. Find encounters that reference a department_id not present in the departments table.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Left join encounters to departments", "Filter where department join fails", "List affected encounters"],
   ["LEFT JOIN departments ON encounters.department_id = departments.dept_id",
    "WHERE departments.dept_id IS NULL"],
   sql="SELECT e.encounter_id, e.patient_mrn, e.admission_date, e.department_id FROM encounters e LEFT JOIN departments d ON e.department_id=d.dept_id WHERE d.dept_id IS NULL",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Diagnoses with Invalid ICD-10 Format",
   "Coding compliance requires validating ICD-10 code formats. Find diagnoses where the icd10_code doesn't match the standard pattern (letter followed by digits and optional dot).",
   "Data Quality", ["sql", "coding"], 25,
   ["Open SQL Console", "Define a regex pattern for valid ICD-10 codes", "Query diagnoses for non-matching codes", "Report invalid entries"],
   ["Valid ICD-10 pattern: starts with a letter, then 2 digits, optional dot and more digits",
    "SQLite doesn't have full regex — use LIKE and LENGTH checks"],
   sql="SELECT diagnosis_id, encounter_id, icd10_code, description FROM diagnoses WHERE icd10_code NOT LIKE '[A-Z]__' AND icd10_code NOT LIKE '[A-Z]__.%' AND LENGTH(icd10_code) < 3",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst", "compliance_officer"])

_s("Medications with Missing Dosage Information",
   "Pharmacy informatics needs to find medication orders that are missing dosage, route, or frequency information.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Query medications for NULL or empty dosage fields", "Include medication name and patient for context", "Count total incomplete orders"],
   ["Check dosage, route, and frequency for NULL or empty",
    "JOIN patients to show patient name"],
   sql="SELECT m.medication_id, m.medication_name, p.mrn, p.first_name||' '||p.last_name AS patient, m.dosage, m.route, m.frequency FROM medications m JOIN patients p ON m.patient_mrn=p.mrn WHERE m.dosage IS NULL OR m.dosage='' OR m.route IS NULL OR m.route='' OR m.frequency IS NULL OR m.frequency=''",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounters with Discharge Before Admission",
   "Data integrity check: find encounters where the discharge date is before the admission date, indicating a data entry error.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Compare discharge_date with admission_date", "Filter where discharge < admission", "Report affected encounters"],
   ["WHERE discharge_date < admission_date",
    "Include department and provider for investigation"],
   sql="SELECT e.encounter_id, e.patient_mrn, e.admission_date, e.discharge_date, d.dept_name, pr.first_name||' '||pr.last_name AS provider FROM encounters e JOIN departments d ON e.department_id=d.dept_id JOIN providers pr ON e.attending_provider_id=pr.provider_id WHERE e.discharge_date IS NOT NULL AND e.discharge_date < e.admission_date",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Lab Results with Non-Numeric Values",
   "The lab interface may be sending non-numeric results that should be numeric. Identify lab results where result_value cannot be cast to a number.",
   "Data Quality", ["sql"], 25,
   ["Open SQL Console", "Attempt to identify non-numeric result_value entries", "List test name, value, and expected range", "Count affected results by test type"],
   ["SQLite: CAST(result_value AS REAL) returns 0 for non-numeric strings",
    "Check where CAST fails but value is not '0'"],
   sql="SELECT lr.result_id, lr.test_name, lr.result_value, lr.unit, lr.reference_range FROM lab_results lr WHERE CAST(lr.result_value AS REAL)=0 AND lr.result_value != '0' AND lr.result_value != '0.0'",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Orphaned Diagnosis Records",
   "Find diagnosis records that reference an encounter_id not present in the encounters table, suggesting data integrity issues.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Left join diagnoses to encounters", "Filter where encounter is missing", "List orphaned diagnoses"],
   ["LEFT JOIN encounters ON diagnoses.encounter_id = encounters.encounter_id",
    "WHERE encounters.encounter_id IS NULL"],
   sql="SELECT dx.diagnosis_id, dx.encounter_id, dx.patient_mrn, dx.icd10_code, dx.description FROM diagnoses dx LEFT JOIN encounters e ON dx.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patients with Implausible Ages",
   "Quality team needs to find patient records with implausible ages — under 0 or over 120 years, which likely indicate DOB entry errors.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Calculate age from DOB", "Filter for implausible values", "List patients for correction"],
   ["Age = (julianday('now') - julianday(dob)) / 365.25",
    "Filter WHERE age < 0 OR age > 120"],
   sql="SELECT mrn, first_name, last_name, dob, ROUND((julianday('now')-julianday(dob))/365.25,1) AS age FROM patients WHERE (julianday('now')-julianday(dob))/365.25 < 0 OR (julianday('now')-julianday(dob))/365.25 > 120",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Vital Signs with Out-of-Range Values",
   "Clinical informatics needs to find vitals entries with physiologically impossible values (e.g., heart rate > 300, temperature > 110F).",
   "Data Quality", ["sql", "ehr"], 25,
   ["Open SQL Console", "Define physiological limits per vital type", "Query vitals for values outside limits", "Report by vital type and department"],
   ["Use CASE on vital_type to set appropriate limits",
    "Heart rate: 20-300, Temperature: 85-110, BP systolic: 40-300"],
   sql="SELECT v.vital_id, v.patient_mrn, v.vital_type, v.value, v.recorded_at FROM vitals v WHERE (v.vital_type='heart_rate' AND (CAST(v.value AS REAL)<20 OR CAST(v.value AS REAL)>300)) OR (v.vital_type='temperature' AND (CAST(v.value AS REAL)<85 OR CAST(v.value AS REAL)>110)) OR (v.vital_type='systolic_bp' AND (CAST(v.value AS REAL)<40 OR CAST(v.value AS REAL)>300))",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Provider Records with Missing Credentials",
   "Medical staff office needs to identify provider records missing credential or specialty information.",
   "Data Quality", ["sql"], 10,
   ["Open SQL Console", "Query providers for NULL credential or specialty", "List affected providers", "Count incomplete records"],
   ["WHERE credential IS NULL OR credential = '' OR specialty IS NULL",
    "Include provider_id for reference"],
   sql="SELECT provider_id, first_name, last_name, credential, specialty FROM providers WHERE credential IS NULL OR credential='' OR specialty IS NULL OR specialty=''",
   difficulty="beginner", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Encounters Assigned to Non-Existent Providers",
   "Verify referential integrity between encounters and providers. Find encounters referencing a provider_id not in the providers table.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Left join encounters to providers", "Filter where provider is missing", "List affected encounters"],
   ["LEFT JOIN providers ON encounters.attending_provider_id = providers.provider_id",
    "WHERE providers.provider_id IS NULL"],
   sql="SELECT e.encounter_id, e.patient_mrn, e.admission_date, e.attending_provider_id FROM encounters e LEFT JOIN providers pr ON e.attending_provider_id=pr.provider_id WHERE pr.provider_id IS NULL",
   difficulty="beginner", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Duplicate Diagnosis Entries per Encounter",
   "Coding team needs to find encounters with the same ICD-10 code entered multiple times, which inflates diagnosis counts.",
   "Data Quality", ["sql", "coding"], 20,
   ["Open SQL Console", "Group diagnoses by encounter and ICD-10 code", "Filter HAVING COUNT > 1", "List duplicates for cleanup"],
   ["GROUP BY encounter_id, icd10_code HAVING COUNT(*) > 1",
    "Include description and count for review"],
   sql="SELECT encounter_id, icd10_code, description, COUNT(*) AS dup_count FROM diagnoses GROUP BY encounter_id, icd10_code HAVING COUNT(*) > 1 ORDER BY dup_count DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst", "compliance_officer"])

_s("Medication Records with Future Start Dates",
   "Pharmacy needs to identify medication records where the start_date is in the future beyond a reasonable scheduling window (more than 7 days ahead).",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Query medications where start_date is far future", "List medication details and patient", "Count affected records"],
   ["WHERE start_date > datetime('now', '+7 days')",
    "Include prescribing provider for follow-up"],
   sql="SELECT m.medication_id, m.medication_name, m.start_date, p.mrn, p.first_name||' '||p.last_name AS patient, pr.first_name||' '||pr.last_name AS prescriber FROM medications m JOIN patients p ON m.patient_mrn=p.mrn JOIN providers pr ON m.prescribing_provider_id=pr.provider_id WHERE m.start_date > datetime('now', '+7 days')",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Consistency Check: Patient MRN in Encounters vs Patients",
   "Verify that every patient_mrn in encounters exists in the patients table. Identify any orphaned encounter records.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Left join encounters to patients on MRN", "Filter where patient is missing", "Quantify the data gap"],
   ["LEFT JOIN patients ON encounters.patient_mrn = patients.mrn",
    "WHERE patients.mrn IS NULL"],
   sql="SELECT e.encounter_id, e.patient_mrn, e.admission_date, e.encounter_type FROM encounters e LEFT JOIN patients p ON e.patient_mrn=p.mrn WHERE p.mrn IS NULL",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Audit Completeness of Vital Signs Documentation",
   "Nursing informatics wants to know what percentage of encounters have at least one vital sign recorded. Break down by department.",
   "Data Quality", ["sql", "report"], 25,
   ["Open SQL Console", "Count encounters with at least one vital", "Compare against total encounters per department", "Calculate completion rate"],
   ["LEFT JOIN vitals on encounter_id, then check for NULL",
    "Use COUNT with and without the vital to get the percentage"],
   sql="SELECT d.dept_name, COUNT(DISTINCT e.encounter_id) AS total_encounters, COUNT(DISTINCT CASE WHEN v.vital_id IS NOT NULL THEN e.encounter_id END) AS with_vitals, ROUND(COUNT(DISTINCT CASE WHEN v.vital_id IS NOT NULL THEN e.encounter_id END)*100.0/NULLIF(COUNT(DISTINCT e.encounter_id),0),1) AS pct_complete FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN vitals v ON e.encounter_id=v.encounter_id GROUP BY d.dept_name ORDER BY pct_complete",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Identify Stale Encounter Records",
   "IT needs to find encounters with admission dates more than 365 days ago that still have no discharge date, suggesting stale or abandoned records.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Query encounters admitted over a year ago", "Filter where still no discharge date", "Prioritize by age of record"],
   ["WHERE admission_date < datetime('now','-365 days') AND discharge_date IS NULL",
    "ORDER BY admission_date ASC for oldest first"],
   sql="SELECT e.encounter_id, e.patient_mrn, e.admission_date, d.dept_name, pr.first_name||' '||pr.last_name AS provider FROM encounters e JOIN departments d ON e.department_id=d.dept_id JOIN providers pr ON e.attending_provider_id=pr.provider_id WHERE e.admission_date < datetime('now','-365 days') AND e.discharge_date IS NULL ORDER BY e.admission_date ASC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Lab Results Missing Reference Ranges",
   "Lab quality management needs to find test results that have no reference range defined, making clinical interpretation difficult.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Query lab_results for NULL or empty reference_range", "Group by test name to find systematic gaps", "Count affected results"],
   ["WHERE reference_range IS NULL OR reference_range = ''",
    "GROUP BY test_name for pattern analysis"],
   sql="SELECT test_name, COUNT(*) AS missing_count FROM lab_results WHERE reference_range IS NULL OR reference_range='' GROUP BY test_name ORDER BY missing_count DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Cross-Table Patient Count Reconciliation",
   "Data governance needs to reconcile patient counts across tables. Compare unique patient_mrn values in patients, encounters, diagnoses, and medications.",
   "Data Quality", ["sql"], 25,
   ["Open SQL Console", "Count distinct MRNs in each table", "Identify MRNs in child tables but not in patients", "Summarize discrepancies"],
   ["Use UNION ALL with labels for each table source",
    "Find MRNs in encounters/diagnoses/medications not in patients"],
   sql="SELECT 'patients' AS source, COUNT(DISTINCT mrn) AS unique_mrns FROM patients UNION ALL SELECT 'encounters', COUNT(DISTINCT patient_mrn) FROM encounters UNION ALL SELECT 'diagnoses', COUNT(DISTINCT patient_mrn) FROM diagnoses UNION ALL SELECT 'medications', COUNT(DISTINCT patient_mrn) FROM medications UNION ALL SELECT 'lab_results', COUNT(DISTINCT patient_mrn) FROM lab_results",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounters with Extremely Long Length of Stay",
   "Utilization review needs to identify encounters with LOS exceeding 30 days, which may indicate data errors or complex cases requiring review.",
   "Data Quality", ["sql", "ehr"], 20,
   ["Open SQL Console", "Calculate LOS for discharged encounters", "Filter where LOS > 30 days", "Include department and diagnosis context"],
   ["julianday(discharge_date) - julianday(admission_date) > 30",
    "Include primary diagnosis for clinical context"],
   sql="SELECT e.encounter_id, p.mrn, p.first_name||' '||p.last_name AS patient, e.admission_date, e.discharge_date, CAST(julianday(e.discharge_date)-julianday(e.admission_date) AS INTEGER) AS los_days, d.dept_name, dx.description AS primary_dx FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn JOIN departments d ON e.department_id=d.dept_id LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE julianday(e.discharge_date)-julianday(e.admission_date) > 30 ORDER BY los_days DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])


# =========================================================================
# COMPLIANCE (51-75)
# =========================================================================

_s("HIPAA Access Audit for Patient {mrn}",
   "Privacy officer needs a complete audit trail for patient {mrn}. Retrieve all audit_log entries showing who accessed this patient's record and when.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console", "Query audit_log for the patient resource", "Include user, action, and timestamp", "Sort chronologically"],
   ["WHERE resource_type='patient' AND resource_id='{mrn}'",
    "ORDER BY timestamp for chronological review"],
   sql="SELECT log_id, user_id, action, resource_type, resource_id, timestamp FROM audit_log WHERE resource_id='{mrn}' ORDER BY timestamp",
   difficulty="intermediate", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Identify After-Hours Access Patterns",
   "Security wants to identify users accessing records between 10 PM and 6 AM, which may indicate unauthorized access.",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console", "Extract hour from audit_log timestamps", "Filter for after-hours access (22:00-06:00)", "Group by user to find patterns"],
   ["Use strftime('%H', timestamp) to extract hour",
    "WHERE hour >= 22 OR hour < 6"],
   sql="SELECT user_id, COUNT(*) AS after_hours_access, MIN(timestamp) AS first_access, MAX(timestamp) AS last_access FROM audit_log WHERE CAST(strftime('%H', timestamp) AS INTEGER) >= 22 OR CAST(strftime('%H', timestamp) AS INTEGER) < 6 GROUP BY user_id ORDER BY after_hours_access DESC",
   difficulty="intermediate", roles=["compliance_officer", "system_administrator"])

_s("Minimum Necessary Access Review for {dept}",
   "HIPAA minimum necessary rule review: determine if users in {dept} are accessing records outside their department.",
   "Compliance", ["sql", "audit"], 35,
   ["Open SQL Console", "Join audit_log with encounter and department data", "Identify cross-department access", "Quantify potential violations"],
   ["Join audit_log to encounters to departments",
    "Compare the accessing user's department to the patient's department"],
   sql=None,
   difficulty="advanced", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Break-the-Glass Event Analysis",
   "Privacy requires a report on all break-the-glass (emergency override) access events in the last 30 days. Show user, patient, timestamp, and justification.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console", "Query audit_log for break-the-glass actions", "Filter to last 30 days", "Review justification completeness"],
   ["Filter WHERE action LIKE '%break%glass%' or '%emergency%override%'",
    "Verify each event has a documented reason"],
   sql="SELECT log_id, user_id, resource_id AS patient, timestamp, action FROM audit_log WHERE (LOWER(action) LIKE '%break%glass%' OR LOWER(action) LIKE '%emergency%') AND timestamp >= datetime('now','-30 days') ORDER BY timestamp DESC",
   difficulty="intermediate", roles=["compliance_officer"])

_s("User Access Frequency Report",
   "Security needs a report on user access frequency: total accesses, unique patients accessed, and unique resource types per user in the last month.",
   "Compliance", ["sql", "audit", "report"], 25,
   ["Open SQL Console", "Aggregate audit_log by user_id", "Calculate metrics per user", "Flag high-volume users"],
   ["COUNT(*) for total, COUNT(DISTINCT resource_id) for unique patients",
    "Filter to last 30 days"],
   sql="SELECT user_id, COUNT(*) AS total_accesses, COUNT(DISTINCT resource_id) AS unique_resources, COUNT(DISTINCT resource_type) AS resource_types, MIN(timestamp) AS first_access, MAX(timestamp) AS last_access FROM audit_log WHERE timestamp >= datetime('now','-30 days') GROUP BY user_id ORDER BY total_accesses DESC",
   difficulty="intermediate", roles=["compliance_officer", "system_administrator"])

_s("PHI Disclosure Tracking Report",
   "Privacy office needs to generate a PHI disclosure log for regulatory reporting. Compile all external data disclosures from the audit trail.",
   "Compliance", ["sql", "audit", "report"], 30,
   ["Open Audit Workbench", "Filter for disclosure-type actions", "Include recipient and purpose if available", "Generate formatted report"],
   ["Look for action types like 'export', 'print', 'fax', 'download'",
    "Cross-reference with patient demographics for the disclosure log"],
   sql="SELECT user_id, action, resource_type, resource_id, timestamp FROM audit_log WHERE LOWER(action) LIKE '%export%' OR LOWER(action) LIKE '%print%' OR LOWER(action) LIKE '%download%' OR LOWER(action) LIKE '%disclose%' ORDER BY timestamp DESC",
   difficulty="intermediate", roles=["compliance_officer"])

_s("Role-Based Access Control Audit",
   "IT security needs to verify that access patterns align with expected role-based access. Compare actual access by user against their assigned role permissions.",
   "Compliance", ["sql", "audit"], 35,
   ["Open Audit Workbench", "Extract user access patterns from audit_log", "Map to expected role permissions", "Identify access outside role scope"],
   ["Group audit actions by user_id and resource_type",
    "Compare against expected access patterns per role"],
   sql=None,
   difficulty="advanced", roles=["compliance_officer", "system_administrator"])

_s("Concurrent Session Detection",
   "Security suspects credential sharing. Find users with audit log entries from significantly different contexts within a short time window.",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console", "Query audit_log looking for same user_id with rapid entries", "Identify overlapping sessions accessing different resource types", "Report suspicious patterns"],
   ["Look for same user_id with entries seconds apart in different contexts",
    "Self-join audit_log on user_id with timestamp proximity"],
   sql="SELECT a1.user_id, a1.timestamp AS time1, a2.timestamp AS time2, a1.resource_id AS resource1, a2.resource_id AS resource2 FROM audit_log a1 JOIN audit_log a2 ON a1.user_id=a2.user_id AND a1.log_id < a2.log_id AND ABS(julianday(a1.timestamp)-julianday(a2.timestamp))*86400 < 60 AND a1.resource_id != a2.resource_id ORDER BY a1.user_id, a1.timestamp",
   difficulty="advanced", roles=["compliance_officer", "system_administrator"])

_s("Patient Consent Compliance Check",
   "Regulatory requires verifying that patient consent records exist for all patients with encounters. Identify patients missing consent documentation.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console", "List patients with encounters", "Check audit_log for consent-related actions", "Find patients with no consent record"],
   ["Look for 'consent' actions in audit_log",
    "LEFT JOIN to find patients without consent entries"],
   sql=None,
   difficulty="intermediate", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Audit Log Completeness Assessment",
   "Security governance needs to verify the audit log is capturing all required events. Check for gaps or periods without any log entries.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console", "Analyze audit_log timestamp distribution", "Identify date gaps where no entries exist", "Report coverage metrics"],
   ["Group by DATE(timestamp) to find active days",
    "Use a date range to identify missing days"],
   sql="SELECT DATE(timestamp) AS log_date, COUNT(*) AS entries FROM audit_log GROUP BY DATE(timestamp) ORDER BY log_date",
   difficulty="intermediate", roles=["compliance_officer", "system_administrator"])

_s("High-Volume Record Access Investigation",
   "A user has been flagged for accessing an unusually high number of patient records. Investigate user access patterns over the last 7 days.",
   "Compliance", ["sql", "audit"], 30,
   ["Open Audit Workbench", "Query top users by access volume", "Analyze the flagged user's access pattern", "Determine if access is appropriate"],
   ["Count accesses per user per day for the last 7 days",
    "Compare against departmental averages"],
   sql="SELECT user_id, DATE(timestamp) AS access_date, COUNT(*) AS daily_accesses, COUNT(DISTINCT resource_id) AS unique_records FROM audit_log WHERE timestamp >= datetime('now','-7 days') GROUP BY user_id, DATE(timestamp) HAVING COUNT(*) > 50 ORDER BY daily_accesses DESC",
   difficulty="advanced", roles=["compliance_officer", "system_administrator"])

_s("Research Data Access Audit",
   "IRB needs to verify that research personnel are only accessing data approved by their protocol. Review research-related access in the audit log.",
   "Compliance", ["sql", "audit"], 30,
   ["Open Audit Workbench", "Filter audit_log for research-related actions", "Cross-reference with approved protocols", "Identify unauthorized research access"],
   ["Look for actions containing 'research' or 'study'",
    "Verify accessed patients are within approved cohorts"],
   sql=None,
   difficulty="advanced", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Data Retention Policy Compliance",
   "Records management needs to verify compliance with data retention policies. Identify records that have exceeded the retention period.",
   "Compliance", ["sql"], 20,
   ["Open SQL Console", "Calculate age of records in each table", "Compare against retention policy limits", "Report records due for archival"],
   ["Use julianday('now') - julianday(date_column) for record age",
    "Typical retention: 7 years (2555 days) for medical records"],
   sql="SELECT 'encounters' AS table_name, COUNT(*) AS records_past_retention FROM encounters WHERE julianday('now')-julianday(admission_date) > 2555 UNION ALL SELECT 'audit_log', COUNT(*) FROM audit_log WHERE julianday('now')-julianday(timestamp) > 2555",
   difficulty="intermediate", roles=["compliance_officer", "system_administrator"])

_s("Emergency Access Protocol Review",
   "Compliance needs to review all emergency department encounters where providers accessed records of patients not directly assigned to them.",
   "Compliance", ["sql", "audit"], 35,
   ["Open SQL Console and Audit Workbench", "Identify ED encounters and their assigned providers", "Cross-reference with audit_log access", "Flag access by non-assigned providers"],
   ["Join encounters (Emergency type) with their attending_provider_id",
    "Compare against audit_log user_id to find non-assigned access"],
   sql=None,
   difficulty="advanced", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("HIPAA Training Compliance Gap Analysis",
   "HR needs to identify users in the audit log who may not have completed required HIPAA training. Find active users with high access volume.",
   "Compliance", ["sql", "audit", "report"], 20,
   ["Open SQL Console", "Identify all unique users in recent audit_log", "Determine access volume per user", "Generate list for HR training verification"],
   ["SELECT DISTINCT user_id from audit_log for active user list",
    "Count accesses per user for priority ranking"],
   sql="SELECT user_id, COUNT(*) AS total_accesses, COUNT(DISTINCT DATE(timestamp)) AS active_days FROM audit_log WHERE timestamp >= datetime('now','-90 days') GROUP BY user_id ORDER BY total_accesses DESC",
   difficulty="beginner", roles=["compliance_officer"])

_s("Security Incident Response: Unauthorized Access Review",
   "A security incident has been reported. Analyze all access for a specific user in the last 48 hours to determine the scope of potential unauthorized access.",
   "Compliance", ["sql", "audit"], 35,
   ["Open Audit Workbench", "Pull all audit entries for the flagged user", "Map accessed resources chronologically", "Identify any sensitive or unusual access patterns"],
   ["Filter audit_log WHERE timestamp >= datetime('now','-48 hours')",
    "Look for access to VIP patients, executive records, or large data exports"],
   sql=None,
   difficulty="advanced", roles=["compliance_officer", "system_administrator"])

_s("Monthly HIPAA Compliance Dashboard Data",
   "The compliance officer needs monthly metrics: total access events, unique users, after-hours access count, and high-volume access alerts.",
   "Compliance", ["sql", "audit", "report"], 25,
   ["Open SQL Console", "Calculate each metric from audit_log", "Filter to current month", "Compile into dashboard format"],
   ["Multiple aggregate queries against audit_log",
    "Use CASE statements or UNION ALL for combined metrics"],
   sql="SELECT 'total_events' AS metric, COUNT(*) AS value FROM audit_log WHERE strftime('%Y-%m',timestamp)=strftime('%Y-%m','now') UNION ALL SELECT 'unique_users', COUNT(DISTINCT user_id) FROM audit_log WHERE strftime('%Y-%m',timestamp)=strftime('%Y-%m','now') UNION ALL SELECT 'after_hours', COUNT(*) FROM audit_log WHERE strftime('%Y-%m',timestamp)=strftime('%Y-%m','now') AND (CAST(strftime('%H',timestamp) AS INTEGER)>=22 OR CAST(strftime('%H',timestamp) AS INTEGER)<6)",
   difficulty="intermediate", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Vendor Access Monitoring",
   "IT governance needs to monitor third-party vendor access to clinical systems. Identify vendor user accounts and their access patterns in the audit log.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console", "Identify vendor-style user_ids (often prefixed or patterned)", "Analyze their access scope and frequency", "Compare against vendor access agreements"],
   ["Vendor accounts may have special prefixes like 'VND_' or 'EXT_'",
    "Check for access to tables beyond their contracted scope"],
   sql="SELECT user_id, COUNT(*) AS total_accesses, COUNT(DISTINCT resource_type) AS resource_types, COUNT(DISTINCT resource_id) AS unique_resources, MIN(timestamp) AS first_seen, MAX(timestamp) AS last_seen FROM audit_log WHERE user_id LIKE 'VND_%' OR user_id LIKE 'EXT_%' GROUP BY user_id ORDER BY total_accesses DESC",
   difficulty="intermediate", roles=["compliance_officer", "system_administrator"])

_s("Patient Right of Access Request Fulfillment",
   "A patient has requested a copy of all their medical records under HIPAA Right of Access. Compile a complete data extraction for patient {mrn}.",
   "Compliance", ["sql", "ehr", "report"], 40,
   ["Query all encounters for the patient", "Pull all diagnoses, medications, labs, and vitals", "Compile audit trail of record access", "Format as complete medical record extract"],
   ["Query each clinical table WHERE patient_mrn = '{mrn}'",
    "Include audit_log entries for this patient's records"],
   sql=None,
   difficulty="advanced", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Audit Trail Integrity Verification",
   "Security governance needs to verify the audit trail hasn't been tampered with. Check for sequential log_id gaps that might indicate deleted entries.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console", "Check log_id sequence for gaps", "Identify missing IDs", "Verify timestamp continuity"],
   ["Self-join audit_log to find where log_id + 1 doesn't exist",
    "Large gaps may indicate deleted records"],
   sql="SELECT a1.log_id AS before_gap, a1.log_id + 1 AS missing_start, MIN(a2.log_id) - 1 AS missing_end FROM audit_log a1 LEFT JOIN audit_log a2 ON a2.log_id > a1.log_id WHERE NOT EXISTS (SELECT 1 FROM audit_log a3 WHERE a3.log_id = a1.log_id + 1) AND a2.log_id IS NOT NULL GROUP BY a1.log_id LIMIT 20",
   difficulty="advanced", roles=["compliance_officer", "system_administrator"])


# =========================================================================
# EHR NAVIGATION (76-100)
# =========================================================================

_s("Review Patient Chart for {mrn}",
   "The attending has asked you to prepare a comprehensive chart review for patient {mrn}. Navigate the EHR to compile demographics, encounters, diagnoses, medications, labs, and vitals.",
   "EHR Navigation", ["ehr", "sql"], 30,
   ["Open EHR Viewer for patient {mrn}", "Review demographics panel", "Navigate to encounter history", "Review medications and active diagnoses", "Check recent lab results and vitals"],
   ["Start with patient lookup by MRN",
    "Check each section systematically: demographics, encounters, diagnoses, meds, labs, vitals"],
   sql=None,
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Medication Reconciliation for {mrn}",
   "Perform medication reconciliation for patient {mrn}. Compare current inpatient medications with their documented outpatient medication list.",
   "EHR Navigation", ["ehr", "sql"], 30,
   ["Open EHR Viewer for patient {mrn}", "Review current inpatient medications", "Check for outpatient medication history", "Identify discrepancies", "Document reconciliation findings"],
   ["Look at medications tied to the current vs. prior encounters",
    "Flag any medications that appear discontinued without documentation"],
   sql="SELECT m.medication_name, m.dosage, m.route, m.frequency, m.start_date, e.encounter_type FROM medications m JOIN encounters e ON m.encounter_id=e.encounter_id WHERE m.patient_mrn='{mrn}' ORDER BY m.start_date DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Verify Lab Result Acknowledgment for {dept}",
   "Quality assurance needs to verify that critical lab results in {dept} are being acknowledged promptly. Check for unacknowledged abnormal results.",
   "EHR Navigation", ["ehr", "sql", "audit"], 25,
   ["Open SQL Console to identify abnormal lab results", "Cross-reference with audit_log for acknowledgment actions", "Identify results without acknowledgment", "Report unacknowledged results by age"],
   ["Abnormal results are outside reference range",
    "Look for 'acknowledge' or 'review' actions in audit_log tied to the result"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Navigate Problem List for {mrn}",
   "The care coordinator needs to review and validate the problem list for patient {mrn}. Identify active diagnoses and check for any that may need updating.",
   "EHR Navigation", ["ehr", "sql", "coding"], 20,
   ["Open EHR Viewer for patient {mrn}", "Navigate to diagnosis history", "Cross-reference with encounter diagnoses", "Identify any stale or resolved problems"],
   ["Compare active diagnoses against recent encounter diagnoses",
    "Look for diagnoses not seen in recent encounters that may be resolved"],
   sql="SELECT dx.icd10_code, dx.description, MAX(dx.diagnosed_date) AS last_diagnosed, COUNT(*) AS times_diagnosed FROM diagnoses dx WHERE dx.patient_mrn='{mrn}' GROUP BY dx.icd10_code, dx.description ORDER BY last_diagnosed DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Track Order Status Across Departments",
   "A care team member needs to track the status of pending orders for a patient across multiple departments. Review the medication and lab order trail.",
   "EHR Navigation", ["ehr", "sql"], 25,
   ["Open EHR Viewer", "Review pending medication orders", "Check pending lab orders", "Track order flow across departments", "Note any delays"],
   ["Check medications with recent start_dates and active status",
    "Check lab_results for pending or recent orders"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Review Discharge Instructions for {dept}",
   "Nursing leadership in {dept} wants to audit discharge instructions. Review recent discharges and verify that complete instructions were documented.",
   "EHR Navigation", ["ehr", "sql", "audit"], 25,
   ["Query recent discharges from {dept}", "Open EHR for each patient", "Check for discharge documentation", "Verify completeness of instructions"],
   ["Filter encounters with recent discharge dates in {dept}",
    "Look for documentation actions in audit_log near discharge time"],
   sql="SELECT e.encounter_id, p.mrn, p.first_name||' '||p.last_name AS patient, e.discharge_date FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn JOIN departments d ON e.department_id=d.dept_id WHERE d.dept_name='{dept}' AND e.discharge_date IS NOT NULL ORDER BY e.discharge_date DESC LIMIT 20",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Locate and Review Allergies for Patient {mrn}",
   "Before a procedure, the anesthesiologist needs a complete allergy review for patient {mrn}. Navigate the EHR and compile all documented allergies.",
   "EHR Navigation", ["ehr"], 15,
   ["Open EHR Viewer for patient {mrn}", "Navigate to allergy section", "Review all documented allergies", "Note severity and reactions"],
   ["Allergies are typically in the patient demographics or a dedicated section",
    "Check for drug allergies, food allergies, and environmental allergies"],
   sql=None,
   difficulty="beginner", roles=["clinical_staff", "clinical_informatics_analyst"])

_s("Verify Provider Signature Status for {dept}",
   "Medical records needs to verify that all clinical documents in {dept} have been properly signed by the attending provider. Find unsigned documents.",
   "EHR Navigation", ["ehr", "sql", "audit"], 30,
   ["Query recent encounters in {dept}", "Check audit_log for signature actions", "Cross-reference encounters with signatures", "List encounters missing provider signatures"],
   ["Look for 'sign' or 'authenticate' actions in audit_log",
    "Compare encounter list against signed-encounter list"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Patient Transfer Workflow Review",
   "A patient is being transferred between departments. Navigate the EHR to verify transfer orders, receiving department acceptance, and continuity of care documentation.",
   "EHR Navigation", ["ehr", "sql"], 25,
   ["Open EHR Viewer for the patient", "Review transfer orders", "Verify receiving department documentation", "Check medication continuity across transfer", "Review vitals around transfer time"],
   ["Look for encounters in different departments for the same patient within 24 hours",
    "Check that medications and orders carried over"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("EHR Downtime Procedure Verification",
   "Test the EHR downtime procedures by verifying that essential patient data can be retrieved using SQL Console when the main EHR viewer is unavailable.",
   "EHR Navigation", ["sql"], 30,
   ["Simulate EHR downtime by using only SQL Console", "Retrieve patient demographics for {mrn}", "Pull active medications", "Get recent lab results and vitals"],
   ["Practice SQL queries for each data type",
    "Build queries that a clinician could use during actual downtime"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Compile Pre-Op Checklist Data for {mrn}",
   "The surgical team needs pre-op data for patient {mrn}: demographics, allergies, current medications, recent labs, and vital signs.",
   "EHR Navigation", ["ehr", "sql"], 25,
   ["Open EHR Viewer for patient {mrn}", "Collect patient demographics", "Review current medications", "Pull most recent labs", "Check latest vitals"],
   ["Query each relevant table for the patient's MRN",
    "Compile results into a structured pre-op summary"],
   sql=None,
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Investigate Clinical Alert Fatigue in {dept}",
   "Clinical informatics has received complaints about alert fatigue in {dept}. Review the frequency and types of clinical alerts generated.",
   "EHR Navigation", ["sql", "audit"], 30,
   ["Query audit_log for alert-related actions in {dept}", "Categorize alerts by type", "Calculate alert frequency per user per shift", "Identify the most common alert types"],
   ["Look for 'alert' actions in audit_log",
    "High frequency suggests potential fatigue issues"],
   sql="SELECT user_id, COUNT(*) AS alert_count, COUNT(DISTINCT DATE(timestamp)) AS active_days FROM audit_log WHERE LOWER(action) LIKE '%alert%' AND timestamp >= datetime('now','-30 days') GROUP BY user_id ORDER BY alert_count DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst"])

_s("Verify Medication Administration Records for {mrn}",
   "Nursing needs to verify that all ordered medications for patient {mrn} have corresponding administration records in the EHR.",
   "EHR Navigation", ["ehr", "sql"], 25,
   ["Open EHR for patient {mrn}", "List all ordered medications", "Check for administration timestamps", "Identify any missed doses"],
   ["Compare medication orders against audit_log for administration actions",
    "Look for temporal gaps in scheduled medications"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Historical Chart Review for Research",
   "A researcher needs to extract structured data from the EHR for a retrospective chart review of patients with {dx_desc}. Navigate the system to compile the dataset.",
   "EHR Navigation", ["ehr", "sql", "report"], 40,
   ["Identify the patient cohort with {dx_desc}", "Design the data extraction query", "Navigate EHR to verify data accuracy for sample patients", "Generate the research dataset"],
   ["Start with diagnoses WHERE description LIKE '%{dx_desc}%'",
    "Include demographics, encounters, labs, medications for the cohort"],
   sql="SELECT p.mrn, p.gender, ROUND((julianday('now')-julianday(p.dob))/365.25) AS age, e.admission_date, e.discharge_date, dx.icd10_code, dx.description FROM patients p JOIN diagnoses dx ON p.mrn=dx.patient_mrn JOIN encounters e ON dx.encounter_id=e.encounter_id WHERE LOWER(dx.description) LIKE LOWER('%{dx_desc}%') ORDER BY p.mrn, e.admission_date",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Validate Clinical Decision Support Rules",
   "IT has deployed new clinical decision support rules. Test them by reviewing how the system responds when accessing patient records with specific conditions.",
   "EHR Navigation", ["ehr", "sql", "audit"], 35,
   ["Identify patients with conditions that should trigger CDS rules", "Navigate EHR to their records", "Document whether alerts fired", "Check audit_log for CDS events"],
   ["Find patients with specific diagnoses or medication combinations",
    "CDS events appear in audit_log with action containing 'cds' or 'alert'"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst"])

_s("Patient Portal Message Review",
   "The patient engagement team wants to understand portal usage patterns. Review audit logs for patient portal access and message activities.",
   "EHR Navigation", ["sql", "audit"], 20,
   ["Query audit_log for portal-related actions", "Analyze message volume and response times", "Identify departments with high portal activity", "Report engagement metrics"],
   ["Look for actions containing 'portal' or 'message'",
    "Calculate time between patient messages and provider responses"],
   sql="SELECT DATE(timestamp) AS date, COUNT(*) AS portal_events FROM audit_log WHERE LOWER(action) LIKE '%portal%' OR LOWER(action) LIKE '%message%' GROUP BY DATE(timestamp) ORDER BY date DESC LIMIT 30",
   difficulty="beginner", roles=["clinical_informatics_analyst"])

_s("EHR Workflow Efficiency Analysis",
   "Informatics leadership wants to measure EHR workflow efficiency by analyzing the time clinicians spend per patient record access.",
   "EHR Navigation", ["sql", "audit"], 35,
   ["Query audit_log to identify record open and close events per user", "Calculate time spent per patient chart", "Aggregate by department and role", "Identify efficiency improvement opportunities"],
   ["Look for pairs of 'open' and 'close' actions for the same resource",
    "Calculate duration between open/close timestamps"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Verify Clinical Note Completion Rates",
   "Quality assurance needs to measure clinical note completion rates by department. Identify encounters without corresponding documentation.",
   "EHR Navigation", ["sql", "audit", "report"], 25,
   ["Query encounters from the last month", "Check audit_log for documentation actions per encounter", "Calculate completion rate by department", "Report departments below threshold"],
   ["Count encounters vs encounters with 'note' or 'document' actions in audit_log",
    "GROUP BY department for comparison"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Navigate Care Plan for Chronic Disease Patient",
   "The care management team needs to review the care plan for a chronic disease patient ({mrn}). Navigate the EHR to compile their full care management picture.",
   "EHR Navigation", ["ehr", "sql"], 30,
   ["Open EHR Viewer for patient {mrn}", "Review chronic diagnoses", "Check medication adherence through refill patterns", "Review lab trends over time", "Identify care gaps"],
   ["Look for chronic condition codes (diabetes E11, hypertension I10, etc.)",
    "Check for regular lab monitoring and medication continuity"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Assess EHR Usability for New Module",
   "A new EHR module has been deployed. Evaluate its adoption by reviewing usage patterns in the audit log and collecting user feedback data.",
   "EHR Navigation", ["sql", "audit"], 25,
   ["Query audit_log for actions related to the new module", "Analyze adoption rates over time", "Identify power users vs non-adopters", "Compare with pre-deployment baseline"],
   ["Look for new action types that appeared after deployment",
    "Track unique users per day for adoption curves"],
   sql="SELECT DATE(timestamp) AS date, COUNT(DISTINCT user_id) AS unique_users, COUNT(*) AS total_actions FROM audit_log WHERE timestamp >= datetime('now','-30 days') GROUP BY DATE(timestamp) ORDER BY date",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Emergency Department Triage Navigation",
   "ED management wants to review triage documentation efficiency. Navigate the system to evaluate how quickly triage data is entered after patient arrival.",
   "EHR Navigation", ["ehr", "sql", "audit"], 30,
   ["Query ED encounters from the last week", "Check for vitals entry timestamps relative to admission time", "Calculate triage-to-documentation time", "Report average times by shift"],
   ["Compare encounter admission_date with first vitals recorded_at",
    "Group by time of day to identify shift-based patterns"],
   sql="SELECT e.encounter_id, e.admission_date, MIN(v.recorded_at) AS first_vital, ROUND((julianday(MIN(v.recorded_at))-julianday(e.admission_date))*1440,1) AS minutes_to_triage FROM encounters e LEFT JOIN vitals v ON e.encounter_id=v.encounter_id WHERE e.encounter_type='Emergency' AND e.admission_date >= datetime('now','-7 days') GROUP BY e.encounter_id ORDER BY minutes_to_triage DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Identify Patients Seen by Multiple Providers",
   "Care coordination wants to find patients who have been seen by 3 or more distinct providers. Include MRN, patient name, and provider count.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console", "Count distinct providers per patient from encounters", "Filter HAVING COUNT >= 3", "Include patient name"],
   ["COUNT(DISTINCT attending_provider_id) per patient_mrn",
    "HAVING COUNT(DISTINCT attending_provider_id) >= 3"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, COUNT(DISTINCT e.attending_provider_id) AS provider_count FROM patients p JOIN encounters e ON p.mrn=e.patient_mrn GROUP BY p.mrn HAVING COUNT(DISTINCT e.attending_provider_id) >= 3 ORDER BY provider_count DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

# ---- Additional Data Quality ----

_s("Diagnoses Without Matching Patient Records",
   "Data governance found diagnosis records that reference MRNs not in the patients table. Identify and quantify these orphaned records.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Left join diagnoses to patients on patient_mrn", "Filter where patient is missing", "Count orphaned records"],
   ["LEFT JOIN patients ON diagnoses.patient_mrn = patients.mrn",
    "WHERE patients.mrn IS NULL"],
   sql="SELECT dx.patient_mrn, COUNT(*) AS orphaned_dx FROM diagnoses dx LEFT JOIN patients p ON dx.patient_mrn=p.mrn WHERE p.mrn IS NULL GROUP BY dx.patient_mrn ORDER BY orphaned_dx DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Medication Records with Invalid Provider References",
   "Pharmacy informatics needs to find medication records that reference a provider not in the providers table.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Left join medications to providers", "Filter where provider is missing", "Count affected prescriptions"],
   ["LEFT JOIN providers ON medications.prescribing_provider_id = providers.provider_id",
    "WHERE providers.provider_id IS NULL"],
   sql="SELECT m.medication_id, m.medication_name, m.patient_mrn, m.prescribing_provider_id FROM medications m LEFT JOIN providers pr ON m.prescribing_provider_id=pr.provider_id WHERE pr.provider_id IS NULL",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounters with Same-Day Admission Across Departments",
   "Registration has flagged patients admitted to multiple departments on the same day. This may indicate errors or same-day transfers.",
   "Data Quality", ["sql"], 25,
   ["Open SQL Console", "Find patients with multiple encounters on the same date", "Check if they are in different departments", "List potential errors"],
   ["GROUP BY patient_mrn, DATE(admission_date) HAVING COUNT(*) > 1",
    "Check for different department_ids in same-day encounters"],
   sql="SELECT e.patient_mrn, DATE(e.admission_date) AS admit_date, COUNT(*) AS encounters, GROUP_CONCAT(DISTINCT d.dept_name) AS departments FROM encounters e JOIN departments d ON e.department_id=d.dept_id GROUP BY e.patient_mrn, DATE(e.admission_date) HAVING COUNT(*) > 1 ORDER BY encounters DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Vitals Recorded Without Valid Encounter",
   "Find vital sign records that reference an encounter_id not present in the encounters table.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console", "Left join vitals to encounters", "Filter where encounter is missing", "Count orphaned vitals"],
   ["LEFT JOIN encounters ON vitals.encounter_id = encounters.encounter_id",
    "WHERE encounters.encounter_id IS NULL"],
   sql="SELECT v.vital_id, v.encounter_id, v.patient_mrn, v.vital_type, v.value FROM vitals v LEFT JOIN encounters e ON v.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Medications with Inconsistent Patient MRN",
   "Find medication records where the patient_mrn doesn't match the patient_mrn on the associated encounter. This indicates a data linkage issue.",
   "Data Quality", ["sql"], 25,
   ["Open SQL Console", "Join medications with encounters on encounter_id", "Compare patient_mrn fields", "Report mismatches"],
   ["JOIN medications to encounters on encounter_id",
    "WHERE medications.patient_mrn != encounters.patient_mrn"],
   sql="SELECT m.medication_id, m.medication_name, m.patient_mrn AS med_mrn, e.patient_mrn AS enc_mrn, m.encounter_id FROM medications m JOIN encounters e ON m.encounter_id=e.encounter_id WHERE m.patient_mrn != e.patient_mrn",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

# ---- Additional Compliance ----

_s("Access Pattern Anomaly Detection",
   "Security wants to detect anomalous access patterns. Find users whose daily access count exceeds 3 standard deviations above the mean.",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console", "Calculate daily access counts per user", "Determine mean and standard deviation", "Flag anomalous days"],
   ["Calculate average daily access per user",
    "3x the average is a simple anomaly threshold"],
   sql="SELECT user_id, DATE(timestamp) AS access_date, COUNT(*) AS daily_count FROM audit_log GROUP BY user_id, DATE(timestamp) HAVING COUNT(*) > (SELECT AVG(cnt)*3 FROM (SELECT COUNT(*) AS cnt FROM audit_log GROUP BY user_id, DATE(timestamp))) ORDER BY daily_count DESC LIMIT 20",
   difficulty="advanced", roles=["compliance_officer", "system_administrator"])

_s("Sensitive Record Access Monitoring",
   "VIP patients require enhanced access monitoring. Generate a report of all access to records for patients over age 90, who may include community leaders.",
   "Compliance", ["sql", "audit"], 25,
   ["Identify patients over age 90", "Query audit_log for access to their records", "List all users who accessed those records", "Report access frequency"],
   ["Calculate age from DOB to find elderly patients",
    "Match patient MRNs against audit_log resource_ids"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, al.user_id, COUNT(*) AS access_count, MAX(al.timestamp) AS last_access FROM patients p JOIN audit_log al ON p.mrn=al.resource_id WHERE (julianday('now')-julianday(p.dob))/365.25 >= 90 GROUP BY p.mrn, al.user_id ORDER BY access_count DESC",
   difficulty="intermediate", roles=["compliance_officer"])

_s("Audit Log Action Type Inventory",
   "IT governance needs a complete inventory of all action types in the audit log to ensure all critical actions are being captured.",
   "Compliance", ["sql", "audit"], 15,
   ["Open SQL Console", "Query distinct action types from audit_log", "Count occurrences of each", "Identify any unexpected action types"],
   ["SELECT DISTINCT action FROM audit_log",
    "GROUP BY action ORDER BY COUNT(*) DESC"],
   sql="SELECT action, COUNT(*) AS occurrences, COUNT(DISTINCT user_id) AS unique_users, MIN(timestamp) AS first_seen, MAX(timestamp) AS last_seen FROM audit_log GROUP BY action ORDER BY occurrences DESC",
   difficulty="beginner", roles=["compliance_officer", "system_administrator"])

_s("Weekend Access Pattern Compliance Review",
   "Review weekend access patterns to ensure they align with scheduled on-call coverage. Weekend access by non-on-call staff may indicate policy violations.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console", "Filter audit_log to weekend days", "Group by user to see weekend access patterns", "Compare with typical weekday patterns"],
   ["Weekend: strftime('%w', timestamp) IN ('0','6')",
    "Compare weekend vs weekday unique user counts"],
   sql="SELECT user_id, SUM(CASE WHEN CAST(strftime('%w',timestamp) AS INTEGER) IN (0,6) THEN 1 ELSE 0 END) AS weekend_access, SUM(CASE WHEN CAST(strftime('%w',timestamp) AS INTEGER) NOT IN (0,6) THEN 1 ELSE 0 END) AS weekday_access, COUNT(*) AS total FROM audit_log WHERE timestamp >= datetime('now','-30 days') GROUP BY user_id HAVING weekend_access > 0 ORDER BY weekend_access DESC",
   difficulty="intermediate", roles=["compliance_officer", "system_administrator"])

_s("Cross-Patient Access Review for Single User",
   "A compliance audit requires reviewing how many unique patient records a specific user accessed in one day. Flag users exceeding 50 unique patients.",
   "Compliance", ["sql", "audit"], 20,
   ["Open SQL Console", "Count unique resource_ids per user per day", "Flag days exceeding threshold", "Report flagged users"],
   ["GROUP BY user_id, DATE(timestamp)",
    "HAVING COUNT(DISTINCT resource_id) > 50"],
   sql="SELECT user_id, DATE(timestamp) AS access_date, COUNT(DISTINCT resource_id) AS unique_records FROM audit_log WHERE timestamp >= datetime('now','-30 days') GROUP BY user_id, DATE(timestamp) HAVING COUNT(DISTINCT resource_id) > 50 ORDER BY unique_records DESC",
   difficulty="intermediate", roles=["compliance_officer"])

# ---- Additional EHR Navigation ----

_s("Review Patient Immunization History in EHR",
   "The public health team needs to review immunization records for patient {mrn}. Navigate the EHR to compile their vaccination history.",
   "EHR Navigation", ["ehr", "sql"], 20,
   ["Open EHR Viewer for patient {mrn}", "Navigate to immunization section", "Review all documented vaccinations", "Note any overdue immunizations"],
   ["Check medications table for vaccine-related entries",
    "Look for immunization-related diagnoses or procedure codes"],
   sql=None,
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("EHR Template Customization Review",
   "IT received requests for EHR template changes. Review current template usage from audit logs and identify the most and least used templates.",
   "EHR Navigation", ["sql", "audit"], 25,
   ["Query audit_log for template-related actions", "Rank templates by usage frequency", "Identify unused templates for retirement", "Document findings for IT"],
   ["Filter actions containing 'template'",
    "GROUP BY template identifier or action detail"],
   sql="SELECT action, COUNT(*) AS usage, COUNT(DISTINCT user_id) AS users FROM audit_log WHERE LOWER(action) LIKE '%template%' GROUP BY action ORDER BY usage DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Navigate Multi-Visit Patient History",
   "A specialist needs to review the complete visit history for a frequently seen patient ({mrn}). Navigate through multiple encounters to build a clinical summary.",
   "EHR Navigation", ["ehr", "sql"], 30,
   ["Open EHR Viewer for patient {mrn}", "Review all encounter dates and types", "Compile diagnoses across visits", "Note medication changes over time", "Summarize the clinical trajectory"],
   ["Use SQL to pull encounter list first, then navigate in EHR",
    "Track diagnosis and medication changes chronologically"],
   sql="SELECT e.encounter_id, e.admission_date, e.discharge_date, e.encounter_type, d.dept_name, GROUP_CONCAT(DISTINCT dx.icd10_code) AS diagnoses FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.patient_mrn='{mrn}' GROUP BY e.encounter_id ORDER BY e.admission_date DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("EHR System Performance Assessment via User Patterns",
   "IT wants to assess EHR performance by analyzing user interaction patterns. Look for periods of unusually low activity that might indicate system slowdowns.",
   "EHR Navigation", ["sql", "audit"], 25,
   ["Query audit_log activity by hour", "Identify hours with unusually low activity", "Compare against typical activity levels", "Flag potential performance issues"],
   ["Unusually low activity during business hours may indicate system issues",
    "Compare each hour against the hourly average"],
   sql="SELECT strftime('%Y-%m-%d %H:00', timestamp) AS hour, COUNT(*) AS activity FROM audit_log WHERE timestamp >= datetime('now','-7 days') GROUP BY strftime('%Y-%m-%d %H', timestamp) ORDER BY activity ASC LIMIT 20",
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

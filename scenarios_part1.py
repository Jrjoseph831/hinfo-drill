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


# ---------------------------------------------------------------------------
# DATA EXTRACTION  (scenarios 1-25)
# ---------------------------------------------------------------------------

_s("Pull 30-Day Readmission Rate for {dept}",
   "Calculate the 30-day readmission rate for {dept}. A readmission is a "
   "patient with more than one encounter within 30 days of discharge.",
   "Data Extraction", ["sql"], 30,
   ["Open SQL Console",
    "Identify encounters and departments tables",
    "Write a self-join on encounters for readmissions within 30 days",
    "Calculate the percentage of readmitted patients"],
   ["Self-join encounters ON patient_mrn",
    "Filter by dept_name = '{dept}'"],
   sql=("SELECT ROUND(COUNT(DISTINCT r.patient_mrn)*100.0 / "
        "NULLIF(COUNT(DISTINCT e.patient_mrn),0), 2) "
        "FROM encounters e "
        "JOIN departments d ON e.department_id=d.dept_id "
        "LEFT JOIN encounters r ON e.patient_mrn=r.patient_mrn "
        "AND r.encounter_id != e.encounter_id "
        "AND r.admission_date BETWEEN e.discharge_date "
        "AND datetime(e.discharge_date, '+30 days') "
        "WHERE d.dept_name='{dept}' AND e.discharge_date IS NOT NULL"),
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Count Active Patients by Gender in {dept}",
   "Retrieve the count of active patients grouped by gender for the "
   "{dept} department.",
   "Data Extraction", ["sql"], 15,
   ["Open SQL Console",
    "Join patients to encounters and departments",
    "Group by gender and count distinct MRNs",
    "Filter for {dept}"],
   ["Use COUNT(DISTINCT p.mrn)",
    "Join on department_id to filter by dept_name"],
   sql=("SELECT p.gender, COUNT(DISTINCT p.mrn) AS patient_count "
        "FROM patients p "
        "JOIN encounters e ON p.mrn=e.patient_mrn "
        "JOIN departments d ON e.department_id=d.dept_id "
        "WHERE d.dept_name='{dept}' "
        "GROUP BY p.gender"),
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("List Top 10 Diagnoses by Frequency",
   "Find the 10 most frequently recorded ICD-10 diagnoses across all "
   "encounters. Include the code, description, and count.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console",
    "Query the diagnoses table",
    "Group by icd10_code and description",
    "Order by count descending and limit to 10"],
   ["GROUP BY icd10_code, description",
    "Use ORDER BY COUNT(*) DESC LIMIT 10"],
   sql=("SELECT icd10_code, description, COUNT(*) AS dx_count "
        "FROM diagnoses "
        "GROUP BY icd10_code, description "
        "ORDER BY dx_count DESC LIMIT 10"),
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Average Length of Stay for {dx_code} - {dx_desc}",
   "Calculate the average length of stay in days for patients diagnosed "
   "with {dx_code} ({dx_desc}).",
   "Data Extraction", ["sql"], 25,
   ["Open SQL Console",
    "Join encounters with diagnoses",
    "Compute length of stay as discharge_date - admission_date",
    "Filter by icd10_code = '{dx_code}' and average the result"],
   ["Use julianday(discharge_date) - julianday(admission_date)",
    "Exclude encounters where discharge_date IS NULL"],
   sql=("SELECT ROUND(AVG(julianday(e.discharge_date) - "
        "julianday(e.admission_date)), 2) AS avg_los "
        "FROM encounters e "
        "JOIN diagnoses dx ON e.encounter_id=dx.encounter_id "
        "WHERE dx.icd10_code='{dx_code}' "
        "AND e.discharge_date IS NOT NULL"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Retrieve Lab Results for Patient {mrn}",
   "Extract all lab results for patient MRN {mrn}, including test name, "
   "result value, unit, and reference range, ordered by date.",
   "Data Extraction", ["sql"], 15,
   ["Open SQL Console",
    "Query lab_results table filtered by patient_mrn",
    "Order results chronologically"],
   ["Filter with WHERE patient_mrn='{mrn}'",
    "Use ORDER BY result_id or join to encounters for date ordering"],
   sql=("SELECT lr.test_name, lr.result_value, lr.unit, lr.reference_range, "
        "e.admission_date "
        "FROM lab_results lr "
        "JOIN encounters e ON lr.encounter_id=e.encounter_id "
        "WHERE lr.patient_mrn='{mrn}' "
        "ORDER BY e.admission_date"),
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Medication Frequency Report for {dept}",
   "Generate a report of the most commonly prescribed medications in {dept}, "
   "showing medication name and prescription count.",
   "Data Extraction", ["sql", "report"], 25,
   ["Open SQL Console",
    "Join medications, encounters, and departments",
    "Group by medication_name",
    "Order by count descending"],
   ["Join medications to encounters on encounter_id",
    "Filter departments by dept_name = '{dept}'"],
   sql=("SELECT m.medication_name, COUNT(*) AS rx_count "
        "FROM medications m "
        "JOIN encounters e ON m.encounter_id=e.encounter_id "
        "JOIN departments d ON e.department_id=d.dept_id "
        "WHERE d.dept_name='{dept}' "
        "GROUP BY m.medication_name "
        "ORDER BY rx_count DESC"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patients With No Discharge Date",
   "Identify all patients who have encounters without a discharge date, "
   "suggesting they may still be admitted or have data entry issues.",
   "Data Extraction", ["sql"], 15,
   ["Open SQL Console",
    "Query encounters where discharge_date IS NULL",
    "Join to patients for demographics",
    "Review results for patterns"],
   ["WHERE e.discharge_date IS NULL",
    "Consider whether encounter_type matters"],
   sql=("SELECT p.mrn, p.first_name, p.last_name, e.encounter_id, "
        "e.admission_date, d.dept_name "
        "FROM encounters e "
        "JOIN patients p ON e.patient_mrn=p.mrn "
        "JOIN departments d ON e.department_id=d.dept_id "
        "WHERE e.discharge_date IS NULL "
        "ORDER BY e.admission_date"),
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Encounter Volume by Specialty",
   "Show the total number of encounters per provider specialty for the "
   "last 12 months.",
   "Data Extraction", ["sql"], 25,
   ["Open SQL Console",
    "Join encounters to providers",
    "Filter by admission_date within the last 12 months",
    "Group by specialty and count"],
   ["Use providers.specialty for grouping",
    "Date filter: admission_date >= date('now','-12 months')"],
   sql=("SELECT pr.specialty, COUNT(*) AS encounter_count "
        "FROM encounters e "
        "JOIN providers pr ON e.attending_provider_id=pr.provider_id "
        "WHERE e.admission_date >= date('now','-12 months') "
        "GROUP BY pr.specialty "
        "ORDER BY encounter_count DESC"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Vital Signs Trend for Patient {mrn}",
   "Extract all vital sign readings for patient {mrn}, ordered by "
   "recorded_at timestamp, to identify trends.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console",
    "Query vitals table for the given MRN",
    "Order by recorded_at",
    "Review for abnormal patterns"],
   ["Filter WHERE patient_mrn='{mrn}'",
    "Include vital_type and value columns"],
   sql=("SELECT v.vital_type, v.value, v.recorded_at "
        "FROM vitals v "
        "WHERE v.patient_mrn='{mrn}' "
        "ORDER BY v.recorded_at"),
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Encounters by Day of Week for {dept}",
   "Determine which day of the week has the highest admission volume in "
   "{dept} to support staffing decisions.",
   "Data Extraction", ["sql", "report"], 30,
   ["Open SQL Console",
    "Extract the day of week from admission_date",
    "Join to departments and filter",
    "Group and count by day of week",
    "Present findings in a report"],
   ["Use strftime('%w', admission_date) for day extraction",
    "Map numeric day to day name for readability"],
   sql=("SELECT CASE CAST(strftime('%w', e.admission_date) AS INTEGER) "
        "WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday' "
        "WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' "
        "WHEN 5 THEN 'Friday' WHEN 6 THEN 'Saturday' END AS day_name, "
        "COUNT(*) AS admission_count "
        "FROM encounters e "
        "JOIN departments d ON e.department_id=d.dept_id "
        "WHERE d.dept_name='{dept}' "
        "GROUP BY strftime('%w', e.admission_date) "
        "ORDER BY admission_count DESC"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Diabetic Patients on Insulin",
   "List all patients who have a diabetes diagnosis (ICD-10 E11%) and are "
   "currently prescribed an insulin medication.",
   "Data Extraction", ["sql"], 30,
   ["Open SQL Console",
    "Join diagnoses and medications through encounters",
    "Filter diagnoses by E11% and medications by '%insulin%'",
    "Return distinct patient list"],
   ["Use LIKE 'E11%' for diabetes codes",
    "Use LOWER(medication_name) LIKE '%insulin%'"],
   sql=("SELECT DISTINCT p.mrn, p.first_name, p.last_name "
        "FROM patients p "
        "JOIN diagnoses dx ON p.mrn=dx.patient_mrn "
        "JOIN medications m ON p.mrn=m.patient_mrn "
        "WHERE dx.icd10_code LIKE 'E11%' "
        "AND LOWER(m.medication_name) LIKE '%insulin%'"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Monthly Encounter Trend for Past Year",
   "Show the number of encounters per month for the past 12 months to "
   "identify seasonal patterns.",
   "Data Extraction", ["sql", "report"], 25,
   ["Open SQL Console",
    "Extract year-month from admission_date",
    "Filter last 12 months",
    "Group and count by month"],
   ["Use strftime('%Y-%m', admission_date)",
    "Filter admission_date >= date('now','-12 months')"],
   sql=("SELECT strftime('%Y-%m', e.admission_date) AS month, "
        "COUNT(*) AS encounter_count "
        "FROM encounters e "
        "WHERE e.admission_date >= date('now','-12 months') "
        "GROUP BY strftime('%Y-%m', e.admission_date) "
        "ORDER BY month"),
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patients With Abnormal Lab Results",
   "Identify patients whose lab result_value falls outside the "
   "reference_range. List patient MRN, test name, value, and range.",
   "Data Extraction", ["sql"], 35,
   ["Open SQL Console",
    "Parse reference_range into low and high bounds",
    "Compare result_value to bounds",
    "Join to patients for demographics",
    "Return flagged results"],
   ["Reference range is often stored as 'low-high' format",
    "Cast result_value to REAL for comparison"],
   sql=("SELECT lr.patient_mrn, p.first_name, p.last_name, "
        "lr.test_name, lr.result_value, lr.reference_range "
        "FROM lab_results lr "
        "JOIN patients p ON lr.patient_mrn=p.mrn "
        "WHERE CAST(lr.result_value AS REAL) < "
        "CAST(SUBSTR(lr.reference_range, 1, INSTR(lr.reference_range,'-')-1) AS REAL) "
        "OR CAST(lr.result_value AS REAL) > "
        "CAST(SUBSTR(lr.reference_range, INSTR(lr.reference_range,'-')+1) AS REAL)"),
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider {provider} Patient Panel List",
   "Generate the complete patient panel for provider {provider}, "
   "including patient MRN, name, and most recent encounter date.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console",
    "Join encounters to providers and patients",
    "Filter by provider name",
    "Use MAX(admission_date) for most recent encounter"],
   ["Group by patient to get latest encounter",
    "Filter provider by last_name or provider_id"],
   sql=("SELECT p.mrn, p.first_name, p.last_name, "
        "MAX(e.admission_date) AS last_visit "
        "FROM patients p "
        "JOIN encounters e ON p.mrn=e.patient_mrn "
        "JOIN providers pr ON e.attending_provider_id=pr.provider_id "
        "WHERE pr.last_name='{provider}' "
        "GROUP BY p.mrn, p.first_name, p.last_name "
        "ORDER BY last_visit DESC"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Emergency Department Wait Time Analysis",
   "Calculate the average time between admission and the first vital sign "
   "recording for emergency encounters, as a proxy for wait time.",
   "Data Extraction", ["sql", "report"], 35,
   ["Open SQL Console",
    "Filter encounters by encounter_type = 'Emergency'",
    "Find the earliest vital per encounter",
    "Compute time difference from admission to first vital",
    "Average across all emergency encounters"],
   ["Use MIN(v.recorded_at) grouped by encounter_id",
    "Compute difference in minutes using julianday"],
   sql=("SELECT ROUND(AVG((julianday(fv.first_vital) - "
        "julianday(e.admission_date)) * 1440), 2) AS avg_wait_minutes "
        "FROM encounters e "
        "JOIN (SELECT encounter_id, MIN(recorded_at) AS first_vital "
        "FROM vitals GROUP BY encounter_id) fv "
        "ON e.encounter_id=fv.encounter_id "
        "WHERE e.encounter_type='Emergency'"),
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Polypharmacy Report: Patients on 5+ Medications",
   "Find patients currently prescribed 5 or more distinct medications, "
   "which may indicate polypharmacy risk.",
   "Data Extraction", ["sql", "report"], 25,
   ["Open SQL Console",
    "Count distinct medications per patient",
    "Filter for counts >= 5",
    "Join patient demographics"],
   ["Use HAVING COUNT(DISTINCT medication_name) >= 5",
    "Group by patient_mrn"],
   sql=("SELECT p.mrn, p.first_name, p.last_name, "
        "COUNT(DISTINCT m.medication_name) AS med_count "
        "FROM patients p "
        "JOIN medications m ON p.mrn=m.patient_mrn "
        "GROUP BY p.mrn, p.first_name, p.last_name "
        "HAVING med_count >= 5 "
        "ORDER BY med_count DESC"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Diagnosis Co-occurrence: {dx_code} and Comorbidities",
   "For patients diagnosed with {dx_code} ({dx_desc}), find the most "
   "common co-occurring diagnoses.",
   "Data Extraction", ["sql"], 35,
   ["Open SQL Console",
    "Identify patients with the target diagnosis",
    "Find other diagnoses for those patients",
    "Exclude the target diagnosis itself",
    "Rank co-occurring diagnoses by frequency"],
   ["Use a subquery to find patient_mrns with {dx_code}",
    "Exclude the same icd10_code from the outer query"],
   sql=("SELECT dx2.icd10_code, dx2.description, COUNT(*) AS co_count "
        "FROM diagnoses dx2 "
        "WHERE dx2.patient_mrn IN "
        "(SELECT DISTINCT patient_mrn FROM diagnoses "
        "WHERE icd10_code='{dx_code}') "
        "AND dx2.icd10_code != '{dx_code}' "
        "GROUP BY dx2.icd10_code, dx2.description "
        "ORDER BY co_count DESC LIMIT 10"),
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Department Census at a Point in Time",
   "Determine the inpatient census for each department at midnight today, "
   "defined as patients admitted before today who have not yet been discharged.",
   "Data Extraction", ["sql"], 30,
   ["Open SQL Console",
    "Filter encounters admitted before today with no discharge or discharged after today",
    "Group by department",
    "Count patients per department"],
   ["admission_date < date('now') AND (discharge_date IS NULL OR discharge_date >= date('now'))",
    "Join departments for department names"],
   sql=("SELECT d.dept_name, COUNT(*) AS census "
        "FROM encounters e "
        "JOIN departments d ON e.department_id=d.dept_id "
        "WHERE e.admission_date < date('now') "
        "AND (e.discharge_date IS NULL OR e.discharge_date >= date('now')) "
        "GROUP BY d.dept_name "
        "ORDER BY census DESC"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Time to First Medication for {dx_code}",
   "Calculate the average time from admission to first medication "
   "administration for patients diagnosed with {dx_code} ({dx_desc}).",
   "Data Extraction", ["sql"], 35,
   ["Open SQL Console",
    "Join encounters, diagnoses, and medications",
    "Find the earliest medication start_date per encounter",
    "Compute the time difference from admission",
    "Average across relevant encounters"],
   ["Use MIN(m.start_date) grouped by encounter_id",
    "Use julianday for date arithmetic"],
   sql=("SELECT ROUND(AVG((julianday(fm.first_med) - "
        "julianday(e.admission_date)) * 24), 2) AS avg_hours_to_first_med "
        "FROM encounters e "
        "JOIN diagnoses dx ON e.encounter_id=dx.encounter_id "
        "JOIN (SELECT encounter_id, MIN(start_date) AS first_med "
        "FROM medications GROUP BY encounter_id) fm "
        "ON e.encounter_id=fm.encounter_id "
        "WHERE dx.icd10_code='{dx_code}'"),
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Age Distribution of Patients in {dept}",
   "Generate an age distribution (in decade buckets) for all patients "
   "ever seen in {dept}.",
   "Data Extraction", ["sql", "report"], 25,
   ["Open SQL Console",
    "Calculate patient age from dob",
    "Create decade buckets using integer division",
    "Group and count"],
   ["Use (strftime('%Y','now') - strftime('%Y', p.dob)) for age",
    "Integer divide by 10 then multiply by 10 for buckets"],
   sql=("SELECT (CAST((strftime('%Y','now') - strftime('%Y', p.dob)) "
        "AS INTEGER) / 10) * 10 AS age_decade, "
        "COUNT(DISTINCT p.mrn) AS patient_count "
        "FROM patients p "
        "JOIN encounters e ON p.mrn=e.patient_mrn "
        "JOIN departments d ON e.department_id=d.dept_id "
        "WHERE d.dept_name='{dept}' "
        "GROUP BY age_decade ORDER BY age_decade"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Unmatched Lab Results Without Encounters",
   "Find lab results that have no matching encounter record, which may "
   "indicate orphaned data.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console",
    "Left join lab_results to encounters",
    "Filter where the encounter join fails",
    "Review orphaned records"],
   ["Use LEFT JOIN and WHERE e.encounter_id IS NULL",
    "Check for NULL encounter_id in lab_results too"],
   sql=("SELECT lr.result_id, lr.patient_mrn, lr.test_name, "
        "lr.encounter_id "
        "FROM lab_results lr "
        "LEFT JOIN encounters e ON lr.encounter_id=e.encounter_id "
        "WHERE e.encounter_id IS NULL"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("High-Volume Providers With 50+ Encounters",
   "Identify providers who have had 50 or more encounters in the past "
   "6 months, along with their specialty.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console",
    "Join encounters to providers",
    "Filter for last 6 months",
    "Group by provider and apply HAVING clause"],
   ["HAVING COUNT(*) >= 50",
    "Date filter: admission_date >= date('now','-6 months')"],
   sql=("SELECT pr.provider_id, pr.first_name, pr.last_name, "
        "pr.specialty, COUNT(*) AS enc_count "
        "FROM encounters e "
        "JOIN providers pr ON e.attending_provider_id=pr.provider_id "
        "WHERE e.admission_date >= date('now','-6 months') "
        "GROUP BY pr.provider_id, pr.first_name, pr.last_name, pr.specialty "
        "HAVING enc_count >= 50 "
        "ORDER BY enc_count DESC"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounter Type Breakdown for {dept}",
   "Show the distribution of encounter types (Inpatient, Outpatient, "
   "Emergency, etc.) for {dept}.",
   "Data Extraction", ["sql"], 15,
   ["Open SQL Console",
    "Join encounters to departments",
    "Group by encounter_type",
    "Count per type"],
   ["Group by e.encounter_type",
    "Filter d.dept_name='{dept}'"],
   sql=("SELECT e.encounter_type, COUNT(*) AS type_count "
        "FROM encounters e "
        "JOIN departments d ON e.department_id=d.dept_id "
        "WHERE d.dept_name='{dept}' "
        "GROUP BY e.encounter_type "
        "ORDER BY type_count DESC"),
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patients Seen by Multiple Providers",
   "Find patients who have been seen by 3 or more distinct providers in "
   "the last 6 months, which may indicate care fragmentation.",
   "Data Extraction", ["sql"], 30,
   ["Open SQL Console",
    "Join encounters to providers and patients",
    "Filter by date range",
    "Group by patient and count distinct providers",
    "Apply HAVING >= 3"],
   ["COUNT(DISTINCT e.attending_provider_id)",
    "Date filter: admission_date >= date('now','-6 months')"],
   sql=("SELECT p.mrn, p.first_name, p.last_name, "
        "COUNT(DISTINCT e.attending_provider_id) AS provider_count "
        "FROM patients p "
        "JOIN encounters e ON p.mrn=e.patient_mrn "
        "WHERE e.admission_date >= date('now','-6 months') "
        "GROUP BY p.mrn, p.first_name, p.last_name "
        "HAVING provider_count >= 3 "
        "ORDER BY provider_count DESC"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Mortality Rate by Diagnosis Category",
   "Calculate the in-hospital mortality rate grouped by the first letter "
   "of the ICD-10 code (diagnosis category). Mortality is approximated by "
   "encounters with a discharge disposition of 'Expired' or where the patient "
   "has no subsequent encounters after a prolonged stay.",
   "Data Extraction", ["sql", "report"], 40,
   ["Open SQL Console",
    "Join encounters with diagnoses",
    "Group by the first character of icd10_code as category",
    "Calculate ratio of expired encounters to total per category",
    "Order by mortality rate descending"],
   ["Use SUBSTR(dx.icd10_code, 1, 1) for category grouping",
    "If discharge disposition is unavailable, use LOS outliers as a proxy",
    "ICD-10 category letters: A-B Infectious, C Neoplasms, I Circulatory, etc."],
   sql=("SELECT SUBSTR(dx.icd10_code, 1, 1) AS dx_category, "
        "COUNT(DISTINCT e.encounter_id) AS total_encounters, "
        "SUM(CASE WHEN julianday(e.discharge_date) - julianday(e.admission_date) > 30 "
        "THEN 1 ELSE 0 END) AS prolonged_stays, "
        "ROUND(SUM(CASE WHEN julianday(e.discharge_date) - julianday(e.admission_date) > 30 "
        "THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT e.encounter_id), 2) AS prolonged_pct "
        "FROM encounters e "
        "JOIN diagnoses dx ON e.encounter_id=dx.encounter_id "
        "WHERE e.discharge_date IS NOT NULL "
        "GROUP BY SUBSTR(dx.icd10_code, 1, 1) "
        "ORDER BY prolonged_pct DESC"),
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

# ---------------------------------------------------------------------------
# DATA QUALITY  (scenarios 26-50)
# ---------------------------------------------------------------------------

_s("Find Duplicate Patient Records",
   "Identify potential duplicate patient records by finding patients "
   "with the same first name, last name, and date of birth but different MRNs.",
   "Data Quality", ["sql", "ehr"], 30,
   ["Open SQL Console",
    "Self-join patients on first_name, last_name, and dob",
    "Exclude self-matches by MRN",
    "Review potential duplicates"],
   ["Self-join patients p1 JOIN patients p2",
    "Add condition p1.mrn < p2.mrn to avoid double-counting"],
   sql=("SELECT p1.mrn AS mrn1, p2.mrn AS mrn2, "
        "p1.first_name, p1.last_name, p1.dob "
        "FROM patients p1 "
        "JOIN patients p2 ON p1.first_name=p2.first_name "
        "AND p1.last_name=p2.last_name AND p1.dob=p2.dob "
        "AND p1.mrn < p2.mrn"),
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounters With Future Admission Dates",
   "Find encounters where the admission_date is in the future, "
   "indicating a data entry error.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console",
    "Query encounters where admission_date > date('now')",
    "Review flagged records"],
   ["WHERE admission_date > date('now')",
    "Check if these are scheduled encounters or errors"],
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Discharge Before Admission Anomalies",
   "Identify encounters where the discharge_date is before the "
   "admission_date, which is clinically impossible.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console",
    "Query encounters where discharge_date < admission_date",
    "Count and list affected records",
    "Report to data steward"],
   ["WHERE discharge_date < admission_date",
    "Include encounter_id for follow-up"],
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Missing Gender in Patient Records",
   "Find all patient records where the gender field is NULL or empty, "
   "and quantify the scope of the data gap.",
   "Data Quality", ["sql", "report"], 20,
   ["Open SQL Console",
    "Query patients where gender IS NULL or gender = ''",
    "Count total vs. affected records",
    "Calculate the percentage of missing data"],
   ["WHERE gender IS NULL OR gender = ''",
    "Compare to total patient count for percentage"],
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Invalid ICD-10 Code Format Detection",
   "Scan the diagnoses table for ICD-10 codes that do not match the "
   "expected format (letter followed by digits, optional dot and more digits).",
   "Data Quality", ["sql", "coding"], 30,
   ["Open SQL Console",
    "Define the expected ICD-10 regex pattern",
    "Query diagnoses where icd10_code does not match",
    "List invalid codes for remediation"],
   ["ICD-10 format: one letter, two digits, optional dot and up to 4 chars",
    "Use NOT GLOB or LIKE patterns for validation"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Lab Results With Non-Numeric Values",
   "Identify lab results where result_value contains non-numeric data "
   "that cannot be used for trending or analytics.",
   "Data Quality", ["sql"], 25,
   ["Open SQL Console",
    "Attempt to cast result_value and find failures",
    "List affected test names and values",
    "Categorize the types of non-numeric entries"],
   ["Use CAST and check for non-numeric patterns",
    "Common non-numeric entries: 'pending', 'see note', '<10'"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Orphaned Diagnoses Without Valid Patients",
   "Find diagnosis records where the patient_mrn does not match any "
   "existing patient record.",
   "Data Quality", ["sql"], 20,
   ["Open SQL Console",
    "Left join diagnoses to patients",
    "Filter where patient join fails",
    "Count orphaned records"],
   ["LEFT JOIN patients p ON dx.patient_mrn=p.mrn WHERE p.mrn IS NULL",
    "These may indicate deleted patients or integration errors"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Medications With Missing Dosage Information",
   "Identify medication records where the dosage field is NULL or empty, "
   "which may compromise patient safety.",
   "Data Quality", ["sql", "report"], 20,
   ["Open SQL Console",
    "Query medications where dosage IS NULL or empty",
    "Group by medication_name to find patterns",
    "Report affected medications"],
   ["WHERE dosage IS NULL OR dosage = ''",
    "Group by medication_name to see which drugs are most affected"],
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Duplicate Encounter Detection",
   "Find potential duplicate encounters: same patient, same admission "
   "date, same department, but different encounter IDs.",
   "Data Quality", ["sql"], 30,
   ["Open SQL Console",
    "Self-join encounters on patient_mrn, admission_date, department_id",
    "Exclude self-matches",
    "Review results for true duplicates vs. legitimate re-encounters"],
   ["Self-join with e1.encounter_id < e2.encounter_id",
    "Match on patient_mrn, admission_date, and department_id"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Vitals With Implausible Values",
   "Detect vital sign entries with physiologically implausible values "
   "(e.g., heart rate > 300, temperature > 110F, systolic BP > 300).",
   "Data Quality", ["sql"], 30,
   ["Open SQL Console",
    "Define plausible ranges per vital_type",
    "Query for values outside those ranges",
    "List flagged records with patient context",
    "Report findings"],
   ["Use CASE or separate queries per vital_type",
    "Heart rate: 20-250, Temperature: 90-108, Systolic BP: 50-300"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst", "clinical_staff"])

_s("Patients With Impossible Date of Birth",
   "Find patient records where date of birth is in the future or implies "
   "an age over 120 years, indicating data entry errors.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console",
    "Check for dob > date('now') or age > 120",
    "List affected patient records"],
   ["WHERE dob > date('now') OR dob < date('now','-120 years')",
    "Include MRN for follow-up correction"],
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounter-Diagnosis Referential Integrity Check",
   "Verify that every diagnosis record references a valid encounter_id "
   "that exists in the encounters table.",
   "Data Quality", ["sql"], 20,
   ["Open SQL Console",
    "Left join diagnoses to encounters on encounter_id",
    "Filter where the encounter is not found",
    "Count and list orphaned diagnosis records"],
   ["LEFT JOIN encounters e ON dx.encounter_id=e.encounter_id",
    "WHERE e.encounter_id IS NULL"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Records With Missing Credentials",
   "Identify provider records where the credential field is NULL or "
   "empty, which affects display and compliance.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console",
    "Query providers where credential IS NULL or empty",
    "List affected providers",
    "Prepare remediation list"],
   ["WHERE credential IS NULL OR credential = ''",
    "Include provider_id and name for follow-up"],
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "system_administrator"])

_s("Medication-Encounter Referential Integrity",
   "Check that all medications reference valid encounter IDs and valid "
   "prescribing provider IDs.",
   "Data Quality", ["sql"], 25,
   ["Open SQL Console",
    "Left join medications to encounters",
    "Left join medications to providers",
    "Filter for any NULL joins",
    "Report broken references"],
   ["Check both encounter_id and prescribing_provider_id foreign keys",
    "Use OR to combine both broken reference conditions"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Standardize Medication Name Variations",
   "Identify variations in medication naming (e.g., 'Metformin' vs "
   "'metformin HCl' vs 'METFORMIN') that impede accurate reporting.",
   "Data Quality", ["sql", "report"], 35,
   ["Open SQL Console",
    "Query distinct medication names",
    "Use LOWER and TRIM to normalize",
    "Identify clusters of similar names",
    "Propose a mapping table for standardization"],
   ["Use LOWER(TRIM(medication_name)) for normalization",
    "Look for names that share a common root word"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Completeness Audit: Required Fields per Encounter",
   "Audit encounters for completeness by checking how many required "
   "fields (admission_date, department_id, attending_provider_id, "
   "encounter_type) are NULL.",
   "Data Quality", ["sql", "audit"], 30,
   ["Open SQL Console",
    "Count NULLs for each required field",
    "Calculate completeness percentage per field",
    "Generate a summary report"],
   ["Use SUM(CASE WHEN field IS NULL THEN 1 ELSE 0 END) for each field",
    "Divide by total encounters for percentage"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst", "compliance_officer"])

_s("Detect Backdated Encounter Entries",
   "Find encounters where the admission_date is significantly earlier "
   "than when the record was likely created, suggesting backdating. "
   "Use the audit_log for record creation timestamps.",
   "Data Quality", ["sql", "audit"], 35,
   ["Open SQL Console",
    "Join encounters to audit_log where resource_type = 'encounter'",
    "Compare admission_date to audit timestamp",
    "Flag records with more than 7 days discrepancy",
    "Report findings"],
   ["Join audit_log ON resource_id = encounter_id AND action = 'CREATE'",
    "Use julianday difference > 7 for flagging"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Lab Results Missing Units",
   "Identify lab result records where the unit field is NULL or empty, "
   "making clinical interpretation unreliable.",
   "Data Quality", ["sql"], 15,
   ["Open SQL Console",
    "Query lab_results where unit IS NULL or empty",
    "Group by test_name to find patterns",
    "Report scope of the issue"],
   ["WHERE unit IS NULL OR unit = ''",
    "Group by test_name to see which tests are affected"],
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Specialty Standardization Review",
   "Review the providers table for inconsistent specialty values "
   "(e.g., 'Cardiology' vs 'cardiology' vs 'Cardiac Medicine') and "
   "propose a standardized list.",
   "Data Quality", ["sql", "report"], 30,
   ["Open SQL Console",
    "Select distinct specialties",
    "Apply LOWER/TRIM to identify near-duplicates",
    "Propose a canonical specialty list",
    "Document mapping recommendations"],
   ["Use LOWER(TRIM(specialty)) to normalize",
    "Count providers per raw specialty to see impact"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "system_administrator"])

_s("Cross-Table Patient MRN Consistency",
   "Verify that all patient_mrn values in encounters, diagnoses, "
   "medications, lab_results, and vitals exist in the patients table.",
   "Data Quality", ["sql"], 35,
   ["Open SQL Console",
    "For each table, left join to patients on MRN",
    "Identify any orphaned MRNs per table",
    "Summarize findings across all tables",
    "Generate remediation report"],
   ["Use UNION ALL to combine checks from multiple tables",
    "LEFT JOIN each table to patients WHERE p.mrn IS NULL"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounter Duration Outlier Detection",
   "Find encounters where the length of stay is more than 3 standard "
   "deviations from the department mean, indicating potential data errors.",
   "Data Quality", ["sql"], 40,
   ["Open SQL Console",
    "Calculate mean and standard deviation of LOS per department",
    "Join back to encounters to find outliers",
    "Flag encounters beyond 3 standard deviations",
    "Review flagged records"],
   ["Compute LOS as julianday(discharge_date) - julianday(admission_date)",
    "Use subquery for department-level mean and stddev"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Validate Vital Sign Recording Timestamps",
   "Check for vital signs recorded outside the encounter's admission "
   "and discharge window, which indicates timestamp errors.",
   "Data Quality", ["sql"], 25,
   ["Open SQL Console",
    "Join vitals to encounters on encounter_id",
    "Check if recorded_at falls outside admission-discharge window",
    "List discrepant records"],
   ["recorded_at < admission_date OR recorded_at > discharge_date",
    "Exclude encounters with NULL discharge_date"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Null Attending Provider on Encounters",
   "Find encounters that have no attending provider assigned, which "
   "violates clinical documentation requirements.",
   "Data Quality", ["sql", "report"], 20,
   ["Open SQL Console",
    "Query encounters where attending_provider_id IS NULL",
    "Group by department to identify worst areas",
    "Calculate percentage of affected encounters"],
   ["WHERE attending_provider_id IS NULL",
    "Join departments for context"],
   difficulty="beginner",
   roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Diagnosis Date After Discharge Date",
   "Identify diagnoses where the diagnosed_date is after the encounter's "
   "discharge_date, which is clinically suspicious.",
   "Data Quality", ["sql"], 20,
   ["Open SQL Console",
    "Join diagnoses to encounters on encounter_id",
    "Compare diagnosed_date to discharge_date",
    "List anomalous records"],
   ["WHERE dx.diagnosed_date > e.discharge_date",
    "Include encounter_id and dates for review"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Frequency Mismatch in Medication Orders",
   "Identify medication records where the frequency field contains "
   "non-standard or inconsistent values (e.g., 'BID' vs 'twice daily' "
   "vs '2x/day') that could cause confusion in clinical workflows.",
   "Data Quality", ["sql", "report"], 25,
   ["Open SQL Console",
    "Query distinct frequency values from medications",
    "Group by LOWER(TRIM(frequency)) to find near-duplicates",
    "Count records per variant to assess scope",
    "Propose a standardized frequency mapping"],
   ["Use LOWER(TRIM(frequency)) to normalize for comparison",
    "Common standard abbreviations: QD, BID, TID, QID, PRN",
    "Group by normalized form and count to see clusters"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "data_analyst"])

# ---------------------------------------------------------------------------
# COMPLIANCE  (scenarios 51-75)
# ---------------------------------------------------------------------------

_s("HIPAA Audit: Who Accessed Patient {mrn} Record?",
   "Review the audit log to determine every user who accessed the record "
   "for patient {mrn}, including action types and timestamps.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console",
    "Query audit_log for resource_type='patient' and resource_id='{mrn}'",
    "Order by timestamp",
    "Review for unauthorized access patterns"],
   ["Filter audit_log WHERE resource_id='{mrn}'",
    "Include action type to distinguish read vs. write"],
   difficulty="intermediate",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Detect After-Hours Record Access",
   "Find all audit log entries where patient records were accessed "
   "between 11 PM and 5 AM, which may indicate unauthorized browsing.",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console",
    "Extract hour from audit_log timestamp",
    "Filter for hours between 23:00 and 05:00",
    "Cross-reference with user roles",
    "Flag suspicious patterns"],
   ["Use strftime('%H', timestamp) to extract hour",
    "Hours >= 23 OR hours < 5"],
   difficulty="intermediate",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Identify Users With Excessive Record Views",
   "Find users who viewed more than 50 distinct patient records in a "
   "single day, which may indicate snooping behavior.",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console",
    "Group audit_log by user_id and date",
    "Count distinct resource_ids where resource_type = 'patient'",
    "Filter for counts > 50",
    "List flagged users and dates"],
   ["Group by user_id, date(timestamp)",
    "HAVING COUNT(DISTINCT resource_id) > 50"],
   difficulty="intermediate",
   roles=["compliance_officer"])

_s("Minimum Necessary Access Review for {dept}",
   "Audit whether users in {dept} are accessing only records relevant "
   "to their department, or if cross-department access is occurring.",
   "Compliance", ["sql", "audit", "report"], 40,
   ["Open SQL Console",
    "Join audit_log to encounters and departments",
    "Identify access events where the encounter department differs from user department",
    "Quantify cross-department access",
    "Generate compliance report"],
   ["Cross-reference audit user_id with department assignments",
    "Flag access to encounters outside the user's department"],
   difficulty="advanced",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Audit Trail Completeness Check",
   "Verify that every encounter has at least one corresponding audit "
   "log entry, ensuring the audit trail is not missing records.",
   "Compliance", ["sql", "audit"], 25,
   ["Open SQL Console",
    "Left join encounters to audit_log",
    "Find encounters with zero audit entries",
    "Report the gap"],
   ["LEFT JOIN audit_log ON resource_id = encounter_id",
    "WHERE resource_type='encounter' and audit entry IS NULL"],
   difficulty="intermediate",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Patient Consent Verification Workflow",
   "Simulate the process of verifying that a patient consent form has "
   "been documented in the EHR before releasing health information.",
   "Compliance", ["ehr", "audit"], 20,
   ["Navigate to patient record in EHR",
    "Locate the consent/authorization section",
    "Verify consent form is on file and not expired",
    "Document the verification in the audit log"],
   ["Check the documents or forms section of the patient chart",
    "Consent must be dated and not expired"],
   difficulty="beginner",
   roles=["compliance_officer", "clinical_staff"])

_s("Break-the-Glass Access Report",
   "Generate a report of all break-the-glass (emergency override) "
   "access events from the audit log and verify each had a legitimate reason.",
   "Compliance", ["sql", "audit", "report"], 35,
   ["Open SQL Console",
    "Query audit_log for action = 'BREAK_THE_GLASS' or similar override actions",
    "List user, patient, timestamp, and reason",
    "Cross-reference with emergency encounters",
    "Flag any without matching emergencies"],
   ["Filter audit_log WHERE action LIKE '%BREAK%' or '%OVERRIDE%'",
    "Join to encounters to check for emergency encounter_type"],
   difficulty="advanced",
   roles=["compliance_officer"])

_s("Role-Based Access Audit for Providers",
   "Verify that provider users are only performing actions appropriate "
   "to their credential level (e.g., residents vs. attending physicians).",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console",
    "Join audit_log to providers",
    "Map expected actions per credential type",
    "Identify actions outside expected scope",
    "Report discrepancies"],
   ["Join audit_log.user_id to providers.provider_id",
    "Group by credential and action to see patterns"],
   difficulty="intermediate",
   roles=["compliance_officer", "system_administrator"])

_s("Data Retention Policy Compliance Check",
   "Identify patient records that exceed the data retention period "
   "(e.g., encounters older than 10 years) and verify if they should "
   "be archived or purged.",
   "Compliance", ["sql", "report"], 25,
   ["Open SQL Console",
    "Find encounters with admission_date older than 10 years",
    "Count affected records by department",
    "Generate retention report",
    "Document recommendations"],
   ["WHERE admission_date < date('now','-10 years')",
    "Check organizational retention policy for exceptions"],
   difficulty="intermediate",
   roles=["compliance_officer", "system_administrator"])

_s("PHI in Free-Text Field Scan",
   "Audit the diagnoses description field for potential embedded PHI "
   "such as patient names, SSNs, or phone numbers that should not appear.",
   "Compliance", ["sql", "audit"], 35,
   ["Open SQL Console",
    "Scan description field for patterns matching SSN, phone, or name formats",
    "Flag records with potential PHI",
    "Report for remediation"],
   ["Look for patterns like ###-##-#### or 10-digit phone numbers",
    "Cross-reference with patient names from the patients table"],
   difficulty="advanced",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("User Account Activity Report",
   "Generate a report of all user accounts that have been active in "
   "the audit log in the past 30 days versus those that have not, "
   "to identify dormant accounts.",
   "Compliance", ["sql", "audit", "report"], 25,
   ["Open SQL Console",
    "Find distinct user_ids active in last 30 days from audit_log",
    "Compare against all known user accounts",
    "Identify dormant accounts",
    "Recommend disabling inactive accounts"],
   ["Subquery for active: SELECT DISTINCT user_id WHERE timestamp >= date('now','-30 days')",
    "Dormant accounts pose a security risk"],
   difficulty="intermediate",
   roles=["compliance_officer", "system_administrator"])

_s("Medication Prescribing Authority Verification",
   "Verify that all medications in the system were prescribed by "
   "providers with valid prescribing credentials (MD, DO, NP, PA).",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console",
    "Join medications to providers on prescribing_provider_id",
    "Check provider credential against allowed prescriber list",
    "Flag medications prescribed by non-authorized credentials",
    "Report findings"],
   ["Valid credentials: 'MD', 'DO', 'NP', 'PA'",
    "WHERE pr.credential NOT IN ('MD','DO','NP','PA')"],
   difficulty="intermediate",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Audit Log Integrity: Gap Detection",
   "Check the audit log for unexplained gaps in log_id sequence or "
   "timestamp gaps exceeding 1 hour, which may indicate log tampering.",
   "Compliance", ["sql", "audit"], 40,
   ["Open SQL Console",
    "Order audit_log by log_id",
    "Check for gaps in sequential log_ids",
    "Check for timestamp gaps > 1 hour",
    "Report any suspicious gaps"],
   ["Use LAG() window function or self-join for sequential checks",
    "julianday difference * 24 > 1 for hour gaps"],
   difficulty="advanced",
   roles=["compliance_officer", "system_administrator"])

_s("Emergency Access Documentation Review",
   "For all emergency encounter types, verify that the attending "
   "provider documented access within 24 hours of the encounter.",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console",
    "Find all emergency encounters",
    "Join to audit_log for documentation events",
    "Check if documentation occurred within 24 hours of admission",
    "Flag encounters missing timely documentation"],
   ["Filter encounters WHERE encounter_type='Emergency'",
    "Compare admission_date to audit timestamp"],
   difficulty="intermediate",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Cross-Reference Provider NPI Validation",
   "Verify that every active provider in the system has a properly "
   "formatted NPI (National Provider Identifier) if the field exists, "
   "or flag missing NPI data.",
   "Compliance", ["sql", "report"], 25,
   ["Open SQL Console",
    "Query providers for NPI field status",
    "Check NPI format (10-digit number)",
    "Flag missing or malformed NPIs",
    "Generate compliance report"],
   ["NPI must be exactly 10 digits",
    "Check for NULL, empty, or non-numeric values"],
   difficulty="intermediate",
   roles=["compliance_officer", "system_administrator"])

_s("Patient Record Amendment Tracking",
   "Review the audit log for all amendment actions on patient records "
   "and verify each amendment has a corresponding reason documented.",
   "Compliance", ["sql", "audit"], 30,
   ["Open SQL Console",
    "Query audit_log for action = 'AMEND' or 'UPDATE' on patient resources",
    "Check for associated reason or note fields",
    "List amendments without documented reasons",
    "Report for HIPAA compliance review"],
   ["Filter WHERE action IN ('AMEND','UPDATE') AND resource_type='patient'",
    "HIPAA requires amendment tracking and reason documentation"],
   difficulty="intermediate",
   roles=["compliance_officer"])

_s("Segregation of Duties: Same-User Create and Approve",
   "Detect instances in the audit log where the same user both created "
   "and approved a clinical record, violating segregation of duties.",
   "Compliance", ["sql", "audit"], 35,
   ["Open SQL Console",
    "Find pairs of CREATE and APPROVE actions for the same resource",
    "Check if user_id is the same for both",
    "Flag violations",
    "Report to compliance team"],
   ["Self-join audit_log on resource_id and resource_type",
    "One row with action='CREATE', other with action='APPROVE'"],
   difficulty="advanced",
   roles=["compliance_officer", "system_administrator"])

_s("HIPAA Right of Access: Patient Data Export",
   "Simulate fulfilling a patient's HIPAA right of access request by "
   "extracting all data for patient {mrn} across all tables.",
   "Compliance", ["sql", "ehr", "report"], 40,
   ["Identify all tables containing patient data",
    "Query each table for patient_mrn = '{mrn}'",
    "Compile encounters, diagnoses, medications, labs, and vitals",
    "Format data for patient-friendly export",
    "Log the disclosure in the audit trail"],
   ["Query patients, encounters, diagnoses, medications, lab_results, vitals",
    "HIPAA requires response within 30 days of request"],
   difficulty="advanced",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Accounting of Disclosures Report",
   "Generate an accounting of all disclosures of patient {mrn}'s "
   "information by querying the audit log for external access events.",
   "Compliance", ["sql", "audit", "report"], 30,
   ["Open SQL Console",
    "Query audit_log for resource_id='{mrn}' and external disclosure actions",
    "Include date, recipient, and purpose of disclosure",
    "Format as required by HIPAA",
    "Provide to patient or compliance team"],
   ["Filter for action types related to disclosure or export",
    "HIPAA requires this report be available for up to 6 years"],
   difficulty="intermediate",
   roles=["compliance_officer"])

_s("Periodic Security Risk Assessment: Access Patterns",
   "Analyze audit log access patterns over the past quarter to identify "
   "unusual spikes in record access volume that may indicate a security incident.",
   "Compliance", ["sql", "audit", "report"], 40,
   ["Open SQL Console",
    "Aggregate daily access counts for the past 90 days",
    "Calculate mean and standard deviation",
    "Flag days with access volume > 2 standard deviations above mean",
    "Generate risk assessment report"],
   ["Group by date(timestamp) for daily counts",
    "Use statistical thresholds for anomaly detection"],
   difficulty="advanced",
   roles=["compliance_officer", "system_administrator"])

_s("Verify Encryption Compliance on Sensitive Fields",
   "Review the database schema and audit log to verify that sensitive "
   "fields (SSN, DOB) are being accessed only through authorized channels.",
   "Compliance", ["sql", "audit"], 30,
   ["Review which fields contain sensitive data",
    "Query audit_log for access to sensitive resource types",
    "Verify that access was through approved applications",
    "Document findings in compliance report"],
   ["Sensitive fields include patient DOB, SSN if stored, contact info",
    "Check action and user_id patterns for unauthorized tools"],
   difficulty="intermediate",
   roles=["compliance_officer", "system_administrator"])

_s("Annual HIPAA Training Compliance Check",
   "Cross-reference system users from the audit log against a training "
   "completion list to identify users who accessed PHI without current "
   "HIPAA training certification.",
   "Compliance", ["sql", "audit", "report"], 30,
   ["Extract distinct user_ids from audit_log for the past year",
    "Compare against training completion records",
    "Identify users with PHI access but no training record",
    "Generate non-compliance report"],
   ["Use audit_log to identify all active users",
    "Flag any user accessing patient data without training"],
   difficulty="intermediate",
   roles=["compliance_officer"])

_s("Incident Response: Investigate Potential Breach for Patient {mrn}",
   "A patient {mrn} reported a potential privacy breach. Investigate "
   "all access to their record in the past 60 days and identify any "
   "unauthorized viewers.",
   "Compliance", ["sql", "audit", "report"], 45,
   ["Query audit_log for all access to patient {mrn} in past 60 days",
    "Identify all unique users who accessed the record",
    "Cross-reference with authorized care team",
    "Flag unauthorized access events",
    "Prepare incident investigation report"],
   ["Filter audit_log WHERE resource_id='{mrn}' AND timestamp >= date('now','-60 days')",
    "Compare accessing users to encounter attending providers"],
   difficulty="advanced",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Meaningful Use: CDS Alert Response Rate",
   "Calculate the percentage of clinical decision support (CDS) alerts "
   "that were acknowledged vs. overridden in the audit log.",
   "Compliance", ["sql", "audit", "report"], 30,
   ["Open SQL Console",
    "Query audit_log for CDS-related actions",
    "Categorize as acknowledged vs. overridden",
    "Calculate response rates",
    "Report for meaningful use attestation"],
   ["Filter WHERE action LIKE '%CDS%' or '%ALERT%'",
    "Separate by action subtype: acknowledge vs. override"],
   difficulty="intermediate",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Data Use Agreement Compliance for Research Queries",
   "Review audit log entries flagged as research-related data access and "
   "verify each has a corresponding approved data use agreement on file.",
   "Compliance", ["sql", "audit", "report"], 35,
   ["Query audit_log for research-tagged access events",
    "Extract unique research user IDs",
    "Cross-reference with approved DUA records",
    "Flag access without valid DUA",
    "Prepare compliance report"],
   ["Filter WHERE action LIKE '%RESEARCH%'",
    "DUA must be current and cover the accessed data scope"],
   difficulty="advanced",
   roles=["compliance_officer"])

# ---------------------------------------------------------------------------
# EHR NAVIGATION  (scenarios 76-100)
# ---------------------------------------------------------------------------

_s("Locate and Review Patient Demographics for {mrn}",
   "Navigate the EHR to find and review the demographic information "
   "for patient {mrn}, including name, DOB, gender, and contact details.",
   "EHR Navigation", ["ehr"], 10,
   ["Open the EHR application",
    "Search for patient by MRN {mrn}",
    "Navigate to the Demographics section",
    "Review and verify displayed information"],
   ["Use the patient search bar with the MRN",
    "Demographics are typically on the patient banner or a dedicated tab"],
   difficulty="beginner",
   roles=["clinical_staff", "clinical_informatics_analyst"])

_s("Review Active Medication List for Patient {mrn}",
   "Navigate the EHR to find the current active medication list for "
   "patient {mrn} and identify any potential issues.",
   "EHR Navigation", ["ehr"], 15,
   ["Open the EHR application",
    "Search for patient {mrn}",
    "Navigate to the Medications tab",
    "Review active medications for completeness and accuracy"],
   ["Look for the Medications or Med List section",
    "Active medications are filtered from historical ones"],
   difficulty="beginner",
   roles=["clinical_staff", "clinical_informatics_analyst"])

_s("Place a Lab Order in the EHR",
   "Walk through the process of placing a Complete Blood Count (CBC) "
   "lab order for patient {mrn} in the EHR.",
   "EHR Navigation", ["ehr"], 20,
   ["Open the EHR and search for patient {mrn}",
    "Navigate to the Orders section",
    "Search for 'CBC' in the order catalog",
    "Complete required fields (priority, specimen type)",
    "Sign and submit the order"],
   ["Orders section may be labeled 'Order Entry' or 'CPOE'",
    "Ensure you select the correct encounter context"],
   difficulty="intermediate",
   roles=["clinical_staff"])

_s("Document a Progress Note",
   "Navigate the EHR to create a new progress note for patient {mrn}, "
   "using the SOAP format template.",
   "EHR Navigation", ["ehr"], 25,
   ["Open the EHR and navigate to patient {mrn}",
    "Go to the Notes or Documentation section",
    "Select the SOAP note template",
    "Complete Subjective, Objective, Assessment, Plan sections",
    "Sign and finalize the note"],
   ["Notes section may be under 'Clinical Documentation' or 'Notes'",
    "SOAP = Subjective, Objective, Assessment, Plan"],
   difficulty="intermediate",
   roles=["clinical_staff"])

_s("Review Lab Results Timeline for Patient {mrn}",
   "Navigate the EHR to view lab results for patient {mrn} in a "
   "timeline or trend view to identify patterns.",
   "EHR Navigation", ["ehr"], 15,
   ["Open the EHR and search for patient {mrn}",
    "Navigate to Lab Results or Results Review",
    "Switch to timeline or trend view",
    "Identify any abnormal trends"],
   ["Look for a 'Trend' or 'Graph' view option",
    "Abnormal values are usually highlighted in red"],
   difficulty="beginner",
   roles=["clinical_staff", "clinical_informatics_analyst"])

_s("Navigate the Problem List and Add a Diagnosis",
   "Open the problem list for patient {mrn} and add {dx_code} "
   "({dx_desc}) as a new active problem.",
   "EHR Navigation", ["ehr", "coding"], 20,
   ["Open the EHR and navigate to patient {mrn}",
    "Go to the Problem List section",
    "Click Add Problem or New Diagnosis",
    "Search for {dx_code} and select {dx_desc}",
    "Save the new problem entry"],
   ["Problem List is usually a dedicated tab or panel",
    "Search by ICD-10 code or description text"],
   difficulty="intermediate",
   roles=["clinical_staff"])

_s("Review and Reconcile Medication List at Discharge",
   "Perform medication reconciliation for patient {mrn} at discharge "
   "by comparing admission medications with current orders.",
   "EHR Navigation", ["ehr"], 30,
   ["Open the EHR and navigate to patient {mrn}",
    "Access the Medication Reconciliation module",
    "Compare pre-admission medications with in-hospital orders",
    "Mark each medication as continue, discontinue, or modify",
    "Complete and sign the reconciliation"],
   ["Med Rec module is typically accessed from the discharge workflow",
    "Pay attention to duplicate therapies and dose changes"],
   difficulty="advanced",
   roles=["clinical_staff"])

_s("View Encounter History for Patient {mrn}",
   "Navigate the EHR to view the complete encounter history for patient "
   "{mrn}, including all inpatient, outpatient, and emergency visits.",
   "EHR Navigation", ["ehr"], 15,
   ["Open the EHR and search for patient {mrn}",
    "Navigate to Encounter History or Visit List",
    "Review encounters sorted by date",
    "Note encounter types and departments"],
   ["Encounter history may be under 'Visits' or 'Encounters'",
    "Filter by encounter type if needed"],
   difficulty="beginner",
   roles=["clinical_staff", "clinical_informatics_analyst"])

_s("Set Up a Clinical Alert Rule in the EHR",
   "Configure a clinical decision support alert that fires when a "
   "provider orders a medication for a patient with a documented allergy.",
   "EHR Navigation", ["ehr"], 40,
   ["Navigate to the EHR administration or CDS module",
    "Select 'Create New Alert Rule'",
    "Define trigger: medication order event",
    "Define condition: patient has allergy matching ordered med",
    "Set alert severity and message text"],
   ["CDS rules are in the Admin or Build section of the EHR",
    "Drug-allergy interaction checks are a core CDS feature"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "system_administrator"])

_s("Generate a Discharge Summary in the EHR",
   "Navigate the EHR to create a discharge summary for patient {mrn}, "
   "including diagnoses, procedures, and follow-up instructions.",
   "EHR Navigation", ["ehr", "report"], 30,
   ["Open the EHR and navigate to patient {mrn}",
    "Go to the Discharge module or summary template",
    "Auto-populate fields from encounter data",
    "Review and edit diagnoses, medications, and instructions",
    "Sign and finalize the discharge summary"],
   ["Discharge summary often auto-populates from encounter data",
    "Include primary diagnosis, procedures, and follow-up plan"],
   difficulty="intermediate",
   roles=["clinical_staff"])

_s("Navigate the Allergy Documentation Module",
   "Document a new allergy for patient {mrn}: Penicillin, reaction "
   "type Anaphylaxis, severity Severe.",
   "EHR Navigation", ["ehr"], 15,
   ["Open the EHR and navigate to patient {mrn}",
    "Go to the Allergies section",
    "Click Add Allergy",
    "Enter Penicillin, Anaphylaxis, Severe",
    "Save the allergy entry"],
   ["Allergies section is usually on the patient banner or sidebar",
    "Severity levels: Mild, Moderate, Severe"],
   difficulty="beginner",
   roles=["clinical_staff"])

_s("Use the EHR Inbox to Manage Results",
   "Navigate the EHR inbox to review pending lab results, acknowledge "
   "normal results, and flag abnormal results for follow-up.",
   "EHR Navigation", ["ehr"], 20,
   ["Open the EHR inbox or In Basket",
    "Navigate to the Results section",
    "Review each pending result",
    "Acknowledge normal results and create tasks for abnormals"],
   ["The inbox is typically called 'In Basket' or 'Message Center'",
    "Abnormal results require documented acknowledgment"],
   difficulty="intermediate",
   roles=["clinical_staff"])

_s("Configure User Preferences and Default Views",
   "Navigate the EHR to set up a provider's user preferences including "
   "default department, preferred note templates, and result display options.",
   "EHR Navigation", ["ehr"], 20,
   ["Open the EHR application",
    "Navigate to User Settings or Preferences",
    "Set default department and encounter context",
    "Configure preferred note templates",
    "Save preferences"],
   ["Preferences are usually under a gear icon or Settings menu",
    "Default views save time during daily workflows"],
   difficulty="intermediate",
   roles=["clinical_informatics_analyst", "system_administrator"])

_s("Navigate the Immunization Record Module",
   "Review and update the immunization record for patient {mrn}, "
   "including adding a new COVID-19 booster dose.",
   "EHR Navigation", ["ehr"], 20,
   ["Open the EHR and navigate to patient {mrn}",
    "Go to the Immunizations section",
    "Review existing immunization history",
    "Add new immunization record with vaccine details",
    "Save and verify the entry"],
   ["Immunizations may be under 'Preventive Care' or 'Health Maintenance'",
    "Include lot number, manufacturer, and administration site"],
   difficulty="intermediate",
   roles=["clinical_staff"])

_s("Use the Patient List Feature for Rounding",
   "Create and configure a patient list in the EHR for morning rounds "
   "in {dept}, including key columns like room, diagnosis, and provider.",
   "EHR Navigation", ["ehr"], 25,
   ["Open the EHR and navigate to Patient Lists",
    "Create a new list filtered by {dept}",
    "Add columns: Room, Primary Dx, Attending, LOS",
    "Sort by room number",
    "Save the list for daily use"],
   ["Patient lists may be called 'Census', 'Worklist', or 'Patient List'",
    "Custom columns enhance rounding efficiency"],
   difficulty="intermediate",
   roles=["clinical_staff", "clinical_informatics_analyst"])

_s("Review the Audit Trail for a Specific Encounter",
   "Navigate the EHR to view the audit trail for a specific encounter "
   "of patient {mrn}, showing who viewed, modified, or printed the record.",
   "EHR Navigation", ["ehr", "audit"], 20,
   ["Open the EHR and navigate to patient {mrn}",
    "Select the encounter in question",
    "Access the Audit Trail or Activity Log feature",
    "Review all access events for this encounter"],
   ["Audit trail is often under a menu like 'More' or 'Chart Activity'",
    "Look for timestamp, user, and action type columns"],
   difficulty="intermediate",
   roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Navigate Referral Management in the EHR",
   "Create a referral order for patient {mrn} to see a Cardiology "
   "specialist, including clinical reason and urgency.",
   "EHR Navigation", ["ehr"], 25,
   ["Open the EHR and navigate to patient {mrn}",
    "Go to Referrals or Orders section",
    "Select 'New Referral' and choose Cardiology",
    "Enter clinical reason and set urgency level",
    "Sign and submit the referral"],
   ["Referrals may be under Orders or a dedicated Referrals tab",
    "Include relevant diagnoses to support the referral reason"],
   difficulty="intermediate",
   roles=["clinical_staff"])

_s("Access and Interpret a CCD/CDA Document",
   "Navigate the EHR to locate and interpret a Continuity of Care "
   "Document (CCD) received for patient {mrn} from an external facility.",
   "EHR Navigation", ["ehr", "hl7"], 30,
   ["Open the EHR and navigate to patient {mrn}",
    "Go to the Health Information Exchange or Documents section",
    "Locate the received CCD document",
    "Review sections: problems, medications, allergies, procedures",
    "Reconcile external data with existing chart"],
   ["CCD documents are often in the Documents or HIE section",
    "CCD follows the HL7 CDA standard with structured XML sections"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Build a Custom Report in the EHR Reporting Module",
   "Use the EHR's built-in reporting tool to build a custom report "
   "showing all patients in {dept} with a length of stay > 7 days.",
   "EHR Navigation", ["ehr", "report"], 35,
   ["Navigate to the EHR Reporting or Analytics module",
    "Select 'Create New Report'",
    "Choose data source: Encounters",
    "Add filters: department = {dept}, LOS > 7 days",
    "Run the report and export results"],
   ["Reporting tools may be called 'Analytics', 'Crystal Reports', or 'Report Builder'",
    "LOS filter may require a calculated field"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "data_analyst"])

_s("Navigate the EHR Downtime Procedures",
   "Walk through the EHR downtime procedure: accessing read-only "
   "copies, using paper forms, and re-entering data after system recovery.",
   "EHR Navigation", ["ehr"], 30,
   ["Review the downtime procedure documentation",
    "Access the read-only downtime database or printed patient summaries",
    "Practice filling out the paper downtime forms",
    "Understand the data re-entry process post-recovery"],
   ["Downtime procedures should be tested regularly",
    "Read-only access may be via a separate application or cached data"],
   difficulty="intermediate",
   roles=["clinical_staff", "clinical_informatics_analyst", "system_administrator"])

_s("Patient Portal Message Review and Response",
   "Navigate the EHR to review and respond to a patient portal message "
   "from patient {mrn} asking about their lab results.",
   "EHR Navigation", ["ehr"], 15,
   ["Open the EHR inbox or patient communication section",
    "Locate the message from patient {mrn}",
    "Review the referenced lab results",
    "Compose and send a clinically appropriate response"],
   ["Patient portal messages are in the In Basket or Messages section",
    "Ensure the response does not include unnecessary PHI"],
   difficulty="beginner",
   roles=["clinical_staff"])

_s("Configure Order Sets for {dept}",
   "Navigate the EHR build tools to create an admission order set "
   "for {dept} including common labs, medications, and nursing orders.",
   "EHR Navigation", ["ehr"], 45,
   ["Navigate to EHR Build or Order Set Editor",
    "Create a new order set named '{dept} Admission Orders'",
    "Add standard lab orders (CBC, BMP, UA)",
    "Add common medications and nursing assessments",
    "Set defaults and save the order set"],
   ["Order Set Builder is in the admin or build section",
    "Include required fields and smart defaults for each order"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "system_administrator"])

_s("Navigate the Clinical Decision Support Dashboard",
   "Access the CDS dashboard to review active clinical alerts, "
   "override rates, and alert fatigue metrics for {dept}.",
   "EHR Navigation", ["ehr", "report"], 30,
   ["Open the EHR and navigate to CDS Administration",
    "Access the alert metrics dashboard",
    "Review override rates by alert type",
    "Identify alerts with high override rates suggesting alert fatigue",
    "Propose optimization recommendations"],
   ["CDS dashboards may be under Admin or Quality sections",
    "Override rates above 80% typically indicate alert fatigue"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst"])

_s("Review and Validate an HL7 ADT Message",
   "Open the EHR integration console to review an incoming HL7 ADT "
   "(Admit/Discharge/Transfer) message and validate its segments.",
   "EHR Navigation", ["ehr", "hl7"], 35,
   ["Navigate to the EHR integration or interface engine",
    "Locate the incoming ADT message queue",
    "Open a specific ADT message",
    "Validate MSH, PID, PV1, and EVN segments",
    "Check for parsing errors or missing fields"],
   ["ADT messages contain MSH (header), PID (patient), PV1 (visit) segments",
    "Field delimiters are typically | with component separator ^"],
   difficulty="advanced",
   roles=["clinical_informatics_analyst", "system_administrator"])

_s("Manage User Access and Security Roles in the EHR",
   "Navigate the EHR administration module to review user access "
   "levels, assign a new role to a user, and deactivate a departed employee.",
   "EHR Navigation", ["ehr", "audit"], 30,
   ["Open the EHR Administration module",
    "Navigate to User Management or Security section",
    "Review the current role assignments for a user",
    "Assign a new security role and deactivate the departed user",
    "Verify changes in the audit log"],
   ["User management is in the Admin or Security section",
    "Always document the reason for role changes"],
   difficulty="intermediate",
   roles=["system_administrator"])


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
assert len(SCENARIOS_PART1) == 100, (
    f"Expected 100 scenarios, got {len(SCENARIOS_PART1)}"
)

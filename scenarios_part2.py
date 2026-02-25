"""scenarios_part2.py - System Administration, Analytics, Revenue Cycle, Clinical Operations scenarios."""

SCENARIOS_PART2 = []


def _s(title, desc, category, tools, minutes, steps, hints, sql=None,
       difficulty="intermediate", roles=None):
    SCENARIOS_PART2.append({
        "title": title, "description": desc, "category": category,
        "tools": tools, "estimated_minutes": minutes, "steps": steps,
        "hints": hints, "sql_answer": sql, "difficulty": difficulty,
        "target_roles": roles or ["clinical_informatics_analyst"],
    })


# =========================================================================
# SYSTEM ADMINISTRATION (1-25)
# =========================================================================

_s("Analyze HL7 ADT Message Flow",
   "The interface engine is reporting increased ADT message failures. Parse recent HL7 ADT messages to identify structural issues or missing required segments.",
   "System Administration", ["hl7", "sql"], 30,
   ["Open HL7 Message Analyzer", "Generate sample ADT messages from database", "Parse and validate message structure", "Identify missing required segments"],
   ["ADT messages must have MSH, EVN, PID, and PV1 segments",
    "Check for missing patient identifiers in PID-3"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 Message Validation Report",
   "Generate a validation report for recent HL7 messages. Identify messages failing structural validation and categorize the errors.",
   "System Administration", ["hl7"], 25,
   ["Open HL7 Message Analyzer", "Run validation on sample messages", "Categorize validation errors by type", "Prioritize fixes by frequency"],
   ["Use the validate_hl7_message function",
    "Common errors: missing segments, invalid data types, wrong delimiters"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Interface Engine Error Log Analysis",
   "The interface team needs an analysis of HL7 message errors. Query the database for failed interface transactions and identify error patterns.",
   "System Administration", ["sql", "hl7"], 30,
   ["Open SQL Console", "Query for interface-related audit_log entries", "Categorize errors by type and source", "Identify peak error times"],
   ["Look for 'interface' or 'hl7' or 'error' actions in audit_log",
    "Group by DATE and HOUR to find peak error times"],
   sql="SELECT DATE(timestamp) AS error_date, COUNT(*) AS error_count FROM audit_log WHERE LOWER(action) LIKE '%error%' OR LOWER(action) LIKE '%fail%' GROUP BY DATE(timestamp) ORDER BY error_date DESC LIMIT 30",
   difficulty="intermediate", roles=["system_administrator"])

_s("Compare HL7 Messages Before and After Interface Update",
   "An interface was recently updated. Compare HL7 message structures before and after the update to verify no data was lost in the transition.",
   "System Administration", ["hl7"], 35,
   ["Generate sample messages representing the old format", "Generate messages in the new format", "Use the compare function to diff", "Document structural changes"],
   ["Use compare_messages to identify differences",
    "Pay attention to segment order and field positions"],
   sql=None,
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 Field Reference Lookup",
   "A new interface developer needs to understand HL7 segment and field definitions. Generate a field reference guide for the most commonly used segments.",
   "System Administration", ["hl7"], 15,
   ["Open HL7 Message Analyzer", "Access field reference documentation", "Review MSH, PID, PV1, OBX segment definitions", "Document key fields and their purposes"],
   ["Use get_hl7_field_reference()",
    "Focus on segments used in ADT and ORU messages"],
   sql=None,
   difficulty="beginner", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Audit Log Volume Monitoring",
   "System administration needs to monitor audit log growth to ensure adequate storage. Analyze daily log volume trends over the past month.",
   "System Administration", ["sql"], 20,
   ["Open SQL Console", "Count audit_log entries per day", "Calculate daily growth rate", "Project storage needs"],
   ["GROUP BY DATE(timestamp) for daily counts",
    "Use AVG for average daily volume"],
   sql="SELECT DATE(timestamp) AS log_date, COUNT(*) AS daily_entries FROM audit_log WHERE timestamp >= datetime('now','-30 days') GROUP BY DATE(timestamp) ORDER BY log_date",
   difficulty="beginner", roles=["system_administrator"])

_s("Database Table Size Assessment",
   "DBA team needs to understand the relative size of clinical database tables. Count records in each major table for capacity planning.",
   "System Administration", ["sql"], 15,
   ["Open SQL Console", "Count records in each clinical table", "Compare relative sizes", "Identify fastest-growing tables"],
   ["Query each table with COUNT(*)",
    "Use UNION ALL for a consolidated view"],
   sql="SELECT 'patients' AS table_name, COUNT(*) AS row_count FROM patients UNION ALL SELECT 'encounters', COUNT(*) FROM encounters UNION ALL SELECT 'diagnoses', COUNT(*) FROM diagnoses UNION ALL SELECT 'medications', COUNT(*) FROM medications UNION ALL SELECT 'lab_results', COUNT(*) FROM lab_results UNION ALL SELECT 'vitals', COUNT(*) FROM vitals UNION ALL SELECT 'audit_log', COUNT(*) FROM audit_log ORDER BY row_count DESC",
   difficulty="beginner", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 OBX Lab Result Message Parsing",
   "Parse incoming HL7 OBX (observation) messages to extract lab result data and verify it matches the lab_results table format.",
   "System Administration", ["hl7", "sql"], 30,
   ["Generate sample HL7 messages with OBX segments", "Parse the OBX segments to extract results", "Map OBX fields to lab_results table columns", "Verify data translation accuracy"],
   ["OBX-3 contains the test identifier, OBX-5 has the result value",
    "OBX-6 contains units, OBX-7 has reference ranges"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("System User Account Audit",
   "IT security needs to audit all user accounts in the system. Identify unique users from the audit log and their last activity dates.",
   "System Administration", ["sql", "audit"], 20,
   ["Open SQL Console", "Extract unique user_ids from audit_log", "Find last activity date per user", "Identify dormant accounts"],
   ["SELECT DISTINCT user_id, MAX(timestamp) AS last_active",
    "Flag users with no activity in 90+ days"],
   sql="SELECT user_id, COUNT(*) AS total_actions, MAX(timestamp) AS last_active, MIN(timestamp) AS first_seen, CAST(julianday('now')-julianday(MAX(timestamp)) AS INTEGER) AS days_inactive FROM audit_log GROUP BY user_id ORDER BY last_active DESC",
   difficulty="intermediate", roles=["system_administrator"])

_s("HL7 Message Throughput Analysis",
   "The interface team needs to understand message processing throughput. Analyze HL7-related audit entries to determine messages processed per hour.",
   "System Administration", ["sql", "hl7"], 25,
   ["Open SQL Console", "Query audit_log for HL7 message events", "Calculate hourly throughput", "Identify peak processing times"],
   ["Filter for hl7 or interface actions in audit_log",
    "Group by strftime('%Y-%m-%d %H', timestamp) for hourly buckets"],
   sql="SELECT strftime('%Y-%m-%d %H:00', timestamp) AS hour, COUNT(*) AS message_count FROM audit_log WHERE LOWER(action) LIKE '%hl7%' OR LOWER(action) LIKE '%interface%' OR LOWER(action) LIKE '%message%' GROUP BY strftime('%Y-%m-%d %H', timestamp) ORDER BY hour DESC LIMIT 48",
   difficulty="intermediate", roles=["system_administrator"])

_s("Database Index Performance Review",
   "The DBA needs to evaluate which queries are running slow. Analyze common query patterns from the audit log and identify potential index candidates.",
   "System Administration", ["sql", "audit"], 35,
   ["Review audit_log for query-related actions", "Identify the most frequently accessed tables and columns", "Analyze common WHERE clause patterns", "Recommend indexing strategy"],
   ["Look for SQL or query actions in audit_log",
    "Tables with frequent joins need indexes on join columns"],
   sql=None,
   difficulty="advanced", roles=["system_administrator"])

_s("HL7 ADT A08 Update Message Generation",
   "Generate and validate HL7 ADT A08 (patient update) messages from the database. Verify that updated demographic data is properly formatted.",
   "System Administration", ["hl7", "sql"], 30,
   ["Query patient demographics from database", "Generate ADT A08 messages", "Validate message structure", "Verify PID segment matches patient data"],
   ["A08 is used for patient information updates",
    "PID segment must accurately reflect current patient demographics"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("System Uptime and Availability Report",
   "Management needs a system availability report. Analyze audit log gaps to estimate system downtime periods over the last month.",
   "System Administration", ["sql", "report"], 30,
   ["Open SQL Console", "Identify time gaps in audit_log entries", "Calculate total gap time exceeding normal thresholds", "Estimate uptime percentage"],
   ["Large gaps (>30 minutes) in audit_log entries may indicate downtime",
    "Calculate total hours vs gap hours for availability percentage"],
   sql=None,
   difficulty="advanced", roles=["system_administrator"])

_s("HL7 Message Segment Frequency Analysis",
   "Interface team wants to understand which HL7 segments are most commonly used. Parse sample messages and count segment type frequencies.",
   "System Administration", ["hl7"], 20,
   ["Generate a batch of sample HL7 messages", "Parse each message", "Count occurrences of each segment type", "Report segment frequency distribution"],
   ["Parse messages and extract segment types (first 3 chars of each line)",
    "MSH, PID, PV1 will be in every message; count optional segments"],
   sql=None,
   difficulty="beginner", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Failed Login Attempt Analysis",
   "Security needs a report on failed login attempts. Query the audit log for authentication failures and identify potential brute-force patterns.",
   "System Administration", ["sql", "audit"], 25,
   ["Open SQL Console", "Query audit_log for failed authentication events", "Group by user_id to find targeted accounts", "Check for rapid-fire attempts"],
   ["Look for 'login_fail' or 'auth_fail' actions",
    "Multiple failures from the same user in short time suggests brute force"],
   sql="SELECT user_id, COUNT(*) AS failed_attempts, MIN(timestamp) AS first_attempt, MAX(timestamp) AS last_attempt FROM audit_log WHERE LOWER(action) LIKE '%fail%' AND (LOWER(action) LIKE '%login%' OR LOWER(action) LIKE '%auth%') GROUP BY user_id HAVING COUNT(*) > 3 ORDER BY failed_attempts DESC",
   difficulty="intermediate", roles=["system_administrator"])

_s("HL7 Message Routing Table Review",
   "The interface manager needs to review the current message routing configuration. Analyze which message types are being sent to which destinations.",
   "System Administration", ["hl7", "sql"], 25,
   ["Generate sample messages of different types", "Parse message headers (MSH) for routing info", "Map message types to destinations", "Identify any routing gaps"],
   ["MSH-9 contains the message type, MSH-5 has the receiving application",
    "Common types: ADT, ORM, ORU, SIU"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator"])

_s("Data Backup Verification",
   "IT operations needs to verify data integrity across the system. Run record count comparisons and checksum analyses on clinical tables.",
   "System Administration", ["sql"], 20,
   ["Open SQL Console", "Count records in each table", "Verify foreign key relationships are intact", "Check for any NULL primary keys"],
   ["Count records and compare expected vs actual",
    "Verify referential integrity with LEFT JOIN checks"],
   sql="SELECT 'patients' AS tbl, COUNT(*) AS total, SUM(CASE WHEN mrn IS NULL THEN 1 ELSE 0 END) AS null_pk FROM patients UNION ALL SELECT 'encounters', COUNT(*), SUM(CASE WHEN encounter_id IS NULL THEN 1 ELSE 0 END) FROM encounters UNION ALL SELECT 'diagnoses', COUNT(*), SUM(CASE WHEN diagnosis_id IS NULL THEN 1 ELSE 0 END) FROM diagnoses",
   difficulty="beginner", roles=["system_administrator"])

_s("Interface Acknowledgment Rate Monitoring",
   "The interface team needs to monitor HL7 ACK/NAK rates. Analyze message acknowledgments to identify interfaces with high rejection rates.",
   "System Administration", ["hl7", "sql", "audit"], 30,
   ["Query audit_log for message send and acknowledgment events", "Calculate ACK vs NAK ratios", "Identify interfaces with lowest acceptance rates", "Investigate root causes"],
   ["Look for 'ack' and 'nak' or 'reject' in audit_log actions",
    "Group by interface/destination for per-interface metrics"],
   sql=None,
   difficulty="advanced", roles=["system_administrator"])

_s("HL7 Message Timestamp Consistency Check",
   "Verify that timestamps in HL7 messages are consistent. Parse sample messages and compare MSH-7 (message datetime) with database encounter dates.",
   "System Administration", ["hl7", "sql"], 25,
   ["Generate HL7 messages from recent encounters", "Parse MSH-7 timestamps", "Compare with encounter admission_date", "Flag significant discrepancies"],
   ["MSH-7 format is YYYYMMDDHHMMSS",
    "Compare with encounter admission_date for temporal consistency"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("System Resource Utilization by Department",
   "IT management wants to understand which departments generate the most system activity. Analyze audit log activity by department context.",
   "System Administration", ["sql", "audit"], 25,
   ["Open SQL Console", "Cross-reference audit_log with department data", "Count activities per department", "Identify heaviest system users"],
   ["Link audit_log resource_id to encounters, then to departments",
    "Group by department for relative usage"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator"])

_s("HL7 Message Size Distribution",
   "Network team wants to understand HL7 message size distribution for bandwidth planning. Analyze message lengths from generated samples.",
   "System Administration", ["hl7"], 20,
   ["Generate a batch of sample HL7 messages", "Calculate the length of each message", "Determine average, min, max, and percentile sizes", "Report size distribution"],
   ["Parse messages and use len() for size",
    "Categorize into size buckets: small (<1KB), medium (1-5KB), large (>5KB)"],
   sql=None,
   difficulty="beginner", roles=["system_administrator"])

_s("Clinical System Integration Health Check",
   "Perform a comprehensive health check on clinical system integrations by validating data flow from encounters through all downstream tables.",
   "System Administration", ["sql", "hl7"], 35,
   ["Verify encounter data propagates to diagnoses", "Check medication linkage to encounters", "Validate lab results reference valid encounters", "Verify vitals are linked correctly"],
   ["Use JOIN and LEFT JOIN to verify referential integrity across all tables",
    "Count orphaned records in each child table"],
   sql="SELECT 'diagnoses' AS child_table, COUNT(*) AS orphaned FROM diagnoses dx LEFT JOIN encounters e ON dx.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL UNION ALL SELECT 'medications', COUNT(*) FROM medications m LEFT JOIN encounters e ON m.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL UNION ALL SELECT 'lab_results', COUNT(*) FROM lab_results lr LEFT JOIN encounters e ON lr.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL UNION ALL SELECT 'vitals', COUNT(*) FROM vitals v LEFT JOIN encounters e ON v.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL",
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 PID Segment Data Quality Validation",
   "Validate the quality of patient demographic data in HL7 PID segments. Check for missing names, DOBs, and gender codes.",
   "System Administration", ["hl7", "sql"], 25,
   ["Generate sample HL7 messages with PID segments", "Parse PID fields", "Check for empty or malformed demographic fields", "Report data quality issues"],
   ["PID-3: patient ID, PID-5: name, PID-7: DOB, PID-8: gender",
    "Empty fields in PID indicate upstream data issues"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("System Configuration Change Audit",
   "IT governance needs to track system configuration changes. Review the audit log for any administrative actions that modified system settings.",
   "System Administration", ["sql", "audit"], 25,
   ["Open SQL Console", "Query audit_log for admin/config actions", "List all configuration changes chronologically", "Identify unauthorized changes"],
   ["Filter for actions containing 'config', 'setting', 'admin', 'update'",
    "Focus on system-level rather than patient-level actions"],
   sql="SELECT log_id, user_id, action, resource_type, resource_id, timestamp FROM audit_log WHERE LOWER(action) LIKE '%config%' OR LOWER(action) LIKE '%setting%' OR LOWER(action) LIKE '%admin%change%' ORDER BY timestamp DESC LIMIT 50",
   difficulty="intermediate", roles=["system_administrator"])


# =========================================================================
# ANALYTICS (26-50)
# =========================================================================

_s("Population Health: Diabetes Prevalence by Age Group",
   "Population health team needs diabetes (E11.x) prevalence by age group. Calculate the percentage of patients with diabetes in each age bracket.",
   "Analytics", ["sql", "report"], 30,
   ["Open SQL Console", "Calculate patient ages", "Identify patients with E11.x diagnoses", "Group by age bracket and calculate prevalence"],
   ["Age brackets: 0-17, 18-44, 45-64, 65+",
    "Use LEFT JOIN to get all patients, not just those with diabetes"],
   sql="SELECT CASE WHEN (julianday('now')-julianday(p.dob))/365.25 < 18 THEN '0-17' WHEN (julianday('now')-julianday(p.dob))/365.25 < 45 THEN '18-44' WHEN (julianday('now')-julianday(p.dob))/365.25 < 65 THEN '45-64' ELSE '65+' END AS age_group, COUNT(DISTINCT p.mrn) AS total_patients, COUNT(DISTINCT dx.patient_mrn) AS diabetic_patients, ROUND(COUNT(DISTINCT dx.patient_mrn)*100.0/NULLIF(COUNT(DISTINCT p.mrn),0),1) AS prevalence_pct FROM patients p LEFT JOIN diagnoses dx ON p.mrn=dx.patient_mrn AND dx.icd10_code LIKE 'E11%' GROUP BY age_group ORDER BY age_group",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Outcome Tracking: Mortality Rate by Department",
   "Quality needs to track in-hospital mortality rates by department. Identify encounters with a 'deceased' status or relevant disposition.",
   "Analytics", ["sql", "report"], 30,
   ["Open SQL Console", "Identify encounters with mortality indicators", "Calculate rate by department", "Compare against benchmarks"],
   ["Look for encounter_type or diagnosis codes indicating mortality",
    "Rate = deaths / total discharges * 100"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Quality Measure: Heart Failure Readmission Rate",
   "CMS quality reporting requires the heart failure (I50.x) 30-day readmission rate. Calculate this hospital-wide metric.",
   "Analytics", ["sql", "report"], 35,
   ["Open SQL Console", "Identify heart failure encounters", "Find readmissions within 30 days", "Calculate the readmission rate"],
   ["Heart failure codes start with I50",
    "Self-join encounters to find readmissions"],
   sql="SELECT COUNT(DISTINCT CASE WHEN r.encounter_id IS NOT NULL THEN e.patient_mrn END) AS readmitted, COUNT(DISTINCT e.patient_mrn) AS total_hf_patients, ROUND(COUNT(DISTINCT CASE WHEN r.encounter_id IS NOT NULL THEN e.patient_mrn END)*100.0/NULLIF(COUNT(DISTINCT e.patient_mrn),0),2) AS readmission_rate FROM encounters e JOIN diagnoses dx ON e.encounter_id=dx.encounter_id LEFT JOIN encounters r ON e.patient_mrn=r.patient_mrn AND r.encounter_id != e.encounter_id AND r.admission_date BETWEEN e.discharge_date AND datetime(e.discharge_date,'+30 days') WHERE dx.icd10_code LIKE 'I50%' AND e.discharge_date IS NOT NULL",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Clinical Dashboard: Daily Census Trend",
   "Build a daily census trend showing the number of patients present each day for the past 30 days.",
   "Analytics", ["sql", "report"], 25,
   ["Open SQL Console", "For each day, count patients with overlapping encounter dates", "Build the daily census query", "Plot the trend data"],
   ["A patient is present on day D if admission_date <= D AND (discharge_date >= D OR discharge_date IS NULL)",
    "Generate a date series using recursive CTE or date arithmetic"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Sepsis Screening Compliance",
   "Infection control wants to know how many patients admitted through the ED had documented vitals within 1 hour. This relates to sepsis screening compliance.",
   "Analytics", ["sql", "report"], 30,
   ["Query ED encounters", "Find earliest vital for each ED encounter", "Calculate time from admission to first vital", "Determine compliance rate (vitals within 60 min)"],
   ["Filter encounters WHERE encounter_type='Emergency'",
    "Calculate minutes between admission_date and first vitals recorded_at"],
   sql="SELECT COUNT(*) AS total_ed, COUNT(CASE WHEN (julianday(first_vital)-julianday(e.admission_date))*1440 <= 60 THEN 1 END) AS compliant, ROUND(COUNT(CASE WHEN (julianday(first_vital)-julianday(e.admission_date))*1440 <= 60 THEN 1 END)*100.0/NULLIF(COUNT(*),0),1) AS compliance_pct FROM encounters e LEFT JOIN (SELECT encounter_id, MIN(recorded_at) AS first_vital FROM vitals GROUP BY encounter_id) v ON e.encounter_id=v.encounter_id WHERE e.encounter_type='Emergency'",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patient Flow Analysis: Admission to Discharge",
   "Operations wants to understand patient flow from admission to discharge. Calculate average time at each stage by department.",
   "Analytics", ["sql", "report"], 30,
   ["Open SQL Console", "Calculate admission to first vital time", "Calculate admission to first diagnosis time", "Calculate total LOS by department"],
   ["Use MIN() to find first event timestamps",
    "Calculate differences in hours or days"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Chronic Disease Comorbidity Analysis",
   "Population health wants to understand comorbidity patterns. For patients with hypertension (I10), what are the most common co-occurring diagnoses?",
   "Analytics", ["sql", "report"], 30,
   ["Open SQL Console", "Identify patients with hypertension", "Find their other diagnoses", "Rank comorbidities by frequency"],
   ["First find all patient_mrn with I10 diagnosis",
    "Then query other diagnoses for those patients, excluding I10"],
   sql="SELECT dx2.icd10_code, dx2.description, COUNT(DISTINCT dx2.patient_mrn) AS patient_count FROM diagnoses dx1 JOIN diagnoses dx2 ON dx1.patient_mrn=dx2.patient_mrn WHERE dx1.icd10_code='I10' AND dx2.icd10_code != 'I10' GROUP BY dx2.icd10_code, dx2.description ORDER BY patient_count DESC LIMIT 20",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Lab Utilization Analysis",
   "Lab administration needs to understand test ordering patterns. Identify the most frequently ordered tests, their volume trends, and ordering departments.",
   "Analytics", ["sql", "report"], 25,
   ["Open SQL Console", "Count lab tests by test_name", "Join with encounters for department context", "Analyze monthly volume trends"],
   ["GROUP BY test_name for frequency",
    "Add department context through encounters join"],
   sql="SELECT lr.test_name, COUNT(*) AS total_orders, COUNT(DISTINCT lr.patient_mrn) AS unique_patients, COUNT(DISTINCT d.dept_name) AS ordering_depts FROM lab_results lr JOIN encounters e ON lr.encounter_id=e.encounter_id JOIN departments d ON e.department_id=d.dept_id GROUP BY lr.test_name ORDER BY total_orders DESC LIMIT 15",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Antibiotic Stewardship Metrics",
   "Infection control needs antibiotic stewardship metrics: average duration of antibiotic therapy, broad-spectrum vs narrow-spectrum usage, and prescriber distribution.",
   "Analytics", ["sql", "report"], 35,
   ["Open SQL Console", "Identify antibiotic medications", "Calculate average prescription duration", "Analyze prescriber patterns"],
   ["Filter medications with antibiotic keywords",
    "Broad-spectrum: vancomycin, meropenem, piperacillin; Narrow: amoxicillin, cephalexin"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("ED Wait Time Analysis",
   "ED management needs to analyze wait times. Calculate the time from ED arrival (admission) to first provider contact (first audit entry) per encounter.",
   "Analytics", ["sql"], 25,
   ["Open SQL Console", "Query ED encounters", "Find first provider interaction from audit_log", "Calculate wait times"],
   ["First provider contact approximated by first audit_log entry for the encounter",
    "Calculate difference in minutes"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Seasonal Diagnosis Pattern Analysis",
   "Public health analytics wants to identify seasonal patterns in diagnoses. Analyze diagnosis frequency by month for the top 10 conditions.",
   "Analytics", ["sql", "report"], 30,
   ["Open SQL Console", "Identify top 10 diagnoses by frequency", "Break down monthly occurrence for each", "Identify seasonal peaks"],
   ["Use strftime('%m', diagnosed_date) for month extraction",
    "Pivot or cross-tab by month for each diagnosis"],
   sql="SELECT dx.icd10_code, dx.description, strftime('%m', dx.diagnosed_date) AS month, COUNT(*) AS occurrences FROM diagnoses dx WHERE dx.icd10_code IN (SELECT icd10_code FROM diagnoses GROUP BY icd10_code ORDER BY COUNT(*) DESC LIMIT 10) GROUP BY dx.icd10_code, dx.description, strftime('%m', dx.diagnosed_date) ORDER BY dx.icd10_code, month",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patient Acuity Scoring",
   "Nursing administration wants to estimate patient acuity based on number of active diagnoses, medications, and abnormal vitals per patient.",
   "Analytics", ["sql", "report"], 35,
   ["Open SQL Console", "Count diagnoses per patient", "Count active medications per patient", "Count abnormal vitals per patient", "Create composite acuity score"],
   ["Combine counts from multiple tables per patient_mrn",
    "Use subqueries or CTEs to calculate each component"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Panel Size Analysis",
   "Medical staff office needs to analyze provider panel sizes — how many unique patients each provider manages.",
   "Analytics", ["sql", "report"], 20,
   ["Open SQL Console", "Count distinct patients per provider", "Include specialty and credential info", "Rank by panel size"],
   ["COUNT(DISTINCT patient_mrn) per provider",
    "Consider only encounters in the last year for active panel"],
   sql="SELECT pr.first_name||' '||pr.last_name AS provider, pr.specialty, pr.credential, COUNT(DISTINCT e.patient_mrn) AS panel_size FROM providers pr JOIN encounters e ON pr.provider_id=e.attending_provider_id WHERE e.admission_date >= datetime('now','-365 days') GROUP BY pr.provider_id ORDER BY panel_size DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Medication Adherence Proxy Analysis",
   "Care management wants to estimate medication adherence by looking at refill patterns — patients with gaps in medication records may be non-adherent.",
   "Analytics", ["sql", "report"], 35,
   ["Open SQL Console", "Identify patients on chronic medications", "Look for prescription continuity over time", "Flag patients with large gaps"],
   ["Chronic meds: look for same medication_name with multiple start_dates",
    "Gaps > 60 days between prescriptions suggest non-adherence"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Hospital Case Mix Index Estimation",
   "Finance wants to estimate the hospital's Case Mix Index (CMI). Calculate the average DRG weight using diagnosis complexity as a proxy.",
   "Analytics", ["sql", "coding", "report"], 35,
   ["Open SQL Console", "Count diagnoses per encounter as complexity proxy", "Weight encounters by diagnosis count", "Calculate overall CMI estimate"],
   ["More diagnoses per encounter suggests higher complexity",
    "CMI is typically the average DRG weight; approximate with diagnosis count"],
   sql="SELECT ROUND(AVG(dx_count),2) AS avg_diagnoses_per_encounter, COUNT(*) AS total_encounters FROM (SELECT e.encounter_id, COUNT(dx.diagnosis_id) AS dx_count FROM encounters e LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.discharge_date IS NOT NULL GROUP BY e.encounter_id)",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Vital Signs Trend Analysis for Patient {mrn}",
   "The care team needs vital sign trends for patient {mrn}. Show all vital readings over time to identify clinical trends.",
   "Analytics", ["sql", "ehr"], 20,
   ["Open SQL Console", "Query vitals for patient {mrn}", "Order by recorded_at", "Identify any concerning trends"],
   ["Query vitals WHERE patient_mrn='{mrn}' ORDER BY recorded_at",
    "Group by vital_type for separate trend lines"],
   sql="SELECT vital_type, value, recorded_at FROM vitals WHERE patient_mrn='{mrn}' ORDER BY vital_type, recorded_at",
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Discharge Disposition Analysis",
   "Case management wants to understand discharge patterns. Analyze where patients go after discharge by encounter type and department.",
   "Analytics", ["sql", "report"], 25,
   ["Open SQL Console", "Categorize encounters by outcome", "Break down by department and encounter type", "Calculate percentages for each disposition"],
   ["Use encounter_type as a proxy for disposition category",
    "GROUP BY department and encounter_type"],
   sql="SELECT d.dept_name, e.encounter_type, COUNT(*) AS encounters, ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM encounters WHERE discharge_date IS NOT NULL),1) AS pct FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE e.discharge_date IS NOT NULL GROUP BY d.dept_name, e.encounter_type ORDER BY d.dept_name, encounters DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Pneumonia Quality Bundle Compliance",
   "Quality needs to assess pneumonia care bundle compliance. For patients with pneumonia (J18.x), check if blood cultures and antibiotics were ordered within appropriate timeframes.",
   "Analytics", ["sql", "report"], 40,
   ["Identify pneumonia patients by ICD-10 J18.x", "Check for blood culture lab results", "Check for antibiotic medication orders", "Calculate bundle compliance rate"],
   ["Pneumonia codes: J18.x",
    "Blood culture: look for 'blood culture' or 'culture' in lab test_name"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Gender-Based Health Disparity Analysis",
   "Health equity team wants to analyze potential disparities in care by gender. Compare average encounter counts, diagnosis counts, and lab orders between genders.",
   "Analytics", ["sql", "report"], 25,
   ["Open SQL Console", "Join patients with encounters, diagnoses, labs", "Aggregate by gender", "Compare utilization metrics"],
   ["GROUP BY p.gender",
    "Use COUNT and AVG for per-patient metrics by gender"],
   sql="SELECT p.gender, COUNT(DISTINCT p.mrn) AS patients, COUNT(DISTINCT e.encounter_id) AS encounters, ROUND(COUNT(DISTINCT e.encounter_id)*1.0/COUNT(DISTINCT p.mrn),1) AS avg_encounters, COUNT(DISTINCT dx.diagnosis_id) AS diagnoses FROM patients p LEFT JOIN encounters e ON p.mrn=e.patient_mrn LEFT JOIN diagnoses dx ON p.mrn=dx.patient_mrn GROUP BY p.gender",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Predictive Risk Scoring: Readmission Factors",
   "Analytics team wants to identify risk factors for readmission. Analyze characteristics of readmitted vs non-readmitted patients.",
   "Analytics", ["sql", "report"], 40,
   ["Identify readmitted patients (encounter within 30 days)", "Extract characteristics: age, gender, diagnosis count, med count", "Compare readmitted vs non-readmitted groups", "Identify significant risk factors"],
   ["Build two cohorts: readmitted and not readmitted",
    "Compare average age, number of diagnoses, medications between groups"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Referral Pattern Analysis",
   "Medical staff office wants to understand referral patterns. Analyze how patients flow between providers across encounters.",
   "Analytics", ["sql"], 30,
   ["Open SQL Console", "Find patients with encounters under different providers", "Map provider-to-provider transitions", "Identify most common referral pathways"],
   ["Look at sequential encounters for the same patient with different providers",
    "ORDER BY patient_mrn, admission_date to see the flow"],
   sql="SELECT pr1.first_name||' '||pr1.last_name||' ('||pr1.specialty||')' AS from_provider, pr2.first_name||' '||pr2.last_name||' ('||pr2.specialty||')' AS to_provider, COUNT(*) AS referrals FROM encounters e1 JOIN encounters e2 ON e1.patient_mrn=e2.patient_mrn AND e2.admission_date > e1.admission_date JOIN providers pr1 ON e1.attending_provider_id=pr1.provider_id JOIN providers pr2 ON e2.attending_provider_id=pr2.provider_id WHERE pr1.provider_id != pr2.provider_id GROUP BY pr1.provider_id, pr2.provider_id ORDER BY referrals DESC LIMIT 20",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])


# =========================================================================
# REVENUE CYCLE (51-75)
# =========================================================================

_s("ICD-10 Code Validation for {dept}",
   "Coding compliance needs to validate ICD-10 codes assigned in {dept}. Check for valid format and common coding errors.",
   "Revenue Cycle", ["sql", "coding"], 25,
   ["Open SQL Console and Code Mapper", "Pull all diagnosis codes for {dept}", "Validate each code format", "Identify potentially incorrect codes"],
   ["Valid ICD-10: letter + 2 digits + optional decimal",
    "Cross-reference with the coding tool for validation"],
   sql="SELECT dx.icd10_code, dx.description, COUNT(*) AS usage_count FROM diagnoses dx JOIN encounters e ON dx.encounter_id=e.encounter_id JOIN departments d ON e.department_id=d.dept_id WHERE d.dept_name='{dept}' GROUP BY dx.icd10_code, dx.description ORDER BY usage_count DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("CPT Code Utilization Analysis",
   "Revenue cycle needs to understand CPT code utilization patterns. Analyze the distribution of procedure codes across departments and providers.",
   "Revenue Cycle", ["sql", "coding"], 30,
   ["Open Code Mapper tool", "Search for common CPT codes", "Analyze utilization by department", "Identify under-coded procedures"],
   ["CPT codes are 5-digit numeric codes",
    "Cross-reference with encounter types for expected procedures"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Charge Capture Gap Analysis for {dept}",
   "Revenue integrity suspects charge capture gaps in {dept}. Compare encounter volumes against expected charge patterns.",
   "Revenue Cycle", ["sql", "coding", "report"], 35,
   ["Query encounters for {dept}", "Compare encounter count with diagnosis count", "Identify encounters with no diagnoses (potential charge gaps)", "Report gap rate"],
   ["Encounters without diagnoses may represent missed charges",
    "LEFT JOIN diagnoses to find encounters with no coding"],
   sql="SELECT COUNT(DISTINCT e.encounter_id) AS total_encounters, COUNT(DISTINCT dx.encounter_id) AS coded_encounters, COUNT(DISTINCT e.encounter_id)-COUNT(DISTINCT dx.encounter_id) AS uncoded, ROUND((COUNT(DISTINCT e.encounter_id)-COUNT(DISTINCT dx.encounter_id))*100.0/NULLIF(COUNT(DISTINCT e.encounter_id),0),1) AS gap_pct FROM encounters e LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id JOIN departments d ON e.department_id=d.dept_id WHERE d.dept_name='{dept}'",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("DRG Assignment Analysis",
   "Finance needs to analyze DRG assignments. Using diagnosis data, estimate DRG complexity and identify potential up-coding or under-coding patterns.",
   "Revenue Cycle", ["sql", "coding", "report"], 40,
   ["Open Code Mapper for DRG info", "Analyze diagnosis patterns per encounter", "Estimate DRG complexity from diagnosis count and types", "Identify outliers"],
   ["More secondary diagnoses typically increase DRG complexity",
    "Compare encounters with similar primary diagnoses but different secondary counts"],
   sql="SELECT dx.icd10_code AS primary_dx, dx.description, COUNT(DISTINCT e.encounter_id) AS encounters, ROUND(AVG(dx_count),1) AS avg_secondary_dx FROM diagnoses dx JOIN encounters e ON dx.encounter_id=e.encounter_id JOIN (SELECT encounter_id, COUNT(*) AS dx_count FROM diagnoses GROUP BY encounter_id) dc ON e.encounter_id=dc.encounter_id GROUP BY dx.icd10_code, dx.description HAVING COUNT(DISTINCT e.encounter_id) >= 3 ORDER BY encounters DESC LIMIT 20",
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Coding Accuracy Audit for Dr. {provider}",
   "Coding compliance wants to audit the coding accuracy for encounters attended by Dr. {provider}. Check for consistency between documented conditions and assigned codes.",
   "Revenue Cycle", ["sql", "coding"], 30,
   ["Query encounters for Dr. {provider}", "Pull all assigned diagnosis codes", "Validate code-description consistency", "Check for specificity issues"],
   ["Filter encounters by attending_provider and get their diagnoses",
    "Unspecified codes (ending in .9) may indicate under-coding"],
   sql="SELECT e.encounter_id, e.admission_date, dx.icd10_code, dx.description FROM encounters e JOIN providers pr ON e.attending_provider_id=pr.provider_id JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE pr.first_name||' '||pr.last_name='{provider}' ORDER BY e.admission_date DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Denial Risk Assessment by Diagnosis",
   "Revenue cycle wants to identify diagnoses with high denial risk. Analyze which ICD-10 codes have been associated with coding queries or audits.",
   "Revenue Cycle", ["sql", "coding", "audit"], 30,
   ["Open SQL Console and Audit Workbench", "Identify coding audit events in audit_log", "Cross-reference with diagnosis codes", "Rank diagnoses by audit frequency"],
   ["Look for 'coding', 'query', or 'denial' actions in audit_log",
    "Higher audit rates suggest higher denial risk"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Revenue Impact of Coding Specificity",
   "Finance wants to understand the revenue impact of non-specific coding. Identify encounters using unspecified ICD-10 codes (ending in .9) that could be more specific.",
   "Revenue Cycle", ["sql", "coding"], 25,
   ["Open SQL Console", "Find diagnoses with unspecified codes", "Count encounters affected", "Estimate specificity improvement opportunity"],
   ["Unspecified codes often end in .9",
    "More specific codes may support higher reimbursement"],
   sql="SELECT dx.icd10_code, dx.description, COUNT(*) AS occurrences, COUNT(DISTINCT dx.encounter_id) AS encounters FROM diagnoses dx WHERE dx.icd10_code LIKE '%.9' GROUP BY dx.icd10_code, dx.description ORDER BY occurrences DESC LIMIT 20",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Outpatient vs Inpatient Revenue Mix",
   "Finance needs to analyze the encounter type mix. Calculate the proportion of inpatient vs outpatient vs emergency encounters and average diagnosis complexity.",
   "Revenue Cycle", ["sql", "report"], 20,
   ["Open SQL Console", "Group encounters by type", "Calculate percentages and average diagnosis counts", "Report the revenue mix"],
   ["GROUP BY encounter_type",
    "Count diagnoses per encounter for complexity proxy"],
   sql="SELECT e.encounter_type, COUNT(*) AS encounters, ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM encounters),1) AS pct, ROUND(AVG(dc.dx_count),1) AS avg_dx_count FROM encounters e LEFT JOIN (SELECT encounter_id, COUNT(*) AS dx_count FROM diagnoses GROUP BY encounter_id) dc ON e.encounter_id=dc.encounter_id GROUP BY e.encounter_type ORDER BY encounters DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("SNOMED to ICD-10 Crosswalk Validation",
   "The coding team needs to validate SNOMED-to-ICD-10 crosswalk mappings. Use the coding tool to check common mappings and identify potential discrepancies.",
   "Revenue Cycle", ["coding"], 25,
   ["Open Code Mapper tool", "Select common SNOMED codes from clinical data", "Run crosswalk to ICD-10", "Compare mapped codes with actual assigned codes"],
   ["Use crosswalk_snomed_to_icd10 function",
    "Compare automated mapping against manually assigned codes"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Coding Query Response Time Analysis",
   "HIM management wants to measure CDI query response times. Track how quickly coding queries are resolved by analyzing audit log timestamps.",
   "Revenue Cycle", ["sql", "audit"], 25,
   ["Open SQL Console", "Find coding query initiation events", "Find corresponding resolution events", "Calculate response times"],
   ["Look for 'query' and 'resolve' actions in audit_log",
    "Match query-resolve pairs by resource_id"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("High-Value Encounter Identification",
   "Revenue cycle wants to identify potentially high-value encounters — those with many diagnoses, medications, and labs that may support complex billing.",
   "Revenue Cycle", ["sql", "coding"], 30,
   ["Open SQL Console", "Count diagnoses, medications, and labs per encounter", "Create a composite complexity score", "Rank encounters by score"],
   ["Join encounter with counts from diagnoses, medications, and lab_results",
    "Composite score = dx_count + med_count + lab_count"],
   sql="SELECT e.encounter_id, e.patient_mrn, e.encounter_type, d.dept_name, COALESCE(dx.cnt,0) AS dx_count, COALESCE(m.cnt,0) AS med_count, COALESCE(lr.cnt,0) AS lab_count, COALESCE(dx.cnt,0)+COALESCE(m.cnt,0)+COALESCE(lr.cnt,0) AS complexity_score FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN (SELECT encounter_id, COUNT(*) AS cnt FROM diagnoses GROUP BY encounter_id) dx ON e.encounter_id=dx.encounter_id LEFT JOIN (SELECT encounter_id, COUNT(*) AS cnt FROM medications GROUP BY encounter_id) m ON e.encounter_id=m.encounter_id LEFT JOIN (SELECT encounter_id, COUNT(*) AS cnt FROM lab_results GROUP BY encounter_id) lr ON e.encounter_id=lr.encounter_id ORDER BY complexity_score DESC LIMIT 20",
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Diagnosis Coding Consistency Check",
   "Coding audit: verify that the same clinical conditions are coded consistently. Find cases where similar descriptions have different ICD-10 codes.",
   "Revenue Cycle", ["sql", "coding"], 25,
   ["Open SQL Console", "Group diagnoses by description", "Identify descriptions mapped to multiple ICD-10 codes", "Report inconsistencies"],
   ["GROUP BY description HAVING COUNT(DISTINCT icd10_code) > 1",
    "These indicate potential coding inconsistencies"],
   sql="SELECT description, GROUP_CONCAT(DISTINCT icd10_code) AS codes, COUNT(DISTINCT icd10_code) AS code_count, COUNT(*) AS total_uses FROM diagnoses GROUP BY description HAVING COUNT(DISTINCT icd10_code) > 1 ORDER BY code_count DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Revenue Cycle KPI Dashboard Data",
   "Finance needs monthly revenue cycle KPIs: total encounters, coded encounters, coding rate, average diagnoses per encounter, and top 5 DRG codes.",
   "Revenue Cycle", ["sql", "coding", "report"], 30,
   ["Open SQL Console", "Calculate each KPI from clinical data", "Compile into dashboard format", "Generate the report"],
   ["Use multiple aggregate queries or UNION ALL",
    "Coding rate = encounters with at least one diagnosis / total encounters"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("ICD-10 Code Suggestion from Clinical Text",
   "The CDI team wants to test automated code suggestion. Use the coding tool to suggest ICD-10 codes from clinical descriptions and compare with actual assignments.",
   "Revenue Cycle", ["coding", "sql"], 25,
   ["Open Code Mapper tool", "Input clinical descriptions from recent encounters", "Compare suggested codes with actual assigned codes", "Measure suggestion accuracy"],
   ["Use suggest_codes function with clinical text",
    "Compare output against actual diagnoses for accuracy"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Unbilled Encounter Identification",
   "Revenue integrity needs to find encounters that appear complete (discharged) but may not have been billed. Look for discharged encounters with minimal coding.",
   "Revenue Cycle", ["sql", "report"], 25,
   ["Open SQL Console", "Find discharged encounters", "Check diagnosis and procedure coding", "Identify encounters with zero or minimal coding"],
   ["Discharged = discharge_date IS NOT NULL",
    "Zero diagnoses likely means unbilled"],
   sql="SELECT e.encounter_id, p.mrn, p.first_name||' '||p.last_name AS patient, e.admission_date, e.discharge_date, d.dept_name, COUNT(dx.diagnosis_id) AS dx_count FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn JOIN departments d ON e.department_id=d.dept_id LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.discharge_date IS NOT NULL GROUP BY e.encounter_id HAVING COUNT(dx.diagnosis_id) = 0 ORDER BY e.discharge_date DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Coding Productivity by Coder",
   "HIM management needs coder productivity metrics. Use audit log to track how many records each coder processes per day.",
   "Revenue Cycle", ["sql", "audit"], 25,
   ["Open SQL Console", "Query audit_log for coding actions", "Group by user (coder) and date", "Calculate average daily productivity"],
   ["Look for 'code', 'assign', or 'diagnosis' actions in audit_log",
    "Calculate encounters coded per user per day"],
   sql="SELECT user_id AS coder, COUNT(DISTINCT DATE(timestamp)) AS active_days, COUNT(*) AS total_actions, ROUND(COUNT(*)*1.0/COUNT(DISTINCT DATE(timestamp)),1) AS avg_daily FROM audit_log WHERE LOWER(action) LIKE '%code%' OR LOWER(action) LIKE '%assign%' OR LOWER(action) LIKE '%diagnosis%' GROUP BY user_id ORDER BY avg_daily DESC",
   difficulty="intermediate", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Secondary Diagnosis Impact Analysis",
   "Finance wants to understand how secondary diagnoses impact encounter complexity. Compare encounters with 1 vs 2+ vs 5+ diagnoses.",
   "Revenue Cycle", ["sql", "coding", "report"], 30,
   ["Open SQL Console", "Count diagnoses per encounter", "Categorize by diagnosis count brackets", "Compare average LOS across brackets"],
   ["GROUP encounter by diagnosis count: 1, 2-4, 5+",
    "More diagnoses often correlate with longer stays"],
   sql="SELECT CASE WHEN dc=1 THEN '1 diagnosis' WHEN dc BETWEEN 2 AND 4 THEN '2-4 diagnoses' ELSE '5+ diagnoses' END AS complexity, COUNT(*) AS encounters, ROUND(AVG(los),1) AS avg_los FROM (SELECT e.encounter_id, COUNT(dx.diagnosis_id) AS dc, julianday(e.discharge_date)-julianday(e.admission_date) AS los FROM encounters e LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.discharge_date IS NOT NULL GROUP BY e.encounter_id) GROUP BY complexity ORDER BY complexity",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Late Coding Detection",
   "Revenue cycle management wants to identify encounters where coding was completed significantly after discharge, causing billing delays.",
   "Revenue Cycle", ["sql", "audit"], 25,
   ["Open SQL Console", "Find discharge dates for encounters", "Find coding action timestamps in audit_log", "Calculate discharge-to-coding lag"],
   ["Compare encounter discharge_date with first coding action timestamp",
    "Flag encounters with > 3 day lag"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Procedure Code Coverage Analysis",
   "Revenue integrity wants to verify that common procedures have appropriate codes documented. Cross-reference encounter types with expected procedure codes.",
   "Revenue Cycle", ["sql", "coding"], 25,
   ["Open Code Mapper", "Identify expected procedures by encounter type", "Check for corresponding documentation", "Report coverage gaps"],
   ["Surgical encounters should have procedure codes",
    "ED encounters should have E&M codes"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Payer Mix Analysis",
   "Finance needs to understand the hospital's payer mix. Analyze encounter distributions and average complexity by potential payer category.",
   "Revenue Cycle", ["sql", "report"], 25,
   ["Open SQL Console", "Categorize patients by age as payer proxy", "Calculate encounter volumes per category", "Report payer mix percentages"],
   ["Age >= 65 approximates Medicare, < 18 approximates Medicaid/CHIP",
    "Use patient DOB to estimate payer category"],
   sql="SELECT CASE WHEN (julianday('now')-julianday(p.dob))/365.25 >= 65 THEN 'Medicare' WHEN (julianday('now')-julianday(p.dob))/365.25 < 18 THEN 'Pediatric/Medicaid' ELSE 'Commercial' END AS payer_category, COUNT(DISTINCT e.encounter_id) AS encounters, COUNT(DISTINCT p.mrn) AS patients, ROUND(COUNT(DISTINCT e.encounter_id)*100.0/(SELECT COUNT(*) FROM encounters),1) AS pct FROM patients p JOIN encounters e ON p.mrn=e.patient_mrn GROUP BY payer_category ORDER BY encounters DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])


# =========================================================================
# CLINICAL OPERATIONS (76-100)
# =========================================================================

_s("Current Bed Occupancy by Department",
   "Bed management needs real-time occupancy. Calculate current bed occupancy as patients admitted but not yet discharged per department.",
   "Clinical Operations", ["sql", "report"], 20,
   ["Open SQL Console", "Count undischarged encounters per department", "Present as current census", "Identify departments at high occupancy"],
   ["WHERE discharge_date IS NULL and admission_date <= date('now')",
    "GROUP BY dept_name"],
   sql="SELECT d.dept_name, COUNT(*) AS current_census FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE e.discharge_date IS NULL AND e.admission_date <= date('now') GROUP BY d.dept_name ORDER BY current_census DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Length of Stay Outlier Detection",
   "Utilization management needs to identify LOS outliers — encounters with stays significantly longer than the departmental average.",
   "Clinical Operations", ["sql", "report"], 25,
   ["Open SQL Console", "Calculate average LOS by department", "Identify encounters exceeding 2x the department average", "List outliers with details"],
   ["Calculate avg LOS per department first",
    "Join back to find encounters > 2x avg"],
   sql="SELECT e.encounter_id, p.mrn, d.dept_name, CAST(julianday(e.discharge_date)-julianday(e.admission_date) AS INTEGER) AS los_days, dept_avg.avg_los FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn JOIN departments d ON e.department_id=d.dept_id JOIN (SELECT department_id, ROUND(AVG(julianday(discharge_date)-julianday(admission_date)),1) AS avg_los FROM encounters WHERE discharge_date IS NOT NULL GROUP BY department_id) dept_avg ON e.department_id=dept_avg.department_id WHERE e.discharge_date IS NOT NULL AND julianday(e.discharge_date)-julianday(e.admission_date) > dept_avg.avg_los * 2 ORDER BY los_days DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Discharge Planning Report for {dept}",
   "Case management needs a discharge planning list for {dept}: patients admitted > 3 days with active diagnoses and current medications.",
   "Clinical Operations", ["sql", "ehr", "report"], 25,
   ["Query long-stay patients in {dept}", "Pull their active diagnoses", "List current medications", "Generate discharge planning report"],
   ["Admitted > 3 days: julianday('now') - julianday(admission_date) > 3",
    "Include diagnosis and medication counts for complexity assessment"],
   sql="SELECT e.encounter_id, p.mrn, p.first_name||' '||p.last_name AS patient, e.admission_date, CAST(julianday('now')-julianday(e.admission_date) AS INTEGER) AS los_days, COUNT(DISTINCT dx.diagnosis_id) AS dx_count, COUNT(DISTINCT m.medication_id) AS med_count FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn JOIN departments d ON e.department_id=d.dept_id LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id LEFT JOIN medications m ON e.encounter_id=m.encounter_id WHERE d.dept_name='{dept}' AND e.discharge_date IS NULL AND julianday('now')-julianday(e.admission_date) > 3 GROUP BY e.encounter_id ORDER BY los_days DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("ED Throughput Analysis",
   "ED administration needs throughput metrics: average time from admission to discharge for ED encounters by day of week.",
   "Clinical Operations", ["sql", "report"], 25,
   ["Open SQL Console", "Filter to ED encounters", "Calculate visit duration in hours", "Average by day of week"],
   ["Filter encounter_type = 'Emergency'",
    "Duration = (julianday(discharge_date) - julianday(admission_date)) * 24"],
   sql="SELECT CASE CAST(strftime('%w',e.admission_date) AS INTEGER) WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' WHEN 6 THEN 'Saturday' END AS day_of_week, COUNT(*) AS ed_visits, ROUND(AVG((julianday(e.discharge_date)-julianday(e.admission_date))*24),1) AS avg_hours FROM encounters e WHERE e.encounter_type='Emergency' AND e.discharge_date IS NOT NULL GROUP BY strftime('%w',e.admission_date) ORDER BY CAST(strftime('%w',e.admission_date) AS INTEGER)",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Workload Distribution",
   "Medical staff office needs to see current provider workload: active (undischarged) patients per provider.",
   "Clinical Operations", ["sql"], 15,
   ["Open SQL Console", "Count undischarged encounters per provider", "Include specialty information", "Rank by current load"],
   ["WHERE discharge_date IS NULL for active patients",
    "GROUP BY attending_provider_id"],
   sql="SELECT pr.first_name||' '||pr.last_name AS provider, pr.specialty, COUNT(*) AS active_patients FROM encounters e JOIN providers pr ON e.attending_provider_id=pr.provider_id WHERE e.discharge_date IS NULL GROUP BY pr.provider_id ORDER BY active_patients DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Surgical Case Volume Analysis",
   "OR management needs monthly surgical case volumes by department and provider.",
   "Clinical Operations", ["sql", "report"], 25,
   ["Open SQL Console", "Filter to surgical encounter types", "Group by month, department, and provider", "Calculate monthly volumes"],
   ["Filter encounter_type for surgical cases",
    "GROUP BY strftime('%Y-%m', admission_date) for monthly"],
   sql="SELECT strftime('%Y-%m', e.admission_date) AS month, d.dept_name, pr.first_name||' '||pr.last_name AS surgeon, COUNT(*) AS cases FROM encounters e JOIN departments d ON e.department_id=d.dept_id JOIN providers pr ON e.attending_provider_id=pr.provider_id WHERE LOWER(e.encounter_type) LIKE '%surg%' OR LOWER(d.dept_name) LIKE '%surg%' OR LOWER(d.dept_name) LIKE '%or%' GROUP BY month, d.dept_name, pr.provider_id ORDER BY month DESC, cases DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patient Wait Time Estimation",
   "Operations wants to estimate patient wait times by calculating the gap between appointment/admission time and first clinical action (vital signs).",
   "Clinical Operations", ["sql"], 25,
   ["Open SQL Console", "Query encounter admission times", "Find first vital signs per encounter", "Calculate wait time as the difference"],
   ["First clinical action approximated by first vitals entry",
    "Wait time = first vital recorded_at - admission_date in minutes"],
   sql="SELECT d.dept_name, COUNT(*) AS encounters, ROUND(AVG((julianday(v.first_vital)-julianday(e.admission_date))*1440),1) AS avg_wait_minutes FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN (SELECT encounter_id, MIN(recorded_at) AS first_vital FROM vitals GROUP BY encounter_id) v ON e.encounter_id=v.encounter_id WHERE v.first_vital IS NOT NULL GROUP BY d.dept_name ORDER BY avg_wait_minutes DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Staffing Ratio Analysis by Department",
   "Nursing administration needs to assess provider-to-patient ratios. Calculate the ratio of active providers to current patients per department.",
   "Clinical Operations", ["sql", "report"], 25,
   ["Open SQL Console", "Count active patients per department", "Count active providers per department", "Calculate ratios"],
   ["Active patients: encounters with no discharge",
    "Active providers: distinct attending_provider_id in current encounters"],
   sql="SELECT d.dept_name, COUNT(DISTINCT e.encounter_id) AS patients, COUNT(DISTINCT e.attending_provider_id) AS providers, ROUND(COUNT(DISTINCT e.encounter_id)*1.0/NULLIF(COUNT(DISTINCT e.attending_provider_id),0),1) AS patient_per_provider FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE e.discharge_date IS NULL GROUP BY d.dept_name ORDER BY patient_per_provider DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Transfer Rate Between Departments",
   "Operations wants to understand inter-department transfer patterns. Identify patients who had encounters in multiple departments.",
   "Clinical Operations", ["sql"], 30,
   ["Open SQL Console", "Find patients with encounters in different departments", "Map transfer pathways", "Calculate transfer frequency"],
   ["Look for same patient_mrn in encounters with different department_ids",
    "Sequential encounters suggest transfers"],
   sql="SELECT d1.dept_name AS from_dept, d2.dept_name AS to_dept, COUNT(*) AS transfers FROM encounters e1 JOIN encounters e2 ON e1.patient_mrn=e2.patient_mrn AND e2.admission_date > e1.admission_date AND julianday(e2.admission_date)-julianday(e1.admission_date) < 1 JOIN departments d1 ON e1.department_id=d1.dept_id JOIN departments d2 ON e2.department_id=d2.dept_id WHERE d1.dept_id != d2.dept_id GROUP BY d1.dept_name, d2.dept_name ORDER BY transfers DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Daily Admission and Discharge Volume",
   "Operations needs to see the daily admission and discharge volumes for capacity planning. Show both metrics per day for the last 30 days.",
   "Clinical Operations", ["sql", "report"], 20,
   ["Open SQL Console", "Count admissions per day", "Count discharges per day", "Combine into a single daily view"],
   ["Admissions: GROUP BY DATE(admission_date)",
    "Discharges: GROUP BY DATE(discharge_date)"],
   sql="SELECT COALESCE(a.dt, d.dt) AS date, COALESCE(a.admissions,0) AS admissions, COALESCE(d.discharges,0) AS discharges FROM (SELECT DATE(admission_date) AS dt, COUNT(*) AS admissions FROM encounters WHERE admission_date >= datetime('now','-30 days') GROUP BY DATE(admission_date)) a FULL OUTER JOIN (SELECT DATE(discharge_date) AS dt, COUNT(*) AS discharges FROM encounters WHERE discharge_date >= datetime('now','-30 days') GROUP BY DATE(discharge_date)) d ON a.dt=d.dt ORDER BY date DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Lab Turnaround Time Analysis",
   "Lab management needs turnaround time analysis. Estimate the time from specimen collection to result availability using encounter and lab data.",
   "Clinical Operations", ["sql", "report"], 25,
   ["Open SQL Console", "Identify lab orders with timestamps", "Estimate turnaround time", "Report by test type"],
   ["Approximate TAT using encounter admission and lab result date",
    "Group by test_name for per-test analysis"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Weekend vs Weekday Operations Comparison",
   "Operations wants to compare weekend vs weekday clinical activity: encounters, labs ordered, medications administered, and vitals documented.",
   "Clinical Operations", ["sql", "report"], 25,
   ["Open SQL Console", "Categorize activities as weekend/weekday", "Count each activity type per category", "Calculate ratios"],
   ["Use strftime('%w', date) where 0=Sunday, 6=Saturday for weekend",
    "CASE WHEN day IN (0,6) THEN 'Weekend' ELSE 'Weekday'"],
   sql="SELECT CASE WHEN CAST(strftime('%w',e.admission_date) AS INTEGER) IN (0,6) THEN 'Weekend' ELSE 'Weekday' END AS day_type, COUNT(DISTINCT e.encounter_id) AS encounters, ROUND(COUNT(DISTINCT e.encounter_id)*1.0/CASE WHEN CAST(strftime('%w',e.admission_date) AS INTEGER) IN (0,6) THEN 2 ELSE 5 END,1) AS avg_per_day FROM encounters e WHERE e.admission_date >= datetime('now','-30 days') GROUP BY day_type",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Same-Day Discharge Rate",
   "Operations wants to know what percentage of encounters are discharged the same day they're admitted (observation/outpatient efficiency).",
   "Clinical Operations", ["sql"], 15,
   ["Open SQL Console", "Identify same-day discharges", "Calculate rate by department", "Compare against benchmarks"],
   ["WHERE DATE(discharge_date) = DATE(admission_date)",
    "Calculate as percentage of total discharges"],
   sql="SELECT d.dept_name, COUNT(*) AS total_discharges, SUM(CASE WHEN DATE(e.discharge_date)=DATE(e.admission_date) THEN 1 ELSE 0 END) AS same_day, ROUND(SUM(CASE WHEN DATE(e.discharge_date)=DATE(e.admission_date) THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS same_day_pct FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE e.discharge_date IS NOT NULL GROUP BY d.dept_name ORDER BY same_day_pct DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Peak Admission Hours Analysis",
   "Capacity planning needs to identify peak admission hours to optimize staffing. Show hourly admission volumes across a typical week.",
   "Clinical Operations", ["sql", "report"], 20,
   ["Open SQL Console", "Extract hour from admission timestamps", "Count admissions per hour", "Identify peak periods"],
   ["Use strftime('%H', admission_date) for hour extraction",
    "GROUP BY hour ORDER BY count for peak identification"],
   sql="SELECT CAST(strftime('%H', admission_date) AS INTEGER) AS hour, COUNT(*) AS admissions FROM encounters GROUP BY CAST(strftime('%H', admission_date) AS INTEGER) ORDER BY hour",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Department Capacity Utilization Trend",
   "Facilities planning needs weekly capacity utilization trends by department for the last 12 weeks.",
   "Clinical Operations", ["sql", "report"], 30,
   ["Open SQL Console", "Calculate weekly census per department", "Determine capacity utilization", "Show 12-week trend"],
   ["Use strftime('%Y-%W', admission_date) for week grouping",
    "Count patients with overlapping stays per week"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Critical Lab Alert Response Time",
   "Lab quality wants to measure how quickly critical lab values receive a clinical response. Cross-reference abnormal labs with subsequent clinical actions.",
   "Clinical Operations", ["sql", "audit"], 30,
   ["Identify critical lab results (far outside reference range)", "Check audit_log for subsequent actions on those patients", "Calculate time from lab result to first action", "Report average response time"],
   ["Critical values: results > 2x upper reference range or < 0.5x lower",
    "Match lab result time with next audit_log entry for same patient"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Patient Throughput by Encounter Type",
   "Operations needs average throughput (admission to discharge time) broken down by encounter type.",
   "Clinical Operations", ["sql", "report"], 20,
   ["Open SQL Console", "Calculate average duration by encounter type", "Include encounter count per type", "Report in hours and days"],
   ["Duration in hours = (julianday(discharge) - julianday(admission)) * 24",
    "GROUP BY encounter_type"],
   sql="SELECT encounter_type, COUNT(*) AS encounters, ROUND(AVG((julianday(discharge_date)-julianday(admission_date))*24),1) AS avg_hours, ROUND(AVG(julianday(discharge_date)-julianday(admission_date)),1) AS avg_days FROM encounters WHERE discharge_date IS NOT NULL GROUP BY encounter_type ORDER BY avg_hours DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Medication Administration Timing Analysis",
   "Pharmacy wants to analyze medication administration timing patterns. Identify peak prescription times and potential gaps in coverage.",
   "Clinical Operations", ["sql"], 25,
   ["Open SQL Console", "Extract hour from medication start_date", "Count prescriptions per hour", "Identify coverage gaps"],
   ["Use strftime('%H', start_date) for hour",
    "Look for hours with very low prescription counts"],
   sql="SELECT CAST(strftime('%H', start_date) AS INTEGER) AS hour, COUNT(*) AS prescriptions FROM medications GROUP BY CAST(strftime('%H', start_date) AS INTEGER) ORDER BY hour",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Cross-Department Consultation Pattern",
   "Medical staff leadership wants to understand consultation patterns. Identify which departments frequently share patients.",
   "Clinical Operations", ["sql"], 30,
   ["Open SQL Console", "Find patients seen by multiple departments", "Map department co-occurrence", "Identify strongest department linkages"],
   ["Self-join encounters on patient_mrn with different department_ids",
    "Count unique patients shared between each department pair"],
   sql="SELECT d1.dept_name AS dept1, d2.dept_name AS dept2, COUNT(DISTINCT e1.patient_mrn) AS shared_patients FROM encounters e1 JOIN encounters e2 ON e1.patient_mrn=e2.patient_mrn AND e1.department_id < e2.department_id JOIN departments d1 ON e1.department_id=d1.dept_id JOIN departments d2 ON e2.department_id=d2.dept_id GROUP BY d1.dept_name, d2.dept_name ORDER BY shared_patients DESC LIMIT 15",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Appointment No-Show Estimation",
   "Operations wants to estimate no-show rates. Identify encounters with very short durations (< 1 hour) or missing vitals that might indicate no-shows.",
   "Clinical Operations", ["sql"], 25,
   ["Open SQL Console", "Find encounters with very short or zero LOS", "Check for missing vitals or documentation", "Estimate no-show rate by department"],
   ["Short encounters with no vitals may be no-shows",
    "LEFT JOIN vitals and check for NULL"],
   sql="SELECT d.dept_name, COUNT(*) AS total, SUM(CASE WHEN v.vital_id IS NULL AND e.discharge_date IS NOT NULL AND (julianday(e.discharge_date)-julianday(e.admission_date))*24 < 1 THEN 1 ELSE 0 END) AS potential_noshow, ROUND(SUM(CASE WHEN v.vital_id IS NULL AND e.discharge_date IS NOT NULL AND (julianday(e.discharge_date)-julianday(e.admission_date))*24 < 1 THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS noshow_pct FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN vitals v ON e.encounter_id=v.encounter_id GROUP BY d.dept_name ORDER BY noshow_pct DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Nursing Documentation Completeness Score",
   "Nursing leadership wants a documentation completeness score per department: percentage of encounters with vitals, at least 2 vital types, and lab results documented.",
   "Clinical Operations", ["sql", "report"], 30,
   ["Open SQL Console", "Check vital documentation per encounter", "Check for multiple vital types per encounter", "Check lab documentation per encounter", "Calculate composite score by department"],
   ["Count encounters with at least one vital entry",
    "Count encounters with 2+ distinct vital_types"],
   sql="SELECT d.dept_name, COUNT(DISTINCT e.encounter_id) AS total, ROUND(COUNT(DISTINCT CASE WHEN v.cnt >= 1 THEN e.encounter_id END)*100.0/NULLIF(COUNT(DISTINCT e.encounter_id),0),1) AS pct_any_vital, ROUND(COUNT(DISTINCT CASE WHEN v.types >= 2 THEN e.encounter_id END)*100.0/NULLIF(COUNT(DISTINCT e.encounter_id),0),1) AS pct_multi_vital FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN (SELECT encounter_id, COUNT(*) AS cnt, COUNT(DISTINCT vital_type) AS types FROM vitals GROUP BY encounter_id) v ON e.encounter_id=v.encounter_id GROUP BY d.dept_name ORDER BY pct_any_vital",
   difficulty="advanced", roles=["clinical_informatics_analyst", "clinical_staff"])

# ---- Additional System Administration ----

_s("HL7 Character Encoding Validation",
   "The interface team has reported garbled characters in patient names. Validate character encoding in HL7 PID segments for non-ASCII characters.",
   "System Administration", ["hl7"], 20,
   ["Generate sample HL7 messages", "Parse PID-5 (patient name) fields", "Check for encoding issues", "Document affected message patterns"],
   ["Non-ASCII characters may be corrupted if encoding headers are wrong",
    "MSH-18 specifies character set; ASCII is default"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator"])

# ---- Additional Analytics ----

_s("Flu Season Impact Analysis",
   "Public health analytics needs to assess flu season impact. Analyze influenza diagnosis frequency by month and correlate with ED visit volume.",
   "Analytics", ["sql", "report"], 25,
   ["Open SQL Console", "Query influenza diagnoses (J09-J11) by month", "Compare with ED encounter volumes", "Identify peak flu months"],
   ["Influenza codes: J09, J10, J11",
    "Compare monthly dx counts with monthly ED volumes"],
   sql="SELECT strftime('%Y-%m', dx.diagnosed_date) AS month, COUNT(*) AS flu_cases, (SELECT COUNT(*) FROM encounters e2 WHERE e2.encounter_type='Emergency' AND strftime('%Y-%m',e2.admission_date)=strftime('%Y-%m',dx.diagnosed_date)) AS ed_visits FROM diagnoses dx WHERE dx.icd10_code LIKE 'J09%' OR dx.icd10_code LIKE 'J10%' OR dx.icd10_code LIKE 'J11%' GROUP BY strftime('%Y-%m', dx.diagnosed_date) ORDER BY month",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Opioid Prescribing Trends",
   "The opioid stewardship committee needs prescribing trend data: monthly opioid prescriptions, unique patients, and prescriber counts over the past year.",
   "Analytics", ["sql", "report"], 25,
   ["Open SQL Console", "Identify opioid medications", "Calculate monthly trends", "Report by prescriber count"],
   ["Opioids: oxycodone, hydrocodone, morphine, fentanyl, codeine",
    "Use strftime('%Y-%m', start_date) for monthly grouping"],
   sql="SELECT strftime('%Y-%m', m.start_date) AS month, COUNT(*) AS rx_count, COUNT(DISTINCT m.patient_mrn) AS patients, COUNT(DISTINCT m.prescribing_provider_id) AS prescribers FROM medications m WHERE LOWER(m.medication_name) LIKE '%oxycodone%' OR LOWER(m.medication_name) LIKE '%hydrocodone%' OR LOWER(m.medication_name) LIKE '%morphine%' OR LOWER(m.medication_name) LIKE '%fentanyl%' OR LOWER(m.medication_name) LIKE '%codeine%' GROUP BY strftime('%Y-%m', m.start_date) ORDER BY month",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("High-Utilizer Patient Identification",
   "Care management wants to identify high-utilizer patients — those with 4+ encounters in the past 6 months. Include demographic and diagnostic context.",
   "Analytics", ["sql", "report"], 25,
   ["Open SQL Console", "Count encounters per patient in last 6 months", "Filter for 4+ encounters", "Include demographics and top diagnoses"],
   ["WHERE admission_date >= datetime('now','-6 months')",
    "GROUP BY patient_mrn HAVING COUNT(*) >= 4"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, p.gender, ROUND((julianday('now')-julianday(p.dob))/365.25) AS age, COUNT(DISTINCT e.encounter_id) AS encounters FROM patients p JOIN encounters e ON p.mrn=e.patient_mrn WHERE e.admission_date >= datetime('now','-6 months') GROUP BY p.mrn HAVING COUNT(DISTINCT e.encounter_id) >= 4 ORDER BY encounters DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patient Age Distribution at Admission",
   "Population health needs the age distribution of patients at time of admission. Create age buckets and count admissions per bucket.",
   "Analytics", ["sql"], 15,
   ["Open SQL Console", "Calculate patient age at admission", "Create age buckets", "Count admissions per bucket"],
   ["Age at admission: (julianday(admission_date) - julianday(dob)) / 365.25",
    "Buckets: 0-17, 18-34, 35-49, 50-64, 65-79, 80+"],
   sql="SELECT CASE WHEN (julianday(e.admission_date)-julianday(p.dob))/365.25 < 18 THEN '0-17' WHEN (julianday(e.admission_date)-julianday(p.dob))/365.25 < 35 THEN '18-34' WHEN (julianday(e.admission_date)-julianday(p.dob))/365.25 < 50 THEN '35-49' WHEN (julianday(e.admission_date)-julianday(p.dob))/365.25 < 65 THEN '50-64' WHEN (julianday(e.admission_date)-julianday(p.dob))/365.25 < 80 THEN '65-79' ELSE '80+' END AS age_group, COUNT(*) AS admissions FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn GROUP BY age_group ORDER BY age_group",
   difficulty="beginner", roles=["data_analyst", "clinical_informatics_analyst"])

# ---- Additional Revenue Cycle ----

_s("Modifier Usage Analysis",
   "Coding compliance needs to review CPT modifier usage patterns. Identify frequently used diagnosis modifiers and verify appropriate application.",
   "Revenue Cycle", ["sql", "coding"], 25,
   ["Open Code Mapper", "Review diagnosis laterality and specificity modifiers", "Identify unmodified codes that should have modifiers", "Report findings"],
   ["Codes needing laterality: musculoskeletal (M), eye (H), ear (H60-H95)",
    "7th character modifiers indicate encounter type (initial, subsequent, sequela)"],
   sql="SELECT dx.icd10_code, dx.description, LENGTH(dx.icd10_code) AS code_length, COUNT(*) AS frequency FROM diagnoses dx WHERE LENGTH(dx.icd10_code) <= 4 AND (dx.icd10_code LIKE 'M%' OR dx.icd10_code LIKE 'S%' OR dx.icd10_code LIKE 'T%') GROUP BY dx.icd10_code, dx.description ORDER BY frequency DESC LIMIT 20",
   difficulty="intermediate", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("ED E&M Level Distribution",
   "Revenue cycle wants to understand E&M coding levels for ED visits. Analyze the distribution of ED encounter complexity based on diagnosis counts.",
   "Revenue Cycle", ["sql", "coding", "report"], 30,
   ["Open SQL Console", "Query ED encounters with diagnosis counts", "Estimate E&M levels based on complexity", "Report level distribution"],
   ["More diagnoses and procedures indicate higher E&M levels",
    "ED E&M: 99281 (Level 1) to 99285 (Level 5)"],
   sql="SELECT CASE WHEN dc <= 1 THEN 'Level 1-2 (Simple)' WHEN dc <= 3 THEN 'Level 3 (Moderate)' WHEN dc <= 5 THEN 'Level 4 (Complex)' ELSE 'Level 5 (Critical)' END AS estimated_level, COUNT(*) AS encounters FROM (SELECT e.encounter_id, COUNT(dx.diagnosis_id) AS dc FROM encounters e LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.encounter_type='Emergency' GROUP BY e.encounter_id) GROUP BY estimated_level ORDER BY estimated_level",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Top Revenue-Contributing Departments",
   "Finance wants to identify departments contributing most to revenue, estimated by encounter volume weighted by diagnosis complexity.",
   "Revenue Cycle", ["sql", "report"], 20,
   ["Open SQL Console", "Count encounters per department", "Weight by average diagnosis count", "Rank departments"],
   ["Revenue proxy = encounter_count * avg_diagnoses_per_encounter",
    "More diagnoses usually correlate with higher reimbursement"],
   sql="SELECT d.dept_name, COUNT(DISTINCT e.encounter_id) AS encounters, ROUND(AVG(COALESCE(dc.cnt,0)),1) AS avg_dx, COUNT(DISTINCT e.encounter_id)*ROUND(AVG(COALESCE(dc.cnt,1)),1) AS revenue_proxy FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN (SELECT encounter_id, COUNT(*) AS cnt FROM diagnoses GROUP BY encounter_id) dc ON e.encounter_id=dc.encounter_id GROUP BY d.dept_name ORDER BY revenue_proxy DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Coding Lag Analysis by Department",
   "Revenue cycle management needs coding delays. Calculate average time between discharge and first diagnosis entry per department.",
   "Revenue Cycle", ["sql"], 25,
   ["Open SQL Console", "Compare discharge_date with diagnosed_date", "Calculate average lag per department", "Identify slowest departments"],
   ["Lag = diagnosed_date - discharge_date in days",
    "Only include post-discharge diagnoses"],
   sql="SELECT d.dept_name, COUNT(DISTINCT e.encounter_id) AS encounters, ROUND(AVG(julianday(dx.diagnosed_date)-julianday(e.discharge_date)),1) AS avg_lag_days FROM encounters e JOIN departments d ON e.department_id=d.dept_id JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.discharge_date IS NOT NULL AND dx.diagnosed_date >= e.discharge_date GROUP BY d.dept_name ORDER BY avg_lag_days DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Complication Code Capture Rate",
   "Quality and coding team wants to assess complication code capture. Analyze long-stay encounters for undocumented complications.",
   "Revenue Cycle", ["sql", "coding"], 25,
   ["Open SQL Console", "Identify encounters with LOS > 7 days", "Check for complication codes (T80-T88)", "Calculate capture rate"],
   ["Complication codes: T80-T88 series",
    "Long LOS without complication codes may indicate under-coding"],
   sql="SELECT d.dept_name, COUNT(DISTINCT e.encounter_id) AS long_stay, COUNT(DISTINCT CASE WHEN dx.icd10_code LIKE 'T8%' THEN e.encounter_id END) AS with_complications, ROUND(COUNT(DISTINCT CASE WHEN dx.icd10_code LIKE 'T8%' THEN e.encounter_id END)*100.0/NULLIF(COUNT(DISTINCT e.encounter_id),0),1) AS capture_pct FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.discharge_date IS NOT NULL AND julianday(e.discharge_date)-julianday(e.admission_date) > 7 GROUP BY d.dept_name ORDER BY long_stay DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

# ---- Additional Clinical Operations ----

_s("Inpatient Midnight Census Calculation",
   "Finance needs midnight census data for each of the last 30 days. Count patients present at midnight per department.",
   "Clinical Operations", ["sql"], 25,
   ["Open SQL Console", "For each day, count patients admitted before midnight and not yet discharged", "Present as daily census trend", "Highlight peak days"],
   ["Patient present at midnight on day D if admission_date <= D AND (discharge_date > D OR discharge_date IS NULL)",
    "Use date arithmetic for the past 30 days"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Encounter Type Transition Mapping",
   "Operations wants to understand how patients transition between encounter types (e.g., Emergency to Inpatient). Map the most common transitions.",
   "Clinical Operations", ["sql"], 25,
   ["Open SQL Console", "Find sequential encounters for the same patient", "Map from-type to to-type transitions", "Count transition frequency"],
   ["Self-join encounters on patient_mrn ordered by date",
    "Compare encounter_types of consecutive encounters"],
   sql="SELECT e1.encounter_type AS from_type, e2.encounter_type AS to_type, COUNT(*) AS transitions FROM encounters e1 JOIN encounters e2 ON e1.patient_mrn=e2.patient_mrn AND e2.admission_date >= e1.admission_date AND e1.encounter_id != e2.encounter_id AND julianday(e2.admission_date)-julianday(COALESCE(e1.discharge_date,e1.admission_date)) < 2 WHERE e1.encounter_type != e2.encounter_type GROUP BY e1.encounter_type, e2.encounter_type ORDER BY transitions DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Observation Unit Utilization",
   "Operations wants to analyze short-stay encounters (< 48 hours): average duration, count, and department distribution.",
   "Clinical Operations", ["sql"], 20,
   ["Open SQL Console", "Filter encounters under 48 hours", "Analyze by department", "Calculate average duration"],
   ["Observation stays typically < 48 hours",
    "Duration in hours for analysis"],
   sql="SELECT d.dept_name, COUNT(*) AS short_stays, ROUND(AVG((julianday(e.discharge_date)-julianday(e.admission_date))*24),1) AS avg_hours FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE e.discharge_date IS NOT NULL AND (julianday(e.discharge_date)-julianday(e.admission_date))*24 <= 48 GROUP BY d.dept_name ORDER BY short_stays DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Night Shift Activity Analysis",
   "Nursing leadership wants to understand night shift (7PM-7AM) clinical activity. Analyze vital documentation during night hours by department.",
   "Clinical Operations", ["sql"], 25,
   ["Open SQL Console", "Filter vitals recorded during night hours", "Count by department", "Compare against day shift volumes"],
   ["Night shift: strftime('%H', recorded_at) >= 19 OR < 7",
    "Compare night vs day vital documentation rates"],
   sql="SELECT d.dept_name, SUM(CASE WHEN CAST(strftime('%H',v.recorded_at) AS INTEGER) >= 19 OR CAST(strftime('%H',v.recorded_at) AS INTEGER) < 7 THEN 1 ELSE 0 END) AS night_vitals, SUM(CASE WHEN CAST(strftime('%H',v.recorded_at) AS INTEGER) >= 7 AND CAST(strftime('%H',v.recorded_at) AS INTEGER) < 19 THEN 1 ELSE 0 END) AS day_vitals FROM vitals v JOIN encounters e ON v.encounter_id=e.encounter_id JOIN departments d ON e.department_id=d.dept_id GROUP BY d.dept_name ORDER BY night_vitals DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

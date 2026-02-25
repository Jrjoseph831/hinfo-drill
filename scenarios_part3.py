"""scenarios_part3.py - Reporting, Communication, Documentation, Advanced Integration scenarios."""

SCENARIOS_PART3 = []


def _s(title, desc, category, tools, minutes, steps, hints, sql=None,
       difficulty="intermediate", roles=None):
    SCENARIOS_PART3.append({
        "title": title, "description": desc, "category": category,
        "tools": tools, "estimated_minutes": minutes, "steps": steps,
        "hints": hints, "sql_answer": sql, "difficulty": difficulty,
        "target_roles": roles or ["clinical_informatics_analyst"],
    })


# =========================================================================
# REPORTING (1-25)
# =========================================================================

_s("Generate CMS Quality Measure Report",
   "Regulatory requires a CMS quality measure report covering readmission rates, average LOS, and mortality indicators across all departments.",
   "Reporting", ["sql", "report"], 35,
   ["Open Report Builder", "Calculate 30-day readmission rate", "Calculate average LOS by department", "Compile metrics into a structured report"],
   ["Use generate_report with quality measure template",
    "Include department-level breakdowns"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Joint Commission Compliance Report",
   "Prepare a Joint Commission compliance report showing documentation completeness rates, medication reconciliation status, and vital sign documentation by department.",
   "Reporting", ["sql", "report"], 40,
   ["Open Report Builder", "Calculate documentation rates per department", "Check medication reconciliation compliance", "Compile into Joint Commission format"],
   ["Documentation rate = encounters with at least 1 audit entry / total encounters",
    "Medication reconciliation: encounters with medications documented"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Monthly Department Activity Report for {dept}",
   "Generate the monthly activity report for {dept}: encounter volume, average LOS, top diagnoses, provider productivity, and lab utilization.",
   "Reporting", ["sql", "report"], 30,
   ["Open SQL Console and Report Builder", "Calculate encounter volume and trends", "Determine top 5 diagnoses", "Compile provider encounter counts", "Summarize lab utilization"],
   ["Filter all queries to {dept} and current month",
    "Use strftime for month filtering"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("State Reportable Conditions Summary",
   "Public health reporting requires a summary of state-reportable conditions diagnosed this quarter. Compile cases by condition type and report to the health department.",
   "Reporting", ["sql", "report", "coding"], 30,
   ["Open SQL Console", "Identify reportable condition ICD-10 codes", "Query diagnoses for matches in the current quarter", "Generate the state report format"],
   ["Reportable conditions include infectious diseases: A00-B99",
    "Filter diagnosed_date to current quarter"],
   sql="SELECT dx.icd10_code, dx.description, COUNT(DISTINCT dx.patient_mrn) AS patient_count, COUNT(*) AS total_cases, MIN(dx.diagnosed_date) AS first_case, MAX(dx.diagnosed_date) AS last_case FROM diagnoses dx WHERE dx.icd10_code LIKE 'A%' OR dx.icd10_code LIKE 'B%' GROUP BY dx.icd10_code, dx.description HAVING COUNT(*) >= 1 ORDER BY patient_count DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Executive Dashboard Summary Report",
   "The C-suite needs a one-page executive summary: total patients, encounters this month, bed occupancy, average LOS, top departments by volume, and staffing ratios.",
   "Reporting", ["sql", "report"], 30,
   ["Open Report Builder", "Calculate each executive metric", "Format for executive audience", "Generate the dashboard report"],
   ["Multiple aggregate queries for each metric",
    "Use UNION ALL or separate queries compiled into a report"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Infection Control Surveillance Report",
   "Infection prevention needs a surveillance report: healthcare-associated infection indicators based on lab results, antibiotic usage, and culture data.",
   "Reporting", ["sql", "report"], 35,
   ["Query lab results for culture-positive results", "Analyze antibiotic prescribing patterns", "Cross-reference with patient demographics", "Generate surveillance report"],
   ["Look for 'culture' in lab test_name",
    "Positive cultures with antibiotic starts suggest treatment of infections"],
   sql="SELECT lr.test_name, COUNT(*) AS total_tests, COUNT(DISTINCT lr.patient_mrn) AS patients FROM lab_results lr WHERE LOWER(lr.test_name) LIKE '%culture%' GROUP BY lr.test_name ORDER BY total_tests DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Pharmacy Utilization Report",
   "Pharmacy leadership needs a utilization report: top 20 medications by volume, prescriber distribution, and average prescription per patient metrics.",
   "Reporting", ["sql", "report"], 25,
   ["Open Report Builder", "Query top medications by prescription count", "Include prescriber analysis", "Calculate per-patient averages"],
   ["GROUP BY medication_name ORDER BY COUNT(*) DESC LIMIT 20",
    "Include COUNT(DISTINCT prescribing_provider_id) and COUNT(DISTINCT patient_mrn)"],
   sql="SELECT m.medication_name, COUNT(*) AS total_rx, COUNT(DISTINCT m.patient_mrn) AS unique_patients, COUNT(DISTINCT m.prescribing_provider_id) AS unique_prescribers, ROUND(COUNT(*)*1.0/NULLIF(COUNT(DISTINCT m.patient_mrn),0),1) AS rx_per_patient FROM medications m GROUP BY m.medication_name ORDER BY total_rx DESC LIMIT 20",
   difficulty="beginner", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Emergency Department Operations Report",
   "ED leadership needs a monthly operations report: total visits, average visit duration, visits by time of day, and top presenting diagnoses.",
   "Reporting", ["sql", "report"], 30,
   ["Open SQL Console and Report Builder", "Calculate ED visit metrics", "Break down by time of day", "Compile top diagnoses"],
   ["Filter encounter_type = 'Emergency'",
    "Use strftime('%H', admission_date) for time-of-day analysis"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Lab Quality Indicator Report",
   "Lab QA needs a report on test volume, abnormal result rates, and missing reference ranges by test type.",
   "Reporting", ["sql", "report"], 25,
   ["Open SQL Console", "Count tests by type", "Calculate abnormal result rates", "Identify tests with missing reference ranges", "Compile into QA report"],
   ["Abnormal = outside reference range",
    "Missing reference = reference_range IS NULL or empty"],
   sql="SELECT test_name, COUNT(*) AS total, SUM(CASE WHEN reference_range IS NULL OR reference_range='' THEN 1 ELSE 0 END) AS missing_range, ROUND(SUM(CASE WHEN reference_range IS NULL OR reference_range='' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) AS pct_missing FROM lab_results GROUP BY test_name ORDER BY total DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Credentialing Data Report",
   "Medical staff office needs a credentialing data report: all providers with their specialties, encounter volumes, and patient panel sizes.",
   "Reporting", ["sql", "report"], 20,
   ["Open SQL Console", "Query all provider data", "Join with encounter counts", "Generate the credentialing report"],
   ["LEFT JOIN providers with encounter aggregates",
    "Include providers with zero encounters"],
   sql="SELECT pr.provider_id, pr.first_name||' '||pr.last_name AS name, pr.credential, pr.specialty, COUNT(DISTINCT e.encounter_id) AS encounters, COUNT(DISTINCT e.patient_mrn) AS patients FROM providers pr LEFT JOIN encounters e ON pr.provider_id=e.attending_provider_id GROUP BY pr.provider_id ORDER BY encounters DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Regulatory Submission: Hospital Compare Data",
   "Quality reporting needs data formatted for CMS Hospital Compare: readmission rates, complication rates, and patient satisfaction proxies.",
   "Reporting", ["sql", "report", "coding"], 40,
   ["Calculate readmission rates for target conditions", "Estimate complication rates from secondary diagnoses", "Compile encounter volume metrics", "Format for CMS submission"],
   ["Target conditions for Hospital Compare: heart failure, pneumonia, hip/knee",
    "Complications: secondary diagnoses added after admission"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Bed Utilization Report",
   "Facilities management needs a bed utilization report: average occupancy by department, peak occupancy days, and turnover rates.",
   "Reporting", ["sql", "report"], 25,
   ["Open SQL Console", "Calculate average daily census by department", "Identify peak occupancy days", "Calculate bed turnover rate"],
   ["Daily census = patients present on that day",
    "Turnover = discharges / average census"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Clinical Research Registry Report",
   "Research department needs a registry of patients matching specific criteria for a clinical trial: age 45-75 with {dx_desc} and no contraindicated medications.",
   "Reporting", ["sql", "report"], 30,
   ["Open SQL Console", "Identify patients in the age range", "Filter by diagnosis {dx_code}", "Exclude patients on contraindicated medications", "Generate registry report"],
   ["Calculate age from DOB for age filter",
    "LEFT JOIN medications to exclude specific drugs"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, p.gender, ROUND((julianday('now')-julianday(p.dob))/365.25) AS age, MAX(dx.diagnosed_date) AS last_dx_date FROM patients p JOIN diagnoses dx ON p.mrn=dx.patient_mrn WHERE dx.icd10_code='{dx_code}' AND (julianday('now')-julianday(p.dob))/365.25 BETWEEN 45 AND 75 GROUP BY p.mrn ORDER BY p.last_name",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Discharge Against Medical Advice Report",
   "Risk management needs a report on patients who left AMA (against medical advice). Identify encounters with early or unusual discharge patterns.",
   "Reporting", ["sql", "report"], 25,
   ["Open SQL Console", "Identify encounters with very short LOS and active diagnoses", "Flag encounters where discharge happened within hours of admission", "Include patient and provider details"],
   ["Very short LOS with active medications may indicate AMA",
    "AMA discharges often have LOS < 1 day with multiple active diagnoses"],
   sql="SELECT e.encounter_id, p.mrn, p.first_name||' '||p.last_name AS patient, d.dept_name, e.admission_date, e.discharge_date, ROUND((julianday(e.discharge_date)-julianday(e.admission_date))*24,1) AS hours, COUNT(DISTINCT dx.diagnosis_id) AS active_dx FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn JOIN departments d ON e.department_id=d.dept_id LEFT JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE e.discharge_date IS NOT NULL AND (julianday(e.discharge_date)-julianday(e.admission_date))*24 < 12 AND e.encounter_type != 'Emergency' GROUP BY e.encounter_id HAVING COUNT(DISTINCT dx.diagnosis_id) >= 2 ORDER BY hours ASC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Surgical Site Infection Tracking Report",
   "Infection prevention needs to track potential surgical site infections. Correlate surgical encounters with subsequent infection diagnoses and antibiotic prescriptions.",
   "Reporting", ["sql", "report", "coding"], 40,
   ["Identify surgical encounters", "Find infection diagnoses within 30 days post-surgery", "Check for antibiotic prescriptions in the same window", "Generate SSI tracking report"],
   ["Surgical encounters: encounter_type or department containing 'surg'",
    "Infection codes: T81.4x (surgical site infection)"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Patient Satisfaction Proxy Report",
   "Patient experience team wants a proxy for satisfaction: average wait time to first clinical contact, documentation completeness, and follow-up rates by department.",
   "Reporting", ["sql", "report"], 30,
   ["Calculate time to first vital (wait time proxy)", "Measure documentation completeness from audit_log", "Calculate follow-up encounter rates", "Compile by department"],
   ["Wait time proxy = first vital recorded_at - admission_date",
    "Follow-up rate = patients with subsequent encounter within 30 days"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Annual Statistical Report Data Compilation",
   "Administration needs data for the hospital's annual statistical report: total admissions, discharges, patient days, average census, and department volumes.",
   "Reporting", ["sql", "report"], 30,
   ["Open SQL Console", "Calculate total admissions for the year", "Calculate total patient days", "Compute average daily census", "Break down by department"],
   ["Patient days = SUM of individual LOS for all encounters",
    "Average census = total patient days / 365"],
   sql="SELECT COUNT(*) AS total_admissions, SUM(CASE WHEN discharge_date IS NOT NULL THEN 1 ELSE 0 END) AS total_discharges, ROUND(SUM(CASE WHEN discharge_date IS NOT NULL THEN julianday(discharge_date)-julianday(admission_date) ELSE julianday('now')-julianday(admission_date) END)) AS total_patient_days, ROUND(SUM(CASE WHEN discharge_date IS NOT NULL THEN julianday(discharge_date)-julianday(admission_date) ELSE julianday('now')-julianday(admission_date) END)/365,1) AS avg_daily_census FROM encounters WHERE admission_date >= datetime('now','-365 days')",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Readmission Root Cause Analysis Report",
   "Quality improvement needs a root cause analysis of readmissions. For readmitted patients, compare their initial diagnosis, LOS, and medications with non-readmitted patients.",
   "Reporting", ["sql", "report"], 40,
   ["Identify readmitted patients", "Extract clinical characteristics", "Compare with non-readmitted cohort", "Document findings in report format"],
   ["Build readmitted and control cohorts",
    "Compare average LOS, diagnosis count, medication count between groups"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Meaningful Use Metrics Report",
   "IT compliance needs to report on Meaningful Use metrics: CPOE rates, e-prescribing rates, and clinical summary provision for patient transitions.",
   "Reporting", ["sql", "report", "audit"], 30,
   ["Calculate CPOE rate from medication entries", "Estimate e-prescribing from audit_log", "Check for clinical summaries at transitions", "Compile into MU report format"],
   ["CPOE rate approximated by medications with prescribing_provider_id",
    "E-prescribing: medications with electronic submission audit entries"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Antibiogram Report Generation",
   "Infection control needs an antibiogram report: antibiotic susceptibility patterns based on culture results and antibiotic prescription data.",
   "Reporting", ["sql", "report"], 35,
   ["Query culture lab results", "Match with antibiotic prescriptions", "Calculate susceptibility patterns", "Generate antibiogram format report"],
   ["Cultures in lab_results where test_name LIKE '%culture%'",
    "Match patient/encounter with antibiotic medications"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Pediatric Quality Metrics Report",
   "Pediatrics needs quality metrics for patients under 18: immunization-related encounters, well-child visit frequency, and common diagnoses.",
   "Reporting", ["sql", "report"], 25,
   ["Open SQL Console", "Filter patients by age < 18", "Analyze encounter patterns for pediatric patients", "Compile common diagnoses and visit frequencies"],
   ["Age filter: (julianday('now')-julianday(dob))/365.25 < 18",
    "Well-child: outpatient encounters for pediatric patients"],
   sql="SELECT dx.icd10_code, dx.description, COUNT(DISTINCT dx.patient_mrn) AS patients, COUNT(*) AS occurrences FROM diagnoses dx JOIN patients p ON dx.patient_mrn=p.mrn WHERE (julianday('now')-julianday(p.dob))/365.25 < 18 GROUP BY dx.icd10_code, dx.description ORDER BY occurrences DESC LIMIT 15",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Geriatric Fall Risk Assessment Report",
   "Geriatrics needs a fall risk report: patients over 65 on multiple medications (polypharmacy) with relevant diagnoses and recent vital sign abnormalities.",
   "Reporting", ["sql", "report"], 30,
   ["Identify geriatric patients (65+)", "Check for polypharmacy (5+ medications)", "Pull fall-risk diagnoses", "Check for orthostatic vital signs"],
   ["Age >= 65, medication count >= 5",
    "Fall-risk diagnoses: dizziness, gait abnormality, weakness"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, ROUND((julianday('now')-julianday(p.dob))/365.25) AS age, m.med_count, COALESCE(dx.dx_count,0) AS risk_dx_count FROM patients p JOIN (SELECT patient_mrn, COUNT(*) AS med_count FROM medications GROUP BY patient_mrn HAVING COUNT(*) >= 5) m ON p.mrn=m.patient_mrn LEFT JOIN (SELECT patient_mrn, COUNT(DISTINCT icd10_code) AS dx_count FROM diagnoses WHERE LOWER(description) LIKE '%fall%' OR LOWER(description) LIKE '%dizz%' OR LOWER(description) LIKE '%gait%' OR LOWER(description) LIKE '%weakness%' GROUP BY patient_mrn) dx ON p.mrn=dx.patient_mrn WHERE (julianday('now')-julianday(p.dob))/365.25 >= 65 ORDER BY m.med_count DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "clinical_staff"])


# =========================================================================
# COMMUNICATION (26-50)
# =========================================================================

_s("HL7 ADT Message Routing Analysis",
   "The interface team needs to analyze ADT message routing. Parse sample ADT messages and verify correct routing based on message type and patient location.",
   "Communication", ["hl7", "sql"], 25,
   ["Generate sample ADT messages", "Parse MSH segment for routing info", "Verify sending/receiving applications", "Check patient location in PV1"],
   ["MSH-3/4: sending app/facility, MSH-5/6: receiving app/facility",
    "PV1-3: patient location should match department data"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Lab Result Interface Validation",
   "Validate that HL7 ORU (lab result) messages correctly map lab data from the lab_results table. Compare parsed message content with database values.",
   "Communication", ["hl7", "sql"], 30,
   ["Generate HL7 messages from lab data", "Parse OBX segments for results", "Compare parsed values with lab_results table", "Document any mapping discrepancies"],
   ["OBX-3: test identifier, OBX-5: value, OBX-6: units, OBX-7: reference range",
    "Values should match lab_results.test_name, result_value, unit, reference_range"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 Message Acknowledgment Workflow",
   "Document the HL7 message acknowledgment workflow. Generate an ADT message, show the expected ACK format, and explain error handling for NAK responses.",
   "Communication", ["hl7"], 20,
   ["Generate a sample ADT message", "Construct the corresponding ACK message", "Document MSA segment codes (AA, AE, AR)", "Explain retry logic for NAK"],
   ["MSA-1: AA=Accept, AE=Error, AR=Reject",
    "MSA-2: Message control ID from original MSH-10"],
   sql=None,
   difficulty="beginner", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Cross-System Patient Identifier Mapping",
   "Patient identifiers differ between systems. Map patient MRNs to HL7 PID-3 identifiers and verify consistency across generated messages.",
   "Communication", ["hl7", "sql"], 25,
   ["Query patient MRNs from database", "Generate HL7 messages for selected patients", "Parse PID-3 to extract identifiers", "Verify MRN mapping consistency"],
   ["PID-3 contains the patient identifier list",
    "Compare parsed PID-3 values with database MRN values"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 Message Error Recovery Procedure",
   "Document the error recovery procedure when HL7 messages fail. Analyze interface errors, identify retry strategies, and create an error handling playbook.",
   "Communication", ["hl7", "audit"], 30,
   ["Query audit_log for interface error events", "Categorize error types", "Define recovery procedures for each type", "Document the error handling playbook"],
   ["Common errors: connection timeout, invalid segment, missing required field",
    "Check audit_log for patterns in error frequency and timing"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator"])

_s("ADT Feed Configuration Review",
   "Review the ADT feed configuration by analyzing which ADT event types (A01, A02, A03, A04, A08) are most frequently generated from encounter data.",
   "Communication", ["hl7", "sql"], 25,
   ["Map encounter events to ADT message types", "Generate sample messages for each type", "Verify message content accuracy", "Document the ADT feed configuration"],
   ["A01=Admit, A02=Transfer, A03=Discharge, A04=Register, A08=Update",
    "Match encounter_type to expected ADT event"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 Segment Delimiter Validation",
   "After an interface upgrade, validate that HL7 segment delimiters are correct. Parse messages and verify field, component, subcomponent, and repetition separators.",
   "Communication", ["hl7"], 15,
   ["Generate sample HL7 messages", "Parse MSH segment for encoding characters", "Verify delimiter configuration", "Document any issues"],
   ["MSH-1: field separator (|), MSH-2: encoding characters (^~\\&)",
    "Any deviation from standard delimiters indicates a configuration issue"],
   sql=None,
   difficulty="beginner", roles=["system_administrator"])

_s("Referral Message Workflow Mapping",
   "Map the electronic referral workflow by analyzing patient encounters across departments and generating the corresponding HL7 REF messages.",
   "Communication", ["hl7", "sql"], 30,
   ["Identify patients with cross-department encounters", "Map the referral pathway", "Generate HL7 messages for the referral", "Validate message content"],
   ["Patients seen in multiple departments suggest referral activity",
    "REF messages or A02 (transfer) messages carry referral data"],
   sql="SELECT e1.patient_mrn, d1.dept_name AS from_dept, d2.dept_name AS to_dept, e1.discharge_date AS referral_date, e2.admission_date AS arrival_date FROM encounters e1 JOIN encounters e2 ON e1.patient_mrn=e2.patient_mrn AND e2.admission_date >= e1.admission_date AND e1.encounter_id != e2.encounter_id JOIN departments d1 ON e1.department_id=d1.dept_id JOIN departments d2 ON e2.department_id=d2.dept_id WHERE d1.dept_id != d2.dept_id ORDER BY e1.discharge_date DESC LIMIT 20",
   difficulty="advanced", roles=["clinical_informatics_analyst", "system_administrator"])

_s("HL7 Batch Message Processing",
   "The interface engine needs to process HL7 messages in batch mode. Generate a batch of messages and validate they can be processed sequentially.",
   "Communication", ["hl7"], 25,
   ["Generate multiple HL7 messages", "Format as a batch with BHS/BTS header/trailer", "Validate batch structure", "Document batch processing requirements"],
   ["Batch starts with BHS (batch header) and ends with BTS (batch trailer)",
    "FHS/FTS for file-level wrapping if sending multiple batches"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator"])

_s("Patient Merge Message Handling",
   "When duplicate patients are merged, an A40 ADT message is sent. Generate and validate A40 messages for patient merge scenarios from duplicate records.",
   "Communication", ["hl7", "sql"], 30,
   ["Identify potential duplicate patients in database", "Generate A40 merge messages", "Validate message structure", "Document merge notification workflow"],
   ["A40 contains the surviving and non-surviving MRN",
    "MRG segment carries the prior (non-surviving) patient ID"],
   sql="SELECT p1.mrn AS mrn1, p2.mrn AS mrn2, p1.first_name, p1.last_name, p1.dob FROM patients p1 JOIN patients p2 ON p1.first_name=p2.first_name AND p1.last_name=p2.last_name AND p1.dob=p2.dob AND p1.mrn < p2.mrn",
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 ORM Order Message Analysis",
   "Analyze HL7 ORM (order) messages to verify that medication and lab orders are properly represented. Compare order data with database records.",
   "Communication", ["hl7", "sql"], 30,
   ["Generate HL7 ORM messages from medication data", "Parse ORC and OBR segments", "Compare with medication table data", "Verify order status and timing"],
   ["ORC: common order segment, OBR: observation request",
    "ORC-1: order control (NW=new, CA=cancel, SC=status change)"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Interface Monitoring Dashboard Data",
   "Build an interface monitoring dashboard. Compile metrics on message volume, error rate, and response time from audit log data.",
   "Communication", ["sql", "hl7", "report"], 25,
   ["Query audit_log for interface-related events", "Calculate message volume per hour", "Determine error rate", "Compile dashboard data"],
   ["Look for 'interface', 'hl7', 'message' actions in audit_log",
    "Error rate = error events / total events * 100"],
   sql="SELECT strftime('%Y-%m-%d %H:00', timestamp) AS hour, COUNT(*) AS total_events, SUM(CASE WHEN LOWER(action) LIKE '%error%' OR LOWER(action) LIKE '%fail%' THEN 1 ELSE 0 END) AS errors, ROUND(SUM(CASE WHEN LOWER(action) LIKE '%error%' OR LOWER(action) LIKE '%fail%' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(*),0),1) AS error_rate FROM audit_log WHERE LOWER(action) LIKE '%interface%' OR LOWER(action) LIKE '%hl7%' OR LOWER(action) LIKE '%message%' GROUP BY strftime('%Y-%m-%d %H', timestamp) ORDER BY hour DESC LIMIT 48",
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Data Exchange Standards Comparison",
   "The CIO wants a comparison of HL7 v2.x message structures used in the current system. Document the message types, their purposes, and key segments.",
   "Communication", ["hl7"], 20,
   ["Review HL7 field reference", "Document ADT, ORM, ORU, SIU message types", "List key segments for each type", "Create a reference comparison document"],
   ["Use get_hl7_field_reference() for segment details",
    "ADT: patient admin, ORM: orders, ORU: results, SIU: scheduling"],
   sql=None,
   difficulty="beginner", roles=["clinical_informatics_analyst"])

_s("HL7 Message Content Encryption Review",
   "Security needs to verify that sensitive data in HL7 messages is properly handled. Review PID segments for PHI content and document protection requirements.",
   "Communication", ["hl7", "audit"], 25,
   ["Generate sample HL7 messages with patient data", "Identify all PHI fields in PID segments", "Document which fields contain sensitive data", "Recommend encryption/masking strategies"],
   ["PHI in PID: name (PID-5), DOB (PID-7), SSN (PID-19), address (PID-11)",
    "All PHI fields must be protected in transit"],
   sql=None,
   difficulty="intermediate", roles=["compliance_officer", "system_administrator"])

_s("HL7 Message Transformation Mapping",
   "A new receiving system requires a different HL7 message format. Document the field mapping between the current and target formats.",
   "Communication", ["hl7"], 30,
   ["Parse current message format", "Document field positions", "Define mapping to target format", "Create transformation specification"],
   ["Compare MSH, PID, PV1 field positions between formats",
    "Document any field splits, merges, or translations needed"],
   sql=None,
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Real-Time Notification System Design",
   "Design a real-time notification system for critical lab results. Map the data flow from lab_results to HL7 ORU messages to provider alerts.",
   "Communication", ["hl7", "sql", "audit"], 35,
   ["Identify critical lab result criteria", "Generate HL7 ORU messages for critical results", "Map the alert workflow through audit_log", "Document the notification pipeline"],
   ["Critical: results significantly outside reference range",
    "ORU messages trigger alerts; track in audit_log"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Interface Testing Protocol Development",
   "Develop an interface testing protocol by generating test HL7 messages covering all message types and validating proper handling.",
   "Communication", ["hl7"], 25,
   ["Generate test messages for each HL7 type (ADT, ORM, ORU)", "Include edge cases: empty fields, special characters", "Validate each test message", "Document expected vs actual results"],
   ["Cover positive and negative test cases",
    "Include messages with missing required fields to test error handling"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator"])

_s("HL7 Message Version Compatibility Check",
   "After an upgrade, verify that HL7 v2.5.1 messages are backward-compatible with v2.3 receivers. Compare structural differences between versions.",
   "Communication", ["hl7"], 25,
   ["Generate messages in v2.5.1 format", "Identify fields that differ from v2.3", "Document breaking changes", "Recommend compatibility strategies"],
   ["v2.5.1 added new segments and fields not in v2.3",
    "Receivers may reject unknown segments or fields"],
   sql=None,
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Clinical Document Sharing Workflow",
   "Map the clinical document sharing workflow: how documents are generated, encoded, and transmitted via HL7 MDM messages.",
   "Communication", ["hl7", "sql", "audit"], 30,
   ["Identify document generation events in audit_log", "Generate MDM-type HL7 messages", "Map the document lifecycle", "Document the sharing workflow"],
   ["MDM (Medical Document Management) messages carry clinical documents",
    "Track document actions in audit_log"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Patient Location Tracking via HL7",
   "Facilities wants to track patient locations through HL7 ADT messages. Map A02 (transfer) messages to understand patient movement between departments.",
   "Communication", ["hl7", "sql"], 25,
   ["Query encounters showing department changes", "Generate A02 transfer messages", "Parse PV1 for location data", "Map patient movement timeline"],
   ["A02 is triggered on patient transfer between units",
    "PV1-3: assigned patient location, PV1-6: prior patient location"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])


# =========================================================================
# DOCUMENTATION (51-75)
# =========================================================================

_s("Clinical Documentation Integrity Review for {dept}",
   "CDI team needs to review documentation integrity in {dept}. Identify encounters where the diagnosis coding may not fully reflect the documented clinical picture.",
   "Documentation", ["sql", "coding", "ehr"], 35,
   ["Query encounters for {dept} with low diagnosis counts", "Use Code Mapper to verify code specificity", "Identify potential CDI query opportunities", "Document findings"],
   ["Encounters with only 1-2 diagnoses for complex admissions suggest under-documentation",
    "Check for unspecified codes (ending in .9) that could be more specific"],
   sql="SELECT e.encounter_id, p.mrn, p.first_name||' '||p.last_name AS patient, e.admission_date, COALESCE(dc.dx_count,0) AS dx_count, CAST(julianday(COALESCE(e.discharge_date,'now'))-julianday(e.admission_date) AS INTEGER) AS los FROM encounters e JOIN patients p ON e.patient_mrn=p.mrn JOIN departments d ON e.department_id=d.dept_id LEFT JOIN (SELECT encounter_id, COUNT(*) AS dx_count FROM diagnoses GROUP BY encounter_id) dc ON e.encounter_id=dc.encounter_id WHERE d.dept_name='{dept}' AND COALESCE(dc.dx_count,0) <= 2 AND julianday(COALESCE(e.discharge_date,'now'))-julianday(e.admission_date) > 3 ORDER BY los DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Problem List Reconciliation Audit",
   "Quality team needs to audit problem list accuracy. Compare active problem lists (recent diagnoses) against encounter diagnoses for consistency.",
   "Documentation", ["sql", "ehr", "coding"], 30,
   ["Query distinct diagnoses per patient as their problem list", "Compare against recent encounter diagnoses", "Identify stale problems not seen recently", "Identify new conditions not on the problem list"],
   ["Active problems: diagnoses seen in the last 12 months",
    "Stale problems: diagnoses not seen in > 12 months"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, dx.icd10_code, dx.description, MAX(dx.diagnosed_date) AS last_seen, CAST(julianday('now')-julianday(MAX(dx.diagnosed_date)) AS INTEGER) AS days_since, CASE WHEN julianday('now')-julianday(MAX(dx.diagnosed_date)) > 365 THEN 'STALE' ELSE 'ACTIVE' END AS status FROM diagnoses dx JOIN patients p ON dx.patient_mrn=p.mrn GROUP BY p.mrn, dx.icd10_code ORDER BY p.mrn, last_seen DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Medication Reconciliation Completeness Check",
   "The Joint Commission requires medication reconciliation at transitions of care. Check if patients have medication documentation at both admission and discharge.",
   "Documentation", ["sql", "ehr"], 25,
   ["Query encounters with both admission and discharge dates", "Check for medication entries near admission", "Check for medication entries near discharge", "Calculate reconciliation completion rate"],
   ["Medications near admission: start_date within 1 day of admission",
    "Medications near discharge: active at discharge time"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Clinical Note Turnaround Time",
   "Medical records needs to measure clinical note turnaround: time from encounter to documentation completion based on audit log entries.",
   "Documentation", ["sql", "audit"], 25,
   ["Query encounters and their admission dates", "Find documentation events in audit_log", "Calculate time from admission to first documentation", "Report by department and provider"],
   ["Look for 'note', 'document', or 'sign' actions in audit_log",
    "Calculate hours between encounter admission and first documentation event"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Discharge Summary Completion Audit",
   "HIM needs to verify discharge summary completion rates. Identify discharged encounters that may be missing discharge documentation.",
   "Documentation", ["sql", "audit", "report"], 25,
   ["Query all discharged encounters", "Check audit_log for discharge documentation events", "Identify encounters without documentation", "Report completion rate by department"],
   ["Look for 'discharge' and ('note' or 'summary') in audit_log actions",
    "Match on encounter or patient resource_id"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Diagnosis Specificity Improvement Opportunities",
   "CDI team wants to identify opportunities to improve diagnosis coding specificity. Find frequently used unspecified ICD-10 codes that could be more specific.",
   "Documentation", ["sql", "coding"], 25,
   ["Open SQL Console and Code Mapper", "Find unspecified codes (ending in .9)", "Count frequency of each", "Use Code Mapper to suggest more specific alternatives"],
   ["Unspecified codes end in .9",
    "Higher frequency unspecified codes have the most impact"],
   sql="SELECT dx.icd10_code, dx.description, COUNT(*) AS frequency, COUNT(DISTINCT dx.patient_mrn) AS patients FROM diagnoses dx WHERE dx.icd10_code LIKE '%.9' GROUP BY dx.icd10_code, dx.description ORDER BY frequency DESC LIMIT 20",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Present on Admission Indicator Review",
   "Coding compliance needs to verify Present on Admission (POA) documentation. Identify diagnoses added after initial encounter assessment.",
   "Documentation", ["sql", "coding"], 30,
   ["Query diagnoses with diagnosed_date", "Compare diagnosis date with encounter admission date", "Flag diagnoses added >24 hours after admission", "Report potential hospital-acquired conditions"],
   ["POA: diagnosed_date within 24 hours of admission_date",
    "Later diagnoses may indicate hospital-acquired conditions"],
   sql="SELECT e.encounter_id, p.mrn, dx.icd10_code, dx.description, e.admission_date, dx.diagnosed_date, ROUND((julianday(dx.diagnosed_date)-julianday(e.admission_date))*24,1) AS hours_after_admission, CASE WHEN (julianday(dx.diagnosed_date)-julianday(e.admission_date))*24 <= 24 THEN 'POA' ELSE 'NOT POA' END AS poa_status FROM diagnoses dx JOIN encounters e ON dx.encounter_id=e.encounter_id JOIN patients p ON dx.patient_mrn=p.mrn WHERE dx.diagnosed_date IS NOT NULL AND e.admission_date IS NOT NULL ORDER BY hours_after_admission DESC LIMIT 30",
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Clinical Documentation Timeliness by Provider",
   "Quality assurance needs to measure documentation timeliness by provider. Compare diagnosis entry dates against encounter admission dates per provider.",
   "Documentation", ["sql", "report"], 25,
   ["Open SQL Console", "Calculate average diagnosis entry delay per provider", "Rank providers by timeliness", "Report outliers"],
   ["Delay = diagnosed_date - admission_date in hours",
    "GROUP BY provider for per-provider analysis"],
   sql="SELECT pr.first_name||' '||pr.last_name AS provider, pr.specialty, COUNT(DISTINCT e.encounter_id) AS encounters, ROUND(AVG((julianday(dx.diagnosed_date)-julianday(e.admission_date))*24),1) AS avg_hours_to_document FROM encounters e JOIN providers pr ON e.attending_provider_id=pr.provider_id JOIN diagnoses dx ON e.encounter_id=dx.encounter_id WHERE dx.diagnosed_date IS NOT NULL GROUP BY pr.provider_id HAVING COUNT(DISTINCT e.encounter_id) >= 3 ORDER BY avg_hours_to_document DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Vital Signs Documentation Frequency Analysis",
   "Nursing leadership wants to analyze how frequently vital signs are documented. Calculate vitals-per-day rate for each department.",
   "Documentation", ["sql", "report"], 20,
   ["Open SQL Console", "Count vitals per encounter-day", "Average by department", "Identify departments below standard"],
   ["Calculate vitals per encounter per day of stay",
    "Standard: at least 3 vital sets per day for inpatients"],
   sql="SELECT d.dept_name, COUNT(v.vital_id) AS total_vitals, COUNT(DISTINCT e.encounter_id) AS encounters, ROUND(COUNT(v.vital_id)*1.0/NULLIF(COUNT(DISTINCT e.encounter_id),0),1) AS vitals_per_encounter FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN vitals v ON e.encounter_id=v.encounter_id GROUP BY d.dept_name ORDER BY vitals_per_encounter",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Duplicate Documentation Detection",
   "Quality needs to identify potential duplicate documentation — multiple audit log entries suggesting the same note was entered more than once for an encounter.",
   "Documentation", ["sql", "audit"], 25,
   ["Open SQL Console", "Query audit_log for documentation actions", "Find duplicate entries per encounter/user", "Report potential duplicates"],
   ["Look for same user, resource, and action within a short time window",
    "Duplicate entries within 5 minutes suggest copy-paste or system issues"],
   sql="SELECT a1.user_id, a1.resource_id, a1.action, COUNT(*) AS duplicate_count, MIN(a1.timestamp) AS first_entry, MAX(a1.timestamp) AS last_entry FROM audit_log a1 WHERE LOWER(a1.action) LIKE '%note%' OR LOWER(a1.action) LIKE '%document%' GROUP BY a1.user_id, a1.resource_id, a1.action, DATE(a1.timestamp) HAVING COUNT(*) > 2 ORDER BY duplicate_count DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Informed Consent Documentation Audit",
   "Risk management needs to verify informed consent documentation for surgical encounters. Check for consent-related audit entries.",
   "Documentation", ["sql", "audit"], 25,
   ["Identify surgical encounters", "Check audit_log for consent documentation", "Calculate consent documentation rate", "Report encounters missing consent"],
   ["Surgical encounters: encounter_type or department related to surgery",
    "Look for 'consent' actions in audit_log"],
   sql=None,
   difficulty="intermediate", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Allergy Documentation Completeness",
   "Patient safety requires comprehensive allergy documentation. Check what percentage of patients have allergy-related entries documented.",
   "Documentation", ["sql", "audit", "ehr"], 20,
   ["Open SQL Console", "Check audit_log for allergy documentation actions", "Compare against total patient count", "Calculate documentation rate"],
   ["Look for 'allergy' actions in audit_log",
    "Count unique patients with allergy documentation vs total patients"],
   sql="SELECT COUNT(DISTINCT p.mrn) AS total_patients, COUNT(DISTINCT al.resource_id) AS patients_with_allergy_doc, ROUND(COUNT(DISTINCT al.resource_id)*100.0/NULLIF(COUNT(DISTINCT p.mrn),0),1) AS documentation_rate FROM patients p LEFT JOIN audit_log al ON p.mrn=al.resource_id AND LOWER(al.action) LIKE '%allergy%'",
   difficulty="beginner", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Copy-Forward Documentation Risk Assessment",
   "Risk management wants to identify potential copy-forward documentation. Find cases where the same diagnosis text appears in consecutive encounters for the same patient.",
   "Documentation", ["sql", "ehr"], 30,
   ["Open SQL Console", "Find patients with identical diagnosis descriptions across encounters", "Check if descriptions are copied without updates", "Report high-risk cases"],
   ["Self-join diagnoses on patient_mrn and description across different encounters",
    "Same description repeated may indicate copy-forward without review"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, dx.description, COUNT(DISTINCT dx.encounter_id) AS encounter_count, MIN(dx.diagnosed_date) AS first_use, MAX(dx.diagnosed_date) AS last_use FROM diagnoses dx JOIN patients p ON dx.patient_mrn=p.mrn GROUP BY p.mrn, dx.description HAVING COUNT(DISTINCT dx.encounter_id) >= 3 ORDER BY encounter_count DESC LIMIT 20",
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Physician Query Response Rate Tracking",
   "CDI management needs to track physician query response rates. Analyze audit log for CDI query and response events.",
   "Documentation", ["sql", "audit"], 25,
   ["Open SQL Console", "Find CDI query events in audit_log", "Find corresponding response events", "Calculate response rate and average response time"],
   ["CDI queries: actions containing 'query' or 'cdi'",
    "Responses: actions containing 'respond' or 'answer' for same resource"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Progress Note Documentation Audit for {dept}",
   "Medical records needs to audit daily progress note documentation in {dept}. Identify days of stay without corresponding note entries.",
   "Documentation", ["sql", "audit"], 30,
   ["Query inpatient encounters in {dept}", "Check audit_log for daily note entries", "Identify stay-days without notes", "Calculate documentation compliance rate"],
   ["For each encounter, check each day between admission and discharge",
    "Look for 'note' or 'progress' actions per day per encounter"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Lab Result Acknowledgment Documentation",
   "Patient safety requires that all abnormal lab results be acknowledged. Track acknowledgment rates from audit log.",
   "Documentation", ["sql", "audit"], 25,
   ["Identify abnormal lab results", "Check audit_log for acknowledgment of each result", "Calculate acknowledgment rate", "Report unacknowledged results"],
   ["Abnormal: results outside reference range",
    "Look for 'acknowledge', 'review', or 'view' actions tied to lab results"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Medication Allergy Cross-Reference Documentation",
   "Pharmacy safety wants to verify that medication prescriptions are cross-referenced against allergy documentation. Audit the documentation trail.",
   "Documentation", ["sql", "audit", "ehr"], 25,
   ["Identify medication prescription events", "Check for allergy review actions before or concurrent with prescribing", "Calculate the cross-reference rate", "Report prescriptions without allergy check"],
   ["Look for 'allergy check' or 'allergy review' actions near prescription time",
    "Time-match: allergy check within 1 hour of medication prescription"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Assessment and Plan Documentation Quality",
   "Quality review needs to evaluate the completeness of clinical assessments. Cross-reference diagnoses with documented assessments in audit trail.",
   "Documentation", ["sql", "audit", "ehr"], 30,
   ["Query encounters with diagnoses", "Check audit_log for assessment documentation", "Calculate encounters with both diagnosis and assessment", "Report documentation quality metrics"],
   ["Assessment documentation: 'assessment', 'plan', or 'a/p' in audit actions",
    "Compare diagnosis count with documentation events per encounter"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Transition of Care Documentation Audit",
   "Joint Commission requires documentation at care transitions. Verify that transfers between departments have corresponding transition documentation.",
   "Documentation", ["sql", "audit"], 30,
   ["Identify patients with encounters in multiple departments", "Check for transition documentation in audit_log", "Calculate transition documentation rate", "Report gaps"],
   ["Transitions: same patient with sequential encounters in different departments",
    "Look for 'transfer', 'handoff', or 'transition' actions"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Documentation Template Utilization Analysis",
   "Informatics wants to understand which documentation templates are most used. Analyze audit log for template-related actions.",
   "Documentation", ["sql", "audit"], 20,
   ["Query audit_log for template actions", "Count usage per template type", "Analyze usage patterns by department", "Identify unused or underused templates"],
   ["Look for 'template' in audit_log actions",
    "Group by action or resource_type for template categories"],
   sql="SELECT action, COUNT(*) AS usage_count, COUNT(DISTINCT user_id) AS unique_users, COUNT(DISTINCT DATE(timestamp)) AS active_days FROM audit_log WHERE LOWER(action) LIKE '%template%' OR LOWER(action) LIKE '%form%' GROUP BY action ORDER BY usage_count DESC",
   difficulty="beginner", roles=["clinical_informatics_analyst"])


# =========================================================================
# ADVANCED INTEGRATION (76-100)
# =========================================================================

_s("End-to-End Patient Journey Analysis",
   "Trace a complete patient journey for {mrn}: from registration through encounters, diagnoses, labs, medications, vitals, and audit trail. Create a comprehensive timeline.",
   "Advanced Integration", ["sql", "ehr", "hl7", "audit", "report"], 50,
   ["Query all encounters for patient {mrn}", "Pull all diagnoses, medications, labs, vitals", "Extract audit trail for this patient", "Generate HL7 messages for key events", "Compile into a patient journey timeline"],
   ["Query each table WHERE patient_mrn = '{mrn}'",
    "Order all events chronologically for the timeline"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst"])

_s("Cross-System Data Reconciliation",
   "Data governance needs to reconcile clinical data across SQL, HL7, and audit systems. Verify that encounter data matches across all three sources.",
   "Advanced Integration", ["sql", "hl7", "audit"], 45,
   ["Query encounter data from SQL", "Generate HL7 messages and parse them back", "Check audit log for corresponding entries", "Identify discrepancies between systems"],
   ["Generate HL7 from SQL data, then parse to verify round-trip",
    "Check audit_log for each encounter to verify audit coverage"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Clinical Decision Support Impact Analysis",
   "Informatics leadership wants to measure CDS effectiveness. Combine audit data (alerts triggered), coding data (diagnoses captured), and clinical data (outcomes).",
   "Advanced Integration", ["sql", "audit", "coding", "report"], 45,
   ["Query CDS alert events from audit_log", "Correlate with diagnosis capture rates", "Analyze patient outcomes for alerted vs non-alerted encounters", "Generate impact report"],
   ["CDS alerts in audit_log actions containing 'alert' or 'cds'",
    "Compare diagnosis completeness between alerted and non-alerted encounters"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst"])

_s("Regulatory Compliance Comprehensive Audit",
   "Prepare for a regulatory survey by conducting a comprehensive audit: check HIPAA access patterns, documentation completeness, coding accuracy, and interface reliability.",
   "Advanced Integration", ["sql", "audit", "coding", "hl7", "report"], 60,
   ["Run HIPAA access audit from audit_log", "Check documentation completeness rates", "Validate coding accuracy with Code Mapper", "Verify HL7 interface health", "Compile comprehensive compliance report"],
   ["This is a multi-tool exercise covering all system aspects",
    "Start with audit log analysis, then coding, then interfaces"],
   sql=None,
   difficulty="advanced", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Revenue Integrity Cross-Functional Review",
   "Revenue integrity team needs a cross-functional review: coding accuracy + documentation completeness + charge capture + provider productivity.",
   "Advanced Integration", ["sql", "coding", "audit", "report"], 50,
   ["Assess coding accuracy using Code Mapper", "Measure documentation completeness from audit trail", "Calculate charge capture rates from encounter-diagnosis matching", "Generate cross-functional revenue integrity report"],
   ["Charge capture gap = encounters without diagnoses",
    "Documentation completeness = encounters with audit documentation events"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Interface Failure Impact Assessment",
   "An interface failure has been detected. Assess the impact by correlating HL7 message errors with missing clinical data and affected patient encounters.",
   "Advanced Integration", ["hl7", "sql", "audit"], 40,
   ["Query audit_log for interface error events", "Identify affected time period", "Check for missing clinical data during that period", "Generate HL7 messages to test current interface status", "Document impact and recovery"],
   ["Interface errors in audit_log with timestamps define the failure window",
    "Check for encounters during failure window with missing labs, vitals, or medications"],
   sql=None,
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Patient Safety Event Investigation",
   "A patient safety event has been reported for patient {mrn}. Conduct a thorough investigation using all available tools: EHR, audit trail, medication records, lab results, and clinical timeline.",
   "Advanced Integration", ["sql", "ehr", "audit", "coding", "report"], 50,
   ["Pull complete patient record for {mrn}", "Review audit trail for all access", "Analyze medication and lab timeline", "Check for any unusual patterns", "Document findings in investigation report"],
   ["Start with full patient data extraction",
    "Look for timing anomalies in medication and lab orders"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Clinical Workflow Optimization Study",
   "Leadership wants a data-driven workflow optimization study. Analyze clinical workflows using audit logs, encounter data, and documentation patterns to identify bottlenecks.",
   "Advanced Integration", ["sql", "audit", "report"], 45,
   ["Map the clinical workflow from audit_log patterns", "Identify time-consuming steps", "Analyze documentation patterns and delays", "Recommend workflow improvements based on data"],
   ["Workflow steps visible in audit_log action sequences",
    "Calculate time between sequential actions per encounter"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst"])

_s("System Migration Readiness Assessment",
   "The hospital is evaluating a system migration. Assess readiness by inventorying data volumes, interface configurations, and usage patterns across all tools.",
   "Advanced Integration", ["sql", "hl7", "audit", "report"], 50,
   ["Inventory all database table sizes and data volumes", "Document interface message types and volumes", "Analyze user access patterns from audit log", "Assess data quality across all tables", "Generate migration readiness report"],
   ["Count records per table for data volume",
    "Analyze HL7 message types for interface inventory"],
   sql=None,
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Healthcare Analytics Platform Validation",
   "Validate the analytics platform by running comprehensive cross-table queries and verifying data consistency across encounters, diagnoses, medications, labs, and vitals.",
   "Advanced Integration", ["sql", "report"], 40,
   ["Run record count reconciliation across tables", "Verify foreign key integrity", "Check for temporal consistency", "Validate data completeness rates", "Generate validation report"],
   ["Start with referential integrity checks",
    "Then check data completeness: what % of encounters have each data type"],
   sql="SELECT 'encounters_to_patients' AS check_type, COUNT(*) AS orphaned FROM encounters e LEFT JOIN patients p ON e.patient_mrn=p.mrn WHERE p.mrn IS NULL UNION ALL SELECT 'diagnoses_to_encounters', COUNT(*) FROM diagnoses dx LEFT JOIN encounters e ON dx.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL UNION ALL SELECT 'meds_to_encounters', COUNT(*) FROM medications m LEFT JOIN encounters e ON m.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL UNION ALL SELECT 'labs_to_encounters', COUNT(*) FROM lab_results lr LEFT JOIN encounters e ON lr.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL UNION ALL SELECT 'vitals_to_encounters', COUNT(*) FROM vitals v LEFT JOIN encounters e ON v.encounter_id=e.encounter_id WHERE e.encounter_id IS NULL",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Multi-Department Quality Scorecard",
   "Quality leadership needs a comprehensive scorecard comparing all departments: LOS, readmissions, documentation rates, coding specificity, and patient volumes.",
   "Advanced Integration", ["sql", "coding", "report"], 45,
   ["Calculate LOS by department", "Calculate readmission rates per department", "Measure documentation rates from audit data", "Assess coding specificity per department", "Compile into comparative scorecard"],
   ["Use multiple subqueries per department",
    "Combine metrics with UNION ALL or multiple JOINs on department"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Provider Performance 360 Review",
   "Credentialing committee needs a 360 performance review for Dr. {provider}: encounter volume, patient outcomes, documentation timeliness, coding accuracy, and peer comparison.",
   "Advanced Integration", ["sql", "coding", "audit", "report"], 45,
   ["Pull encounter volume and patient panel", "Analyze patient outcomes (LOS, readmissions)", "Measure documentation timeliness from audit trail", "Assess coding accuracy and specificity", "Compare against peer providers in same specialty"],
   ["Filter all queries by the target provider",
    "Calculate peer averages for comparison"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Population Health Risk Stratification",
   "Care management wants to risk-stratify the patient population using diagnosis count, medication count, lab abnormalities, and encounter frequency.",
   "Advanced Integration", ["sql", "report"], 40,
   ["Calculate diagnosis count per patient", "Count active medications per patient", "Count abnormal labs per patient", "Count encounters in the last year", "Create composite risk score and stratify"],
   ["Combine counts from multiple tables per patient",
    "Risk tiers: Low (score 0-3), Medium (4-7), High (8+)"],
   sql="SELECT p.mrn, p.first_name||' '||p.last_name AS patient, COALESCE(dx.cnt,0) AS dx_count, COALESCE(m.cnt,0) AS med_count, COALESCE(e.cnt,0) AS encounter_count, COALESCE(dx.cnt,0)+COALESCE(m.cnt,0)+COALESCE(e.cnt,0) AS risk_score, CASE WHEN COALESCE(dx.cnt,0)+COALESCE(m.cnt,0)+COALESCE(e.cnt,0) >= 8 THEN 'HIGH' WHEN COALESCE(dx.cnt,0)+COALESCE(m.cnt,0)+COALESCE(e.cnt,0) >= 4 THEN 'MEDIUM' ELSE 'LOW' END AS risk_tier FROM patients p LEFT JOIN (SELECT patient_mrn, COUNT(DISTINCT icd10_code) AS cnt FROM diagnoses GROUP BY patient_mrn) dx ON p.mrn=dx.patient_mrn LEFT JOIN (SELECT patient_mrn, COUNT(*) AS cnt FROM medications GROUP BY patient_mrn) m ON p.mrn=m.patient_mrn LEFT JOIN (SELECT patient_mrn, COUNT(*) AS cnt FROM encounters WHERE admission_date >= datetime('now','-365 days') GROUP BY patient_mrn) e ON p.mrn=e.patient_mrn ORDER BY risk_score DESC",
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Infection Outbreak Investigation",
   "Infection control has detected a potential outbreak. Investigate using lab cultures, patient location data, temporal analysis, and audit trail to identify the source and scope.",
   "Advanced Integration", ["sql", "hl7", "audit", "report"], 50,
   ["Query lab results for culture-positive results in a time window", "Map affected patients' locations via encounters and departments", "Analyze temporal clustering", "Check audit trail for infection control actions", "Generate outbreak investigation report"],
   ["Start with lab results containing 'culture' + 'positive'",
    "Map patients to departments and timeframes for cluster analysis"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Comprehensive Billing Audit",
   "Finance requested a comprehensive billing audit combining coding analysis, documentation review, charge capture verification, and provider productivity assessment.",
   "Advanced Integration", ["sql", "coding", "audit", "report"], 50,
   ["Analyze coding accuracy and specificity", "Review documentation completeness", "Check charge capture (encounters with diagnoses)", "Assess provider productivity", "Compile findings into audit report"],
   ["Start with charge capture gap analysis",
    "Then check coding specificity (unspecified code frequency)"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Clinical Informatics Maturity Assessment",
   "The CMIO wants to assess clinical informatics maturity. Evaluate system utilization, data quality, documentation completeness, interface reliability, and analytics capability.",
   "Advanced Integration", ["sql", "hl7", "audit", "coding", "report"], 55,
   ["Assess data quality across all tables", "Measure documentation completeness", "Evaluate interface message quality", "Analyze coding accuracy", "Generate maturity scorecard"],
   ["Data quality: completeness, consistency, accuracy across tables",
    "Interface quality: message validation pass rate"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst"])

_s("Interoperability Gap Analysis",
   "The interoperability committee needs a gap analysis. Evaluate HL7 message coverage, data mapping completeness, and cross-system data consistency.",
   "Advanced Integration", ["hl7", "sql", "audit", "report"], 45,
   ["Generate HL7 messages for all data types", "Validate message completeness", "Check data mapping accuracy (SQL to HL7 round-trip)", "Identify data elements not covered by interfaces", "Report interoperability gaps"],
   ["Generate and parse messages to verify data survives round-trip",
    "Compare HL7 field population rates for completeness"],
   sql=None,
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Emergency Preparedness Data Readiness",
   "Emergency management wants to verify data readiness for surge scenarios. Test ability to quickly extract patient census, capacity, staffing, and critical supplies data.",
   "Advanced Integration", ["sql", "report"], 35,
   ["Generate real-time census by department", "Calculate available capacity", "List providers currently with patients", "Generate surge capacity report"],
   ["Census = undischarged patients per department",
    "Capacity = theoretical max - current census"],
   sql="SELECT d.dept_name, COUNT(e.encounter_id) AS current_census, COUNT(DISTINCT e.attending_provider_id) AS active_providers FROM encounters e JOIN departments d ON e.department_id=d.dept_id WHERE e.discharge_date IS NULL GROUP BY d.dept_name ORDER BY current_census DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "system_administrator"])

_s("Year-End Comprehensive Analytics Report",
   "Generate the year-end comprehensive analytics report covering all domains: patient volumes, quality metrics, financial indicators, operational efficiency, and compliance status.",
   "Advanced Integration", ["sql", "coding", "audit", "report"], 60,
   ["Calculate annual patient volumes and trends", "Compute quality metrics (readmissions, LOS, mortality proxies)", "Analyze financial indicators (coding accuracy, charge capture)", "Measure operational efficiency (throughput, wait times)", "Assess compliance (audit completeness, documentation rates)"],
   ["This is the most comprehensive report combining all data domains",
    "Start with high-level aggregates, then drill into departmental detail"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("New Provider Onboarding Verification",
   "A new provider has joined {dept}. Verify their system access is correctly configured by checking encounter assignments, audit trail, and documentation patterns.",
   "Advanced Integration", ["sql", "audit", "ehr"], 25,
   ["Check for recent encounters assigned to the new provider", "Review their audit log activity", "Verify documentation patterns", "Confirm appropriate access levels"],
   ["Filter encounters by attending_provider for recent dates",
    "Check audit_log for the new provider's user activities"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Care Coordination Effectiveness Study",
   "Care coordination team wants to measure effectiveness. Analyze transition documentation, follow-up rates, medication continuity, and readmission prevention across the care continuum.",
   "Advanced Integration", ["sql", "audit", "report"], 40,
   ["Measure care transition documentation rates", "Calculate follow-up encounter rates within 7 and 30 days", "Assess medication continuity across encounters", "Compare readmission rates for coordinated vs uncoordinated patients"],
   ["Follow-up = subsequent encounter within 30 days for same patient",
    "Medication continuity = same medications across sequential encounters"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Clinical Data Warehouse Quality Dashboard",
   "Build a data quality dashboard covering completeness, accuracy, consistency, and timeliness metrics for the clinical data warehouse.",
   "Advanced Integration", ["sql", "report"], 40,
   ["Calculate completeness rates for each table", "Verify data accuracy (foreign keys, value ranges)", "Check consistency (cross-table reconciliation)", "Measure timeliness (data entry lag from events)", "Compile into dashboard format"],
   ["Completeness = non-NULL required fields / total records",
    "Timeliness = average lag between event and data entry"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Telehealth Integration Assessment",
   "As telehealth grows, assess how well telehealth encounters integrate with the clinical system. Check documentation, coding, and follow-up patterns for telehealth vs in-person visits.",
   "Advanced Integration", ["sql", "coding", "audit", "report"], 35,
   ["Identify telehealth encounters (if encounter_type indicates)", "Compare documentation rates with in-person visits", "Check coding completeness", "Analyze follow-up patterns", "Report telehealth integration gaps"],
   ["Telehealth encounters may be tagged in encounter_type",
    "Compare all metrics between telehealth and in-person cohorts"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

_s("Comprehensive Patient Safety Dashboard",
   "Patient safety officer needs a dashboard combining medication safety (interactions, allergies), fall risk (age, polypharmacy), infection indicators, and documentation gaps.",
   "Advanced Integration", ["sql", "audit", "coding", "report"], 50,
   ["Calculate medication interaction risk counts", "Identify fall-risk patients (65+, 5+ meds)", "Track infection indicators from lab cultures", "Measure documentation gap rates", "Compile comprehensive safety dashboard"],
   ["Combine multiple risk factor queries",
    "Present as counts and rates by department"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Multi-Facility Data Comparison Framework",
   "Corporate needs a framework for comparing clinical metrics across facilities. Design the comparative analysis using current facility data as a baseline.",
   "Advanced Integration", ["sql", "report"], 35,
   ["Calculate key metrics for current facility", "Design benchmark comparison structure", "Identify metrics suitable for cross-facility comparison", "Generate comparison report template"],
   ["Key metrics: LOS, readmission rate, coding accuracy, documentation completeness",
    "Design a framework that could accept data from additional facilities"],
   sql=None,
   difficulty="advanced", roles=["clinical_informatics_analyst", "data_analyst"])

# ---- Additional Reporting ----

_s("Controlled Substance Prescribing Report",
   "DEA compliance requires a report on controlled substance prescriptions: medication name, prescriber, volume, and patient count.",
   "Reporting", ["sql", "report"], 25,
   ["Open SQL Console", "Identify controlled substance medications", "Aggregate by medication and prescriber", "Generate compliance report"],
   ["Controlled substances: opioids, benzodiazepines, stimulants, barbiturates",
    "Include prescriber credential and specialty for DEA reporting"],
   sql="SELECT m.medication_name, pr.first_name||' '||pr.last_name AS prescriber, pr.credential, COUNT(*) AS rx_count, COUNT(DISTINCT m.patient_mrn) AS patients FROM medications m JOIN providers pr ON m.prescribing_provider_id=pr.provider_id WHERE LOWER(m.medication_name) LIKE '%oxycodone%' OR LOWER(m.medication_name) LIKE '%hydrocodone%' OR LOWER(m.medication_name) LIKE '%alprazolam%' OR LOWER(m.medication_name) LIKE '%diazepam%' OR LOWER(m.medication_name) LIKE '%lorazepam%' OR LOWER(m.medication_name) LIKE '%morphine%' OR LOWER(m.medication_name) LIKE '%fentanyl%' GROUP BY m.medication_name, pr.provider_id ORDER BY rx_count DESC",
   difficulty="intermediate", roles=["compliance_officer", "clinical_informatics_analyst"])

_s("Wound Care Quality Report",
   "Wound care team needs a quality report: patients with wound-related diagnoses, treatment documentation rates, and healing outcome indicators.",
   "Reporting", ["sql", "report", "coding"], 30,
   ["Identify wound-related diagnoses (L89, L97, T81.4)", "Count affected patients by department", "Check for follow-up encounters", "Generate quality report"],
   ["Pressure ulcers: L89.x, Chronic ulcers: L97.x",
    "Follow-up rate indicates healing outcome tracking"],
   sql="SELECT dx.icd10_code, dx.description, COUNT(DISTINCT dx.patient_mrn) AS patients, COUNT(DISTINCT dx.encounter_id) AS encounters FROM diagnoses dx WHERE dx.icd10_code LIKE 'L89%' OR dx.icd10_code LIKE 'L97%' OR dx.icd10_code LIKE 'T81.4%' GROUP BY dx.icd10_code, dx.description ORDER BY patients DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Blood Utilization Report",
   "Transfusion medicine needs a blood utilization report: blood product administrations, ordering patterns by department, and crossmatch-to-transfusion ratios.",
   "Reporting", ["sql", "report"], 25,
   ["Open SQL Console", "Query medications for blood products", "Analyze ordering patterns", "Generate utilization report"],
   ["Blood products in medications: PRBC, FFP, platelets, cryoprecipitate",
    "GROUP BY department and medication_name"],
   sql="SELECT d.dept_name, m.medication_name, COUNT(*) AS administrations, COUNT(DISTINCT m.patient_mrn) AS patients FROM medications m JOIN encounters e ON m.encounter_id=e.encounter_id JOIN departments d ON e.department_id=d.dept_id WHERE LOWER(m.medication_name) LIKE '%blood%' OR LOWER(m.medication_name) LIKE '%prbc%' OR LOWER(m.medication_name) LIKE '%platelet%' OR LOWER(m.medication_name) LIKE '%plasma%' OR LOWER(m.medication_name) LIKE '%transfus%' GROUP BY d.dept_name, m.medication_name ORDER BY administrations DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "data_analyst"])

# ---- Additional Communication ----

_s("HL7 SIU Scheduling Message Analysis",
   "Scheduling interfaces use HL7 SIU messages. Analyze scheduling message patterns and verify appointment data flows correctly.",
   "Communication", ["hl7", "sql"], 25,
   ["Generate sample scheduling-related data", "Map to SIU message format", "Parse and validate SIU messages", "Verify scheduling data integrity"],
   ["SIU: Scheduling Information Unsolicited",
    "S12=New appointment, S14=Modification, S15=Cancellation"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 Message Queue Monitoring",
   "Interface operations needs to monitor message queue depth. Analyze message throughput patterns and identify potential queue bottlenecks.",
   "Communication", ["hl7", "sql", "audit"], 25,
   ["Query audit_log for message processing events", "Calculate processing rate per hour", "Identify periods of low throughput", "Estimate queue depth from processing lag"],
   ["Processing rate = messages per hour from audit_log",
    "Low throughput periods may indicate queue buildup"],
   sql="SELECT strftime('%H', timestamp) AS hour, COUNT(*) AS messages, ROUND(COUNT(*)/60.0,1) AS per_minute FROM audit_log WHERE LOWER(action) LIKE '%message%' OR LOWER(action) LIKE '%hl7%' GROUP BY strftime('%H', timestamp) ORDER BY hour",
   difficulty="intermediate", roles=["system_administrator"])

_s("Multi-System Patient Matching Analysis",
   "Patient matching across systems is critical. Analyze how well patient identifiers align between the clinical database and HL7 message data.",
   "Communication", ["hl7", "sql"], 30,
   ["Query patient demographics from database", "Generate HL7 messages for patients", "Parse PID segments and extract identifiers", "Verify matching accuracy"],
   ["PID-3: patient identifier, PID-5: name, PID-7: DOB",
    "All three fields should match between systems"],
   sql=None,
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("HL7 Notification Workflow Documentation",
   "Document the complete HL7 notification workflow for critical results. Map from lab result entry through message generation to provider notification.",
   "Communication", ["hl7", "sql", "audit"], 30,
   ["Map the critical result data flow", "Generate sample ORU messages for critical results", "Trace the notification chain in audit_log", "Document the complete workflow"],
   ["Critical results trigger ORU messages with special flags",
    "Trace the chain: lab entry -> HL7 message -> provider alert -> acknowledgment"],
   sql=None,
   difficulty="advanced", roles=["system_administrator", "clinical_informatics_analyst"])

_s("Interface Redundancy and Failover Testing",
   "IT disaster recovery needs to document interface redundancy. Test message generation and validate that backup routing would work during primary failure.",
   "Communication", ["hl7", "audit"], 25,
   ["Generate test HL7 messages", "Document primary routing configuration", "Identify backup routing options", "Validate message structure for both paths"],
   ["Primary vs backup routing is configured in MSH-5/MSH-6",
    "Messages should be identical regardless of routing path"],
   sql=None,
   difficulty="intermediate", roles=["system_administrator"])

# ---- Additional Documentation ----

_s("Operative Note Documentation Audit",
   "Surgery quality committee needs to verify operative note completeness for all surgical encounters. Check for documentation within 24 hours of surgery.",
   "Documentation", ["sql", "audit"], 25,
   ["Identify surgical encounters", "Check audit_log for operative note actions", "Calculate documentation rate within 24 hours", "Report by surgeon"],
   ["Surgical encounters: department or type containing 'surg'",
    "Operative notes should be documented within 24 hours"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("History and Physical Documentation Timeliness",
   "Medical staff requirements mandate H&P completion within 24 hours of admission. Audit compliance using audit trail data.",
   "Documentation", ["sql", "audit"], 25,
   ["Query recent admissions", "Check audit_log for H&P documentation events", "Calculate time from admission to H&P completion", "Report compliance by department"],
   ["Look for 'history', 'physical', or 'H&P' in audit_log actions",
    "Must be within 24 hours of admission_date"],
   sql=None,
   difficulty="intermediate", roles=["clinical_informatics_analyst", "compliance_officer"])

_s("Nursing Assessment Documentation Compliance",
   "Nursing regulatory requires initial assessment within 8 hours of admission. Track compliance from vital signs documentation.",
   "Documentation", ["sql", "ehr"], 25,
   ["Query encounters with admission dates", "Find first vital signs per encounter", "Calculate time from admission to first assessment", "Report compliance rate by department"],
   ["First vital signs as proxy for initial nursing assessment",
    "Must be within 8 hours: (julianday(first_vital)-julianday(admission))*24 <= 8"],
   sql="SELECT d.dept_name, COUNT(DISTINCT e.encounter_id) AS total, COUNT(DISTINCT CASE WHEN (julianday(v.first_vital)-julianday(e.admission_date))*24 <= 8 THEN e.encounter_id END) AS compliant, ROUND(COUNT(DISTINCT CASE WHEN (julianday(v.first_vital)-julianday(e.admission_date))*24 <= 8 THEN e.encounter_id END)*100.0/NULLIF(COUNT(DISTINCT e.encounter_id),0),1) AS compliance_pct FROM encounters e JOIN departments d ON e.department_id=d.dept_id LEFT JOIN (SELECT encounter_id, MIN(recorded_at) AS first_vital FROM vitals GROUP BY encounter_id) v ON e.encounter_id=v.encounter_id WHERE v.first_vital IS NOT NULL GROUP BY d.dept_name ORDER BY compliance_pct",
   difficulty="intermediate", roles=["clinical_informatics_analyst", "clinical_staff"])

_s("Documentation Burden Analysis by Role",
   "Informatics wants to quantify documentation burden. Analyze audit log to determine how much time different user roles spend on documentation activities.",
   "Documentation", ["sql", "audit"], 30,
   ["Query audit_log for documentation-related actions", "Categorize by user role or department", "Calculate documentation volume per user", "Identify roles with highest documentation burden"],
   ["Documentation actions: 'note', 'document', 'sign', 'template', 'assessment'",
    "Group by user_id and count documentation events per day"],
   sql="SELECT user_id, COUNT(*) AS doc_events, COUNT(DISTINCT DATE(timestamp)) AS active_days, ROUND(COUNT(*)*1.0/COUNT(DISTINCT DATE(timestamp)),1) AS avg_daily FROM audit_log WHERE LOWER(action) LIKE '%note%' OR LOWER(action) LIKE '%document%' OR LOWER(action) LIKE '%sign%' OR LOWER(action) LIKE '%template%' GROUP BY user_id HAVING COUNT(*) > 10 ORDER BY avg_daily DESC",
   difficulty="intermediate", roles=["clinical_informatics_analyst"])

_s("Verbal Order Documentation Compliance",
   "Regulatory requires that verbal orders be authenticated by the ordering provider within 48 hours. Track compliance from audit trail.",
   "Documentation", ["sql", "audit"], 25,
   ["Query audit_log for verbal order events", "Find corresponding authentication events", "Calculate time to authentication", "Report compliance rate"],
   ["Verbal orders: actions containing 'verbal' or 'telephone'",
    "Authentication: 'sign', 'authenticate', 'co-sign' actions for same resource"],
   sql=None,
   difficulty="intermediate", roles=["compliance_officer", "clinical_informatics_analyst"])

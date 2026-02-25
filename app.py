"""
app.py - Flask backend for the Health Informatics Learning Platform.
Provides API endpoints for scenario management, task generation, email
simulation, SQL console, Python execution, EHR browsing, and dashboards.
"""

import os
import json
import random
import sqlite3
import subprocess
import tempfile
import re
import uuid
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session

from database import init_db, seed_data

app = Flask(__name__)
app.secret_key = "hinfo-drill-secret-2026"

DB_PATH = os.path.join(os.path.dirname(__file__), "hinfo_drill.db")

# ---------------------------------------------------------------------------
# In-memory scenario store
# ---------------------------------------------------------------------------
SCENARIOS = {}


def _get_sid():
    return session.get("scenario_id")


def _get_scenario():
    sid = _get_sid()
    return SCENARIOS.get(sid) if sid else None


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _fmt_dt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _now():
    return datetime.now()


# ---------------------------------------------------------------------------
# Task templates
# ---------------------------------------------------------------------------
# Each template uses {placeholders} filled with real DB data at runtime.
# SQL references the NEW schema: patients.id, encounters.id, diagnoses table,
# medication_orders.medication_id -> medications, lab_results.value, etc.

TASK_TEMPLATES = []


def _t(title, desc, category, tools, minutes, steps, hints, sql_answer=None):
    TASK_TEMPLATES.append(dict(
        title=title, description=desc, category=category,
        tools=tools, estimated_minutes=minutes, steps=steps,
        hints=hints, sql_answer=sql_answer,
    ))


# ---- Data Extraction ----
_t("Pull 30-Day Readmission Rate for {dept}",
   "The CMO has requested the 30-day readmission rate for the {dept} department. A readmission is a patient with more than one encounter within 30 days of a prior discharge. Calculate (readmitted / total discharged) as a percentage.",
   "Data Extraction", ["sql"], 30,
   ["Open the SQL Console", "Identify encounters and departments tables", "Write a self-join to find readmissions within 30 days", "Calculate the rate as a percentage"],
   ["Self-join encounters ON patient_id where second admit_date is within 30 days of first discharge_date",
    "Filter by department using JOIN departments",
    "SELECT ROUND(COUNT(DISTINCT r.patient_id)*100.0 / COUNT(DISTINCT e.patient_id), 2) ..."],
   "SELECT ROUND(COUNT(DISTINCT r.patient_id)*100.0 / NULLIF(COUNT(DISTINCT e.patient_id),0), 2) AS readmission_rate FROM encounters e JOIN departments d ON e.department_id=d.id LEFT JOIN encounters r ON e.patient_id=r.patient_id AND r.id != e.id AND r.admit_date BETWEEN e.discharge_date AND datetime(e.discharge_date, '+30 days') WHERE d.name='{dept}' AND e.discharge_date IS NOT NULL")

_t("Extract Patients with {dx_desc} in the Last 90 Days",
   "The quality team needs all patients diagnosed with {dx_desc} ({dx_code}) in the last 90 days. Include patient MRN, name, encounter date, attending provider, and department.",
   "Data Extraction", ["sql", "ehr"], 20,
   ["Open SQL Console", "Query diagnoses table filtering on icd10_code", "Join with patients, providers, and encounters", "Review results in EHR viewer"],
   ["Filter diagnoses WHERE icd10_code = '{dx_code}'",
    "JOIN encounters ON diagnoses.encounter_id = encounters.id",
    "Add date filter: diagnosis_date >= datetime('now','-90 days')"],
   "SELECT p.mrn, p.first_name, p.last_name, e.admit_date, pr.first_name||' '||pr.last_name AS provider, dep.name AS department FROM diagnoses dx JOIN encounters e ON dx.encounter_id=e.id JOIN patients p ON dx.patient_id=p.id JOIN providers pr ON e.provider_id=pr.id JOIN departments dep ON e.department_id=dep.id WHERE dx.icd10_code='{dx_code}' AND dx.diagnosis_date >= datetime('now','-90 days')")

_t("Generate Medication Report for Dr. {provider}",
   "The pharmacy director needs all medications prescribed by Dr. {provider} this month. Include medication name, patient name, dose, route, frequency, and order date.",
   "Data Extraction", ["sql"], 25,
   ["Open SQL Console", "Query medication_orders joined with providers, patients, and medications", "Filter by provider and date range", "Sort by medication name"],
   ["JOIN providers ON medication_orders.ordering_provider_id = providers.id",
    "JOIN medications ON medication_orders.medication_id = medications.id",
    "Filter: start_date >= date('now','start of month')"],
   "SELECT m.name AS medication, p.first_name||' '||p.last_name AS patient, mo.dose||' '||mo.unit AS dosage, mo.route, mo.frequency, mo.start_date FROM medication_orders mo JOIN medications m ON mo.medication_id=m.id JOIN providers pr ON mo.ordering_provider_id=pr.id JOIN patients p ON mo.patient_id=p.id WHERE pr.first_name||' '||pr.last_name='{provider}' AND mo.start_date >= date('now','start of month') ORDER BY m.name")

_t("Find Critical Lab Results in Past 7 Days",
   "The laboratory director flagged an increase in critical results. Pull all lab results with abnormal_flag = 'C' from the past 7 days. Include patient info, test name, value, reference range, and ordering provider.",
   "Data Extraction", ["sql"], 20,
   ["Open SQL Console", "Query lab_results where abnormal_flag = 'C'", "Join with patients and providers", "Filter by result_date within last 7 days"],
   ["SELECT from lab_results WHERE abnormal_flag = 'C'",
    "Use datetime('now','-7 days') for the date filter",
    "JOIN patients and providers for full context"],
   "SELECT p.mrn, p.first_name||' '||p.last_name AS patient, lr.test_name, lr.value, lr.unit, lr.reference_range_low||'-'||lr.reference_range_high AS ref_range, lr.abnormal_flag, lr.result_date, pr.first_name||' '||pr.last_name AS ordering_provider FROM lab_results lr JOIN patients p ON lr.patient_id=p.id JOIN providers pr ON lr.ordering_provider_id=pr.id WHERE lr.abnormal_flag='C' AND lr.result_date >= datetime('now','-7 days') ORDER BY lr.result_date DESC")

_t("Calculate Average Length of Stay by Department",
   "Administration needs the average LOS (in days) by department for the current quarter. Only include discharged encounters. Sort by longest average LOS.",
   "Data Extraction", ["sql"], 25,
   ["Open SQL Console", "Calculate LOS using admit_date and discharge_date", "Group by department", "Use julianday() for date math in SQLite"],
   ["LOS = julianday(discharge_date) - julianday(admit_date)",
    "GROUP BY department and use AVG()",
    "Filter WHERE discharge_date IS NOT NULL"],
   "SELECT d.name AS department, ROUND(AVG(julianday(e.discharge_date)-julianday(e.admit_date)),1) AS avg_los_days, COUNT(*) AS encounter_count FROM encounters e JOIN departments d ON e.department_id=d.id WHERE e.discharge_date IS NOT NULL AND e.admit_date >= date('now','start of year','-3 months') GROUP BY d.name ORDER BY avg_los_days DESC")

_t("Identify Frequent ED Visitors (>= 3 visits in 6 months)",
   "Care coordination wants patients with 3+ Emergency visits in the past 6 months for case management. Include visit count and most recent visit date.",
   "Data Extraction", ["sql"], 20,
   ["Query encounters filtered by encounter_type = 'emergency'", "Group by patient and count visits", "Filter HAVING count >= 3", "Join with patients for demographics"],
   ["Filter: encounter_type = 'emergency' AND admit_date >= datetime('now','-6 months')",
    "GROUP BY patient_id HAVING COUNT(*) >= 3",
    "Use MAX(admit_date) for most recent visit"],
   "SELECT p.mrn, p.first_name||' '||p.last_name AS patient, COUNT(*) AS ed_visits, MAX(e.admit_date) AS latest_visit FROM encounters e JOIN patients p ON e.patient_id=p.id WHERE e.encounter_type='emergency' AND e.admit_date >= datetime('now','-6 months') GROUP BY e.patient_id HAVING COUNT(*)>=3 ORDER BY ed_visits DESC")

_t("Top 10 Diagnoses by Volume This Quarter",
   "Population Health needs the top 10 most common diagnoses this quarter by encounter volume. Include ICD-10 code, description, and patient count.",
   "Data Extraction", ["sql"], 20,
   ["Query diagnoses joined with encounters", "Group by ICD-10 code", "Order by count descending, limit 10"],
   ["GROUP BY icd10_code, description",
    "Filter diagnosis_date for current quarter",
    "COUNT(DISTINCT patient_id) for unique patients"],
   "SELECT dx.icd10_code, dx.description, COUNT(*) AS diagnosis_count, COUNT(DISTINCT dx.patient_id) AS unique_patients FROM diagnoses dx WHERE dx.diagnosis_date >= date('now','start of year','-3 months') GROUP BY dx.icd10_code, dx.description ORDER BY diagnosis_count DESC LIMIT 10")

# ---- Data Quality ----
_t("Identify Potential Duplicate Patient Records",
   "HIM suspects duplicate patient records. Find patients sharing the same first name, last name, and DOB but different MRNs — likely duplicate registrations needing merge.",
   "Data Quality", ["sql", "ehr"], 30,
   ["Query patients for matching demographics with different MRNs", "Self-join on first_name, last_name, dob", "Verify duplicates in the EHR viewer", "Document findings"],
   ["Self-join: p1 JOIN patients p2 ON matching fields",
    "Add condition p1.id < p2.id to avoid duplicate pairs",
    "Match on first_name, last_name, and dob"],
   "SELECT p1.mrn AS mrn_1, p2.mrn AS mrn_2, p1.first_name, p1.last_name, p1.dob FROM patients p1 JOIN patients p2 ON p1.first_name=p2.first_name AND p1.last_name=p2.last_name AND p1.dob=p2.dob AND p1.id < p2.id")

_t("Find Encounters Missing Primary Diagnosis",
   "For billing compliance, identify encounters that have no corresponding primary diagnosis in the diagnoses table. These need resolution before claims submission.",
   "Data Quality", ["sql"], 20,
   ["LEFT JOIN encounters with diagnoses where diagnosis_type='primary'", "Find encounters with NULL diagnosis", "Include department and provider for follow-up"],
   ["LEFT JOIN diagnoses ON encounters.id = diagnoses.encounter_id AND diagnosis_type='primary'",
    "WHERE dx.id IS NULL means no primary diagnosis exists",
    "Filter to only discharged encounters that should have coding"],
   "SELECT e.id AS encounter_id, p.mrn, p.first_name||' '||p.last_name AS patient, e.encounter_type, e.admit_date, d.name AS department, pr.first_name||' '||pr.last_name AS attending FROM encounters e JOIN patients p ON e.patient_id=p.id JOIN departments d ON e.department_id=d.id JOIN providers pr ON e.provider_id=pr.id LEFT JOIN diagnoses dx ON e.id=dx.encounter_id AND dx.diagnosis_type='primary' WHERE dx.id IS NULL AND e.discharge_date IS NOT NULL ORDER BY e.admit_date DESC")

_t("Audit Medication Orders for Unusual Dosages",
   "Patient Safety requested an audit of medication orders with potentially dangerous dosages. Identify orders where the numeric dose seems unusually high (dose > 1000 for standard oral meds).",
   "Data Quality", ["sql"], 30,
   ["Query medication_orders and cast dose to numeric", "Filter for unusually high values", "Join with patients, providers, and medications", "Cross-reference with drug class"],
   ["CAST(dose AS REAL) to compare numerically",
    "Look for doses where CAST(dose AS REAL) > 1000",
    "JOIN medications for drug name context"],
   "SELECT mo.id, p.mrn, p.first_name||' '||p.last_name AS patient, m.name AS medication, mo.dose||' '||mo.unit AS dosage, mo.route, mo.frequency, pr.first_name||' '||pr.last_name AS prescriber FROM medication_orders mo JOIN patients p ON mo.patient_id=p.id JOIN providers pr ON mo.ordering_provider_id=pr.id JOIN medications m ON mo.medication_id=m.id WHERE CAST(mo.dose AS REAL) > 1000 ORDER BY CAST(mo.dose AS REAL) DESC")

_t("Validate Vital Signs for Out-of-Range Values",
   "Clinical Engineering flagged potential device errors. Find vital signs with implausible values: heart_rate < 20 or > 220, temperature < 90 or > 110, spo2 < 50, blood_pressure_systolic < 50 or > 250.",
   "Data Quality", ["sql"], 20,
   ["Query vital_signs with range checks", "Join with patients", "Flag which vital is out of range"],
   ["Use OR conditions for each vital sign range",
    "heart_rate NOT BETWEEN 20 AND 220, etc.",
    "CASE expressions can label which vital is abnormal"],
   "SELECT v.id, p.mrn, p.first_name||' '||p.last_name AS patient, v.recorded_at, v.heart_rate, v.temperature, v.spo2, v.blood_pressure_systolic, CASE WHEN v.heart_rate<20 OR v.heart_rate>220 THEN 'HR' WHEN v.temperature<90 OR v.temperature>110 THEN 'Temp' WHEN v.spo2<50 THEN 'SpO2' WHEN v.blood_pressure_systolic<50 OR v.blood_pressure_systolic>250 THEN 'SBP' END AS flagged_vital FROM vital_signs v JOIN patients p ON v.patient_id=p.id WHERE v.heart_rate<20 OR v.heart_rate>220 OR v.temperature<90 OR v.temperature>110 OR v.spo2<50 OR v.blood_pressure_systolic<50 OR v.blood_pressure_systolic>250")

_t("Check Lab Results Without Valid Orders",
   "Lab management wants to verify data integrity. Find any lab results whose encounter_id doesn't match a valid encounter, or where the encounter is cancelled.",
   "Data Quality", ["sql"], 25,
   ["LEFT JOIN lab_results with encounters", "Check for NULLs or non-matching encounters", "Count mismatches by test type"],
   ["LEFT JOIN encounters ON lab_results.encounter_id = encounters.id",
    "WHERE e.id IS NULL for orphaned results",
    "Group by test_name to see patterns"],
   "SELECT lr.test_name, COUNT(*) AS mismatched_count FROM lab_results lr LEFT JOIN encounters e ON lr.encounter_id=e.id WHERE e.id IS NULL GROUP BY lr.test_name ORDER BY mismatched_count DESC")

# ---- Compliance & Audit ----
_t("HIPAA Access Audit for Patient MRN {mrn}",
   "The Privacy Officer received a complaint about unauthorized access to a patient's records. Run a complete access audit for patient MRN {mrn}. Document who accessed the record, when, what actions, and from what IP address.",
   "Compliance", ["sql", "ehr"], 35,
   ["Query audit_log for the specific patient record", "Review access patterns", "Identify unusual access (after hours, excessive views)", "Document findings"],
   ["The audit_log tracks record_id which corresponds to patient IDs for patient table access",
    "Filter WHERE table_name = 'patients' AND record_id = (patient id)",
    "Check timestamps and group by user_id"],
   "SELECT al.timestamp, al.user_id, al.action, al.table_name, al.record_id, al.ip_address FROM audit_log al WHERE al.record_id = (SELECT id FROM patients WHERE mrn='{mrn}') AND al.table_name IN ('patients','encounters','lab_results','medication_orders') ORDER BY al.timestamp DESC")

_t("After-Hours Access Report",
   "Security wants all EHR access outside business hours (before 6 AM or after 8 PM) in the last 30 days. Group by user and flag anyone with more than 10 after-hours events.",
   "Compliance", ["sql"], 30,
   ["Query audit_log with time-of-day filter", "Use strftime to extract hour", "Group by user", "Flag excessive access"],
   ["strftime('%H', timestamp) to get hour",
    "WHERE CAST(strftime('%H',timestamp) AS INTEGER) < 6 OR >= 20",
    "GROUP BY user_id HAVING COUNT(*) > 10"],
   "SELECT user_id, COUNT(*) AS after_hours_events, MIN(timestamp) AS earliest, MAX(timestamp) AS latest FROM audit_log WHERE (CAST(strftime('%H',timestamp) AS INTEGER) < 6 OR CAST(strftime('%H',timestamp) AS INTEGER) >= 20) AND timestamp >= datetime('now','-30 days') GROUP BY user_id ORDER BY after_hours_events DESC")

# ---- System/Interface ----
_t("Investigate HL7 Interface Errors",
   "The lab interface team reports message failures. Review the HL7 message log, identify error patterns, calculate the error rate, and determine if a specific sending facility is affected.",
   "System", ["sql"], 30,
   ["Query hl7_messages for errors", "Calculate error rate by status", "Look for time and facility patterns", "Identify specific error messages"],
   ["Filter WHERE status = 'error'",
    "Group by sending_facility, status to see rates",
    "Check error_message column for common patterns"],
   "SELECT sending_facility, status, COUNT(*) AS msg_count, GROUP_CONCAT(DISTINCT error_message) AS errors FROM hl7_messages GROUP BY sending_facility, status ORDER BY msg_count DESC")

_t("System Status Review and Alert Triage",
   "IT Operations needs a summary of all system statuses. Identify any systems that are degraded or down, and calculate the health score based on response times.",
   "System", ["sql", "dashboard"], 25,
   ["Query system_status table", "Identify degraded/down systems", "Review response times", "Check on the dashboard"],
   ["SELECT * FROM system_status ORDER BY last_check DESC",
    "Focus on status != 'operational'",
    "Higher response_time_ms indicates degradation"],
   "SELECT system_name, status, response_time_ms, last_check, notes FROM system_status ORDER BY CASE status WHEN 'down' THEN 1 WHEN 'degraded' THEN 2 ELSE 3 END, response_time_ms DESC")

_t("Review Clinical Alerts and Acknowledgment Status",
   "The Chief Nursing Officer wants a report on clinical alerts: how many are unacknowledged, what types are most common, and which are high severity. Triage and summarize.",
   "System", ["sql"], 25,
   ["Query clinical_alerts table", "Group by alert_type and severity", "Identify unacknowledged alerts", "Prioritize by severity"],
   ["SELECT from clinical_alerts",
    "GROUP BY alert_type, severity for summary counts",
    "Filter WHERE status != 'acknowledged' for open alerts"],
   "SELECT alert_type, severity, status, COUNT(*) AS alert_count FROM clinical_alerts GROUP BY alert_type, severity, status ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, alert_count DESC")

# ---- Analytics ----
_t("Build Department Utilization Dashboard",
   "The COO requested a department utilization dashboard. For each clinical department show: active encounters, total encounters this month, bed count, and estimated occupancy rate.",
   "Analytics", ["sql", "dashboard"], 35,
   ["Query departments joined with encounters", "Calculate active encounter count", "Calculate occupancy rate using bed_count", "Present as dashboard metrics"],
   ["LEFT JOIN encounters WHERE status='active' or open",
    "Use bed_count from departments for occupancy",
    "Occupancy = active_encounters / bed_count * 100"],
   "SELECT d.name, d.bed_count, COUNT(CASE WHEN e.status='active' THEN 1 END) AS active_encounters, COUNT(CASE WHEN e.admit_date >= date('now','start of month') THEN 1 END) AS month_total, CASE WHEN d.bed_count > 0 THEN ROUND(COUNT(CASE WHEN e.status='active' THEN 1 END)*100.0/d.bed_count,1) ELSE 0 END AS occupancy_pct FROM departments d LEFT JOIN encounters e ON d.department_id=d.id AND e.department_id=d.id WHERE d.bed_count > 0 GROUP BY d.id ORDER BY occupancy_pct DESC")

_t("Analyze Admission Trends by Diagnosis Category",
   "Population Health wants to understand admission trends over the past 3 months, broken down by the most common diagnosis categories.",
   "Analytics", ["sql", "python"], 35,
   ["Join encounters with diagnoses", "Group by month and diagnosis", "Calculate trend", "Optionally visualize with Python"],
   ["JOIN diagnoses ON encounters.id = diagnoses.encounter_id",
    "strftime('%Y-%m', admit_date) for monthly grouping",
    "GROUP BY month and icd10_code"],
   "SELECT strftime('%Y-%m', e.admit_date) AS month, dx.icd10_code, dx.description, COUNT(*) AS admissions FROM encounters e JOIN diagnoses dx ON e.id=dx.encounter_id WHERE e.admit_date >= datetime('now','-3 months') AND dx.diagnosis_type='primary' GROUP BY month, dx.icd10_code ORDER BY month, admissions DESC")

_t("Create Infection Control Surveillance Report",
   "Infection Prevention needs a report tracking sepsis (A41.9) and pneumonia (J18.9) cases by department and month. Include case counts and mortality (discharge_disposition = 'expired').",
   "Analytics", ["sql"], 30,
   ["Query encounters + diagnoses for sepsis and pneumonia", "Group by month, department, diagnosis", "Calculate mortality rate"],
   ["Filter icd10_code IN ('A41.9','J18.9')",
    "GROUP BY month, department, icd10_code",
    "Count WHERE discharge_disposition = 'expired' for mortality"],
   "SELECT strftime('%Y-%m', e.admit_date) AS month, d.name AS department, dx.icd10_code, dx.description, COUNT(*) AS cases, SUM(CASE WHEN e.discharge_disposition='expired' THEN 1 ELSE 0 END) AS deaths FROM encounters e JOIN diagnoses dx ON e.id=dx.encounter_id JOIN departments d ON e.department_id=d.id WHERE dx.icd10_code IN ('A41.9','J18.9') GROUP BY month, d.name, dx.icd10_code ORDER BY month DESC, cases DESC")

_t("Quality Measures Performance Summary",
   "Quality department needs the latest quarter's core quality measure performance. Calculate rates and flag any measures below the 80% target.",
   "Analytics", ["sql", "dashboard"], 25,
   ["Query quality_measures for the most recent period", "Calculate performance rates", "Flag below-target measures", "Display on dashboard"],
   ["SELECT from quality_measures",
    "Rate = numerator/denominator or already calculated",
    "Filter WHERE rate < 0.80 for below-target"],
   "SELECT qm.measure_code, qm.measure_name, d.name AS department, qm.numerator, qm.denominator, ROUND(qm.rate*100,1) AS performance_pct, CASE WHEN qm.rate < 0.80 THEN 'BELOW TARGET' ELSE 'MEETS TARGET' END AS status FROM quality_measures qm LEFT JOIN departments d ON qm.department_id=d.id ORDER BY qm.rate ASC")

# ---- Reporting ----
_t("Monthly Executive Summary Metrics",
   "Prepare the monthly executive summary: total encounters, average LOS, ED volume, top 5 diagnoses, and overall system health. This goes to the C-suite.",
   "Reporting", ["sql", "dashboard"], 40,
   ["Pull total encounter counts by type", "Calculate average LOS", "Get top diagnoses", "Check system status", "Compile into dashboard view"],
   ["Run multiple queries for each section",
    "encounters: GROUP BY encounter_type",
    "diagnoses: GROUP BY icd10_code, description ORDER BY COUNT(*) DESC LIMIT 5"],
   None)

_t("Provider Productivity Report",
   "Medical staff office needs provider productivity: encounter volume per provider for the current month. Include name, specialty, encounter count, and average per week.",
   "Reporting", ["sql"], 25,
   ["Query encounters grouped by provider", "Join with providers for details", "Calculate weekly average", "Sort by volume"],
   ["GROUP BY provider_id",
    "JOIN providers for name and specialty",
    "Weekly avg: count / 4"],
   "SELECT pr.first_name||' '||pr.last_name AS provider, pr.specialty, COUNT(*) AS encounters, ROUND(COUNT(*)*1.0/4,1) AS avg_per_week FROM encounters e JOIN providers pr ON e.provider_id=pr.id WHERE e.admit_date >= date('now','start of month') GROUP BY pr.id ORDER BY encounters DESC")

_t("Procedure Volume Analysis by Department",
   "Surgical services needs a procedure volume report by department and CPT code for the current quarter. Include procedure count and unique patient count.",
   "Reporting", ["sql"], 25,
   ["Query procedures joined with departments", "Group by department and CPT code", "Calculate volumes"],
   ["JOIN departments ON procedures table has no direct dept link — go through encounters",
    "GROUP BY cpt_code, description",
    "COUNT(DISTINCT patient_id) for unique patients"],
   "SELECT d.name AS department, pr.cpt_code, pr.description, COUNT(*) AS procedure_count, COUNT(DISTINCT pr.patient_id) AS unique_patients FROM procedures pr JOIN encounters e ON pr.encounter_id=e.id JOIN departments d ON e.department_id=d.id WHERE pr.procedure_date >= date('now','start of year','-3 months') GROUP BY d.name, pr.cpt_code ORDER BY procedure_count DESC")

# ---- Email Response Tasks ----
_t("Respond to CMO's Readmission Data Request",
   "Dr. {provider} (CMO) emailed requesting latest readmission data for the board meeting. Pull the data, compose a professional response, and reply.",
   "Communication", ["email", "sql"], 30,
   ["Read the CMO's email in the inbox", "Pull readmission data using SQL", "Analyze the results", "Compose and send a professional reply"],
   ["Check inbox for the CMO's email first",
    "Readmission query involves self-joining encounters",
    "Reply should include key numbers and trends"],
   None)

_t("Address Compliance Audit Request",
   "The Compliance Officer emailed about an upcoming audit needing specific data by end of shift. Review the email, pull the data, and respond with findings.",
   "Communication", ["email", "sql"], 35,
   ["Read the compliance email", "Identify what data is needed", "Query appropriate tables", "Compose reply with findings"],
   ["The email will specify what compliance data is needed",
    "Likely involves audit_log or access patterns",
    "Be thorough — compliance audits need complete data"],
   None)

_t("Help Nursing Director with Staffing Metrics",
   "The Nursing Director needs metrics for a staffing request: patient census by department, average daily admissions, and patient acuity. Reply with the data.",
   "Communication", ["email", "sql"], 25,
   ["Read the nursing director's email", "Pull department census", "Calculate daily admissions", "Determine acuity metrics", "Reply with data"],
   ["Census = active encounters by department",
    "Daily admissions = total / days",
    "Acuity proxy: ICU encounters / total"],
   None)

_t("Troubleshoot Interface Issue from IT",
   "IT emailed about lab result interface errors. Investigate the HL7 message log, identify the failure pattern, and provide a summary with recommended next steps.",
   "Communication", ["email", "sql"], 30,
   ["Read IT's email", "Query hl7_messages for errors", "Identify patterns", "Reply with analysis"],
   ["Filter hl7_messages WHERE status='error'",
    "Group by sending_facility and error_message",
    "Check if errors cluster at specific times"],
   None)

# ---- Documentation ----
_t("Create Quick Reference for Common SQL Reports",
   "Your manager wants a quick reference with 5 common SQL queries the team runs: patient lookup, encounter search, lab results, medication list, and department census.",
   "Documentation", ["sql"], 30,
   ["Write patient lookup query", "Write encounter search query", "Write lab results query", "Write medication list query", "Write census query", "Compile with explanations"],
   ["Patient lookup: SELECT from patients WHERE mrn = ? OR last_name LIKE ?",
    "Encounter search: JOIN encounters with patients, filter by date",
    "Keep queries simple and well-commented"],
   None)

_t("Document Data Quality Findings",
   "After running data quality checks, document findings in a structured format: issues found, severity, affected record counts, and recommended remediation.",
   "Documentation", ["sql"], 25,
   ["Run duplicate patient check", "Run missing diagnosis check", "Run dosage audit", "Compile findings with severity ratings", "Write remediation recommendations"],
   ["Run each data quality query for current counts",
    "Classify severity: Critical/High/Medium/Low",
    "Include specific record counts"],
   None)


# ---------------------------------------------------------------------------
# Email generation
# ---------------------------------------------------------------------------

def _generate_emails(scenario, tasks, conn):
    emails = []
    now = _now()
    shift_start = now

    emails.append({
        "id": "email_000",
        "from_name": "Sarah Mitchell",
        "from_role": "Shift Manager, Clinical Informatics",
        "from_email": "s.mitchell@hospital.org",
        "subject": f"Good Morning - {now.strftime('%A %B %d')} Shift Briefing",
        "body": (
            f"Good morning,\n\n"
            f"Welcome to your shift. Quick overview:\n\n"
            f"- You have {len(tasks)} task(s) queued today\n"
            f"- The Lab Interface has been experiencing intermittent HL7 errors — IT is investigating\n"
            f"- Monthly board meeting is this Friday — executive reports are high priority\n"
            f"- Reminder: HIPAA refresher training due by end of month\n\n"
            f"Please check your task queue and prioritize accordingly. Reach out if you need anything.\n\n"
            f"Best,\nSarah Mitchell\nClinical Informatics Manager"
        ),
        "priority": "normal",
        "timestamp": _fmt_dt(shift_start - timedelta(minutes=15)),
        "read": False,
        "category": "briefing",
        "related_task_id": None,
    })

    senders = [
        ("Dr. James Rodriguez", "Chief Medical Officer", "j.rodriguez@hospital.org"),
        ("Dr. Karen Liu", "VP of Quality", "k.liu@hospital.org"),
        ("Janet Collins RN", "Nursing Director", "j.collins@hospital.org"),
        ("Alex Turner", "IT Support Lead", "a.turner@hospital.org"),
        ("Peter Zhang PharmD", "Pharmacy Director", "p.zhang@hospital.org"),
        ("Helen Park", "HIM Manager", "h.park@hospital.org"),
        ("Dr. Robert Kim", "Cardiology Chief", "r.kim@hospital.org"),
        ("Lisa Chen", "Lab Director", "l.chen@hospital.org"),
        ("Maria Santos", "Compliance Officer", "m.santos@hospital.org"),
        ("Tom Williams", "Revenue Cycle Manager", "t.williams@hospital.org"),
    ]

    for i, task in enumerate(tasks):
        sender = senders[i % len(senders)]
        cat = task["category"]
        if cat in ("Data Extraction", "Reporting"):
            body = f"Hi,\n\nI need your help with a data request.\n\n{task['description']}\n\nCould you please have this ready by end of shift? {'This is for the board meeting — please prioritize.' if task.get('priority') == 'high' else 'No huge rush, but great to get it today.'}\n\nLet me know if you have questions.\n\nThanks,\n{sender[0]}\n{sender[1]}"
        elif cat == "Data Quality":
            body = f"Hello,\n\nWe've identified a potential data quality concern.\n\n{task['description']}\n\nPlease run the necessary checks and document findings. Include affected record counts and severity.\n\nRegards,\n{sender[0]}\n{sender[1]}"
        elif cat == "Compliance":
            body = f"IMPORTANT - Compliance Request\n\n{task['description']}\n\nThis is time-sensitive due to regulatory requirements. Please complete ASAP and send results.\n\nThank you,\n{sender[0]}\n{sender[1]}"
        elif cat == "System":
            body = f"Hi Team,\n\nWe're seeing system issues that need investigation.\n\n{task['description']}\n\nPlease investigate and report back. Escalate if critical.\n\nThanks,\n{sender[0]}\n{sender[1]}"
        elif cat == "Communication":
            body = f"Hi,\n\n{task['description']}\n\nPlease look into this and get back to me when you can.\n\nBest,\n{sender[0]}\n{sender[1]}"
        else:
            body = f"Hi,\n\n{task['description']}\n\nPlease complete when you have a chance today.\n\nBest regards,\n{sender[0]}\n{sender[1]}"

        priority = "high" if cat == "Compliance" else random.choice(["normal", "normal", "high", "low"])
        emails.append({
            "id": f"email_{i+1:03d}",
            "from_name": sender[0],
            "from_role": sender[1],
            "from_email": sender[2],
            "subject": f"Request: {task['title']}",
            "body": body,
            "priority": priority,
            "timestamp": _fmt_dt(shift_start + timedelta(minutes=random.randint(0, 30))),
            "read": False,
            "category": "task_request",
            "related_task_id": task["id"],
        })

    # Noise emails
    noise = [
        {"from_name": "IT Department", "from_role": "IT", "from_email": "it@hospital.org",
         "subject": "Scheduled Maintenance: EHR Downtime Saturday 2-6 AM",
         "body": "All,\n\nScheduled maintenance for the EHR system is planned for Saturday 2:00 AM - 6:00 AM. The system will be unavailable during this window.\n\nDowntime procedures are posted on the intranet. Ensure your department has printed downtime forms.\n\nIT Department",
         "priority": "normal", "category": "system_notification"},
        {"from_name": "HR Department", "from_role": "HR", "from_email": "hr@hospital.org",
         "subject": "Reminder: Annual Compliance Training Due Feb 28",
         "body": "Dear Staff,\n\nAnnual compliance training must be completed by February 28, 2026:\n\n- HIPAA Privacy & Security\n- Infection Control\n- Fire Safety\n- Workplace Violence Prevention\n\nAccess the learning portal at training.hospital.org.\n\nHR Department",
         "priority": "low", "category": "policy_update"},
        {"from_name": "Clinical Informatics", "from_role": "CI Team", "from_email": "ci@hospital.org",
         "subject": "New Feature: Improved Lab Result Trending",
         "body": "Team,\n\nNew EHR feature: improved lab result trending. Providers can now see up to 12 months of results in graphical format.\n\nPlease review and provide feedback. Training materials on the intranet.\n\nCI Team",
         "priority": "low", "category": "fyi"},
        {"from_name": "Dr. Patricia Adams", "from_role": "Neurology Chief", "from_email": "p.adams@hospital.org",
         "subject": "FYI - Neuro Dept Meeting Moved to Thursday",
         "body": "Hi,\n\nNeurology department meeting rescheduled from Wednesday to Thursday at 3 PM in Conference Room B.\n\nAgenda: EHR workflow updates and new stroke order set review.\n\nThanks,\nDr. Adams",
         "priority": "low", "category": "meeting"},
    ]
    for j, n in enumerate(noise):
        emails.append({
            "id": f"email_n{j:02d}",
            "from_name": n["from_name"], "from_role": n["from_role"], "from_email": n["from_email"],
            "subject": n["subject"], "body": n["body"], "priority": n["priority"],
            "timestamp": _fmt_dt(shift_start + timedelta(minutes=random.randint(5, 60))),
            "read": False, "category": n["category"], "related_task_id": None,
        })

    emails.sort(key=lambda e: e["timestamp"])
    return emails


# ---------------------------------------------------------------------------
# Task instantiation
# ---------------------------------------------------------------------------

def _instantiate_tasks(scenario, conn):
    task_count = scenario.get("task_count", 5)
    time_target = scenario.get("task_time_target_minutes", 120)

    random.seed()
    templates = list(TASK_TEMPLATES)
    random.shuffle(templates)
    selected = templates[:min(task_count, len(templates))]

    depts = [r["name"] for r in conn.execute("SELECT name FROM departments WHERE bed_count > 0").fetchall()]
    provs = [f"{r['first_name']} {r['last_name']}" for r in conn.execute("SELECT first_name, last_name FROM providers WHERE credentials IN ('MD','DO') LIMIT 20").fetchall()]
    dx_rows = conn.execute("SELECT DISTINCT icd10_code, description FROM diagnoses LIMIT 50").fetchall()
    mrns = [r["mrn"] for r in conn.execute("SELECT mrn FROM patients LIMIT 50").fetchall()]

    if not dx_rows:
        dx_rows = [{"icd10_code": "I10", "description": "Essential hypertension"}]

    tasks = []
    for i, tpl in enumerate(selected):
        dept = random.choice(depts) if depts else "Emergency Department"
        prov = random.choice(provs) if provs else "James Rodriguez"
        dx_row = random.choice(dx_rows)
        mrn = random.choice(mrns) if mrns else "MRN-000001"

        scale = time_target / max(task_count * 25, 1)
        est = max(10, int(tpl["estimated_minutes"] * scale))

        subs = {"dept": dept, "provider": prov, "dx_code": dx_row["icd10_code"],
                "dx_desc": dx_row["description"], "mrn": mrn}

        title = tpl["title"].format(**subs)
        desc = tpl["description"].format(**subs)
        sql_answer = tpl["sql_answer"].format(**subs) if tpl["sql_answer"] else None
        hints = [h.format(**subs) for h in tpl["hints"]]

        priority = "high" if tpl["category"] == "Compliance" else random.choice(["normal", "normal", "high", "low"])

        tasks.append({
            "id": f"task_{i+1:03d}",
            "title": title, "description": desc,
            "category": tpl["category"], "priority": priority,
            "estimated_minutes": est, "status": "pending",
            "steps": [{"text": s, "completed": False} for s in tpl["steps"]],
            "hints": hints, "hints_revealed": 0,
            "required_tools": tpl["tools"],
            "sql_answer": sql_answer, "related_email_id": None,
        })

    return tasks


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scenario/start", methods=["POST"])
def start_scenario():
    data = request.get_json(force=True)
    scenario = {
        "facility_type": data.get("facility_type", "Community Hospital"),
        "role": data.get("role", "Clinical Informatics Analyst"),
        "shift_duration": int(data.get("shift_duration", 8)),
        "task_count": int(data.get("task_count", 5)),
        "difficulty": data.get("difficulty", "intermediate"),
        "assistance_level": data.get("assistance_level", "hints"),
        "python_enabled": bool(data.get("python_enabled", False)),
        "task_time_target_minutes": int(data.get("task_time_target_minutes", 120)),
        "started_at": _fmt_dt(_now()),
    }

    init_db(DB_PATH)
    seed_data(DB_PATH)

    conn = _db()
    tasks = _instantiate_tasks(scenario, conn)
    emails = _generate_emails(scenario, tasks, conn)

    for email in emails:
        if email.get("related_task_id"):
            for t in tasks:
                if t["id"] == email["related_task_id"]:
                    t["related_email_id"] = email["id"]

    sid = str(uuid.uuid4())
    session["scenario_id"] = sid
    SCENARIOS[sid] = {"config": scenario, "tasks": tasks, "emails": emails}
    conn.close()

    return jsonify({"status": "ok", "scenario": scenario,
                     "task_count": len(tasks), "email_count": len(emails)})


@app.route("/api/scenario/reset", methods=["POST"])
def reset_scenario():
    sid = _get_sid()
    if sid and sid in SCENARIOS:
        del SCENARIOS[sid]
    session.pop("scenario_id", None)
    return jsonify({"status": "ok"})


@app.route("/api/scenario/state")
def get_scenario_state():
    sc = _get_scenario()
    if not sc:
        return jsonify({"active": False})
    tasks = sc["tasks"]
    return jsonify({
        "active": True, "config": sc["config"],
        "tasks_total": len(tasks),
        "tasks_completed": sum(1 for t in tasks if t["status"] == "completed"),
        "emails_unread": sum(1 for e in sc["emails"] if not e["read"]),
    })


# ---- Emails ----
@app.route("/api/emails")
def get_emails():
    sc = _get_scenario()
    if not sc:
        return jsonify({"emails": []})
    f = request.args.get("filter", "all")
    emails = sc["emails"]
    if f == "unread":
        emails = [e for e in emails if not e["read"]]
    elif f == "urgent":
        emails = [e for e in emails if e["priority"] in ("high", "urgent")]
    elif f == "task":
        emails = [e for e in emails if e["related_task_id"]]
    return jsonify({"emails": emails})


@app.route("/api/emails/<email_id>/read", methods=["POST"])
def mark_email_read(email_id):
    sc = _get_scenario()
    if not sc:
        return jsonify({"error": "No active scenario"}), 400
    for e in sc["emails"]:
        if e["id"] == email_id:
            e["read"] = True
            return jsonify({"status": "ok"})
    return jsonify({"error": "Email not found"}), 404


@app.route("/api/emails/<email_id>/reply", methods=["POST"])
def reply_email(email_id):
    sc = _get_scenario()
    if not sc:
        return jsonify({"error": "No active scenario"}), 400
    data = request.get_json(force=True)
    for e in sc["emails"]:
        if e["id"] == email_id:
            resp = f"Thank you for your response regarding '{e['subject']}'. I've received your information and will follow up if needed.\n\nBest regards,\n{e['from_name']}"
            return jsonify({"status": "ok", "auto_response": resp})
    return jsonify({"error": "Email not found"}), 404


# ---- Tasks ----
@app.route("/api/tasks")
def get_tasks():
    sc = _get_scenario()
    if not sc:
        return jsonify({"tasks": []})
    safe = []
    for t in sc["tasks"]:
        st = dict(t)
        st.pop("sql_answer", None)
        st["hints"] = t["hints"][:t["hints_revealed"]]
        safe.append(st)
    return jsonify({"tasks": safe})


@app.route("/api/tasks/<task_id>/status", methods=["POST"])
def update_task_status(task_id):
    sc = _get_scenario()
    if not sc:
        return jsonify({"error": "No active scenario"}), 400
    data = request.get_json(force=True)
    for t in sc["tasks"]:
        if t["id"] == task_id:
            t["status"] = data.get("status", "in_progress")
            return jsonify({"status": "ok", "task_status": t["status"]})
    return jsonify({"error": "Task not found"}), 404


@app.route("/api/tasks/<task_id>/steps", methods=["POST"])
def update_task_steps(task_id):
    sc = _get_scenario()
    if not sc:
        return jsonify({"error": "No active scenario"}), 400
    data = request.get_json(force=True)
    idx = data.get("step_index", 0)
    for t in sc["tasks"]:
        if t["id"] == task_id and 0 <= idx < len(t["steps"]):
            t["steps"][idx]["completed"] = data.get("completed", True)
            return jsonify({"status": "ok"})
    return jsonify({"error": "Not found"}), 404


@app.route("/api/tasks/<task_id>/hint")
def get_hint(task_id):
    sc = _get_scenario()
    if not sc:
        return jsonify({"error": "No active scenario"}), 400
    level = sc["config"]["assistance_level"]
    if level == "none":
        return jsonify({"hint": None, "message": "No assistance available."})
    for t in sc["tasks"]:
        if t["id"] == task_id:
            total = len(t["hints"])
            rev = t["hints_revealed"]
            if level == "minimal" and rev >= 1:
                return jsonify({"hint": None, "message": "Max hints reached for minimal assistance."})
            if rev >= total:
                return jsonify({"hint": None, "message": "All hints revealed."})
            t["hints_revealed"] = rev + 1
            return jsonify({"hint": t["hints"][rev], "hints_remaining": total - rev - 1})
    return jsonify({"error": "Task not found"}), 404


@app.route("/api/tasks/<task_id>/submit", methods=["POST"])
def submit_task(task_id):
    sc = _get_scenario()
    if not sc:
        return jsonify({"error": "No active scenario"}), 400
    data = request.get_json(force=True)
    work = data.get("work", "")
    tool = data.get("tool_used", "")
    for t in sc["tasks"]:
        if t["id"] == task_id:
            if t.get("sql_answer") and tool == "sql" and work.strip():
                if "select" in work.lower() and "from" in work.lower():
                    t["status"] = "completed"
                    return jsonify({"status": "completed", "message": "SQL query looks good. Task completed!"})
                return jsonify({"status": "needs_revision", "message": "Doesn't appear to be a complete SQL query."})
            if len(work.strip()) > 20:
                t["status"] = "completed"
                return jsonify({"status": "completed", "message": "Submission received. Task completed!"})
            return jsonify({"status": "needs_revision", "message": "Please provide more detail."})
    return jsonify({"error": "Task not found"}), 404


@app.route("/api/help/task/<task_id>")
def get_task_help(task_id):
    sc = _get_scenario()
    if not sc:
        return jsonify({"error": "No active scenario"}), 400
    level = sc["config"]["assistance_level"]
    for t in sc["tasks"]:
        if t["id"] == task_id:
            if level == "none":
                return jsonify({"help": "No assistance available."})
            elif level == "minimal":
                return jsonify({"help": f"Category: {t['category']}\nTools: {', '.join(t['required_tools'])}"})
            elif level == "hints":
                steps = "\n".join(f"  {i+1}. {s['text']}" for i, s in enumerate(t["steps"]))
                return jsonify({"help": f"Category: {t['category']}\nTools: {', '.join(t['required_tools'])}\nTime: ~{t['estimated_minutes']} min\n\nSteps:\n{steps}\n\nUse 'Get Hint' for more guidance."})
            else:
                steps = "\n".join(f"  {i+1}. {s['text']}" for i, s in enumerate(t["steps"]))
                all_h = "\n".join(f"  - {h}" for h in t["hints"])
                sql = f"\n\nExpected SQL:\n{t['sql_answer']}" if t.get("sql_answer") else ""
                return jsonify({"help": f"FULL WALKTHROUGH\n\nCategory: {t['category']}\nTools: {', '.join(t['required_tools'])}\nTime: ~{t['estimated_minutes']} min\n\nSteps:\n{steps}\n\nHints:\n{all_h}{sql}"})
    return jsonify({"error": "Task not found"}), 404


# ---- SQL Console ----
@app.route("/api/sql/execute", methods=["POST"])
def execute_sql():
    data = request.get_json(force=True)
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400
    first = query.split()[0].upper() if query.split() else ""
    if first not in ("SELECT", "WITH", "EXPLAIN", "PRAGMA"):
        return jsonify({"error": "Only SELECT queries are allowed (read-only console)."}), 400
    if re.search(r'\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|ATTACH|DETACH)\b', query, re.I):
        return jsonify({"error": "Modification queries are not allowed."}), 400
    try:
        t0 = time.time()
        conn = _db()
        cur = conn.execute(query)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        ms = round((time.time() - t0) * 1000, 1)
        conn.close()
        return jsonify({"columns": cols, "rows": [list(r) for r in rows],
                         "row_count": len(rows), "execution_time_ms": ms})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/sql/tables")
def list_tables():
    conn = _db()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    result = {}
    for t in tables:
        name = t["name"]
        cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
        result[name] = [{"name": c["name"], "type": c["type"]} for c in cols]
    conn.close()
    return jsonify({"tables": result})


# ---- Python Console ----
@app.route("/api/python/execute", methods=["POST"])
def execute_python():
    sc = _get_scenario()
    if not sc or not sc["config"].get("python_enabled"):
        return jsonify({"error": "Python console not enabled for this scenario."}), 403
    data = request.get_json(force=True)
    code = data.get("code", "").strip()
    if not code:
        return jsonify({"error": "Empty code"}), 400
    preamble = f"import sqlite3, json, csv, statistics, os\nfrom datetime import datetime, timedelta\nconn = sqlite3.connect('{DB_PATH}')\nconn.row_factory = sqlite3.Row\ncursor = conn.cursor()\n"
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(preamble + "\n" + code)
            tmp = f.name
        result = subprocess.run(["python3", tmp], capture_output=True, text=True,
                                timeout=10, cwd=os.path.dirname(__file__))
        os.unlink(tmp)
        return jsonify({"output": result.stdout, "error": result.stderr, "returncode": result.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timed out (10s limit).", "output": ""}), 400
    except Exception as exc:
        return jsonify({"error": str(exc), "output": ""}), 500


# ---- EHR ----
@app.route("/api/ehr/patients")
def search_patients():
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))
    offset = (page - 1) * per_page
    conn = _db()
    if search:
        like = f"%{search}%"
        rows = conn.execute("SELECT * FROM patients WHERE mrn LIKE ? OR first_name LIKE ? OR last_name LIKE ? ORDER BY last_name LIMIT ? OFFSET ?",
                            (like, like, like, per_page, offset)).fetchall()
        total = conn.execute("SELECT COUNT(*) as c FROM patients WHERE mrn LIKE ? OR first_name LIKE ? OR last_name LIKE ?",
                             (like, like, like)).fetchone()["c"]
    else:
        rows = conn.execute("SELECT * FROM patients ORDER BY last_name LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
        total = conn.execute("SELECT COUNT(*) as c FROM patients").fetchone()["c"]
    conn.close()
    return jsonify({"patients": [dict(r) for r in rows], "total": total, "page": page, "per_page": per_page})


@app.route("/api/ehr/patients/<mrn>")
def get_patient(mrn):
    conn = _db()
    patient = conn.execute("SELECT * FROM patients WHERE mrn=?", (mrn,)).fetchone()
    if not patient:
        conn.close()
        return jsonify({"error": "Patient not found"}), 404
    pid = patient["id"]
    encounters = conn.execute("SELECT e.*, d.name as dept_name, pr.first_name||' '||pr.last_name as provider_name FROM encounters e LEFT JOIN departments d ON e.department_id=d.id LEFT JOIN providers pr ON e.provider_id=pr.id WHERE e.patient_id=? ORDER BY e.admit_date DESC", (pid,)).fetchall()
    dx = conn.execute("SELECT * FROM diagnoses WHERE patient_id=? ORDER BY diagnosis_date DESC", (pid,)).fetchall()
    meds = conn.execute("SELECT mo.*, m.name as med_name FROM medication_orders mo LEFT JOIN medications m ON mo.medication_id=m.id WHERE mo.patient_id=? ORDER BY mo.start_date DESC", (pid,)).fetchall()
    labs = conn.execute("SELECT * FROM lab_results WHERE patient_id=? ORDER BY result_date DESC", (pid,)).fetchall()
    allergies = conn.execute("SELECT * FROM allergies WHERE patient_id=?", (pid,)).fetchall()
    vitals = conn.execute("SELECT * FROM vital_signs WHERE patient_id=? ORDER BY recorded_at DESC LIMIT 20", (pid,)).fetchall()
    conn.close()
    return jsonify({
        "patient": dict(patient),
        "encounters": [dict(r) for r in encounters],
        "diagnoses": [dict(r) for r in dx],
        "medications": [dict(r) for r in meds],
        "lab_results": [dict(r) for r in labs],
        "allergies": [dict(r) for r in allergies],
        "vitals": [dict(r) for r in vitals],
    })


@app.route("/api/ehr/encounters/<int:enc_id>")
def get_encounter(enc_id):
    conn = _db()
    enc = conn.execute("SELECT * FROM encounters WHERE id=?", (enc_id,)).fetchone()
    if not enc:
        conn.close()
        return jsonify({"error": "Encounter not found"}), 404
    patient = conn.execute("SELECT * FROM patients WHERE id=?", (enc["patient_id"],)).fetchone()
    provider = conn.execute("SELECT * FROM providers WHERE id=?", (enc["provider_id"],)).fetchone()
    dept = conn.execute("SELECT * FROM departments WHERE id=?", (enc["department_id"],)).fetchone()
    dx = conn.execute("SELECT * FROM diagnoses WHERE encounter_id=?", (enc_id,)).fetchall()
    meds = conn.execute("SELECT mo.*, m.name as med_name FROM medication_orders mo LEFT JOIN medications m ON mo.medication_id=m.id WHERE mo.encounter_id=?", (enc_id,)).fetchall()
    labs = conn.execute("SELECT * FROM lab_results WHERE encounter_id=?", (enc_id,)).fetchall()
    vitals = conn.execute("SELECT * FROM vital_signs WHERE encounter_id=?", (enc_id,)).fetchall()
    conn.close()
    return jsonify({
        "encounter": dict(enc),
        "patient": dict(patient) if patient else None,
        "provider": dict(provider) if provider else None,
        "department": dict(dept) if dept else None,
        "diagnoses": [dict(r) for r in dx],
        "medications": [dict(r) for r in meds],
        "lab_results": [dict(r) for r in labs],
        "vitals": [dict(r) for r in vitals],
    })


# ---- Dashboard ----
@app.route("/api/dashboard/metrics")
def dashboard_metrics():
    conn = _db()
    total_patients = conn.execute("SELECT COUNT(*) as c FROM patients").fetchone()["c"]
    enc_30d = conn.execute("SELECT COUNT(*) as c FROM encounters WHERE admit_date >= datetime('now','-30 days')").fetchone()["c"]
    avg_los = conn.execute("SELECT ROUND(AVG(julianday(discharge_date)-julianday(admit_date)),1) as v FROM encounters WHERE discharge_date IS NOT NULL").fetchone()["v"] or 0
    ed_7d = conn.execute("SELECT COUNT(*) as c FROM encounters WHERE encounter_type='emergency' AND admit_date >= datetime('now','-7 days')").fetchone()["c"]
    active = conn.execute("SELECT COUNT(*) as c FROM encounters WHERE status='active'").fetchone()["c"]
    crit_labs = conn.execute("SELECT COUNT(*) as c FROM lab_results WHERE abnormal_flag='C' AND result_date >= datetime('now','-7 days')").fetchone()["c"]
    hl7_err = conn.execute("SELECT COUNT(*) as c FROM hl7_messages WHERE status='error'").fetchone()["c"]
    alerts = conn.execute("SELECT COUNT(*) as c FROM clinical_alerts WHERE status != 'acknowledged'").fetchone()["c"]
    conn.close()
    return jsonify({
        "total_patients": total_patients, "encounters_30d": enc_30d,
        "avg_los_days": avg_los, "ed_visits_7d": ed_7d,
        "active_encounters": active, "critical_labs_7d": crit_labs,
        "hl7_errors": hl7_err, "open_alerts": alerts,
    })


@app.route("/api/dashboard/charts")
def dashboard_charts():
    conn = _db()
    by_type = conn.execute("SELECT encounter_type, COUNT(*) as count FROM encounters GROUP BY encounter_type ORDER BY count DESC").fetchall()
    top_dx = conn.execute("SELECT dx.description, COUNT(*) as count FROM diagnoses dx GROUP BY dx.description ORDER BY count DESC LIMIT 10").fetchall()
    dept_census = conn.execute("SELECT d.name, COUNT(e.id) as active FROM departments d LEFT JOIN encounters e ON d.id=e.department_id AND e.status='active' GROUP BY d.id ORDER BY active DESC").fetchall()
    monthly = conn.execute("SELECT strftime('%Y-%m', admit_date) as month, COUNT(*) as count FROM encounters WHERE admit_date >= datetime('now','-6 months') GROUP BY month ORDER BY month").fetchall()
    sys_health = conn.execute("SELECT system_name, status, response_time_ms FROM system_status ORDER BY system_name").fetchall()
    conn.close()
    return jsonify({
        "encounters_by_type": [dict(r) for r in by_type],
        "top_diagnoses": [dict(r) for r in top_dx],
        "department_census": [dict(r) for r in dept_census],
        "monthly_encounters": [dict(r) for r in monthly],
        "system_health": [dict(r) for r in sys_health],
    })


@app.route("/api/ehr/alerts")
def get_alerts():
    conn = _db()
    alerts = conn.execute("SELECT ca.*, p.mrn, p.first_name||' '||p.last_name as patient_name FROM clinical_alerts ca LEFT JOIN patients p ON ca.patient_id=p.id ORDER BY ca.created_at DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify({"alerts": [dict(r) for r in alerts]})


@app.route("/api/ehr/hl7")
def get_hl7():
    conn = _db()
    status = request.args.get("status", "")
    if status:
        msgs = conn.execute("SELECT * FROM hl7_messages WHERE status=? ORDER BY created_at DESC LIMIT 50", (status,)).fetchall()
    else:
        msgs = conn.execute("SELECT * FROM hl7_messages ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify({"messages": [dict(r) for r in msgs]})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Initializing database...")
        init_db(DB_PATH)
        seed_data(DB_PATH)
    app.run(debug=True, host="0.0.0.0", port=5000)

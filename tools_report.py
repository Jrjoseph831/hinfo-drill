"""
tools_report.py - Report Builder for the Health Informatics Learning
Platform.

Generates structured clinical and administrative reports from real
SQLite database data.  Each report template runs actual SQL queries and
returns structured, JSON-serialisable data.

Public API
----------
    get_report_templates()
    generate_report(db_path, template_name, params)
    format_report_text(report_data)
"""

import sqlite3
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _db(db_path):
    """Return an sqlite3.Connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_to_dicts(rows):
    """Convert a list of sqlite3.Row objects to a list of plain dicts."""
    return [dict(r) for r in rows]


def _safe_div(numerator, denominator, digits=2):
    """Return rounded division or 0.0 when denominator is zero."""
    if not denominator:
        return 0.0
    return round(numerator / denominator, digits)


def _default_date_range():
    """Return (start, end) date strings spanning the last 30 days."""
    end = datetime(2026, 2, 25)
    start = end - timedelta(days=30)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Report template registry
# ---------------------------------------------------------------------------

REPORT_TEMPLATES = [
    {
        "name": "monthly_executive_summary",
        "title": "Monthly Executive Summary",
        "description": "High-level overview of hospital operations including patient volume, financials, and key metrics.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "department_utilization",
        "title": "Department Utilization Report",
        "description": "Bed utilization, encounter volume, and staffing metrics by department.",
        "parameters": ["start_date", "end_date", "department_id"],
    },
    {
        "name": "quality_measures_dashboard",
        "title": "Quality Measures Dashboard",
        "description": "Clinical quality indicators including readmissions, mortality, infection rates, and patient safety.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "readmission_analysis",
        "title": "Readmission Analysis Report",
        "description": "30-day readmission rates by department, diagnosis, and provider with root-cause indicators.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "ed_throughput",
        "title": "ED Throughput Report",
        "description": "Emergency Department volumes, wait times, admission rates, and left-without-being-seen metrics.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "infection_control",
        "title": "Infection Control Surveillance",
        "description": "Suspected healthcare-associated infection tracking based on antibiotic use and culture data.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "claim_denial",
        "title": "Insurance Claim Denial Report",
        "description": "Claim denial rates, top denial reasons, payer analysis, and financial impact.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "provider_productivity",
        "title": "Provider Productivity Report",
        "description": "Encounter volume, procedure counts, and RVU estimates by provider.",
        "parameters": ["start_date", "end_date", "department_id"],
    },
    {
        "name": "lab_turnaround",
        "title": "Lab Turnaround Time Report",
        "description": "Collected-to-resulted turnaround times by test type with outlier analysis.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "patient_safety",
        "title": "Patient Safety Event Summary",
        "description": "Safety-relevant events including critical lab values, system alerts, and anomalous patterns.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "medication_reconciliation",
        "title": "Medication Reconciliation Audit",
        "description": "Analysis of medication orders for potential duplicates, interactions, and reconciliation gaps.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "coding_accuracy",
        "title": "Coding Accuracy Report",
        "description": "Aggregate coding accuracy metrics across encounters including DRG alignment and missing codes.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "hl7_interface_status",
        "title": "HL7 Interface Status Report",
        "description": "HL7 message volumes, error rates, and interface health by sending/receiving system.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "hipaa_compliance",
        "title": "HIPAA Compliance Summary",
        "description": "PHI access audit summary, suspicious access patterns, and compliance posture.",
        "parameters": ["start_date", "end_date"],
    },
    {
        "name": "bed_management",
        "title": "Bed Management Report",
        "description": "Census, average length of stay, occupancy estimates, and discharge patterns by department.",
        "parameters": ["start_date", "end_date"],
    },
]


# ---------------------------------------------------------------------------
# Individual report generators
# ---------------------------------------------------------------------------

def _report_monthly_executive_summary(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    total_encounters = conn.execute(
        "SELECT COUNT(*) FROM encounters WHERE admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    encounters_by_type = _rows_to_dicts(conn.execute(
        "SELECT encounter_type, COUNT(*) as count FROM encounters "
        "WHERE admission_date BETWEEN ? AND ? GROUP BY encounter_type ORDER BY count DESC",
        (start, end)
    ).fetchall())

    total_patients = conn.execute(
        "SELECT COUNT(DISTINCT patient_mrn) FROM encounters WHERE admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    avg_los = conn.execute(
        "SELECT ROUND(AVG(los_days), 1) FROM encounters "
        "WHERE encounter_type = 'inpatient' AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0] or 0

    total_claims = conn.execute(
        "SELECT COUNT(*) FROM insurance_claims WHERE submitted_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    financials = conn.execute(
        "SELECT ROUND(SUM(claim_amount), 2) as total_billed, "
        "ROUND(SUM(paid_amount), 2) as total_collected, "
        "ROUND(SUM(denied_amount), 2) as total_denied "
        "FROM insurance_claims WHERE submitted_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()

    total_billed = financials["total_billed"] or 0
    total_collected = financials["total_collected"] or 0
    total_denied = financials["total_denied"] or 0
    collection_rate = _safe_div(total_collected, total_billed, 1)

    denial_count = conn.execute(
        "SELECT COUNT(*) FROM insurance_claims WHERE claim_status = 'denied' "
        "AND submitted_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]
    denial_rate = _safe_div(denial_count, total_claims, 1) * 100

    top_diagnoses = _rows_to_dicts(conn.execute(
        "SELECT icd10_code, description, COUNT(*) as count FROM diagnoses "
        "WHERE diagnosed_date BETWEEN ? AND ? "
        "GROUP BY icd10_code ORDER BY count DESC LIMIT 10",
        (start, end)
    ).fetchall())

    dept_volume = _rows_to_dicts(conn.execute(
        "SELECT d.dept_name, COUNT(*) as encounter_count "
        "FROM encounters e JOIN departments d ON e.department_id = d.dept_id "
        "WHERE e.admission_date BETWEEN ? AND ? "
        "GROUP BY d.dept_name ORDER BY encounter_count DESC",
        (start, end)
    ).fetchall())

    return {
        "sections": [
            {
                "title": "Patient Volume",
                "data": {
                    "total_encounters": total_encounters,
                    "unique_patients": total_patients,
                    "encounters_by_type": encounters_by_type,
                },
            },
            {
                "title": "Length of Stay",
                "data": {"average_los_inpatient_days": avg_los},
            },
            {
                "title": "Financial Summary",
                "data": {
                    "total_claims_submitted": total_claims,
                    "total_billed": total_billed,
                    "total_collected": total_collected,
                    "total_denied": total_denied,
                    "collection_rate_pct": collection_rate * 100,
                    "denial_rate_pct": denial_rate,
                },
            },
            {
                "title": "Top 10 Diagnoses",
                "data": top_diagnoses,
            },
            {
                "title": "Department Volume",
                "data": dept_volume,
            },
        ],
        "summary": (
            f"During {start} to {end}, the facility recorded {total_encounters} encounters "
            f"across {total_patients} unique patients. Average inpatient LOS was {avg_los} days. "
            f"Total billed: ${total_billed:,.2f}, collected: ${total_collected:,.2f} "
            f"({collection_rate*100:.1f}% collection rate). Denial rate: {denial_rate:.1f}%."
        ),
    }


def _report_department_utilization(conn, params):
    start, end = params.get("start_date"), params.get("end_date")
    dept_id = params.get("department_id")

    dept_filter = ""
    query_params = [start, end]
    if dept_id:
        dept_filter = "AND e.department_id = ?"
        query_params.append(int(dept_id))

    utilization = _rows_to_dicts(conn.execute(
        f"SELECT d.dept_name, d.dept_code, COUNT(e.encounter_id) as encounters, "
        f"COUNT(DISTINCT e.patient_mrn) as unique_patients, "
        f"ROUND(AVG(e.los_days), 1) as avg_los, "
        f"MAX(e.los_days) as max_los, "
        f"SUM(CASE WHEN e.encounter_type = 'inpatient' THEN 1 ELSE 0 END) as inpatient_count, "
        f"SUM(CASE WHEN e.encounter_type = 'ED' THEN 1 ELSE 0 END) as ed_count, "
        f"SUM(CASE WHEN e.encounter_type = 'outpatient' THEN 1 ELSE 0 END) as outpatient_count "
        f"FROM encounters e "
        f"JOIN departments d ON e.department_id = d.dept_id "
        f"WHERE e.admission_date BETWEEN ? AND ? {dept_filter} "
        f"GROUP BY d.dept_name ORDER BY encounters DESC",
        query_params
    ).fetchall())

    provider_counts = _rows_to_dicts(conn.execute(
        f"SELECT d.dept_name, COUNT(DISTINCT e.attending_provider_id) as providers, "
        f"COUNT(e.encounter_id) as encounters, "
        f"ROUND(CAST(COUNT(e.encounter_id) AS REAL) / MAX(COUNT(DISTINCT e.attending_provider_id), 1), 1) as encounters_per_provider "
        f"FROM encounters e "
        f"JOIN departments d ON e.department_id = d.dept_id "
        f"WHERE e.admission_date BETWEEN ? AND ? {dept_filter} "
        f"GROUP BY d.dept_name ORDER BY encounters DESC",
        query_params
    ).fetchall())

    daily_volume = _rows_to_dicts(conn.execute(
        f"SELECT DATE(e.admission_date) as date, COUNT(*) as encounters "
        f"FROM encounters e "
        f"WHERE e.admission_date BETWEEN ? AND ? {dept_filter} "
        f"GROUP BY DATE(e.admission_date) ORDER BY date",
        query_params
    ).fetchall())

    total_enc = sum(u["encounters"] for u in utilization)
    dept_count = len(utilization)

    return {
        "sections": [
            {"title": "Department Utilization", "data": utilization},
            {"title": "Provider Distribution", "data": provider_counts},
            {"title": "Daily Volume Trend", "data": daily_volume},
        ],
        "summary": (
            f"Report covers {start} to {end}: {total_enc} total encounters "
            f"across {dept_count} departments."
        ),
    }


def _report_quality_measures(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    # Readmission indicator: patients with >1 inpatient encounter within 30 days
    readmit_rows = conn.execute(
        "SELECT e1.patient_mrn, COUNT(DISTINCT e1.encounter_id) as admissions "
        "FROM encounters e1 "
        "WHERE e1.encounter_type = 'inpatient' AND e1.admission_date BETWEEN ? AND ? "
        "GROUP BY e1.patient_mrn HAVING admissions > 1",
        (start, end)
    ).fetchall()
    readmission_patients = len(readmit_rows)

    total_inpatient_patients = conn.execute(
        "SELECT COUNT(DISTINCT patient_mrn) FROM encounters "
        "WHERE encounter_type = 'inpatient' AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]
    readmission_rate = _safe_div(readmission_patients, total_inpatient_patients, 3) * 100

    # Mortality indicator
    expired = conn.execute(
        "SELECT COUNT(*) FROM encounters WHERE disposition = 'Expired' "
        "AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]
    total_discharges = conn.execute(
        "SELECT COUNT(*) FROM encounters WHERE status = 'closed' "
        "AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]
    mortality_rate = _safe_div(expired, total_discharges, 3) * 100

    # Critical lab values
    critical_labs = conn.execute(
        "SELECT COUNT(*) FROM lab_results WHERE abnormal_flag = 'C' "
        "AND collected_datetime BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    # Average LOS
    avg_los = conn.execute(
        "SELECT ROUND(AVG(los_days), 1) FROM encounters "
        "WHERE encounter_type = 'inpatient' AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0] or 0

    # LAMA (left against medical advice)
    lama = conn.execute(
        "SELECT COUNT(*) FROM encounters WHERE disposition = 'Left against medical advice' "
        "AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    # ED encounters converted to inpatient (proxy)
    ed_admits = conn.execute(
        "SELECT COUNT(DISTINCT e1.patient_mrn) FROM encounters e1 "
        "JOIN encounters e2 ON e1.patient_mrn = e2.patient_mrn "
        "WHERE e1.encounter_type = 'ED' AND e2.encounter_type = 'inpatient' "
        "AND e1.admission_date BETWEEN ? AND ? "
        "AND e2.admission_date BETWEEN e1.admission_date AND DATE(e1.admission_date, '+1 day')",
        (start, end)
    ).fetchone()[0]

    return {
        "sections": [
            {
                "title": "Quality Indicators",
                "data": {
                    "readmission_rate_pct": round(readmission_rate, 1),
                    "readmission_patients": readmission_patients,
                    "total_inpatient_patients": total_inpatient_patients,
                    "mortality_rate_pct": round(mortality_rate, 2),
                    "expired_count": expired,
                    "total_discharges": total_discharges,
                    "avg_los_days": avg_los,
                    "lama_count": lama,
                    "ed_to_inpatient_conversions": ed_admits,
                },
            },
            {
                "title": "Patient Safety",
                "data": {
                    "critical_lab_values": critical_labs,
                },
            },
        ],
        "summary": (
            f"Quality measures for {start} to {end}: "
            f"Readmission rate {readmission_rate:.1f}%, "
            f"Mortality rate {mortality_rate:.2f}%, "
            f"Average LOS {avg_los} days, "
            f"Critical lab values: {critical_labs}, "
            f"LAMA: {lama}."
        ),
    }


def _report_readmission_analysis(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    by_dept = _rows_to_dicts(conn.execute(
        "SELECT d.dept_name, COUNT(DISTINCT e1.patient_mrn) as readmit_patients, "
        "COUNT(DISTINCT e2.patient_mrn) as total_patients, "
        "ROUND(CAST(COUNT(DISTINCT e1.patient_mrn) AS REAL) * 100 / "
        "MAX(COUNT(DISTINCT e2.patient_mrn), 1), 1) as readmit_rate_pct "
        "FROM encounters e2 "
        "JOIN departments d ON e2.department_id = d.dept_id "
        "LEFT JOIN encounters e1 ON e1.patient_mrn = e2.patient_mrn "
        "  AND e1.encounter_type = 'inpatient' "
        "  AND e1.encounter_id != e2.encounter_id "
        "  AND e1.admission_date BETWEEN e2.discharge_date AND DATE(e2.discharge_date, '+30 days') "
        "WHERE e2.encounter_type = 'inpatient' AND e2.admission_date BETWEEN ? AND ? "
        "GROUP BY d.dept_name ORDER BY readmit_rate_pct DESC",
        (start, end)
    ).fetchall())

    by_diagnosis = _rows_to_dicts(conn.execute(
        "SELECT dx.icd10_code, dx.description, COUNT(DISTINCT dx.encounter_id) as encounters "
        "FROM diagnoses dx "
        "JOIN encounters e ON dx.encounter_id = e.encounter_id "
        "WHERE e.encounter_type = 'inpatient' AND e.admission_date BETWEEN ? AND ? "
        "AND dx.diagnosis_type = 'primary' "
        "AND dx.patient_mrn IN ("
        "  SELECT patient_mrn FROM encounters "
        "  WHERE encounter_type = 'inpatient' AND admission_date BETWEEN ? AND ? "
        "  GROUP BY patient_mrn HAVING COUNT(*) > 1"
        ") "
        "GROUP BY dx.icd10_code ORDER BY encounters DESC LIMIT 10",
        (start, end, start, end)
    ).fetchall())

    return {
        "sections": [
            {"title": "Readmission Rates by Department", "data": by_dept},
            {"title": "Top Diagnoses Among Readmitted Patients", "data": by_diagnosis},
        ],
        "summary": f"Readmission analysis for {start} to {end}.",
    }


def _report_ed_throughput(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    total_ed = conn.execute(
        "SELECT COUNT(*) FROM encounters WHERE encounter_type = 'ED' "
        "AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    avg_los = conn.execute(
        "SELECT ROUND(AVG(los_days * 24), 1) FROM encounters "
        "WHERE encounter_type = 'ED' AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0] or 0

    by_complaint = _rows_to_dicts(conn.execute(
        "SELECT chief_complaint, COUNT(*) as count FROM encounters "
        "WHERE encounter_type = 'ED' AND admission_date BETWEEN ? AND ? "
        "GROUP BY chief_complaint ORDER BY count DESC LIMIT 10",
        (start, end)
    ).fetchall())

    by_disposition = _rows_to_dicts(conn.execute(
        "SELECT disposition, COUNT(*) as count FROM encounters "
        "WHERE encounter_type = 'ED' AND admission_date BETWEEN ? AND ? "
        "AND disposition IS NOT NULL "
        "GROUP BY disposition ORDER BY count DESC",
        (start, end)
    ).fetchall())

    daily_volume = _rows_to_dicts(conn.execute(
        "SELECT DATE(admission_date) as date, COUNT(*) as visits "
        "FROM encounters WHERE encounter_type = 'ED' "
        "AND admission_date BETWEEN ? AND ? "
        "GROUP BY DATE(admission_date) ORDER BY date",
        (start, end)
    ).fetchall())

    hourly = _rows_to_dicts(conn.execute(
        "SELECT CAST(STRFTIME('%H', admission_date) AS INTEGER) as hour, COUNT(*) as visits "
        "FROM encounters WHERE encounter_type = 'ED' "
        "AND admission_date BETWEEN ? AND ? "
        "GROUP BY hour ORDER BY hour",
        (start, end)
    ).fetchall())

    lama = conn.execute(
        "SELECT COUNT(*) FROM encounters "
        "WHERE encounter_type = 'ED' AND disposition = 'Left against medical advice' "
        "AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    return {
        "sections": [
            {
                "title": "ED Overview",
                "data": {
                    "total_visits": total_ed,
                    "avg_los_hours": avg_los,
                    "lama_count": lama,
                    "lama_rate_pct": _safe_div(lama, total_ed, 1) * 100,
                },
            },
            {"title": "Top Chief Complaints", "data": by_complaint},
            {"title": "Disposition Distribution", "data": by_disposition},
            {"title": "Daily Volume", "data": daily_volume},
            {"title": "Hourly Volume Distribution", "data": hourly},
        ],
        "summary": (
            f"ED processed {total_ed} visits ({start} to {end}). "
            f"Average ED LOS: {avg_los} hours. LAMA: {lama}."
        ),
    }


def _report_infection_control(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    # Proxy: IV antibiotic use patterns suggest possible infections
    iv_antibiotics = _rows_to_dicts(conn.execute(
        "SELECT medication_name, COUNT(*) as orders, "
        "COUNT(DISTINCT patient_mrn) as patients "
        "FROM medications "
        "WHERE route = 'IV' AND medication_name IN "
        "('Ceftriaxone','Vancomycin','Piperacillin-Tazobactam','Levofloxacin') "
        "AND start_date BETWEEN ? AND ? "
        "GROUP BY medication_name ORDER BY orders DESC",
        (start, end)
    ).fetchall())

    infection_dx = _rows_to_dicts(conn.execute(
        "SELECT dx.icd10_code, dx.description, COUNT(*) as count "
        "FROM diagnoses dx "
        "JOIN encounters e ON dx.encounter_id = e.encounter_id "
        "WHERE (dx.icd10_code LIKE 'A%' OR dx.icd10_code LIKE 'B%' "
        "  OR dx.icd10_code = 'N39.0' OR dx.icd10_code = 'T81.4XXA' "
        "  OR dx.icd10_code LIKE 'J1%') "
        "AND e.admission_date BETWEEN ? AND ? "
        "GROUP BY dx.icd10_code ORDER BY count DESC LIMIT 15",
        (start, end)
    ).fetchall())

    culture_orders = conn.execute(
        "SELECT COUNT(*) FROM lab_results "
        "WHERE (test_name LIKE '%Culture%' OR test_code IN ('87086','87070')) "
        "AND collected_datetime BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    by_department = _rows_to_dicts(conn.execute(
        "SELECT d.dept_name, COUNT(DISTINCT dx.encounter_id) as infection_encounters "
        "FROM diagnoses dx "
        "JOIN encounters e ON dx.encounter_id = e.encounter_id "
        "JOIN departments d ON e.department_id = d.dept_id "
        "WHERE (dx.icd10_code LIKE 'A%' OR dx.icd10_code LIKE 'B%' "
        "  OR dx.icd10_code = 'N39.0' OR dx.icd10_code = 'T81.4XXA') "
        "AND e.admission_date BETWEEN ? AND ? "
        "GROUP BY d.dept_name ORDER BY infection_encounters DESC",
        (start, end)
    ).fetchall())

    return {
        "sections": [
            {"title": "IV Antibiotic Usage", "data": iv_antibiotics},
            {"title": "Infection-Related Diagnoses", "data": infection_dx},
            {
                "title": "Culture Orders",
                "data": {"total_cultures_ordered": culture_orders},
            },
            {"title": "Infections by Department", "data": by_department},
        ],
        "summary": (
            f"Infection surveillance for {start} to {end}: "
            f"{culture_orders} cultures ordered. See breakdown by department and antibiotic."
        ),
    }


def _report_claim_denial(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    overview = conn.execute(
        "SELECT COUNT(*) as total_claims, "
        "SUM(CASE WHEN claim_status = 'denied' THEN 1 ELSE 0 END) as denied, "
        "SUM(CASE WHEN claim_status = 'paid' THEN 1 ELSE 0 END) as paid, "
        "SUM(CASE WHEN claim_status = 'appealed' THEN 1 ELSE 0 END) as appealed, "
        "ROUND(SUM(claim_amount), 2) as total_billed, "
        "ROUND(SUM(denied_amount), 2) as total_denied_amt "
        "FROM insurance_claims WHERE submitted_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()
    overview_data = dict(overview)
    overview_data["denial_rate_pct"] = _safe_div(
        overview_data["denied"], overview_data["total_claims"], 1
    ) * 100

    by_reason = _rows_to_dicts(conn.execute(
        "SELECT denial_reason, COUNT(*) as count, "
        "ROUND(SUM(denied_amount), 2) as total_denied "
        "FROM insurance_claims "
        "WHERE claim_status IN ('denied', 'appealed') "
        "AND submitted_date BETWEEN ? AND ? "
        "AND denial_reason IS NOT NULL "
        "GROUP BY denial_reason ORDER BY count DESC",
        (start, end)
    ).fetchall())

    by_payer = _rows_to_dicts(conn.execute(
        "SELECT insurance_plan, COUNT(*) as total_claims, "
        "SUM(CASE WHEN claim_status = 'denied' THEN 1 ELSE 0 END) as denied, "
        "ROUND(SUM(denied_amount), 2) as total_denied_amt "
        "FROM insurance_claims WHERE submitted_date BETWEEN ? AND ? "
        "GROUP BY insurance_plan ORDER BY denied DESC LIMIT 10",
        (start, end)
    ).fetchall())

    monthly_trend = _rows_to_dicts(conn.execute(
        "SELECT STRFTIME('%Y-%m', submitted_date) as month, "
        "COUNT(*) as total, "
        "SUM(CASE WHEN claim_status = 'denied' THEN 1 ELSE 0 END) as denied "
        "FROM insurance_claims WHERE submitted_date BETWEEN ? AND ? "
        "GROUP BY month ORDER BY month",
        (start, end)
    ).fetchall())

    return {
        "sections": [
            {"title": "Claims Overview", "data": overview_data},
            {"title": "Top Denial Reasons", "data": by_reason},
            {"title": "Denials by Payer", "data": by_payer},
            {"title": "Monthly Trend", "data": monthly_trend},
        ],
        "summary": (
            f"Claims report for {start} to {end}: {overview_data['total_claims']} claims submitted, "
            f"{overview_data['denied']} denied ({overview_data['denial_rate_pct']:.1f}%). "
            f"Total denied amount: ${overview_data.get('total_denied_amt', 0) or 0:,.2f}."
        ),
    }


def _report_provider_productivity(conn, params):
    start, end = params.get("start_date"), params.get("end_date")
    dept_id = params.get("department_id")

    dept_filter = ""
    query_params = [start, end]
    if dept_id:
        dept_filter = "AND p.department_id = ?"
        query_params.append(int(dept_id))

    productivity = _rows_to_dicts(conn.execute(
        f"SELECT p.provider_id, p.first_name || ' ' || p.last_name as provider_name, "
        f"p.credential, p.specialty, "
        f"COUNT(DISTINCT e.encounter_id) as encounters, "
        f"COUNT(DISTINCT e.patient_mrn) as unique_patients "
        f"FROM providers p "
        f"LEFT JOIN encounters e ON p.provider_id = e.attending_provider_id "
        f"  AND e.admission_date BETWEEN ? AND ? "
        f"WHERE p.active = 1 {dept_filter} "
        f"GROUP BY p.provider_id ORDER BY encounters DESC LIMIT 30",
        query_params
    ).fetchall())

    procedure_counts = _rows_to_dicts(conn.execute(
        f"SELECT p.first_name || ' ' || p.last_name as provider_name, "
        f"COUNT(pr.procedure_id) as procedures "
        f"FROM providers p "
        f"LEFT JOIN procedures pr ON p.provider_id = pr.performing_provider_id "
        f"  AND pr.procedure_date BETWEEN ? AND ? "
        f"WHERE p.active = 1 {dept_filter} "
        f"GROUP BY p.provider_id HAVING procedures > 0 ORDER BY procedures DESC LIMIT 20",
        query_params
    ).fetchall())

    return {
        "sections": [
            {"title": "Provider Encounter Volume", "data": productivity},
            {"title": "Procedure Volume by Provider", "data": procedure_counts},
        ],
        "summary": (
            f"Provider productivity report for {start} to {end}. "
            f"{len(productivity)} active providers evaluated."
        ),
    }


def _report_lab_turnaround(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    tat_by_test = _rows_to_dicts(conn.execute(
        "SELECT test_name, COUNT(*) as count, "
        "ROUND(AVG((JULIANDAY(resulted_datetime) - JULIANDAY(collected_datetime)) * 24 * 60), 0) as avg_tat_minutes, "
        "ROUND(MIN((JULIANDAY(resulted_datetime) - JULIANDAY(collected_datetime)) * 24 * 60), 0) as min_tat_minutes, "
        "ROUND(MAX((JULIANDAY(resulted_datetime) - JULIANDAY(collected_datetime)) * 24 * 60), 0) as max_tat_minutes "
        "FROM lab_results "
        "WHERE collected_datetime BETWEEN ? AND ? "
        "AND resulted_datetime IS NOT NULL AND collected_datetime IS NOT NULL "
        "GROUP BY test_name ORDER BY avg_tat_minutes DESC",
        (start, end)
    ).fetchall())

    abnormal_rates = _rows_to_dicts(conn.execute(
        "SELECT test_name, COUNT(*) as total, "
        "SUM(CASE WHEN abnormal_flag != 'N' THEN 1 ELSE 0 END) as abnormal, "
        "ROUND(SUM(CASE WHEN abnormal_flag != 'N' THEN 1.0 ELSE 0 END) * 100 / COUNT(*), 1) as abnormal_rate_pct "
        "FROM lab_results WHERE collected_datetime BETWEEN ? AND ? "
        "GROUP BY test_name ORDER BY abnormal_rate_pct DESC LIMIT 15",
        (start, end)
    ).fetchall())

    stat_breakdown = _rows_to_dicts(conn.execute(
        "SELECT l.status, COUNT(*) as count "
        "FROM lab_results l "
        "WHERE l.collected_datetime BETWEEN ? AND ? "
        "GROUP BY l.status",
        (start, end)
    ).fetchall())

    return {
        "sections": [
            {"title": "Turnaround Time by Test", "data": tat_by_test},
            {"title": "Abnormal Result Rates", "data": abnormal_rates},
            {"title": "Lab Result Status Breakdown", "data": stat_breakdown},
        ],
        "summary": (
            f"Lab TAT report for {start} to {end}: "
            f"{len(tat_by_test)} test types analyzed."
        ),
    }


def _report_patient_safety(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    critical_labs = _rows_to_dicts(conn.execute(
        "SELECT l.test_name, l.result_value, l.result_unit, "
        "l.reference_range_low, l.reference_range_high, "
        "l.patient_mrn, l.collected_datetime "
        "FROM lab_results l "
        "WHERE l.abnormal_flag = 'C' AND l.collected_datetime BETWEEN ? AND ? "
        "ORDER BY l.collected_datetime DESC LIMIT 20",
        (start, end)
    ).fetchall())

    system_alerts = _rows_to_dicts(conn.execute(
        "SELECT alert_type, severity, COUNT(*) as count "
        "FROM system_alerts WHERE created_at BETWEEN ? AND ? "
        "GROUP BY alert_type, severity ORDER BY count DESC",
        (start, end)
    ).fetchall())

    security_alerts = _rows_to_dicts(conn.execute(
        "SELECT message, severity, created_at "
        "FROM system_alerts WHERE alert_type = 'security' "
        "AND created_at BETWEEN ? AND ? "
        "ORDER BY created_at DESC",
        (start, end)
    ).fetchall())

    expired = conn.execute(
        "SELECT COUNT(*) FROM encounters WHERE disposition = 'Expired' "
        "AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    return {
        "sections": [
            {"title": "Critical Lab Values", "data": critical_labs},
            {"title": "System Alerts Summary", "data": system_alerts},
            {"title": "Security Alerts", "data": security_alerts},
            {"title": "Mortality", "data": {"expired_patients": expired}},
        ],
        "summary": (
            f"Patient safety report for {start} to {end}: "
            f"{len(critical_labs)} critical lab values, {expired} mortalities, "
            f"{len(security_alerts)} security alerts."
        ),
    }


def _report_medication_reconciliation(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    active_meds_per_patient = _rows_to_dicts(conn.execute(
        "SELECT patient_mrn, COUNT(*) as active_medications "
        "FROM medications WHERE status = 'active' "
        "AND start_date BETWEEN ? AND ? "
        "GROUP BY patient_mrn ORDER BY active_medications DESC LIMIT 20",
        (start, end)
    ).fetchall())

    polypharmacy = conn.execute(
        "SELECT COUNT(DISTINCT patient_mrn) FROM ("
        "  SELECT patient_mrn, COUNT(*) as med_count "
        "  FROM medications WHERE status = 'active' "
        "  AND start_date BETWEEN ? AND ? "
        "  GROUP BY patient_mrn HAVING med_count >= 10"
        ")",
        (start, end)
    ).fetchone()[0]

    # Potential duplicates: same patient, same medication, overlapping dates
    potential_dups = _rows_to_dicts(conn.execute(
        "SELECT m1.patient_mrn, m1.medication_name, "
        "COUNT(*) as duplicate_count "
        "FROM medications m1 "
        "JOIN medications m2 ON m1.patient_mrn = m2.patient_mrn "
        "  AND m1.medication_name = m2.medication_name "
        "  AND m1.med_id < m2.med_id "
        "  AND m1.status = 'active' AND m2.status = 'active' "
        "  AND m1.start_date BETWEEN ? AND ? "
        "GROUP BY m1.patient_mrn, m1.medication_name "
        "ORDER BY duplicate_count DESC LIMIT 15",
        (start, end)
    ).fetchall())

    discontinued_meds = _rows_to_dicts(conn.execute(
        "SELECT medication_name, COUNT(*) as count "
        "FROM medications WHERE status = 'discontinued' "
        "AND start_date BETWEEN ? AND ? "
        "GROUP BY medication_name ORDER BY count DESC LIMIT 10",
        (start, end)
    ).fetchall())

    med_route_distribution = _rows_to_dicts(conn.execute(
        "SELECT route, COUNT(*) as count FROM medications "
        "WHERE start_date BETWEEN ? AND ? "
        "GROUP BY route ORDER BY count DESC",
        (start, end)
    ).fetchall())

    return {
        "sections": [
            {"title": "Polypharmacy Alert", "data": {
                "patients_with_10_plus_active_meds": polypharmacy,
                "top_medication_counts": active_meds_per_patient,
            }},
            {"title": "Potential Duplicate Orders", "data": potential_dups},
            {"title": "Top Discontinued Medications", "data": discontinued_meds},
            {"title": "Medication Route Distribution", "data": med_route_distribution},
        ],
        "summary": (
            f"Medication reconciliation audit for {start} to {end}: "
            f"{polypharmacy} patients with 10+ active meds (polypharmacy risk), "
            f"{len(potential_dups)} potential duplicate medication orders found."
        ),
    }


def _report_coding_accuracy(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    # Encounters without any diagnosis
    no_dx = conn.execute(
        "SELECT COUNT(*) FROM encounters e "
        "LEFT JOIN diagnoses d ON e.encounter_id = d.encounter_id "
        "WHERE e.admission_date BETWEEN ? AND ? AND e.status = 'closed' "
        "AND d.diagnosis_id IS NULL",
        (start, end)
    ).fetchone()[0]

    # Inpatient encounters without DRG
    no_drg = conn.execute(
        "SELECT COUNT(*) FROM encounters "
        "WHERE encounter_type = 'inpatient' AND drg_code IS NULL "
        "AND status = 'closed' AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    # Encounters without primary diagnosis
    no_primary = conn.execute(
        "SELECT COUNT(DISTINCT e.encounter_id) FROM encounters e "
        "JOIN diagnoses d ON e.encounter_id = d.encounter_id "
        "WHERE e.admission_date BETWEEN ? AND ? AND e.status = 'closed' "
        "AND e.encounter_id NOT IN ("
        "  SELECT encounter_id FROM diagnoses WHERE diagnosis_type = 'primary'"
        ")",
        (start, end)
    ).fetchone()[0]

    total_closed = conn.execute(
        "SELECT COUNT(*) FROM encounters WHERE status = 'closed' "
        "AND admission_date BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    # DRG distribution
    drg_distribution = _rows_to_dicts(conn.execute(
        "SELECT drg_code, COUNT(*) as count FROM encounters "
        "WHERE encounter_type = 'inpatient' AND drg_code IS NOT NULL "
        "AND admission_date BETWEEN ? AND ? "
        "GROUP BY drg_code ORDER BY count DESC LIMIT 15",
        (start, end)
    ).fetchall())

    # Diagnosis code frequency
    dx_freq = _rows_to_dicts(conn.execute(
        "SELECT dx.icd10_code, dx.description, COUNT(*) as count "
        "FROM diagnoses dx "
        "JOIN encounters e ON dx.encounter_id = e.encounter_id "
        "WHERE e.admission_date BETWEEN ? AND ? "
        "GROUP BY dx.icd10_code ORDER BY count DESC LIMIT 15",
        (start, end)
    ).fetchall())

    return {
        "sections": [
            {
                "title": "Coding Completeness",
                "data": {
                    "total_closed_encounters": total_closed,
                    "encounters_without_diagnosis": no_dx,
                    "encounters_without_primary_dx": no_primary,
                    "inpatient_without_drg": no_drg,
                    "missing_dx_rate_pct": _safe_div(no_dx, total_closed, 1) * 100,
                    "missing_primary_dx_rate_pct": _safe_div(no_primary, total_closed, 1) * 100,
                },
            },
            {"title": "DRG Distribution", "data": drg_distribution},
            {"title": "Top Diagnosis Codes", "data": dx_freq},
        ],
        "summary": (
            f"Coding accuracy for {start} to {end}: {total_closed} closed encounters. "
            f"{no_dx} without any diagnosis ({_safe_div(no_dx, total_closed, 1)*100:.1f}%), "
            f"{no_primary} missing primary dx, "
            f"{no_drg} inpatient encounters without DRG."
        ),
    }


def _report_hl7_interface_status(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    total = conn.execute(
        "SELECT COUNT(*) FROM hl7_messages WHERE message_datetime BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    by_status = _rows_to_dicts(conn.execute(
        "SELECT status, COUNT(*) as count FROM hl7_messages "
        "WHERE message_datetime BETWEEN ? AND ? GROUP BY status ORDER BY count DESC",
        (start, end)
    ).fetchall())

    by_sender = _rows_to_dicts(conn.execute(
        "SELECT sending_system, COUNT(*) as total, "
        "SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors "
        "FROM hl7_messages WHERE message_datetime BETWEEN ? AND ? "
        "GROUP BY sending_system ORDER BY errors DESC",
        (start, end)
    ).fetchall())

    by_type = _rows_to_dicts(conn.execute(
        "SELECT message_type, trigger_event, COUNT(*) as count "
        "FROM hl7_messages WHERE message_datetime BETWEEN ? AND ? "
        "GROUP BY message_type, trigger_event ORDER BY count DESC",
        (start, end)
    ).fetchall())

    interface_alerts = _rows_to_dicts(conn.execute(
        "SELECT severity, message, created_at "
        "FROM system_alerts WHERE alert_type = 'interface_error' "
        "AND created_at BETWEEN ? AND ? ORDER BY created_at DESC LIMIT 10",
        (start, end)
    ).fetchall())

    error_count = sum(r["count"] for r in by_status if r["status"] == "error")
    error_rate = _safe_div(error_count, total, 2) * 100

    return {
        "sections": [
            {
                "title": "Interface Overview",
                "data": {
                    "total_messages": total,
                    "error_count": error_count,
                    "error_rate_pct": error_rate,
                },
            },
            {"title": "Status Distribution", "data": by_status},
            {"title": "Volume by Sending System", "data": by_sender},
            {"title": "Message Type Distribution", "data": by_type},
            {"title": "Recent Interface Alerts", "data": interface_alerts},
        ],
        "summary": (
            f"HL7 interface status for {start} to {end}: {total} messages, "
            f"{error_count} errors ({error_rate:.1f}% error rate)."
        ),
    }


def _report_hipaa_compliance(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    total_accesses = conn.execute(
        "SELECT COUNT(*) FROM audit_log WHERE timestamp BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    access_by_action = _rows_to_dicts(conn.execute(
        "SELECT action, COUNT(*) as count FROM audit_log "
        "WHERE timestamp BETWEEN ? AND ? "
        "GROUP BY action ORDER BY count DESC",
        (start, end)
    ).fetchall())

    access_by_resource = _rows_to_dicts(conn.execute(
        "SELECT resource_type, COUNT(*) as count FROM audit_log "
        "WHERE timestamp BETWEEN ? AND ? "
        "GROUP BY resource_type ORDER BY count DESC",
        (start, end)
    ).fetchall())

    # After-hours access (before 6 AM or after 10 PM)
    after_hours = conn.execute(
        "SELECT COUNT(*) FROM audit_log "
        "WHERE timestamp BETWEEN ? AND ? "
        "AND (CAST(STRFTIME('%H', timestamp) AS INTEGER) < 6 "
        "  OR CAST(STRFTIME('%H', timestamp) AS INTEGER) >= 22)",
        (start, end)
    ).fetchone()[0]

    # High-volume users
    high_volume = _rows_to_dicts(conn.execute(
        "SELECT u.username, u.full_name, u.role, COUNT(*) as accesses "
        "FROM audit_log a JOIN users u ON a.user_id = u.user_id "
        "WHERE a.timestamp BETWEEN ? AND ? "
        "GROUP BY u.user_id ORDER BY accesses DESC LIMIT 10",
        (start, end)
    ).fetchall())

    # Export/print activity (potential PHI leakage)
    sensitive_actions = _rows_to_dicts(conn.execute(
        "SELECT u.username, u.role, a.action, COUNT(*) as count "
        "FROM audit_log a JOIN users u ON a.user_id = u.user_id "
        "WHERE a.action IN ('export', 'print') "
        "AND a.timestamp BETWEEN ? AND ? "
        "GROUP BY u.user_id, a.action ORDER BY count DESC LIMIT 15",
        (start, end)
    ).fetchall())

    security_alerts = conn.execute(
        "SELECT COUNT(*) FROM system_alerts WHERE alert_type = 'security' "
        "AND created_at BETWEEN ? AND ?",
        (start, end)
    ).fetchone()[0]

    return {
        "sections": [
            {
                "title": "Access Summary",
                "data": {
                    "total_access_events": total_accesses,
                    "after_hours_accesses": after_hours,
                    "after_hours_pct": _safe_div(after_hours, total_accesses, 1) * 100,
                    "security_alerts": security_alerts,
                },
            },
            {"title": "Access by Action Type", "data": access_by_action},
            {"title": "Access by Resource Type", "data": access_by_resource},
            {"title": "High-Volume Users", "data": high_volume},
            {"title": "Export/Print Activity", "data": sensitive_actions},
        ],
        "summary": (
            f"HIPAA compliance summary for {start} to {end}: "
            f"{total_accesses} access events, {after_hours} after-hours "
            f"({_safe_div(after_hours, total_accesses, 1)*100:.1f}%), "
            f"{security_alerts} security alerts."
        ),
    }


def _report_bed_management(conn, params):
    start, end = params.get("start_date"), params.get("end_date")

    # Census by department for inpatient
    census = _rows_to_dicts(conn.execute(
        "SELECT d.dept_name, COUNT(*) as total_encounters, "
        "SUM(CASE WHEN e.status = 'open' THEN 1 ELSE 0 END) as currently_open, "
        "ROUND(AVG(e.los_days), 1) as avg_los "
        "FROM encounters e "
        "JOIN departments d ON e.department_id = d.dept_id "
        "WHERE e.encounter_type = 'inpatient' AND e.admission_date BETWEEN ? AND ? "
        "GROUP BY d.dept_name ORDER BY total_encounters DESC",
        (start, end)
    ).fetchall())

    discharge_patterns = _rows_to_dicts(conn.execute(
        "SELECT disposition, COUNT(*) as count FROM encounters "
        "WHERE encounter_type = 'inpatient' AND admission_date BETWEEN ? AND ? "
        "AND disposition IS NOT NULL "
        "GROUP BY disposition ORDER BY count DESC",
        (start, end)
    ).fetchall())

    los_distribution = _rows_to_dicts(conn.execute(
        "SELECT CASE "
        "  WHEN los_days <= 1 THEN '0-1 days' "
        "  WHEN los_days <= 3 THEN '1-3 days' "
        "  WHEN los_days <= 5 THEN '3-5 days' "
        "  WHEN los_days <= 7 THEN '5-7 days' "
        "  WHEN los_days <= 14 THEN '7-14 days' "
        "  ELSE '14+ days' END as los_bucket, "
        "COUNT(*) as count "
        "FROM encounters "
        "WHERE encounter_type = 'inpatient' AND admission_date BETWEEN ? AND ? "
        "GROUP BY los_bucket ORDER BY MIN(los_days)",
        (start, end)
    ).fetchall())

    daily_census = _rows_to_dicts(conn.execute(
        "SELECT DATE(admission_date) as date, "
        "COUNT(*) as admissions "
        "FROM encounters WHERE encounter_type = 'inpatient' "
        "AND admission_date BETWEEN ? AND ? "
        "GROUP BY DATE(admission_date) ORDER BY date",
        (start, end)
    ).fetchall())

    return {
        "sections": [
            {"title": "Census by Department", "data": census},
            {"title": "Discharge Disposition", "data": discharge_patterns},
            {"title": "Length of Stay Distribution", "data": los_distribution},
            {"title": "Daily Admission Volume", "data": daily_census},
        ],
        "summary": (
            f"Bed management report for {start} to {end}: "
            f"{sum(c['total_encounters'] for c in census)} inpatient encounters across "
            f"{len(census)} departments."
        ),
    }


# ---------------------------------------------------------------------------
# Report dispatcher
# ---------------------------------------------------------------------------

_REPORT_GENERATORS = {
    "monthly_executive_summary": _report_monthly_executive_summary,
    "department_utilization": _report_department_utilization,
    "quality_measures_dashboard": _report_quality_measures,
    "readmission_analysis": _report_readmission_analysis,
    "ed_throughput": _report_ed_throughput,
    "infection_control": _report_infection_control,
    "claim_denial": _report_claim_denial,
    "provider_productivity": _report_provider_productivity,
    "lab_turnaround": _report_lab_turnaround,
    "patient_safety": _report_patient_safety,
    "medication_reconciliation": _report_medication_reconciliation,
    "coding_accuracy": _report_coding_accuracy,
    "hl7_interface_status": _report_hl7_interface_status,
    "hipaa_compliance": _report_hipaa_compliance,
    "bed_management": _report_bed_management,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_report_templates():
    """Return the list of available report templates.

    Returns
    -------
    list of dict
        Each dict has keys: name, title, description, parameters.
    """
    return REPORT_TEMPLATES


def generate_report(db_path, template_name, params=None):
    """Generate a report from a named template.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    template_name : str
        One of the template names from ``get_report_templates()``.
    params : dict, optional
        Template-specific parameters (e.g. start_date, end_date,
        department_id). Defaults are applied for dates if omitted.

    Returns
    -------
    dict
        Keys: title, template_name, generated_at, parameters, sections
        (list of section dicts), summary.
    """
    if not template_name:
        return {"error": "template_name is required"}

    template_name = template_name.strip().lower()
    generator = _REPORT_GENERATORS.get(template_name)
    if not generator:
        return {
            "error": f"Unknown template '{template_name}'",
            "available_templates": [t["name"] for t in REPORT_TEMPLATES],
        }

    # Apply defaults
    if params is None:
        params = {}
    if "start_date" not in params or "end_date" not in params:
        default_start, default_end = _default_date_range()
        params.setdefault("start_date", default_start)
        params.setdefault("end_date", default_end)

    # Find template metadata
    tmpl_meta = next((t for t in REPORT_TEMPLATES if t["name"] == template_name), {})

    conn = _db(db_path)
    try:
        result = generator(conn, params)
        return {
            "title": tmpl_meta.get("title", template_name),
            "template_name": template_name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "parameters": params,
            "sections": result.get("sections", []),
            "summary": result.get("summary", ""),
        }
    except Exception as exc:
        return {
            "error": f"Report generation failed: {str(exc)}",
            "template_name": template_name,
            "parameters": params,
        }
    finally:
        conn.close()


def format_report_text(report_data):
    """Format a report dict into a human-readable text string.

    Parameters
    ----------
    report_data : dict
        The output of ``generate_report()``.

    Returns
    -------
    str
        A formatted plain-text report.
    """
    if not report_data or "error" in report_data:
        return report_data.get("error", "No report data provided")

    lines = []
    title = report_data.get("title", "Report")
    lines.append("=" * 70)
    lines.append(f"  {title.upper()}")
    lines.append("=" * 70)
    lines.append(f"Generated: {report_data.get('generated_at', 'N/A')}")

    params = report_data.get("parameters", {})
    if params:
        param_str = ", ".join(f"{k}: {v}" for k, v in params.items() if v)
        lines.append(f"Parameters: {param_str}")

    lines.append("")

    # Summary
    summary = report_data.get("summary", "")
    if summary:
        lines.append("SUMMARY")
        lines.append("-" * 70)
        # Wrap long summary lines
        words = summary.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 > 68:
                lines.append(f"  {current_line}")
                current_line = word
            else:
                current_line = f"{current_line} {word}".strip()
        if current_line:
            lines.append(f"  {current_line}")
        lines.append("")

    # Sections
    for section in report_data.get("sections", []):
        section_title = section.get("title", "Section")
        lines.append(f"{section_title}")
        lines.append("-" * 70)

        data = section.get("data")
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, list):
                    lines.append(f"  {key}:")
                    for item in val[:10]:
                        if isinstance(item, dict):
                            item_str = ", ".join(f"{k}: {v}" for k, v in item.items())
                            lines.append(f"    - {item_str}")
                        else:
                            lines.append(f"    - {item}")
                    if len(val) > 10:
                        lines.append(f"    ... and {len(val) - 10} more")
                elif isinstance(val, float):
                    lines.append(f"  {key}: {val:,.2f}")
                elif isinstance(val, int):
                    lines.append(f"  {key}: {val:,}")
                else:
                    lines.append(f"  {key}: {val}")
        elif isinstance(data, list):
            for item in data[:20]:
                if isinstance(item, dict):
                    item_str = ", ".join(f"{k}: {v}" for k, v in item.items())
                    lines.append(f"  - {item_str}")
                else:
                    lines.append(f"  - {item}")
            if len(data) > 20:
                lines.append(f"  ... and {len(data) - 20} more rows")
        else:
            lines.append(f"  {data}")

        lines.append("")

    lines.append("=" * 70)
    lines.append("  END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)

"""
tools_hl7.py - HL7 v2.x Message Analyzer for the Health Informatics
Learning Platform.

Provides parsing, validation, generation, and analysis of HL7 v2.5.1
messages. Sample messages are generated from real patient/encounter data
stored in the platform's SQLite database.

Public API
----------
    parse_hl7_message(raw_message)
    validate_hl7_message(raw_message)
    generate_sample_messages(db_path, count=10)
    analyze_interface_errors(db_path)
    compare_messages(msg1, msg2)
    get_hl7_field_reference()
"""

import sqlite3
import random
import re
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SEGMENT_TERMINATORS = ("\r", "\n", "\r\n")

# Standard HL7 v2.5.1 field separators
_FIELD_SEP = "|"
_COMP_SEP = "^"
_REP_SEP = "~"
_ESC_CHAR = "\\"
_SUB_SEP = "&"
_ENCODING_CHARS = "^~\\&"


def _db(db_path):
    """Return an sqlite3.Connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _hl7_timestamp(dt_str=None, dt_obj=None):
    """Convert a datetime string or object to HL7 timestamp (YYYYMMDDHHmmss)."""
    if dt_obj is not None:
        return dt_obj.strftime("%Y%m%d%H%M%S")
    if dt_str:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(dt_str, fmt).strftime("%Y%m%d%H%M%S")
            except ValueError:
                continue
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _split_segments(raw_message):
    """Split a raw HL7 message into individual segment strings."""
    # Normalize line endings to \r then split
    text = raw_message.replace("\r\n", "\r").replace("\n", "\r")
    segments = [s.strip() for s in text.split("\r") if s.strip()]
    return segments


def _parse_segment(segment_text):
    """Parse a single HL7 segment string into a dict."""
    fields = segment_text.split(_FIELD_SEP)
    seg_name = fields[0] if fields else ""
    parsed_fields = {}
    for idx, field_val in enumerate(fields):
        # For MSH, field 1 is the field separator itself
        if seg_name == "MSH" and idx == 1:
            parsed_fields[f"{seg_name}.1"] = _FIELD_SEP
            continue
        parsed_fields[f"{seg_name}.{idx}"] = field_val
        # Parse components
        if _COMP_SEP in field_val:
            components = field_val.split(_COMP_SEP)
            for cidx, comp in enumerate(components, start=1):
                parsed_fields[f"{seg_name}.{idx}.{cidx}"] = comp
    return {
        "segment_name": seg_name,
        "raw": segment_text,
        "fields": parsed_fields,
    }


def _extract_patient_info(parsed_segments):
    """Extract patient demographics from parsed PID segment."""
    pid_seg = None
    for seg in parsed_segments:
        if seg["segment_name"] == "PID":
            pid_seg = seg
            break
    if not pid_seg:
        return {}

    fields = pid_seg["fields"]
    # PID.3 = Patient Identifier List
    patient_id = fields.get("PID.3", "")
    # PID.5 = Patient Name (Family^Given^Middle^Suffix^Prefix)
    full_name = fields.get("PID.5", "")
    last_name = fields.get("PID.5.1", "")
    first_name = fields.get("PID.5.2", "")
    # PID.7 = Date of Birth
    dob = fields.get("PID.7", "")
    # PID.8 = Administrative Sex
    gender = fields.get("PID.8", "")
    # PID.10 = Race
    race = fields.get("PID.10", "")
    # PID.11 = Patient Address
    address = fields.get("PID.11", "")
    # PID.13 = Phone Number - Home
    phone = fields.get("PID.13", "")
    # PID.19 = SSN (or insurance ID)
    ssn = fields.get("PID.19", "")

    return {
        "patient_id": patient_id,
        "full_name": full_name,
        "last_name": last_name,
        "first_name": first_name,
        "date_of_birth": dob,
        "gender": gender,
        "race": race,
        "address": address,
        "phone": phone,
        "ssn_or_id": ssn,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_hl7_message(raw_message):
    """Parse an HL7 v2.x message into a structured dict.

    Parameters
    ----------
    raw_message : str
        The raw HL7 message text, segments separated by \\r or \\n.

    Returns
    -------
    dict
        Keys: message_type, trigger_event, sending_application,
        receiving_application, message_datetime, message_control_id,
        version, segments (list of parsed segment dicts), patient_info,
        segment_count, segment_names.
    """
    if not raw_message or not raw_message.strip():
        return {"error": "Empty message provided"}

    segments_raw = _split_segments(raw_message)
    if not segments_raw:
        return {"error": "No valid segments found in message"}

    parsed_segments = [_parse_segment(s) for s in segments_raw]

    # Extract MSH fields
    msh = parsed_segments[0] if parsed_segments[0]["segment_name"] == "MSH" else None
    if not msh:
        return {
            "error": "Message does not begin with MSH segment",
            "segments": parsed_segments,
        }

    msh_fields = msh["fields"]
    msg_type_field = msh_fields.get("MSH.9", "")
    msg_type = msh_fields.get("MSH.9.1", msg_type_field.split(_COMP_SEP)[0] if _COMP_SEP in msg_type_field else msg_type_field)
    trigger_event = msh_fields.get("MSH.9.2", "")

    return {
        "message_type": msg_type,
        "trigger_event": trigger_event,
        "sending_application": msh_fields.get("MSH.3", ""),
        "sending_facility": msh_fields.get("MSH.4", ""),
        "receiving_application": msh_fields.get("MSH.5", ""),
        "receiving_facility": msh_fields.get("MSH.6", ""),
        "message_datetime": msh_fields.get("MSH.7", ""),
        "message_control_id": msh_fields.get("MSH.10", ""),
        "processing_id": msh_fields.get("MSH.11", ""),
        "version": msh_fields.get("MSH.12", ""),
        "segments": parsed_segments,
        "patient_info": _extract_patient_info(parsed_segments),
        "segment_count": len(parsed_segments),
        "segment_names": [s["segment_name"] for s in parsed_segments],
    }


def validate_hl7_message(raw_message):
    """Validate an HL7 v2.x message and return a list of issues.

    Parameters
    ----------
    raw_message : str
        The raw HL7 message text.

    Returns
    -------
    list of dict
        Each dict has keys: severity ('error' or 'warning'), segment,
        field, message.
    """
    issues = []

    if not raw_message or not raw_message.strip():
        return [{"severity": "error", "segment": "MSH", "field": "N/A",
                 "message": "Empty message"}]

    segments_raw = _split_segments(raw_message)
    if not segments_raw:
        return [{"severity": "error", "segment": "MSH", "field": "N/A",
                 "message": "No segments found"}]

    # Validate MSH segment exists and is first
    first_seg = segments_raw[0]
    if not first_seg.startswith("MSH"):
        issues.append({
            "severity": "error", "segment": "MSH", "field": "MSH.0",
            "message": "Message must begin with MSH segment"
        })
        return issues

    # Parse MSH
    msh_fields = first_seg.split(_FIELD_SEP)

    # MSH.1 - Field Separator
    if len(msh_fields) < 2 or msh_fields[0] != "MSH":
        issues.append({
            "severity": "error", "segment": "MSH", "field": "MSH.1",
            "message": "Invalid MSH segment header"
        })

    # MSH.2 - Encoding Characters
    if len(msh_fields) >= 2:
        enc_chars = msh_fields[1]
        if enc_chars != _ENCODING_CHARS:
            issues.append({
                "severity": "warning", "segment": "MSH", "field": "MSH.2",
                "message": f"Non-standard encoding characters: '{enc_chars}' (expected '{_ENCODING_CHARS}')"
            })

    # MSH.3 - Sending Application
    if len(msh_fields) < 4 or not msh_fields[2]:
        issues.append({
            "severity": "warning", "segment": "MSH", "field": "MSH.3",
            "message": "Sending application is empty"
        })

    # MSH.5 - Receiving Application
    if len(msh_fields) < 6 or not msh_fields[4]:
        issues.append({
            "severity": "warning", "segment": "MSH", "field": "MSH.5",
            "message": "Receiving application is empty"
        })

    # MSH.7 - Message Date/Time
    if len(msh_fields) >= 8 and msh_fields[6]:
        ts = msh_fields[6]
        if not re.match(r"^\d{8,14}$", ts):
            issues.append({
                "severity": "error", "segment": "MSH", "field": "MSH.7",
                "message": f"Invalid timestamp format: '{ts}' (expected YYYYMMDDHHmmss)"
            })
    else:
        issues.append({
            "severity": "error", "segment": "MSH", "field": "MSH.7",
            "message": "Message timestamp is missing"
        })

    # MSH.9 - Message Type
    if len(msh_fields) >= 10:
        msg_type = msh_fields[8]
        if not msg_type:
            issues.append({
                "severity": "error", "segment": "MSH", "field": "MSH.9",
                "message": "Message type is missing"
            })
        elif _COMP_SEP not in msg_type:
            issues.append({
                "severity": "warning", "segment": "MSH", "field": "MSH.9",
                "message": f"Message type '{msg_type}' should include trigger event (e.g., ADT^A01)"
            })
    else:
        issues.append({
            "severity": "error", "segment": "MSH", "field": "MSH.9",
            "message": "Message type field is missing"
        })

    # MSH.10 - Message Control ID
    if len(msh_fields) >= 11:
        ctrl_id = msh_fields[9]
        if not ctrl_id:
            issues.append({
                "severity": "error", "segment": "MSH", "field": "MSH.10",
                "message": "Message control ID is empty"
            })
    else:
        issues.append({
            "severity": "error", "segment": "MSH", "field": "MSH.10",
            "message": "Message control ID is missing"
        })

    # MSH.12 - Version ID
    if len(msh_fields) >= 13:
        version = msh_fields[11]
        valid_versions = ["2.1", "2.2", "2.3", "2.3.1", "2.4", "2.5", "2.5.1", "2.6", "2.7", "2.8"]
        if version and version not in valid_versions:
            issues.append({
                "severity": "warning", "segment": "MSH", "field": "MSH.12",
                "message": f"Unrecognized HL7 version: '{version}'"
            })
    else:
        issues.append({
            "severity": "warning", "segment": "MSH", "field": "MSH.12",
            "message": "Version ID is missing"
        })

    # Check for PID segment presence for clinical messages
    segment_names = []
    for seg_text in segments_raw:
        seg_id = seg_text.split(_FIELD_SEP)[0] if _FIELD_SEP in seg_text else seg_text[:3]
        segment_names.append(seg_id)

    if len(msh_fields) >= 10:
        msg_type_str = msh_fields[8] if len(msh_fields) > 8 else ""
        clinical_types = ["ADT", "ORM", "ORU", "DFT", "SIU", "MDM"]
        type_prefix = msg_type_str.split(_COMP_SEP)[0] if msg_type_str else ""
        if type_prefix in clinical_types and "PID" not in segment_names:
            issues.append({
                "severity": "error", "segment": "PID", "field": "N/A",
                "message": f"PID segment is required for {type_prefix} messages but is missing"
            })

    # Validate PID segment if present
    for seg_text in segments_raw:
        if seg_text.startswith("PID"):
            pid_fields = seg_text.split(_FIELD_SEP)
            # PID.3 - Patient Identifier List
            if len(pid_fields) < 4 or not pid_fields[3]:
                issues.append({
                    "severity": "error", "segment": "PID", "field": "PID.3",
                    "message": "Patient identifier list is empty"
                })
            # PID.5 - Patient Name
            if len(pid_fields) < 6 or not pid_fields[5]:
                issues.append({
                    "severity": "error", "segment": "PID", "field": "PID.5",
                    "message": "Patient name is empty"
                })
            # PID.7 - Date of Birth
            if len(pid_fields) < 8 or not pid_fields[7]:
                issues.append({
                    "severity": "warning", "segment": "PID", "field": "PID.7",
                    "message": "Date of birth is empty"
                })
            # PID.8 - Administrative Sex
            if len(pid_fields) >= 9 and pid_fields[8]:
                valid_genders = ["M", "F", "O", "U", "A", "N"]
                if pid_fields[8] not in valid_genders:
                    issues.append({
                        "severity": "warning", "segment": "PID", "field": "PID.8",
                        "message": f"Invalid administrative sex value: '{pid_fields[8]}'"
                    })
            break

    # Validate OBX segments if present
    for seg_text in segments_raw:
        if seg_text.startswith("OBX"):
            obx_fields = seg_text.split(_FIELD_SEP)
            # OBX.2 - Value Type
            if len(obx_fields) >= 3:
                valid_types = ["NM", "ST", "TX", "CE", "CWE", "SN", "DT", "TM", "TS", "FT", "ED"]
                vtype = obx_fields[2]
                if vtype and vtype not in valid_types:
                    issues.append({
                        "severity": "warning", "segment": "OBX", "field": "OBX.2",
                        "message": f"Unusual value type: '{vtype}'"
                    })
            # OBX.3 - Observation Identifier
            if len(obx_fields) < 4 or not obx_fields[3]:
                issues.append({
                    "severity": "error", "segment": "OBX", "field": "OBX.3",
                    "message": "Observation identifier is empty in OBX segment"
                })
            # OBX.11 - Observation Result Status
            if len(obx_fields) >= 12:
                valid_statuses = ["F", "P", "C", "R", "I", "S", "X", "U", "W"]
                obs_status = obx_fields[11]
                if obs_status and obs_status not in valid_statuses:
                    issues.append({
                        "severity": "warning", "segment": "OBX", "field": "OBX.11",
                        "message": f"Invalid observation result status: '{obs_status}'"
                    })

    if not issues:
        issues.append({
            "severity": "info", "segment": "N/A", "field": "N/A",
            "message": "Message passed all validation checks"
        })

    return issues


def generate_sample_messages(db_path, count=10):
    """Generate realistic HL7 v2.5.1 messages using actual database data.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    count : int
        Number of sample messages to generate (default 10).

    Returns
    -------
    list of dict
        Each dict has keys: message_type, trigger_event, raw_message,
        patient_mrn, encounter_id, description.
    """
    conn = _db(db_path)
    try:
        # Fetch patients with encounters, diagnoses, labs, etc.
        patients = conn.execute(
            "SELECT p.mrn, p.first_name, p.last_name, p.dob, p.gender, "
            "p.race, p.address, p.city, p.state, p.zip, p.phone, "
            "p.insurance_plan, p.insurance_id "
            "FROM patients p ORDER BY RANDOM() LIMIT ?", (count * 2,)
        ).fetchall()

        if not patients:
            return [{"error": "No patients found in database"}]

        encounters = conn.execute(
            "SELECT e.encounter_id, e.patient_mrn, e.encounter_type, "
            "e.admission_date, e.discharge_date, e.attending_provider_id, "
            "e.department_id, e.chief_complaint, e.disposition, e.drg_code, "
            "e.los_days, e.status "
            "FROM encounters e ORDER BY RANDOM() LIMIT ?", (count * 2,)
        ).fetchall()

        providers = conn.execute(
            "SELECT provider_id, npi, first_name, last_name, credential, "
            "specialty, department_id FROM providers WHERE active = 1 "
            "ORDER BY RANDOM() LIMIT 20"
        ).fetchall()

        departments = conn.execute(
            "SELECT dept_id, dept_name, dept_code FROM departments"
        ).fetchall()
        dept_map = {d["dept_id"]: d for d in departments}

        messages = []
        message_templates = [
            ("ADT", "A01", "Admit/Visit Notification"),
            ("ADT", "A03", "Discharge/End Visit"),
            ("ADT", "A08", "Update Patient Information"),
            ("ORU", "R01", "Unsolicited Observation Result"),
            ("ORM", "O01", "General Order Message"),
            ("ADT", "A04", "Register a Patient"),
            ("DFT", "P03", "Post Detail Financial Transaction"),
            ("SIU", "S12", "Schedule Information Unsolicited"),
        ]

        sending_systems = [
            "LabCorp_Interface", "Quest_Interface", "RadPACS_v4",
            "PharmacyRx_Pro", "BedMgmt_2000", "Registration_Portal",
            "ED_Tracker", "OR_Scheduling_v3",
        ]
        receiving_systems = [
            "MainEHR_Prod", "DataWarehouse", "ClinicalReporting",
            "HIE_Gateway",
        ]

        for i in range(min(count, len(patients))):
            pat = dict(patients[i % len(patients)])
            enc = dict(encounters[i % len(encounters)]) if encounters else None
            prov = dict(providers[i % len(providers)]) if providers else None

            template = message_templates[i % len(message_templates)]
            msg_type, trigger, description = template

            ctrl_id = f"MSG{100000 + i:06d}"
            now_ts = _hl7_timestamp(dt_obj=datetime.now())
            sender = random.choice(sending_systems)
            receiver = random.choice(receiving_systems)

            # Gender code
            gender_code = "U"
            if pat["gender"]:
                g = pat["gender"].lower()
                if g.startswith("m"):
                    gender_code = "M"
                elif g.startswith("f"):
                    gender_code = "F"
                elif g.startswith("n"):
                    gender_code = "O"

            dob_ts = _hl7_timestamp(pat["dob"]) if pat["dob"] else ""

            # Build address components
            addr_street = (pat["address"] or "").replace("^", " ")
            addr_city = pat["city"] or ""
            addr_state = pat["state"] or ""
            addr_zip = pat["zip"] or ""

            # Provider info
            prov_id_str = ""
            prov_name = ""
            prov_npi = ""
            if prov:
                prov_id_str = str(prov["provider_id"])
                prov_name = f"{prov['last_name']}^{prov['first_name']}^^^{prov['credential'] or ''}"
                prov_npi = prov["npi"] or ""

            # Encounter info
            enc_id_str = ""
            admit_ts = now_ts
            discharge_ts = ""
            dept_code = ""
            complaint = ""
            enc_type = ""
            if enc:
                enc_id_str = str(enc["encounter_id"])
                admit_ts = _hl7_timestamp(enc["admission_date"]) if enc["admission_date"] else now_ts
                discharge_ts = _hl7_timestamp(enc["discharge_date"]) if enc["discharge_date"] else ""
                dept_info = dept_map.get(enc["department_id"])
                dept_code = dept_info["dept_code"] if dept_info else ""
                complaint = enc["chief_complaint"] or ""
                enc_type = enc["encounter_type"] or ""

            # Patient class mapping
            patient_class = "I"  # Inpatient default
            if enc_type == "outpatient":
                patient_class = "O"
            elif enc_type == "ED":
                patient_class = "E"
            elif enc_type == "observation":
                patient_class = "B"

            # Build segments
            segments = []

            # MSH segment
            msh = (
                f"MSH|^~\\&|{sender}|MERIT_HEALTH|{receiver}|MERIT_HEALTH|"
                f"{now_ts}||{msg_type}^{trigger}^{msg_type}_{trigger}|{ctrl_id}|P|2.5.1|||AL|NE"
            )
            segments.append(msh)

            # EVN segment (Event Type)
            evn = f"EVN|{trigger}|{now_ts}|||{prov_id_str}^{prov_name}"
            segments.append(evn)

            # PID segment
            pid = (
                f"PID|1||{pat['mrn']}^^^MERIT_HEALTH^MR~{pat.get('insurance_id', '')}^^^{pat.get('insurance_plan', '')}^PI||"
                f"{pat['last_name']}^{pat['first_name']}^^^||"
                f"{dob_ts}|{gender_code}||{pat.get('race', '')}|"
                f"{addr_street}^^{addr_city}^{addr_state}^{addr_zip}^US||"
                f"{pat.get('phone', '')}|||||{pat.get('insurance_id', '')}|||||||||||N"
            )
            segments.append(pid)

            # PV1 segment (Patient Visit)
            pv1 = (
                f"PV1|1|{patient_class}|{dept_code}^^^MERIT_HEALTH||||"
                f"{prov_npi}^{prov_name}|{prov_npi}^{prov_name}||||||||||"
                f"{enc_id_str}|||||||||||||||||||||||||"
                f"{admit_ts}|{discharge_ts}"
            )
            segments.append(pv1)

            # Additional segments based on message type
            if msg_type == "ORU" and trigger == "R01":
                # Add OBR and OBX for lab results
                labs = conn.execute(
                    "SELECT test_name, test_code, result_value, result_unit, "
                    "reference_range_low, reference_range_high, abnormal_flag, "
                    "collected_datetime, resulted_datetime "
                    "FROM lab_results WHERE patient_mrn = ? "
                    "ORDER BY RANDOM() LIMIT 4", (pat["mrn"],)
                ).fetchall()

                if labs:
                    obr_ts = _hl7_timestamp(labs[0]["collected_datetime"]) if labs[0]["collected_datetime"] else now_ts
                    obr = (
                        f"OBR|1|{ctrl_id}^{sender}|{ctrl_id}^{receiver}|"
                        f"85025^Complete Blood Count^CPT|||{obr_ts}|||||||"
                        f"{obr_ts}|^^^Blood|{prov_npi}^{prov_name}||||||"
                        f"{_hl7_timestamp(labs[0]['resulted_datetime']) if labs[0]['resulted_datetime'] else now_ts}|||F"
                    )
                    segments.append(obr)

                    for j, lab in enumerate(labs, start=1):
                        ref_range = ""
                        if lab["reference_range_low"] is not None and lab["reference_range_high"] is not None:
                            ref_range = f"{lab['reference_range_low']}-{lab['reference_range_high']}"
                        flag = lab["abnormal_flag"] or "N"
                        obx = (
                            f"OBX|{j}|NM|{lab['test_code']}^{lab['test_name']}^LN||"
                            f"{lab['result_value']}|{lab['result_unit'] or ''}|"
                            f"{ref_range}|{flag}|||F|||"
                            f"{_hl7_timestamp(lab['resulted_datetime']) if lab['resulted_datetime'] else now_ts}"
                        )
                        segments.append(obx)

            elif msg_type == "ORM" and trigger == "O01":
                # Add ORC and OBR for order
                orc = (
                    f"ORC|NW|{ctrl_id}^{sender}||{ctrl_id}^{receiver}|SC|||"
                    f"{now_ts}||{prov_npi}^{prov_name}|||||"
                    f"MERIT_HEALTH^MERIT HEALTH SYSTEM^FI"
                )
                segments.append(orc)
                obr = (
                    f"OBR|1|{ctrl_id}^{sender}|{ctrl_id}^{receiver}|"
                    f"80053^Comprehensive Metabolic Panel^CPT|||{now_ts}|||||||"
                    f"{now_ts}|^^^Blood|{prov_npi}^{prov_name}"
                )
                segments.append(obr)

            elif msg_type == "ADT":
                # Add DG1 for diagnoses if available
                diagnoses = conn.execute(
                    "SELECT d.icd10_code, d.description, d.diagnosis_type "
                    "FROM diagnoses d "
                    "WHERE d.patient_mrn = ? ORDER BY RANDOM() LIMIT 3",
                    (pat["mrn"],)
                ).fetchall()
                for k, dx in enumerate(diagnoses, start=1):
                    dx_type_code = "A" if dx["diagnosis_type"] == "admitting" else \
                                   "W" if dx["diagnosis_type"] == "primary" else "F"
                    dg1 = (
                        f"DG1|{k}|I10|{dx['icd10_code']}^{dx['description']}^I10||"
                        f"{admit_ts}|{dx_type_code}"
                    )
                    segments.append(dg1)

                # Add IN1 for insurance
                if pat.get("insurance_plan"):
                    in1 = (
                        f"IN1|1|{pat.get('insurance_plan', '')}^^^{pat.get('insurance_plan', '')}|"
                        f"{pat.get('insurance_plan', '')}|{pat.get('insurance_plan', '')}||||||||"
                        f"||||||{pat['last_name']}^{pat['first_name']}|18|"
                        f"{dob_ts}|{addr_street}^^{addr_city}^{addr_state}^{addr_zip}^US||||||||||||||||"
                        f"{pat.get('insurance_id', '')}"
                    )
                    segments.append(in1)

            elif msg_type == "DFT" and trigger == "P03":
                # Add FT1 for financial transaction
                procs = conn.execute(
                    "SELECT p.cpt_code, p.description, p.procedure_date "
                    "FROM procedures p WHERE p.patient_mrn = ? "
                    "ORDER BY RANDOM() LIMIT 2", (pat["mrn"],)
                ).fetchall()
                for k, proc in enumerate(procs, start=1):
                    proc_ts = _hl7_timestamp(proc["procedure_date"]) if proc["procedure_date"] else now_ts
                    ft1 = (
                        f"FT1|{k}||{proc_ts}|{proc_ts}|CG|"
                        f"{proc['cpt_code']}^{proc['description']}^CPT||||||1||||||"
                        f"{prov_npi}^{prov_name}"
                    )
                    segments.append(ft1)

            raw_message = "\r".join(segments)
            messages.append({
                "message_type": msg_type,
                "trigger_event": trigger,
                "description": description,
                "raw_message": raw_message,
                "patient_mrn": pat["mrn"],
                "encounter_id": enc_id_str,
                "segment_count": len(segments),
                "segment_names": [s.split(_FIELD_SEP)[0] for s in segments],
            })

        return messages
    finally:
        conn.close()


def analyze_interface_errors(db_path):
    """Analyze HL7 interface errors from the database.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.

    Returns
    -------
    dict
        Keys: total_messages, error_count, error_rate, errors_by_type,
        errors_by_sending_system, errors_by_receiving_system,
        error_timeline, affected_patients, recent_errors,
        system_alerts_summary.
    """
    conn = _db(db_path)
    try:
        # Total messages and error counts
        total_messages = conn.execute(
            "SELECT COUNT(*) FROM hl7_messages"
        ).fetchone()[0]

        error_count = conn.execute(
            "SELECT COUNT(*) FROM hl7_messages WHERE status = 'error'"
        ).fetchone()[0]

        error_rate = round(error_count / max(total_messages, 1) * 100, 2)

        # Errors by message type
        errors_by_type_rows = conn.execute(
            "SELECT message_type, trigger_event, COUNT(*) as cnt "
            "FROM hl7_messages WHERE status = 'error' "
            "GROUP BY message_type, trigger_event ORDER BY cnt DESC"
        ).fetchall()
        errors_by_type = [
            {"message_type": r["message_type"], "trigger_event": r["trigger_event"],
             "count": r["cnt"]}
            for r in errors_by_type_rows
        ]

        # Errors by sending system
        errors_by_sender = conn.execute(
            "SELECT sending_system, COUNT(*) as cnt "
            "FROM hl7_messages WHERE status = 'error' "
            "GROUP BY sending_system ORDER BY cnt DESC"
        ).fetchall()
        errors_by_sending_system = [
            {"system": r["sending_system"], "count": r["cnt"]}
            for r in errors_by_sender
        ]

        # Errors by receiving system
        errors_by_receiver = conn.execute(
            "SELECT receiving_system, COUNT(*) as cnt "
            "FROM hl7_messages WHERE status = 'error' "
            "GROUP BY receiving_system ORDER BY cnt DESC"
        ).fetchall()
        errors_by_receiving_system = [
            {"system": r["receiving_system"], "count": r["cnt"]}
            for r in errors_by_receiver
        ]

        # Error timeline (by day)
        error_timeline_rows = conn.execute(
            "SELECT DATE(message_datetime) as day, COUNT(*) as cnt "
            "FROM hl7_messages WHERE status = 'error' "
            "GROUP BY DATE(message_datetime) ORDER BY day"
        ).fetchall()
        error_timeline = [
            {"date": r["day"], "count": r["cnt"]}
            for r in error_timeline_rows
        ]

        # Affected patients
        affected_rows = conn.execute(
            "SELECT DISTINCT h.patient_mrn, p.first_name, p.last_name "
            "FROM hl7_messages h "
            "LEFT JOIN patients p ON h.patient_mrn = p.mrn "
            "WHERE h.status = 'error' LIMIT 20"
        ).fetchall()
        affected_patients = [
            {"mrn": r["patient_mrn"],
             "name": f"{r['first_name'] or ''} {r['last_name'] or ''}".strip()}
            for r in affected_rows
        ]

        # Recent errors (last 10)
        recent_rows = conn.execute(
            "SELECT message_id, message_type, trigger_event, sending_system, "
            "receiving_system, patient_mrn, message_datetime, "
            "raw_message_preview "
            "FROM hl7_messages WHERE status = 'error' "
            "ORDER BY message_datetime DESC LIMIT 10"
        ).fetchall()
        recent_errors = [
            {
                "message_id": r["message_id"],
                "message_type": f"{r['message_type']}^{r['trigger_event']}",
                "sending_system": r["sending_system"],
                "receiving_system": r["receiving_system"],
                "patient_mrn": r["patient_mrn"],
                "datetime": r["message_datetime"],
                "preview": r["raw_message_preview"],
            }
            for r in recent_rows
        ]

        # System alerts related to interfaces
        alerts_rows = conn.execute(
            "SELECT severity, COUNT(*) as cnt "
            "FROM system_alerts WHERE alert_type = 'interface_error' "
            "GROUP BY severity"
        ).fetchall()
        alerts_summary = {r["severity"]: r["cnt"] for r in alerts_rows}

        # Message status distribution
        status_rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM hl7_messages "
            "GROUP BY status ORDER BY cnt DESC"
        ).fetchall()
        status_distribution = {r["status"]: r["cnt"] for r in status_rows}

        return {
            "total_messages": total_messages,
            "error_count": error_count,
            "error_rate_percent": error_rate,
            "status_distribution": status_distribution,
            "errors_by_type": errors_by_type,
            "errors_by_sending_system": errors_by_sending_system,
            "errors_by_receiving_system": errors_by_receiving_system,
            "error_timeline": error_timeline,
            "affected_patients": affected_patients,
            "recent_errors": recent_errors,
            "system_alerts_summary": alerts_summary,
        }
    finally:
        conn.close()


def compare_messages(msg1, msg2):
    """Compare two HL7 messages and return a structured diff.

    Parameters
    ----------
    msg1 : str
        First HL7 message (raw text).
    msg2 : str
        Second HL7 message (raw text).

    Returns
    -------
    dict
        Keys: segments_added, segments_removed, segments_modified,
        field_changes (list of per-field diffs), summary.
    """
    segs1 = _split_segments(msg1)
    segs2 = _split_segments(msg2)

    parsed1 = {s.split(_FIELD_SEP)[0]: s for s in segs1}
    parsed2 = {s.split(_FIELD_SEP)[0]: s for s in segs2}

    # Handle duplicate segment names by using (name, index) keys
    seg_list1 = []
    seg_count1 = {}
    for s in segs1:
        name = s.split(_FIELD_SEP)[0]
        idx = seg_count1.get(name, 0)
        seg_count1[name] = idx + 1
        seg_list1.append((name, idx, s))

    seg_list2 = []
    seg_count2 = {}
    for s in segs2:
        name = s.split(_FIELD_SEP)[0]
        idx = seg_count2.get(name, 0)
        seg_count2[name] = idx + 1
        seg_list2.append((name, idx, s))

    # Build lookup dicts
    lookup1 = {(name, idx): raw for name, idx, raw in seg_list1}
    lookup2 = {(name, idx): raw for name, idx, raw in seg_list2}

    keys1 = set(lookup1.keys())
    keys2 = set(lookup2.keys())

    segments_added = []
    for key in sorted(keys2 - keys1):
        segments_added.append({
            "segment": key[0],
            "instance": key[1],
            "content": lookup2[key],
        })

    segments_removed = []
    for key in sorted(keys1 - keys2):
        segments_removed.append({
            "segment": key[0],
            "instance": key[1],
            "content": lookup1[key],
        })

    # Compare matching segments field by field
    field_changes = []
    segments_modified = []
    common_keys = keys1 & keys2
    for key in sorted(common_keys):
        raw1 = lookup1[key]
        raw2 = lookup2[key]
        if raw1 == raw2:
            continue

        segments_modified.append(key[0])
        fields1 = raw1.split(_FIELD_SEP)
        fields2 = raw2.split(_FIELD_SEP)
        max_fields = max(len(fields1), len(fields2))

        for fi in range(max_fields):
            val1 = fields1[fi] if fi < len(fields1) else ""
            val2 = fields2[fi] if fi < len(fields2) else ""
            if val1 != val2:
                field_changes.append({
                    "segment": key[0],
                    "instance": key[1],
                    "field_index": fi,
                    "field_id": f"{key[0]}.{fi}",
                    "old_value": val1,
                    "new_value": val2,
                })

    total_changes = len(segments_added) + len(segments_removed) + len(field_changes)
    if total_changes == 0:
        summary = "Messages are identical"
    else:
        parts = []
        if segments_added:
            parts.append(f"{len(segments_added)} segment(s) added")
        if segments_removed:
            parts.append(f"{len(segments_removed)} segment(s) removed")
        if field_changes:
            parts.append(f"{len(field_changes)} field(s) modified across {len(segments_modified)} segment(s)")
        summary = "; ".join(parts)

    return {
        "segments_added": segments_added,
        "segments_removed": segments_removed,
        "segments_modified": list(set(segments_modified)),
        "field_changes": field_changes,
        "total_changes": total_changes,
        "summary": summary,
    }


def get_hl7_field_reference():
    """Return a reference dict mapping common HL7 v2.5.1 segments and fields
    to human-readable descriptions.

    Returns
    -------
    dict
        Top-level keys are segment names. Each maps to a dict with
        'description' and 'fields' (a dict of field positions to descriptions).
    """
    return {
        "MSH": {
            "description": "Message Header - contains metadata about the message itself",
            "fields": {
                "MSH.1": "Field Separator (|)",
                "MSH.2": "Encoding Characters (^~\\&)",
                "MSH.3": "Sending Application",
                "MSH.4": "Sending Facility",
                "MSH.5": "Receiving Application",
                "MSH.6": "Receiving Facility",
                "MSH.7": "Date/Time of Message (YYYYMMDDHHmmss)",
                "MSH.8": "Security",
                "MSH.9": "Message Type (e.g., ADT^A01)",
                "MSH.10": "Message Control ID",
                "MSH.11": "Processing ID (P=Production, T=Training, D=Debug)",
                "MSH.12": "Version ID (e.g., 2.5.1)",
                "MSH.15": "Accept Acknowledgment Type",
                "MSH.16": "Application Acknowledgment Type",
            },
        },
        "EVN": {
            "description": "Event Type - describes the trigger event",
            "fields": {
                "EVN.1": "Event Type Code",
                "EVN.2": "Recorded Date/Time",
                "EVN.3": "Date/Time Planned Event",
                "EVN.4": "Event Reason Code",
                "EVN.5": "Operator ID",
                "EVN.6": "Event Occurred",
            },
        },
        "PID": {
            "description": "Patient Identification - core patient demographics",
            "fields": {
                "PID.1": "Set ID",
                "PID.2": "Patient ID (External)",
                "PID.3": "Patient Identifier List (MRN, etc.)",
                "PID.4": "Alternate Patient ID",
                "PID.5": "Patient Name (Last^First^Middle^Suffix^Prefix)",
                "PID.6": "Mother's Maiden Name",
                "PID.7": "Date/Time of Birth",
                "PID.8": "Administrative Sex (M, F, O, U)",
                "PID.9": "Patient Alias",
                "PID.10": "Race",
                "PID.11": "Patient Address (Street^Other^City^State^Zip^Country)",
                "PID.12": "County Code",
                "PID.13": "Phone Number - Home",
                "PID.14": "Phone Number - Business",
                "PID.15": "Primary Language",
                "PID.16": "Marital Status",
                "PID.17": "Religion",
                "PID.18": "Patient Account Number",
                "PID.19": "SSN Number",
                "PID.22": "Ethnic Group",
                "PID.29": "Patient Death Date/Time",
                "PID.30": "Patient Death Indicator",
            },
        },
        "PV1": {
            "description": "Patient Visit - encounter/visit information",
            "fields": {
                "PV1.1": "Set ID",
                "PV1.2": "Patient Class (I=Inpatient, O=Outpatient, E=Emergency, B=Obstetrics)",
                "PV1.3": "Assigned Patient Location (Unit^Room^Bed^Facility)",
                "PV1.4": "Admission Type",
                "PV1.7": "Attending Doctor (ID^Last^First^MI^Suffix^Prefix^Credential)",
                "PV1.8": "Referring Doctor",
                "PV1.9": "Consulting Doctor",
                "PV1.10": "Hospital Service",
                "PV1.14": "Admit Source",
                "PV1.17": "Admitting Doctor",
                "PV1.18": "Patient Type",
                "PV1.19": "Visit Number",
                "PV1.36": "Discharge Disposition",
                "PV1.44": "Admit Date/Time",
                "PV1.45": "Discharge Date/Time",
            },
        },
        "PV2": {
            "description": "Patient Visit - Additional Information",
            "fields": {
                "PV2.3": "Admit Reason",
                "PV2.12": "Visit Description",
                "PV2.25": "Visit Priority Code",
            },
        },
        "OBR": {
            "description": "Observation Request - order for a test/procedure",
            "fields": {
                "OBR.1": "Set ID",
                "OBR.2": "Placer Order Number",
                "OBR.3": "Filler Order Number",
                "OBR.4": "Universal Service Identifier (Test Code^Description^Coding System)",
                "OBR.7": "Observation Date/Time",
                "OBR.14": "Specimen Received Date/Time",
                "OBR.15": "Specimen Source",
                "OBR.16": "Ordering Provider",
                "OBR.22": "Results Report/Status Change Date/Time",
                "OBR.25": "Result Status (F=Final, P=Preliminary, C=Corrected)",
            },
        },
        "OBX": {
            "description": "Observation/Result - individual test result values",
            "fields": {
                "OBX.1": "Set ID",
                "OBX.2": "Value Type (NM=Numeric, ST=String, TX=Text, CE=Coded Entry)",
                "OBX.3": "Observation Identifier (Code^Description^Coding System)",
                "OBX.4": "Observation Sub-ID",
                "OBX.5": "Observation Value",
                "OBX.6": "Units",
                "OBX.7": "Reference Range",
                "OBX.8": "Abnormal Flags (N=Normal, L=Low, H=High, C=Critical)",
                "OBX.11": "Observation Result Status (F=Final, P=Preliminary)",
                "OBX.14": "Date/Time of Observation",
            },
        },
        "ORC": {
            "description": "Common Order - order control information",
            "fields": {
                "ORC.1": "Order Control (NW=New, CA=Cancel, XO=Change, SC=Status Change)",
                "ORC.2": "Placer Order Number",
                "ORC.3": "Filler Order Number",
                "ORC.4": "Placer Group Number",
                "ORC.5": "Order Status",
                "ORC.9": "Date/Time of Transaction",
                "ORC.12": "Ordering Provider",
                "ORC.13": "Enterer's Location",
                "ORC.15": "Order Effective Date/Time",
                "ORC.21": "Ordering Facility Name",
            },
        },
        "DG1": {
            "description": "Diagnosis - patient diagnosis information",
            "fields": {
                "DG1.1": "Set ID",
                "DG1.2": "Diagnosis Coding Method (I10=ICD-10)",
                "DG1.3": "Diagnosis Code (Code^Description^Coding System)",
                "DG1.4": "Diagnosis Description",
                "DG1.5": "Diagnosis Date/Time",
                "DG1.6": "Diagnosis Type (A=Admitting, W=Working, F=Final)",
                "DG1.15": "Diagnosis Priority",
                "DG1.16": "Diagnosing Clinician",
            },
        },
        "IN1": {
            "description": "Insurance - patient insurance information",
            "fields": {
                "IN1.1": "Set ID",
                "IN1.2": "Insurance Plan ID",
                "IN1.3": "Insurance Company ID",
                "IN1.4": "Insurance Company Name",
                "IN1.8": "Group Number",
                "IN1.12": "Plan Effective Date",
                "IN1.13": "Plan Expiration Date",
                "IN1.16": "Name of Insured",
                "IN1.36": "Policy Number",
                "IN1.46": "Prior Insurance Plan ID",
            },
        },
        "AL1": {
            "description": "Patient Allergy Information",
            "fields": {
                "AL1.1": "Set ID",
                "AL1.2": "Allergen Type (DA=Drug Allergy, FA=Food Allergy, EA=Environmental)",
                "AL1.3": "Allergen Code/Description",
                "AL1.4": "Allergy Severity (SV=Severe, MO=Moderate, MI=Mild)",
                "AL1.5": "Allergy Reaction Code",
                "AL1.6": "Identification Date",
            },
        },
        "FT1": {
            "description": "Financial Transaction - charge/billing data",
            "fields": {
                "FT1.1": "Set ID",
                "FT1.2": "Transaction ID",
                "FT1.4": "Transaction Date",
                "FT1.6": "Transaction Type (CG=Charge, CD=Credit)",
                "FT1.7": "Transaction Code (CPT code^Description^Coding System)",
                "FT1.10": "Transaction Quantity",
                "FT1.16": "Assigned Patient Location",
                "FT1.20": "Procedure Code",
                "FT1.21": "Ordering Provider",
            },
        },
        "NK1": {
            "description": "Next of Kin / Associated Parties",
            "fields": {
                "NK1.1": "Set ID",
                "NK1.2": "Name",
                "NK1.3": "Relationship",
                "NK1.4": "Address",
                "NK1.5": "Phone Number",
                "NK1.7": "Contact Role",
            },
        },
        "SCH": {
            "description": "Scheduling Activity Information",
            "fields": {
                "SCH.1": "Placer Appointment ID",
                "SCH.2": "Filler Appointment ID",
                "SCH.6": "Event Reason",
                "SCH.7": "Appointment Reason",
                "SCH.11": "Appointment Timing Quantity",
                "SCH.12": "Placer Contact Person",
                "SCH.16": "Filler Contact Person",
                "SCH.25": "Filler Status Code",
            },
        },
        "RXA": {
            "description": "Pharmacy/Treatment Administration",
            "fields": {
                "RXA.1": "Give Sub-ID Counter",
                "RXA.2": "Administration Sub-ID Counter",
                "RXA.3": "Date/Time Start of Administration",
                "RXA.4": "Date/Time End of Administration",
                "RXA.5": "Administered Code (NDC^Drug Name^Coding System)",
                "RXA.6": "Administered Amount",
                "RXA.7": "Administered Units",
                "RXA.9": "Administration Notes",
                "RXA.10": "Administering Provider",
            },
        },
        "ZPD": {
            "description": "Custom Z-segment (facility-specific patient data)",
            "fields": {
                "ZPD.1": "Set ID",
                "ZPD.2": "Custom Field 1 (facility-defined)",
                "ZPD.3": "Custom Field 2 (facility-defined)",
            },
        },
    }

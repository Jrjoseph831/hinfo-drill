"""
tools_audit.py - Audit Workbench for the Health Informatics Learning
Platform.

Provides HIPAA audit analysis, anomaly detection, access pattern
evaluation, and compliance reporting against the platform's SQLite
database.

Public API
----------
    analyze_user_access(db_path, user_id=None)
    detect_anomalies(db_path)
    generate_access_timeline(db_path, resource_type, resource_id)
    build_audit_report(db_path, start_date, end_date)
    check_minimum_necessary(db_path, user_id)
    identify_break_the_glass(db_path)
    role_access_matrix(db_path)
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _db(db_path):
    """Return an sqlite3.Connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_to_dicts(rows):
    """Convert sqlite3.Row objects to a list of plain dicts."""
    return [dict(r) for r in rows]


def _safe_div(num, denom, digits=2):
    """Return rounded division or 0.0 when denominator is zero."""
    if not denom:
        return 0.0
    return round(num / denom, digits)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_user_access(db_path, user_id=None):
    """Analyze access patterns for a specific user or all users.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    user_id : int or str, optional
        Specific user ID to analyze. If None, returns aggregate analysis
        for all users.

    Returns
    -------
    dict
        Keys vary by whether user_id is provided.  Always includes
        access_summary, resource_breakdown, temporal_patterns, and
        risk_indicators.
    """
    conn = _db(db_path)
    try:
        if user_id is not None:
            user_id = int(user_id)
            # Fetch user info
            user = conn.execute(
                "SELECT u.*, d.dept_name FROM users u "
                "LEFT JOIN departments d ON u.department_id = d.dept_id "
                "WHERE u.user_id = ?", (user_id,)
            ).fetchone()
            if not user:
                return {"error": f"User {user_id} not found"}

            user_info = dict(user)

            # Total accesses
            total_accesses = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE user_id = ?",
                (user_id,)
            ).fetchone()[0]

            # Access by action
            by_action = _rows_to_dicts(conn.execute(
                "SELECT action, COUNT(*) as count FROM audit_log "
                "WHERE user_id = ? GROUP BY action ORDER BY count DESC",
                (user_id,)
            ).fetchall())

            # Access by resource type
            by_resource = _rows_to_dicts(conn.execute(
                "SELECT resource_type, COUNT(*) as count FROM audit_log "
                "WHERE user_id = ? GROUP BY resource_type ORDER BY count DESC",
                (user_id,)
            ).fetchall())

            # Hourly distribution
            hourly = _rows_to_dicts(conn.execute(
                "SELECT CAST(STRFTIME('%H', timestamp) AS INTEGER) as hour, "
                "COUNT(*) as count FROM audit_log "
                "WHERE user_id = ? GROUP BY hour ORDER BY hour",
                (user_id,)
            ).fetchall())

            # After-hours access
            after_hours = conn.execute(
                "SELECT COUNT(*) FROM audit_log "
                "WHERE user_id = ? AND ("
                "  CAST(STRFTIME('%H', timestamp) AS INTEGER) < 6 "
                "  OR CAST(STRFTIME('%H', timestamp) AS INTEGER) >= 22"
                ")", (user_id,)
            ).fetchone()[0]

            # Weekend access
            weekend = conn.execute(
                "SELECT COUNT(*) FROM audit_log "
                "WHERE user_id = ? AND CAST(STRFTIME('%w', timestamp) AS INTEGER) IN (0, 6)",
                (user_id,)
            ).fetchone()[0]

            # Daily access trend (last 30 days)
            daily_trend = _rows_to_dicts(conn.execute(
                "SELECT DATE(timestamp) as date, COUNT(*) as count "
                "FROM audit_log WHERE user_id = ? "
                "GROUP BY DATE(timestamp) ORDER BY date",
                (user_id,)
            ).fetchall())

            # Unique resources accessed
            unique_resources = conn.execute(
                "SELECT COUNT(DISTINCT resource_type || ':' || resource_id) "
                "FROM audit_log WHERE user_id = ?",
                (user_id,)
            ).fetchone()[0]

            # Unique patient charts accessed
            patient_charts = conn.execute(
                "SELECT COUNT(DISTINCT resource_id) FROM audit_log "
                "WHERE user_id = ? AND resource_type = 'patient_chart'",
                (user_id,)
            ).fetchone()[0]

            # Export/print activity
            exports = conn.execute(
                "SELECT COUNT(*) FROM audit_log "
                "WHERE user_id = ? AND action IN ('export', 'print')",
                (user_id,)
            ).fetchone()[0]

            # IP addresses used
            ip_addresses = _rows_to_dicts(conn.execute(
                "SELECT ip_address, COUNT(*) as count FROM audit_log "
                "WHERE user_id = ? GROUP BY ip_address ORDER BY count DESC LIMIT 10",
                (user_id,)
            ).fetchall())

            # Risk indicators
            risk_indicators = []
            if after_hours > total_accesses * 0.15:
                risk_indicators.append({
                    "risk": "High after-hours access",
                    "detail": f"{after_hours} of {total_accesses} accesses ({_safe_div(after_hours, total_accesses, 2)*100:.1f}%) occurred outside normal hours",
                    "severity": "medium",
                })
            if patient_charts > 50:
                risk_indicators.append({
                    "risk": "High-volume patient chart access",
                    "detail": f"Accessed {patient_charts} distinct patient charts",
                    "severity": "medium",
                })
            if exports > 20:
                risk_indicators.append({
                    "risk": "Excessive export/print activity",
                    "detail": f"{exports} export/print actions recorded",
                    "severity": "high",
                })
            if len(ip_addresses) > 5:
                risk_indicators.append({
                    "risk": "Multiple IP addresses",
                    "detail": f"Accessed from {len(ip_addresses)} different IP addresses",
                    "severity": "low",
                })
            # Check if user accessed resources outside their department
            if user_info.get("role") == "nurse" and user_info.get("department_id"):
                dept_id = user_info["department_id"]
                cross_dept = conn.execute(
                    "SELECT COUNT(*) FROM audit_log a "
                    "WHERE a.user_id = ? AND a.resource_type = 'patient_chart' "
                    "AND a.resource_id IN ("
                    "  SELECT CAST(encounter_id AS TEXT) FROM encounters "
                    "  WHERE department_id != ?"
                    ")", (user_id, dept_id)
                ).fetchone()[0]
                if cross_dept > 10:
                    risk_indicators.append({
                        "risk": "Cross-department chart access",
                        "detail": f"Accessed {cross_dept} records from other departments",
                        "severity": "medium",
                    })

            if not risk_indicators:
                risk_indicators.append({
                    "risk": "No anomalies detected",
                    "detail": "Access patterns appear within normal parameters",
                    "severity": "info",
                })

            return {
                "user_info": user_info,
                "access_summary": {
                    "total_accesses": total_accesses,
                    "unique_resources": unique_resources,
                    "patient_charts_accessed": patient_charts,
                    "export_print_count": exports,
                    "after_hours_count": after_hours,
                    "weekend_count": weekend,
                },
                "resource_breakdown": by_resource,
                "action_breakdown": by_action,
                "temporal_patterns": {
                    "hourly_distribution": hourly,
                    "daily_trend": daily_trend,
                },
                "ip_addresses": ip_addresses,
                "risk_indicators": risk_indicators,
            }

        else:
            # Aggregate analysis for all users
            total_accesses = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
            total_users = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM audit_log"
            ).fetchone()[0]

            by_role = _rows_to_dicts(conn.execute(
                "SELECT u.role, COUNT(*) as accesses, "
                "COUNT(DISTINCT a.user_id) as users "
                "FROM audit_log a JOIN users u ON a.user_id = u.user_id "
                "GROUP BY u.role ORDER BY accesses DESC"
            ).fetchall())

            top_users = _rows_to_dicts(conn.execute(
                "SELECT u.user_id, u.username, u.full_name, u.role, "
                "COUNT(*) as accesses "
                "FROM audit_log a JOIN users u ON a.user_id = u.user_id "
                "GROUP BY u.user_id ORDER BY accesses DESC LIMIT 15"
            ).fetchall())

            by_resource = _rows_to_dicts(conn.execute(
                "SELECT resource_type, COUNT(*) as count FROM audit_log "
                "GROUP BY resource_type ORDER BY count DESC"
            ).fetchall())

            by_action = _rows_to_dicts(conn.execute(
                "SELECT action, COUNT(*) as count FROM audit_log "
                "GROUP BY action ORDER BY count DESC"
            ).fetchall())

            after_hours_total = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE "
                "CAST(STRFTIME('%H', timestamp) AS INTEGER) < 6 "
                "OR CAST(STRFTIME('%H', timestamp) AS INTEGER) >= 22"
            ).fetchone()[0]

            return {
                "access_summary": {
                    "total_accesses": total_accesses,
                    "unique_users": total_users,
                    "after_hours_accesses": after_hours_total,
                    "after_hours_pct": _safe_div(after_hours_total, total_accesses, 2) * 100,
                },
                "by_role": by_role,
                "top_users": top_users,
                "resource_breakdown": by_resource,
                "action_breakdown": by_action,
            }
    finally:
        conn.close()


def detect_anomalies(db_path):
    """Detect suspicious access patterns in the audit log.

    Checks for after-hours access, excessive volume, unauthorized
    resource types, rapid-fire access, and other anomalies.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.

    Returns
    -------
    list of dict
        Each dict has keys: anomaly_type, severity, user_id, username,
        role, detail, recommendation.
    """
    conn = _db(db_path)
    try:
        anomalies = []

        # 1. After-hours heavy usage (more than 20 accesses outside 6 AM - 10 PM)
        after_hours_users = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, COUNT(*) as cnt "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "WHERE CAST(STRFTIME('%H', a.timestamp) AS INTEGER) < 6 "
            "  OR CAST(STRFTIME('%H', a.timestamp) AS INTEGER) >= 22 "
            "GROUP BY a.user_id HAVING cnt > 20 "
            "ORDER BY cnt DESC"
        ).fetchall()
        for row in after_hours_users:
            anomalies.append({
                "anomaly_type": "after_hours_access",
                "severity": "medium",
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "detail": f"{row['cnt']} accesses outside normal hours (before 6 AM or after 10 PM)",
                "recommendation": "Verify user has legitimate need for after-hours access. "
                                  "Consider whether role requires off-hours access.",
            })

        # 2. Excessive daily access volume (more than 3x average for their role)
        role_avg = conn.execute(
            "SELECT u.role, "
            "ROUND(CAST(COUNT(*) AS REAL) / MAX(COUNT(DISTINCT a.user_id), 1), 0) as avg_per_user "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "GROUP BY u.role"
        ).fetchall()
        role_avg_map = {r["role"]: r["avg_per_user"] for r in role_avg}

        user_totals = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, COUNT(*) as cnt "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "GROUP BY a.user_id ORDER BY cnt DESC"
        ).fetchall()
        for row in user_totals:
            avg = role_avg_map.get(row["role"], 100)
            if avg > 0 and row["cnt"] > avg * 3:
                anomalies.append({
                    "anomaly_type": "excessive_access_volume",
                    "severity": "high",
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "role": row["role"],
                    "detail": (
                        f"{row['cnt']} total accesses vs role average of {int(avg)}. "
                        f"This is {_safe_div(row['cnt'], avg, 1)}x the average for '{row['role']}' role."
                    ),
                    "recommendation": "Review access patterns and verify business justification "
                                      "for the high volume of access.",
                })

        # 3. Broad patient chart access (accessing many distinct patient charts)
        broad_access = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, "
            "COUNT(DISTINCT a.resource_id) as distinct_charts "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "WHERE a.resource_type = 'patient_chart' "
            "GROUP BY a.user_id HAVING distinct_charts > 50 "
            "ORDER BY distinct_charts DESC"
        ).fetchall()
        for row in broad_access:
            sev = "high" if row["distinct_charts"] > 100 else "medium"
            anomalies.append({
                "anomaly_type": "broad_chart_access",
                "severity": sev,
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "detail": (
                    f"Accessed {row['distinct_charts']} distinct patient charts. "
                    f"Role '{row['role']}' typically does not require access to this many records."
                ),
                "recommendation": "Investigate whether the breadth of chart access is justified. "
                                  "This may indicate snooping or an overly broad access role.",
            })

        # 4. High export/print volume (potential data exfiltration)
        export_users = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, "
            "COUNT(*) as export_count "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "WHERE a.action IN ('export', 'print') "
            "GROUP BY a.user_id HAVING export_count > 15 "
            "ORDER BY export_count DESC"
        ).fetchall()
        for row in export_users:
            anomalies.append({
                "anomaly_type": "excessive_export_print",
                "severity": "high",
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "detail": f"{row['export_count']} export/print actions - possible data exfiltration risk",
                "recommendation": "Review exported content for PHI. Confirm with user's supervisor "
                                  "that these exports are operationally necessary.",
            })

        # 5. Weekend-only access (accessing only on weekends is unusual)
        weekend_only = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, "
            "SUM(CASE WHEN CAST(STRFTIME('%w', a.timestamp) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END) as weekend, "
            "COUNT(*) as total "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "GROUP BY a.user_id "
            "HAVING total > 10 AND CAST(weekend AS REAL) / total > 0.6"
        ).fetchall()
        for row in weekend_only:
            pct = _safe_div(row["weekend"], row["total"], 1) * 100
            anomalies.append({
                "anomaly_type": "predominantly_weekend_access",
                "severity": "low",
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "detail": f"{pct:.0f}% of {row['total']} accesses occurred on weekends",
                "recommendation": "Verify if weekend-heavy access aligns with work schedule.",
            })

        # 6. Access from many different IP addresses
        multi_ip = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, "
            "COUNT(DISTINCT a.ip_address) as ip_count "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "GROUP BY a.user_id HAVING ip_count > 8 "
            "ORDER BY ip_count DESC"
        ).fetchall()
        for row in multi_ip:
            anomalies.append({
                "anomaly_type": "multiple_ip_addresses",
                "severity": "low",
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "detail": f"Access from {row['ip_count']} different IP addresses",
                "recommendation": "May indicate shared credentials or legitimate mobile usage. "
                                  "Verify with user.",
            })

        # 7. Inactive user with recent access
        inactive_access = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, u.active, "
            "COUNT(*) as cnt, MAX(a.timestamp) as last_access "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "WHERE u.active = 0 "
            "GROUP BY a.user_id ORDER BY last_access DESC"
        ).fetchall()
        for row in inactive_access:
            anomalies.append({
                "anomaly_type": "inactive_user_access",
                "severity": "critical",
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "detail": (
                    f"Inactive/disabled user account has {row['cnt']} audit entries. "
                    f"Last access: {row['last_access']}"
                ),
                "recommendation": "URGENT: Immediately investigate. Inactive accounts should "
                                  "not generate new access events. Check for unauthorized account reactivation.",
            })

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        anomalies.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))

        return anomalies
    finally:
        conn.close()


def generate_access_timeline(db_path, resource_type, resource_id):
    """Generate a chronological access timeline for a specific resource.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    resource_type : str
        Type of resource (e.g., 'patient_chart', 'lab_result').
    resource_id : str or int
        ID of the specific resource.

    Returns
    -------
    dict
        Keys: resource_type, resource_id, total_accesses, unique_users,
        timeline (list of access events), access_summary.
    """
    conn = _db(db_path)
    try:
        resource_id = str(resource_id)

        timeline = _rows_to_dicts(conn.execute(
            "SELECT a.log_id, a.user_id, u.username, u.full_name, u.role, "
            "a.action, a.timestamp, a.ip_address, a.details "
            "FROM audit_log a "
            "LEFT JOIN users u ON a.user_id = u.user_id "
            "WHERE a.resource_type = ? AND a.resource_id = ? "
            "ORDER BY a.timestamp ASC",
            (resource_type, resource_id)
        ).fetchall())

        if not timeline:
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "total_accesses": 0,
                "unique_users": 0,
                "timeline": [],
                "access_summary": "No access events found for this resource.",
            }

        unique_users = len(set(e["user_id"] for e in timeline))

        # Summarize by user
        user_summary = {}
        for entry in timeline:
            uid = entry["user_id"]
            if uid not in user_summary:
                user_summary[uid] = {
                    "user_id": uid,
                    "username": entry["username"],
                    "full_name": entry["full_name"],
                    "role": entry["role"],
                    "access_count": 0,
                    "actions": defaultdict(int),
                    "first_access": entry["timestamp"],
                    "last_access": entry["timestamp"],
                }
            user_summary[uid]["access_count"] += 1
            user_summary[uid]["actions"][entry["action"]] += 1
            user_summary[uid]["last_access"] = entry["timestamp"]

        # Convert actions defaultdict to regular dict for JSON serialization
        user_list = []
        for uid, info in user_summary.items():
            info["actions"] = dict(info["actions"])
            user_list.append(info)
        user_list.sort(key=lambda x: x["access_count"], reverse=True)

        # Action breakdown
        action_counts = defaultdict(int)
        for entry in timeline:
            action_counts[entry["action"]] += 1

        first_ts = timeline[0]["timestamp"] if timeline else None
        last_ts = timeline[-1]["timestamp"] if timeline else None

        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "total_accesses": len(timeline),
            "unique_users": unique_users,
            "first_access": first_ts,
            "last_access": last_ts,
            "action_breakdown": dict(action_counts),
            "user_summary": user_list,
            "timeline": timeline,
            "access_summary": (
                f"Resource '{resource_type}:{resource_id}' was accessed "
                f"{len(timeline)} times by {unique_users} user(s) "
                f"between {first_ts} and {last_ts}."
            ),
        }
    finally:
        conn.close()


def build_audit_report(db_path, start_date, end_date):
    """Build a comprehensive HIPAA audit report for a date range.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    start_date : str
        Start date (YYYY-MM-DD).
    end_date : str
        End date (YYYY-MM-DD).

    Returns
    -------
    dict
        Comprehensive audit report with overview, user activity,
        resource access, anomalies, and compliance posture.
    """
    conn = _db(db_path)
    try:
        # Overview
        total_events = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE timestamp BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()[0]

        unique_users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM audit_log "
            "WHERE timestamp BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()[0]

        # Action distribution
        action_dist = _rows_to_dicts(conn.execute(
            "SELECT action, COUNT(*) as count FROM audit_log "
            "WHERE timestamp BETWEEN ? AND ? "
            "GROUP BY action ORDER BY count DESC",
            (start_date, end_date)
        ).fetchall())

        # Resource distribution
        resource_dist = _rows_to_dicts(conn.execute(
            "SELECT resource_type, COUNT(*) as count FROM audit_log "
            "WHERE timestamp BETWEEN ? AND ? "
            "GROUP BY resource_type ORDER BY count DESC",
            (start_date, end_date)
        ).fetchall())

        # User activity
        user_activity = _rows_to_dicts(conn.execute(
            "SELECT u.user_id, u.username, u.full_name, u.role, "
            "u.department_id, d.dept_name, u.access_level, u.active, "
            "COUNT(*) as total_accesses, "
            "SUM(CASE WHEN a.action = 'view' THEN 1 ELSE 0 END) as views, "
            "SUM(CASE WHEN a.action = 'edit' THEN 1 ELSE 0 END) as edits, "
            "SUM(CASE WHEN a.action = 'export' THEN 1 ELSE 0 END) as exports, "
            "SUM(CASE WHEN a.action = 'print' THEN 1 ELSE 0 END) as prints, "
            "COUNT(DISTINCT a.resource_type || ':' || a.resource_id) as unique_resources, "
            "MIN(a.timestamp) as first_access, MAX(a.timestamp) as last_access "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "LEFT JOIN departments d ON u.department_id = d.dept_id "
            "WHERE a.timestamp BETWEEN ? AND ? "
            "GROUP BY u.user_id ORDER BY total_accesses DESC",
            (start_date, end_date)
        ).fetchall())

        # After-hours analysis
        after_hours = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE timestamp BETWEEN ? AND ? "
            "AND (CAST(STRFTIME('%H', timestamp) AS INTEGER) < 6 "
            "  OR CAST(STRFTIME('%H', timestamp) AS INTEGER) >= 22)",
            (start_date, end_date)
        ).fetchone()[0]

        weekend_access = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE timestamp BETWEEN ? AND ? "
            "AND CAST(STRFTIME('%w', timestamp) AS INTEGER) IN (0, 6)",
            (start_date, end_date)
        ).fetchone()[0]

        # Daily volume
        daily_volume = _rows_to_dicts(conn.execute(
            "SELECT DATE(timestamp) as date, COUNT(*) as events "
            "FROM audit_log WHERE timestamp BETWEEN ? AND ? "
            "GROUP BY DATE(timestamp) ORDER BY date",
            (start_date, end_date)
        ).fetchall())

        # Hourly distribution
        hourly_dist = _rows_to_dicts(conn.execute(
            "SELECT CAST(STRFTIME('%H', timestamp) AS INTEGER) as hour, "
            "COUNT(*) as events FROM audit_log "
            "WHERE timestamp BETWEEN ? AND ? "
            "GROUP BY hour ORDER BY hour",
            (start_date, end_date)
        ).fetchall())

        # Role-based summary
        by_role = _rows_to_dicts(conn.execute(
            "SELECT u.role, COUNT(*) as accesses, "
            "COUNT(DISTINCT a.user_id) as users, "
            "SUM(CASE WHEN a.action IN ('export', 'print') THEN 1 ELSE 0 END) as export_print "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "WHERE a.timestamp BETWEEN ? AND ? "
            "GROUP BY u.role ORDER BY accesses DESC",
            (start_date, end_date)
        ).fetchall())

        # Security alerts in period
        security_alerts = _rows_to_dicts(conn.execute(
            "SELECT * FROM system_alerts "
            "WHERE alert_type = 'security' AND created_at BETWEEN ? AND ? "
            "ORDER BY created_at DESC",
            (start_date, end_date)
        ).fetchall())

        # Detect anomalies for this period
        anomalies = detect_anomalies(db_path)

        # Compliance score heuristic
        compliance_score = 100
        if after_hours > total_events * 0.20:
            compliance_score -= 10
        if len([a for a in anomalies if a["severity"] == "critical"]) > 0:
            compliance_score -= 25
        if len([a for a in anomalies if a["severity"] == "high"]) > 3:
            compliance_score -= 15
        elif len([a for a in anomalies if a["severity"] == "high"]) > 0:
            compliance_score -= 10
        if len([a for a in anomalies if a["severity"] == "medium"]) > 5:
            compliance_score -= 10
        if len(security_alerts) > 5:
            compliance_score -= 5
        compliance_score = max(0, min(100, compliance_score))

        if compliance_score >= 85:
            posture = "Good"
        elif compliance_score >= 70:
            posture = "Acceptable"
        elif compliance_score >= 50:
            posture = "Needs Improvement"
        else:
            posture = "Critical - Immediate Action Required"

        return {
            "report_title": "HIPAA Audit Report",
            "period": {"start_date": start_date, "end_date": end_date},
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overview": {
                "total_access_events": total_events,
                "unique_users": unique_users,
                "after_hours_accesses": after_hours,
                "after_hours_pct": _safe_div(after_hours, total_events, 2) * 100,
                "weekend_accesses": weekend_access,
                "weekend_pct": _safe_div(weekend_access, total_events, 2) * 100,
            },
            "action_distribution": action_dist,
            "resource_distribution": resource_dist,
            "user_activity": user_activity,
            "role_summary": by_role,
            "temporal_analysis": {
                "daily_volume": daily_volume,
                "hourly_distribution": hourly_dist,
            },
            "anomalies_detected": anomalies,
            "anomaly_count": len(anomalies),
            "security_alerts": security_alerts,
            "compliance_posture": {
                "score": compliance_score,
                "rating": posture,
                "findings_count": len(anomalies),
                "critical_findings": len([a for a in anomalies if a["severity"] == "critical"]),
                "high_findings": len([a for a in anomalies if a["severity"] == "high"]),
                "medium_findings": len([a for a in anomalies if a["severity"] == "medium"]),
                "low_findings": len([a for a in anomalies if a["severity"] == "low"]),
            },
            "summary": (
                f"HIPAA audit for {start_date} to {end_date}: "
                f"{total_events} access events by {unique_users} users. "
                f"After-hours: {after_hours} ({_safe_div(after_hours, total_events, 2)*100:.1f}%). "
                f"{len(anomalies)} anomalies detected. "
                f"Compliance score: {compliance_score}/100 ({posture})."
            ),
        }
    finally:
        conn.close()


def check_minimum_necessary(db_path, user_id):
    """Analyze whether a user accessed only the minimum necessary information.

    Evaluates access breadth relative to the user's role and department
    to assess compliance with the HIPAA minimum necessary standard.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.
    user_id : int or str
        The user ID to evaluate.

    Returns
    -------
    dict
        Keys: user_info, access_scope, role_comparison, findings,
        minimum_necessary_score, assessment.
    """
    conn = _db(db_path)
    try:
        user_id = int(user_id)

        user = conn.execute(
            "SELECT u.*, d.dept_name FROM users u "
            "LEFT JOIN departments d ON u.department_id = d.dept_id "
            "WHERE u.user_id = ?", (user_id,)
        ).fetchone()
        if not user:
            return {"error": f"User {user_id} not found"}

        user_info = dict(user)
        role = user["role"]
        dept_id = user["department_id"]

        # What this user accessed
        user_resources = _rows_to_dicts(conn.execute(
            "SELECT resource_type, COUNT(DISTINCT resource_id) as distinct_resources, "
            "COUNT(*) as total_accesses "
            "FROM audit_log WHERE user_id = ? "
            "GROUP BY resource_type ORDER BY total_accesses DESC",
            (user_id,)
        ).fetchall())

        total_user_accesses = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE user_id = ?", (user_id,)
        ).fetchone()[0]

        # Unique patient charts this user accessed
        user_patient_charts = conn.execute(
            "SELECT COUNT(DISTINCT resource_id) FROM audit_log "
            "WHERE user_id = ? AND resource_type = 'patient_chart'",
            (user_id,)
        ).fetchone()[0]

        # Role-average comparison
        role_avg_charts = conn.execute(
            "SELECT ROUND(AVG(chart_count), 0) FROM ("
            "  SELECT COUNT(DISTINCT a.resource_id) as chart_count "
            "  FROM audit_log a JOIN users u ON a.user_id = u.user_id "
            "  WHERE u.role = ? AND a.resource_type = 'patient_chart' "
            "  GROUP BY a.user_id"
            ")", (role,)
        ).fetchone()[0] or 0

        role_avg_total = conn.execute(
            "SELECT ROUND(AVG(total), 0) FROM ("
            "  SELECT COUNT(*) as total FROM audit_log a "
            "  JOIN users u ON a.user_id = u.user_id "
            "  WHERE u.role = ? GROUP BY a.user_id"
            ")", (role,)
        ).fetchone()[0] or 0

        # Cross-department access
        if dept_id:
            own_dept_access = conn.execute(
                "SELECT COUNT(*) FROM audit_log a "
                "WHERE a.user_id = ? AND a.resource_type = 'encounter' "
                "AND a.resource_id IN ("
                "  SELECT CAST(encounter_id AS TEXT) FROM encounters WHERE department_id = ?"
                ")", (user_id, dept_id)
            ).fetchone()[0]

            other_dept_access = conn.execute(
                "SELECT COUNT(*) FROM audit_log a "
                "WHERE a.user_id = ? AND a.resource_type = 'encounter' "
                "AND a.resource_id IN ("
                "  SELECT CAST(encounter_id AS TEXT) FROM encounters WHERE department_id != ?"
                ")", (user_id, dept_id)
            ).fetchone()[0]
        else:
            own_dept_access = 0
            other_dept_access = 0

        total_dept_access = own_dept_access + other_dept_access
        cross_dept_pct = _safe_div(other_dept_access, total_dept_access, 2) * 100

        # What actions did they take
        user_actions = _rows_to_dicts(conn.execute(
            "SELECT action, COUNT(*) as count FROM audit_log "
            "WHERE user_id = ? GROUP BY action ORDER BY count DESC",
            (user_id,)
        ).fetchall())

        # Export/print volume
        exports = conn.execute(
            "SELECT COUNT(*) FROM audit_log "
            "WHERE user_id = ? AND action IN ('export', 'print')",
            (user_id,)
        ).fetchone()[0]

        # Expected access pattern by role
        expected_resources = {
            "physician": ["patient_chart", "lab_result", "medication_order", "encounter", "report"],
            "nurse": ["patient_chart", "lab_result", "medication_order", "encounter"],
            "admin": ["user_account", "report", "encounter"],
            "analyst": ["report", "encounter", "patient_chart"],
            "pharmacist": ["medication_order", "patient_chart", "lab_result"],
        }

        expected = expected_resources.get(role, [])
        accessed_types = {r["resource_type"] for r in user_resources}
        unexpected_types = accessed_types - set(expected)

        # Build findings
        findings = []
        score = 100

        # Check chart volume vs role average
        if role_avg_charts > 0 and user_patient_charts > role_avg_charts * 2:
            findings.append({
                "finding": "Excessive patient chart access",
                "severity": "high",
                "detail": (
                    f"Accessed {user_patient_charts} patient charts vs role average of "
                    f"{int(role_avg_charts)}. This is {_safe_div(user_patient_charts, role_avg_charts, 1)}x "
                    f"the average for '{role}' role."
                ),
            })
            score -= 20

        # Check for unexpected resource types
        if unexpected_types:
            findings.append({
                "finding": "Access to unexpected resource types",
                "severity": "medium",
                "detail": (
                    f"Accessed resource types not typically associated with '{role}' role: "
                    f"{', '.join(unexpected_types)}. Expected: {', '.join(expected)}."
                ),
            })
            score -= 10

        # Check cross-department access
        if cross_dept_pct > 30:
            findings.append({
                "finding": "Significant cross-department access",
                "severity": "medium",
                "detail": (
                    f"{cross_dept_pct:.0f}% of encounter-related accesses were outside "
                    f"assigned department ({user_info.get('dept_name', 'Unknown')})."
                ),
            })
            score -= 10

        # Check export volume
        if exports > 10:
            findings.append({
                "finding": "High export/print volume",
                "severity": "medium",
                "detail": f"{exports} export/print actions recorded.",
            })
            score -= 10

        # Check total volume vs role average
        if role_avg_total > 0 and total_user_accesses > role_avg_total * 2.5:
            findings.append({
                "finding": "Total access volume exceeds role norms",
                "severity": "medium",
                "detail": (
                    f"Total {total_user_accesses} accesses vs role average of {int(role_avg_total)}."
                ),
            })
            score -= 10

        score = max(0, min(100, score))

        if score >= 80:
            assessment = "Compliant - access patterns appear to follow minimum necessary standards"
        elif score >= 60:
            assessment = "Partially Compliant - some access patterns warrant review"
        else:
            assessment = "Non-Compliant - access patterns significantly exceed minimum necessary"

        if not findings:
            findings.append({
                "finding": "No concerns identified",
                "severity": "info",
                "detail": "Access patterns are consistent with the user's role and department.",
            })

        return {
            "user_info": user_info,
            "access_scope": {
                "total_accesses": total_user_accesses,
                "resource_breakdown": user_resources,
                "patient_charts_accessed": user_patient_charts,
                "actions": user_actions,
                "export_print_count": exports,
            },
            "role_comparison": {
                "role": role,
                "role_avg_chart_access": int(role_avg_charts),
                "role_avg_total_access": int(role_avg_total),
                "user_chart_access": user_patient_charts,
                "user_total_access": total_user_accesses,
                "expected_resource_types": expected,
                "unexpected_resource_types": list(unexpected_types),
            },
            "department_analysis": {
                "assigned_department": user_info.get("dept_name", "Unknown"),
                "own_department_accesses": own_dept_access,
                "other_department_accesses": other_dept_access,
                "cross_department_pct": cross_dept_pct,
            },
            "findings": findings,
            "minimum_necessary_score": score,
            "assessment": assessment,
        }
    finally:
        conn.close()


def identify_break_the_glass(db_path):
    """Identify potential Break-the-Glass (emergency override) access events.

    In the absence of an explicit BTG flag, this function uses heuristics
    to find access patterns that resemble emergency override situations:
    rapid access to multiple records, after-hours activity on critical
    resources, or access by users who do not normally access a resource type.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.

    Returns
    -------
    list of dict
        Each dict describes a potential BTG event with keys: user_id,
        username, role, btg_type, detail, timestamp_range, severity,
        records_affected.
    """
    conn = _db(db_path)
    try:
        btg_events = []

        # 1. Rapid-fire access: many records in a short time window
        # Users who accessed 10+ distinct resources in under 5 minutes
        users = conn.execute(
            "SELECT DISTINCT user_id FROM audit_log"
        ).fetchall()

        for u_row in users:
            uid = u_row["user_id"]
            entries = conn.execute(
                "SELECT log_id, action, resource_type, resource_id, timestamp "
                "FROM audit_log WHERE user_id = ? ORDER BY timestamp",
                (uid,)
            ).fetchall()

            if len(entries) < 10:
                continue

            # Sliding window: check for 10+ accesses within 5 minutes
            found = False
            for i in range(len(entries)):
                if found:
                    break
                try:
                    ts_i = datetime.strptime(entries[i]["timestamp"], "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    continue

                window_resources = set()
                window_end_idx = i
                for j in range(i, len(entries)):
                    try:
                        ts_j = datetime.strptime(entries[j]["timestamp"], "%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        continue
                    if (ts_j - ts_i).total_seconds() > 300:  # 5 minutes
                        break
                    window_resources.add(entries[j]["resource_id"])
                    window_end_idx = j

                if len(window_resources) >= 10:
                    user_info = conn.execute(
                        "SELECT username, full_name, role FROM users WHERE user_id = ?",
                        (uid,)
                    ).fetchone()
                    if user_info:
                        btg_events.append({
                            "user_id": uid,
                            "username": user_info["username"],
                            "full_name": user_info["full_name"],
                            "role": user_info["role"],
                            "btg_type": "rapid_access",
                            "detail": (
                                f"Accessed {len(window_resources)} distinct resources within "
                                f"5 minutes. This pattern may indicate an emergency override "
                                f"or urgent clinical need."
                            ),
                            "timestamp_range": {
                                "start": entries[i]["timestamp"],
                                "end": entries[window_end_idx]["timestamp"],
                            },
                            "severity": "medium",
                            "records_affected": len(window_resources),
                        })
                    found = True  # one detection per user is enough

        # 2. After-hours + critical resource access
        after_hours_critical = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, "
            "COUNT(*) as cnt, MIN(a.timestamp) as first_ts, MAX(a.timestamp) as last_ts "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "WHERE a.resource_type = 'patient_chart' "
            "AND (CAST(STRFTIME('%H', a.timestamp) AS INTEGER) < 5 "
            "  OR CAST(STRFTIME('%H', a.timestamp) AS INTEGER) >= 23) "
            "GROUP BY a.user_id HAVING cnt >= 5 "
            "ORDER BY cnt DESC"
        ).fetchall()
        for row in after_hours_critical:
            btg_events.append({
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "btg_type": "after_hours_critical_access",
                "detail": (
                    f"{row['cnt']} patient chart accesses during late-night hours "
                    f"(11 PM - 5 AM). May indicate emergency clinical situation."
                ),
                "timestamp_range": {
                    "start": row["first_ts"],
                    "end": row["last_ts"],
                },
                "severity": "high",
                "records_affected": row["cnt"],
            })

        # 3. Role-inappropriate access patterns (e.g., admin accessing patient_chart heavily)
        role_inappropriate = conn.execute(
            "SELECT a.user_id, u.username, u.full_name, u.role, "
            "COUNT(*) as cnt "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "WHERE u.role = 'admin' AND a.resource_type = 'patient_chart' "
            "GROUP BY a.user_id HAVING cnt > 20 "
            "ORDER BY cnt DESC"
        ).fetchall()
        for row in role_inappropriate:
            btg_events.append({
                "user_id": row["user_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "btg_type": "role_inappropriate_access",
                "detail": (
                    f"Admin user accessed {row['cnt']} patient chart records. "
                    f"Admins typically do not need clinical chart access. "
                    f"May indicate a BTG event or policy violation."
                ),
                "timestamp_range": None,
                "severity": "high",
                "records_affected": row["cnt"],
            })

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        btg_events.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))

        return btg_events
    finally:
        conn.close()


def role_access_matrix(db_path):
    """Build a matrix of roles vs resource types vs access patterns.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database.

    Returns
    -------
    dict
        Keys: matrix (dict of role -> resource_type -> action -> counts),
        roles, resource_types, action_types, role_totals, deviations,
        summary.
    """
    conn = _db(db_path)
    try:
        # Build the matrix
        matrix_rows = _rows_to_dicts(conn.execute(
            "SELECT u.role, a.resource_type, a.action, "
            "COUNT(*) as access_count, "
            "COUNT(DISTINCT a.user_id) as user_count "
            "FROM audit_log a "
            "JOIN users u ON a.user_id = u.user_id "
            "GROUP BY u.role, a.resource_type, a.action "
            "ORDER BY u.role, a.resource_type, a.action"
        ).fetchall())

        # Get unique roles, resource types, actions
        roles = sorted(set(r["role"] for r in matrix_rows))
        resource_types = sorted(set(r["resource_type"] for r in matrix_rows))
        actions = sorted(set(r["action"] for r in matrix_rows))

        # Build a structured matrix
        matrix = {}
        for role in roles:
            matrix[role] = {}
            for rtype in resource_types:
                matrix[role][rtype] = {}
                for action in actions:
                    matching = [
                        r for r in matrix_rows
                        if r["role"] == role and r["resource_type"] == rtype
                        and r["action"] == action
                    ]
                    if matching:
                        matrix[role][rtype][action] = {
                            "count": matching[0]["access_count"],
                            "users": matching[0]["user_count"],
                        }
                    else:
                        matrix[role][rtype][action] = {
                            "count": 0,
                            "users": 0,
                        }

        # Role totals
        role_totals = _rows_to_dicts(conn.execute(
            "SELECT u.role, COUNT(*) as total_accesses, "
            "COUNT(DISTINCT a.user_id) as total_users, "
            "COUNT(DISTINCT a.resource_type) as resource_types_accessed "
            "FROM audit_log a JOIN users u ON a.user_id = u.user_id "
            "GROUP BY u.role ORDER BY total_accesses DESC"
        ).fetchall())

        # Expected access pattern definitions for comparison
        expected_patterns = {
            "physician": {
                "primary_resources": ["patient_chart", "lab_result", "medication_order", "encounter"],
                "expected_actions": ["view", "edit"],
                "notes": "Physicians should primarily access clinical data for their assigned patients.",
            },
            "nurse": {
                "primary_resources": ["patient_chart", "lab_result", "medication_order", "encounter"],
                "expected_actions": ["view", "edit"],
                "notes": "Nurses should access clinical data for patients in their unit.",
            },
            "admin": {
                "primary_resources": ["user_account", "report"],
                "expected_actions": ["view", "edit", "export"],
                "notes": "Admins should primarily access system administration resources.",
            },
            "analyst": {
                "primary_resources": ["report", "encounter"],
                "expected_actions": ["view", "export"],
                "notes": "Analysts should primarily access aggregate/reporting data.",
            },
            "pharmacist": {
                "primary_resources": ["medication_order", "patient_chart", "lab_result"],
                "expected_actions": ["view", "edit"],
                "notes": "Pharmacists should primarily access medication and related clinical data.",
            },
        }

        # Identify deviations from expected patterns
        deviations = []
        for role in roles:
            expected = expected_patterns.get(role, {})
            primary = set(expected.get("primary_resources", []))
            for rtype in resource_types:
                total_for_resource = sum(
                    matrix[role][rtype][a]["count"] for a in actions
                )
                if total_for_resource > 0 and rtype not in primary:
                    deviations.append({
                        "role": role,
                        "resource_type": rtype,
                        "access_count": total_for_resource,
                        "note": f"'{role}' role accessed '{rtype}' {total_for_resource} times - not in expected primary resources",
                    })

        return {
            "matrix": matrix,
            "roles": roles,
            "resource_types": resource_types,
            "action_types": actions,
            "role_totals": role_totals,
            "expected_patterns": expected_patterns,
            "deviations": deviations,
            "summary": (
                f"Access matrix covers {len(roles)} roles accessing "
                f"{len(resource_types)} resource types via {len(actions)} action types. "
                f"{len(deviations)} access pattern deviations from expected role norms detected."
            ),
        }
    finally:
        conn.close()

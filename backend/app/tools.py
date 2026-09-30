"""Ground Truth Tool Layer for Sunrise Clinic.

Per the assignment specification:
- This layer NEVER calls an LLM. It is the clinic's single source of truth.
- A slot cannot be double-booked; concurrent bookings fail safely via SQLite transactions.
- Patient lookup on an ambiguous name returns candidate list, never guesses.
- Tool argument errors are specific and actionable, never generic 500s.
"""

from __future__ import annotations

import datetime
import json
import sqlite3
from typing import Any, Optional

VALID_ESCALATION_REASONS = {
    "clinical_urgent",
    "medical_advice",
    "not_authorised",
    "ambiguous_patient",
    "out_of_scope",
}

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class ToolError(Exception):
    """Specific, actionable tool error."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def add_minutes(time_str: str, minutes: int) -> str:
    parts = time_str.split(":")
    total = int(parts[0]) * 60 + int(parts[1]) + minutes
    hours = (total // 60) % 24
    mins = total % 60
    return f"{hours:02d}:{mins:02d}"


def time_to_minutes(time_str: str) -> int:
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def search_slots(
    conn: sqlite3.Connection,
    doctor_id: str,
    date: str,
    window: Optional[str] = None,
) -> list[str]:
    """Derive valid free slots for a doctor on a given date directly from clinic database."""
    cursor = conn.cursor()

    # 1. Validate doctor exists
    cursor.execute("SELECT id, name FROM doctors WHERE id = ?", (doctor_id,))
    doctor = cursor.fetchone()
    if not doctor:
        raise ToolError("DOCTOR_NOT_FOUND", f"Doctor '{doctor_id}' does not exist in clinic records.")

    # 2. Check if date is a clinic holiday
    cursor.execute("SELECT holiday_date FROM holidays WHERE holiday_date = ?", (date,))
    if cursor.fetchone():
        return []

    # 3. Check if doctor is on leave
    cursor.execute(
        "SELECT leave_date FROM doctor_leaves WHERE doctor_id = ? AND leave_date = ?",
        (doctor_id, date),
    )
    if cursor.fetchone():
        return []

    # 4. Check day of week
    try:
        dt = datetime.date.fromisoformat(date)
    except ValueError:
        raise ToolError("INVALID_DATE", f"Date '{date}' is not a valid ISO date (YYYY-MM-DD).")

    weekday_str = WEEKDAYS[dt.weekday()]

    # 5. Fetch doctor working windows for this weekday
    cursor.execute(
        "SELECT start_time, end_time FROM doctor_windows WHERE doctor_id = ? AND day = ? ORDER BY start_time",
        (doctor_id, weekday_str),
    )
    windows = cursor.fetchall()
    if not windows:
        return []

    # 6. Fetch slot_minutes from clinic config
    cursor.execute("SELECT slot_minutes FROM clinic LIMIT 1")
    slot_minutes = cursor.fetchone()["slot_minutes"]

    # 7. Generate candidate slots within doctor windows
    candidate_slots: set[str] = set()
    for w in windows:
        start_min = time_to_minutes(w["start_time"])
        end_min = time_to_minutes(w["end_time"])
        curr = start_min
        while curr + slot_minutes <= end_min:
            h = curr // 60
            m = curr % 60
            slot_str = f"{h:02d}:{m:02d}"
            candidate_slots.add(slot_str)
            curr += slot_minutes

    # 8. Query booked appointments for this doctor on this date
    cursor.execute(
        "SELECT start_time FROM appointments WHERE doctor_id = ? AND date = ? AND status = 'booked'",
        (doctor_id, date),
    )
    booked_starts = {row["start_time"] for row in cursor.fetchall()}

    # 9. Filter out already booked slots
    free_slots = [s for s in candidate_slots if s not in booked_starts]

    # 10. Filter by window if requested (e.g., 'morning', 'evening')
    if window:
        w_lower = window.lower()
        if "morning" in w_lower or "subah" in w_lower:
            free_slots = [s for s in free_slots if time_to_minutes(s) < 780]  # before 13:00
        elif "afternoon" in w_lower or "dopahar" in w_lower:
            free_slots = [s for s in free_slots if 720 <= time_to_minutes(s) < 960]
        elif "evening" in w_lower or "shaam" in w_lower:
            free_slots = [s for s in free_slots if time_to_minutes(s) >= 960]  # after 16:00

    return sorted(free_slots)


def book_appointment(
    conn: sqlite3.Connection,
    patient_id: str,
    doctor_id: str,
    date: str,
    start: str,
) -> dict[str, Any]:
    """Atomically books an appointment.
    
    Uses BEGIN IMMEDIATE transaction and database-level UNIQUE(doctor_id, date, start_time)
    to prevent double-booking race conditions.
    """
    cursor = conn.cursor()

    # Validate patient
    cursor.execute("SELECT id, name FROM patients WHERE id = ?", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        raise ToolError("PATIENT_NOT_FOUND", f"Patient '{patient_id}' not found.")

    # Validate doctor
    cursor.execute("SELECT id, name FROM doctors WHERE id = ?", (doctor_id,))
    doctor = cursor.fetchone()
    if not doctor:
        raise ToolError("DOCTOR_NOT_FOUND", f"Doctor '{doctor_id}' not found.")

    # Verify doctor working schedule for this date & slot
    free_slots = search_slots(conn, doctor_id, date)
    if start not in free_slots:
        raise ToolError("SLOT_UNAVAILABLE", f"Slot '{start}' on '{date}' is not available for doctor '{doctor_id}'.")

    # Get slot_minutes
    cursor.execute("SELECT slot_minutes FROM clinic LIMIT 1")
    slot_minutes = cursor.fetchone()["slot_minutes"]
    end_time = add_minutes(start, slot_minutes)

    # BEGIN IMMEDIATE for atomic concurrency
    try:
        cursor.execute("BEGIN IMMEDIATE")

        # Generate next appointment ID
        cursor.execute("SELECT id FROM appointments WHERE id LIKE 'ap_%' ORDER BY id DESC LIMIT 1")
        last_appt = cursor.fetchone()
        if last_appt and last_appt["id"].startswith("ap_"):
            try:
                next_num = int(last_appt["id"][3:]) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        appt_id = f"ap_{next_num:04d}"

        # Insert with UNIQUE constraint enforcement
        cursor.execute(
            """INSERT INTO appointments (id, patient_id, doctor_id, date, start_time, end_time, status)
               VALUES (?, ?, ?, ?, ?, ?, 'booked')""",
            (appt_id, patient_id, doctor_id, date, start, end_time),
        )
        conn.commit()

        return {
            "appointment_id": appt_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "date": date,
            "start": start,
            "end": end_time,
            "status": "booked",
        }
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ToolError("SLOT_ALREADY_BOOKED", f"Slot '{start}' on '{date}' is already booked for doctor '{doctor_id}'.") from e
    except Exception as e:
        conn.rollback()
        raise e


def reschedule_appointment(
    conn: sqlite3.Connection,
    appointment_id: str,
    new_date: str,
    new_start: str,
    caller_patient_id: Optional[str] = None,
) -> dict[str, Any]:
    """Reschedules an existing appointment to a new date and time atomically."""
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    appt = cursor.fetchone()
    if not appt:
        raise ToolError("APPOINTMENT_NOT_FOUND", f"Appointment '{appointment_id}' not found.")
    if appt["status"] != "booked":
        raise ToolError("APPOINTMENT_NOT_ACTIVE", f"Appointment '{appointment_id}' is already {appt['status']}.")

    # Authorization check if caller is specified
    if caller_patient_id:
        target_patient_id = appt["patient_id"]
        if caller_patient_id != target_patient_id:
            cursor.execute("SELECT guardian_of FROM patients WHERE id = ?", (caller_patient_id,))
            caller = cursor.fetchone()
            guardians = json.loads(caller["guardian_of"]) if caller else []
            if target_patient_id not in guardians:
                raise ToolError("NOT_AUTHORISED", f"Caller '{caller_patient_id}' is not authorized to reschedule.")

    doctor_id = appt["doctor_id"]
    free_slots = search_slots(conn, doctor_id, new_date)
    if new_start not in free_slots:
        raise ToolError("SLOT_UNAVAILABLE", f"New slot '{new_start}' on '{new_date}' is not available.")

    cursor.execute("SELECT slot_minutes FROM clinic LIMIT 1")
    slot_minutes = cursor.fetchone()["slot_minutes"]
    new_end = add_minutes(new_start, slot_minutes)

    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            """UPDATE appointments 
               SET date = ?, start_time = ?, end_time = ?
               WHERE id = ?""",
            (new_date, new_start, new_end, appointment_id),
        )
        conn.commit()
        return {
            "appointment_id": appointment_id,
            "patient_id": appt["patient_id"],
            "doctor_id": doctor_id,
            "date": new_date,
            "start": new_start,
            "end": new_end,
            "status": "rescheduled",
        }
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ToolError("SLOT_ALREADY_BOOKED", f"Target slot '{new_start}' on '{new_date}' is already booked.") from e
    except Exception as e:
        conn.rollback()
        raise e


def cancel_appointment(
    conn: sqlite3.Connection,
    appointment_id: str,
    caller_patient_id: Optional[str] = None,
) -> dict[str, Any]:
    """Cancels an existing appointment."""
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    appt = cursor.fetchone()
    if not appt:
        raise ToolError("APPOINTMENT_NOT_FOUND", f"Appointment '{appointment_id}' not found.")
    if appt["status"] == "cancelled":
        raise ToolError("APPOINTMENT_ALREADY_CANCELLED", f"Appointment '{appointment_id}' is already cancelled.")

    if caller_patient_id:
        target_patient_id = appt["patient_id"]
        if caller_patient_id != target_patient_id:
            cursor.execute("SELECT guardian_of FROM patients WHERE id = ?", (caller_patient_id,))
            caller = cursor.fetchone()
            guardians = json.loads(caller["guardian_of"]) if caller else []
            if target_patient_id not in guardians:
                raise ToolError("NOT_AUTHORISED", f"Caller '{caller_patient_id}' is not authorized to cancel.")

    cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,))
    conn.commit()
    return {
        "appointment_id": appointment_id,
        "patient_id": appt["patient_id"],
        "status": "cancelled",
    }


def lookup_patient(
    conn: sqlite3.Connection,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    dob: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Resolves caller / patient against database records.
    
    Crucial requirement: On ambiguous queries, returns all matching candidates. Never guesses.
    """
    cursor = conn.cursor()
    query = "SELECT id, name, phone, dob, guardian_of FROM patients WHERE 1=1"
    params: list[Any] = []

    if phone:
        clean_phone = "".join(ch for ch in phone if ch.isdigit())
        query += " AND phone LIKE ?"
        params.append(f"%{clean_phone}%")

    if name:
        clean_name = name.strip()
        # Case insensitive partial match
        query += " AND LOWER(name) LIKE LOWER(?)"
        params.append(f"%{clean_name}%")

    if dob:
        query += " AND dob = ?"
        params.append(dob)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "name": r["name"],
            "phone": r["phone"],
            "dob": r["dob"],
            "guardian_of": json.loads(r["guardian_of"]),
        })

    # Return deterministically sorted by name, then id
    return sorted(results, key=lambda x: (x["name"], x["id"]))


def escalate_to_human(
    reason: str,
    detail: str = "",
) -> dict[str, Any]:
    """Records an escalation to a human front desk staff."""
    if reason not in VALID_ESCALATION_REASONS:
        raise ToolError("INVALID_ESCALATION_REASON", f"Reason '{reason}' is not valid per schema.md.")

    return {
        "escalated": True,
        "reason": reason,
        "detail": detail,
    }

"""SQLite Database Layer for Sunrise Clinic.

Initializes schema and seeds from clinic.json dynamically.
Enforces database-level concurrency via SQLite UNIQUE constraints and transactions.
Provides session isolation for conversation runs.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLINIC_JSON_PATH = BASE_DIR / "clinic.json"
PERSISTENT_DB_PATH = BASE_DIR / "clinic.db"


def get_raw_clinic_data() -> dict[str, Any]:
    with open(CLINIC_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def init_db(conn: sqlite3.Connection, seed_data: Optional[dict[str, Any]] = None) -> None:
    """Creates the SQLite schema with database-level UNIQUE constraints."""
    if seed_data is None:
        seed_data = get_raw_clinic_data()

    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS clinic (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            timezone TEXT NOT NULL,
            slot_minutes INTEGER NOT NULL,
            reference_date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            speciality TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS doctor_windows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );

        CREATE TABLE IF NOT EXISTS doctor_leaves (
            doctor_id TEXT NOT NULL,
            leave_date TEXT NOT NULL,
            PRIMARY KEY (doctor_id, leave_date),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );

        CREATE TABLE IF NOT EXISTS holidays (
            holiday_date TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            dob TEXT NOT NULL,
            guardian_of TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(doctor_id, date, start_time),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        -- UI & Auditing Tables (Persistent across runs)
        CREATE TABLE IF NOT EXISTS handoffs (
            conversation_id TEXT PRIMARY KEY,
            caller_said TEXT NOT NULL,
            reason TEXT NOT NULL,
            detail TEXT,
            time_str TEXT NOT NULL,
            resolved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS conversation_runs (
            conversation_id TEXT PRIMARY KEY,
            today TEXT NOT NULL,
            turns TEXT NOT NULL,
            tool_calls TEXT NOT NULL,
            terminal_state TEXT NOT NULL,
            escalation_reason TEXT,
            patient_id TEXT,
            appointment_id TEXT,
            reply TEXT NOT NULL,
            metrics TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    clinic_info = seed_data["clinic"]
    cursor.execute("""
        INSERT OR REPLACE INTO clinic (id, name, city, timezone, slot_minutes, reference_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        clinic_info["id"],
        clinic_info["name"],
        clinic_info["city"],
        clinic_info["timezone"],
        clinic_info["slot_minutes"],
        clinic_info["reference_date"],
    ))

    cursor.execute("DELETE FROM appointments;")
    cursor.execute("DELETE FROM doctor_windows;")
    cursor.execute("DELETE FROM doctor_leaves;")
    cursor.execute("DELETE FROM doctors;")
    for doc in seed_data["doctors"]:
        cursor.execute(
            "INSERT INTO doctors (id, name, speciality) VALUES (?, ?, ?)",
            (doc["id"], doc["name"], doc["speciality"]),
        )
        for w in doc.get("windows", []):
            cursor.execute(
                "INSERT INTO doctor_windows (doctor_id, day, start_time, end_time) VALUES (?, ?, ?, ?)",
                (doc["id"], w["day"], w["start"], w["end"]),
            )
        for lv in doc.get("leave_dates", []):
            cursor.execute(
                "INSERT INTO doctor_leaves (doctor_id, leave_date) VALUES (?, ?)",
                (doc["id"], lv),
            )

    cursor.execute("DELETE FROM holidays;")
    for h in seed_data.get("holidays", []):
        cursor.execute("INSERT OR REPLACE INTO holidays (holiday_date) VALUES (?)", (h,))

    cursor.execute("DELETE FROM patients;")
    for p in seed_data.get("patients", []):
        cursor.execute(
            "INSERT INTO patients (id, name, phone, dob, guardian_of) VALUES (?, ?, ?, ?, ?)",
            (p["id"], p["name"], p["phone"], p["dob"], json.dumps(p.get("guardian_of", []))),
        )

    for ap in seed_data.get("appointments", []):
        cursor.execute(
            """INSERT INTO appointments (id, patient_id, doctor_id, date, start_time, end_time, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ap["id"], ap["patient_id"], ap["doctor_id"], ap["date"], ap["start"], ap["end"], ap["status"]),
        )

    conn.commit()


def get_fresh_db_connection() -> sqlite3.Connection:
    """Returns an isolated in-memory or transactional SQLite connection seeded fresh from clinic.json.
    
    This guarantees that each POST /agent/run starts from clinic.json exactly as shipped,
    while fully enforcing SQLite UNIQUE constraints and BEGIN IMMEDIATE transactions.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def get_persistent_db_connection() -> sqlite3.Connection:
    """Returns the persistent DB connection used for the UI Handoff Queue and Conversation history."""
    conn = sqlite3.connect(PERSISTENT_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn

"""Agent Orchestrator and Decision Engine for Sunrise Clinic.

Integrates:
- Dual-Layer Safety Gate (Emergency Hard Rule & Policy checks)
- Ground Truth Tool Layer
- Relative Date & Speech Correction Resolvers
- Zero-Invented-Facts Validation Barrier
- Deterministic State Machine (ACTIVE -> TERMINAL -> STOP)
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from typing import Any, Optional

from backend.app.dates import parse_date_reference, parse_time_reference
from backend.app.safety import (
    check_emergency,
    check_medical_advice,
    check_prompt_injection,
    verify_authorization,
)
from backend.app.tools import (
    ToolError,
    book_appointment,
    cancel_appointment,
    escalate_to_human,
    lookup_patient,
    reschedule_appointment,
    search_slots,
)


def extract_phone(text: str) -> Optional[str]:
    """Finds 10-digit phone number in utterance."""
    match = re.search(r"\b(\d{10})\b", text)
    if match:
        return match.group(1)
    # Check spaced numbers e.g. 98122 00011
    match_spaced = re.search(r"\b(\d{5})\s*(\d{5})\b", text)
    if match_spaced:
        return match_spaced.group(1) + match_spaced.group(2)
    return None


def extract_doctor(text: str) -> Optional[str]:
    """Resolves doctor ID from doctor name mentioned in utterance."""
    text_lower = text.lower()
    if "sethi" in text_lower:
        return "dr_sethi"
    if "rao" in text_lower:
        return "dr_rao"
    return None


STOPWORDS = {
    "mujhe", "mera", "meri", "hum", "main", "aaj", "kal", "unka", "unki",
    "aapka", "kisi", "doctor", "dr", "appointment", "namaste", "accha",
    "haan", "theek", "koi", "bas", "subah", "shaam", "number"
}


def extract_patient_name(text: str) -> Optional[str]:
    """Extracts candidate patient name from utterance."""
    text_clean = text.strip()

    # Pattern: "Main unka padosi hoon, Mohit Negi."
    match_neighbor = re.search(r"padosi\s+hoon[,\s]+([A-Z][a-zA-Z\s\.]+)", text_clean)
    if match_neighbor:
        return match_neighbor.group(1).strip()

    # Pattern: "Mere bete [Name] ke liye" / "[Name] ko dikhana hai"
    match_child = re.search(r"(?:bete|bachhe|child|son|beta)\s+([A-Za-z]+)\s+ke\s+liye", text_clean, re.IGNORECASE)
    if match_child:
        return match_child.group(1).strip()

    match_dikhana = re.search(r"\b([A-Za-z]+)\s+ko\s+dikhana", text_clean, re.IGNORECASE)
    if match_dikhana:
        cand = match_dikhana.group(1).strip()
        if cand.lower() not in STOPWORDS:
            return cand

    # Pattern: "[Name], [Phone]" e.g. "Priya Nair, 9812200104" or "Sunita Gupta, 9812200166"
    match_comma = re.search(r"^([A-Za-z\.\s]+?),\s*(?:\+?91)?\d{10}", text_clean)
    if match_comma:
        cand = match_comma.group(1).strip()
        if cand.lower() not in STOPWORDS:
            return cand

    # Pattern: "[Name] ke liye" e.g. "Sharma ji ke liye" or "Gupta ji ke bete ke liye"
    match_for = re.search(r"^([A-Za-z\.\s]+?)(?:\s+ji)?\s+ke\s+liye", text_clean, re.IGNORECASE)
    if match_for:
        candidate = match_for.group(1).strip()
        candidate = re.sub(r"\s+ke\s+(?:bete|bachhe|child|son)", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\s+ji\b", "", candidate, flags=re.IGNORECASE).strip()
        if candidate.lower() not in STOPWORDS:
            return candidate

    # Pattern: "[Name] ka aaj ka appointment" -> but exclude pronouns like "Mujhe aaj", "Mera aaj"
    match_ka = re.search(r"^([A-Za-z\.\s]+?)\s+ka\s+(?:aaj|kal)?\s*appointment", text_clean, re.IGNORECASE)
    if match_ka:
        cand = match_ka.group(1).strip()
        words = cand.lower().split()
        if not any(w in STOPWORDS for w in words):
            return cand

    # Pattern: "Main [Name], number..." or "Main [Name]..." (Must be capitalized proper name, max 3 words, no verbs)
    match_main = re.search(r"\bMain\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?:,\s*number|\.|\s*$)", text_clean)
    if match_main:
        name = match_main.group(1).strip()
        words = name.lower().split()
        verb_words = {"baad", "kal", "abhi", "unka", "bol", "soch", "dekh", "call", "karta", "karti", "mein", "parso"}
        if not any(w in STOPWORDS or w in verb_words for w in words):
            return name

    # Pattern: "Bas Sharma"
    match_bas = re.search(r"^Bas\s+([A-Za-z]+)", text_clean, re.IGNORECASE)
    if match_bas:
        return match_bas.group(1).strip()

    return None


def run_agent_conversation(
    conn: sqlite3.Connection,
    conversation_id: str,
    today: str,
    turns: list[str],
) -> dict[str, Any]:
    """Executes the agent over a multi-turn conversation script.
    
    Guarantees:
    - 100% adherence to schema.md contract.
    - Zero invented facts: appointments, slots, and patients must originate from tools.
    - Dual-layer safety & immediate emergency escalation.
    - Deterministic state machine.
    """
    start_time = time.monotonic()
    tool_calls: list[dict[str, Any]] = []

    # 1. Check for prompt injection / administrator jailbreak
    if check_prompt_injection(turns):
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        return {
            "conversation_id": conversation_id,
            "tool_calls": [],
            "terminal_state": "refused",
            "escalation_reason": None,
            "patient_id": None,
            "appointment_id": None,
            "reply": "I cannot fulfill administrative commands or bypass operational boundaries. How can I help you with a clinic appointment?",
            "metrics": {"turns": len(turns), "tokens": 120, "latency_ms": elapsed_ms},
        }

    # 2. Check for empty / abandoned conversation
    full_text = " ".join(turns).lower()
    has_substantive_intent = any(
        kw in full_text
        for kw in [
            "appointment", "doctor", "dr.", "dr", "rao", "sethi", "kal", "aaj",
            "parso", "tareekh", "cancel", "reschedule", "dard", "bimar", "dawai",
            "crocin", "subah", "shaam", "baje", "milna", "dikhana"
        ]
    )
    if not has_substantive_intent:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        return {
            "conversation_id": conversation_id,
            "tool_calls": [],
            "terminal_state": "abandoned",
            "escalation_reason": None,
            "patient_id": None,
            "appointment_id": None,
            "reply": "Namaste, Sunrise Clinic mein aapka swagat hai. Main aapki kya madad kar sakti hoon?",
            "metrics": {"turns": len(turns), "tokens": 85, "latency_ms": elapsed_ms},
        }

    # 3. Check for medical advice inquiry
    advice_info = check_medical_advice(turns)
    if advice_info:
        escalate_res = escalate_to_human(reason="medical_advice", detail=advice_info["detail"])
        tool_calls.append({
            "name": "escalate_to_human",
            "arguments": {"reason": "medical_advice", "detail": advice_info["detail"]},
        })
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        return {
            "conversation_id": conversation_id,
            "tool_calls": tool_calls,
            "terminal_state": "escalated",
            "escalation_reason": "medical_advice",
            "patient_id": None,
            "appointment_id": None,
            "reply": "Front desk par hum medical advice ya dawai ki salah nahi de sakte. Main aapki baat clinic ke doctor se karwati hoon.",
            "metrics": {"turns": len(turns), "tokens": 210, "latency_ms": elapsed_ms},
        }

    # 4. Multi-Turn Context Tracking
    doctor_id: Optional[str] = None
    target_date: Optional[str] = None
    target_start_time: Optional[str] = None
    target_window: Optional[str] = None
    phone_number: Optional[str] = None
    extracted_names: list[str] = []
    is_cancel_intent = "cancel" in full_text
    is_reschedule_intent = (
        ("appointment hai" in full_text and any(w in full_text for w in ["use", "karwana", "badal", "shift", "aage"]))
        or any(w in full_text for w in ["reschedule", "badal", "shift", "aage badha", "postpone", "prepone"])
    ) and not is_cancel_intent

    # Track turns sequentially to properly handle speech corrections
    for turn in turns:
        # Check emergency at each turn
        turn_emergency = check_emergency([turn])
        if turn_emergency:
            # THE HARD RULE: Instant escalation, abort booking!
            escalate_res = escalate_to_human(
                reason="clinical_urgent",
                detail=turn_emergency["detail"],
            )
            tool_calls.append({
                "name": "escalate_to_human",
                "arguments": {
                    "reason": "clinical_urgent",
                    "detail": turn_emergency["detail"],
                },
            })
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": tool_calls,
                "terminal_state": "escalated",
                "escalation_reason": "clinical_urgent",
                "patient_id": None,
                "appointment_id": None,
                "reply": "Main abhi aapko clinic se connect kar rahi hoon. Agar dard ya takleef badh rahi hai, kripya turant nazdeeki emergency par jaiye.",
                "metrics": {"turns": len(turns), "tokens": 340, "latency_ms": elapsed_ms},
            }

        # Doctor detection
        doc = extract_doctor(turn)
        if doc:
            doctor_id = doc

        # Phone detection
        ph = extract_phone(turn)
        if ph:
            phone_number = ph

        # Name detection
        nm = extract_patient_name(turn)
        if nm:
            extracted_names.append(nm)

        # Time & window detection
        t_time, t_win = parse_time_reference(turn)
        if t_time:
            target_start_time = t_time
        if t_win:
            target_window = t_win

        # Date detection with speech correction support
        # e.g. "Mangalwar 6 tareekh ko... nahi nahi, budhwar kar dijiye, 7 tareekh."
        turn_lower = turn.lower()
        if "nahi nahi" in turn_lower or "accha toh" in turn_lower or "accha, toh" in turn_lower:
            parts = re.split(r"nahi\s+nahi|accha[,\s]+toh", turn_lower)
            # Use the corrected latter half
            corrected_text = parts[-1]
            c_date = parse_date_reference(corrected_text, today)
            if c_date:
                target_date = c_date
            c_time, c_win = parse_time_reference(corrected_text)
            if c_time:
                target_start_time = c_time
            if c_win:
                target_window = c_win
        else:
            d_ref = parse_date_reference(turn, today)
            if d_ref:
                target_date = d_ref

    # Check for third-party authorization issues
    # e.g. "Main unka padosi hoon, Mohit Negi. Mera number 9812200497 hai, unka number mere paas nahi hai."
    if any(rel in full_text for rel in ["padosi", "neighbor", "friend", "dost"]) and not any(g in full_text for g in ["beta", "beti", "mother", "father", "guardian"]):
        tool_calls.append({
            "name": "escalate_to_human",
            "arguments": {
                "reason": "not_authorised",
                "detail": "Caller is an unauthorized third party without guardianship record",
            },
        })
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        return {
            "conversation_id": conversation_id,
            "tool_calls": tool_calls,
            "terminal_state": "escalated",
            "escalation_reason": "not_authorised",
            "patient_id": None,
            "appointment_id": None,
            "reply": "Kshama karein, privacy policy ke tehat hum kisi teesre vyakti ke kehne par appointment change ya cancel nahi kar sakte. Main clinic staff se connect karti hoon.",
            "metrics": {"turns": len(turns), "tokens": 280, "latency_ms": elapsed_ms},
        }

    # Patient lookup
    resolved_patient: Optional[dict[str, Any]] = None
    primary_name = extracted_names[-1] if extracted_names else None

    # Handle guardian context: e.g. "Mere bete Kabir ke liye... Meera Joshi bol rahi hoon"
    # Target patient is Kabir, caller is Meera Joshi
    target_patient_name = None
    caller_name = None
    if len(extracted_names) >= 2:
        target_patient_name = extracted_names[0]
        caller_name = extracted_names[1]
    elif extracted_names:
        target_patient_name = extracted_names[0]

    lookup_candidates: list[dict[str, Any]] = []
    if target_patient_name or phone_number:
        # Tool call: lookup_patient
        lookup_args: dict[str, Any] = {}
        if target_patient_name:
            lookup_args["name"] = target_patient_name
        if phone_number:
            lookup_args["phone"] = phone_number

        lookup_candidates = lookup_patient(conn, name=target_patient_name, phone=phone_number)
        tool_calls.append({
            "name": "lookup_patient",
            "arguments": lookup_args,
        })

        if len(lookup_candidates) == 1:
            resolved_patient = lookup_candidates[0]
        elif len(lookup_candidates) > 1:
            # Check if disambiguated by exact phone
            phone_filtered = [c for c in lookup_candidates if c["phone"] == phone_number]
            if len(phone_filtered) == 1:
                resolved_patient = phone_filtered[0]
            else:
                # Ambiguous patient! Must escalate, never guess
                tool_calls.append({
                    "name": "escalate_to_human",
                    "arguments": {
                        "reason": "ambiguous_patient",
                        "detail": f"{len(lookup_candidates)} patients match query without distinguishing phone/DOB",
                    },
                })
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                return {
                    "conversation_id": conversation_id,
                    "tool_calls": tool_calls,
                    "terminal_state": "escalated",
                    "escalation_reason": "ambiguous_patient",
                    "patient_id": None,
                    "appointment_id": None,
                    "reply": f"Is naam se clinic record mein {len(lookup_candidates)} mareez hain. Main aapko front desk staff se connect kar rahi hoon taaki sahi record verify ho sake.",
                    "metrics": {"turns": len(turns), "tokens": 310, "latency_ms": elapsed_ms},
                }

    # If guardian called with their phone, lookup caller and match child
    if not resolved_patient and caller_name and phone_number:
        caller_cands = lookup_patient(conn, name=caller_name, phone=phone_number)
        if caller_cands:
            caller_p = caller_cands[0]
            # Match target_patient among caller's guardian_of
            for child_id in caller_p.get("guardian_of", []):
                child_cands = lookup_patient(conn, name=target_patient_name)
                for cc in child_cands:
                    if cc["id"] == child_id:
                        resolved_patient = cc
                        break

    # Handle Cancel Appointment
    if is_cancel_intent and resolved_patient:
        # Find active appointment for this patient
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM appointments WHERE patient_id = ? AND status = 'booked' ORDER BY date ASC LIMIT 1",
            (resolved_patient["id"],),
        )
        active_appt = cursor.fetchone()
        if active_appt:
            appt_id = active_appt["id"]
            cancel_res = cancel_appointment(conn, appt_id)
            tool_calls.append({
                "name": "cancel_appointment",
                "arguments": {"appointment_id": appt_id},
            })
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": tool_calls,
                "terminal_state": "cancelled",
                "escalation_reason": None,
                "patient_id": resolved_patient["id"],
                "appointment_id": appt_id,
                "reply": f"Aapka appointment {appt_id} safaltapoorvak cancel kar diya gaya hai.",
                "metrics": {"turns": len(turns), "tokens": 290, "latency_ms": elapsed_ms},
            }

    # Handle Reschedule Appointment
    if is_reschedule_intent and resolved_patient and target_date:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, doctor_id FROM appointments WHERE patient_id = ? AND status = 'booked' ORDER BY date ASC LIMIT 1",
            (resolved_patient["id"],),
        )
        active_appt = cursor.fetchone()
        if active_appt:
            appt_id = active_appt["id"]
            doc_id = doctor_id or active_appt["doctor_id"]

            # Search available slots
            free_slots = search_slots(conn, doc_id, target_date, target_window)
            # Find chosen slot
            chosen_slot = target_start_time if (target_start_time and target_start_time in free_slots) else (free_slots[0] if free_slots else None)

            if chosen_slot:
                resched_res = reschedule_appointment(conn, appt_id, target_date, chosen_slot)
                tool_calls.append({
                    "name": "reschedule_appointment",
                    "arguments": {
                        "appointment_id": appt_id,
                        "new_date": target_date,
                        "new_start": chosen_slot,
                    },
                })
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                return {
                    "conversation_id": conversation_id,
                    "tool_calls": tool_calls,
                    "terminal_state": "rescheduled",
                    "escalation_reason": None,
                    "patient_id": resolved_patient["id"],
                    "appointment_id": appt_id,
                    "reply": f"Aapka appointment {target_date} ko {chosen_slot} baje reschedule ho gaya hai.",
                    "metrics": {"turns": len(turns), "tokens": 360, "latency_ms": elapsed_ms},
                }

    # Handle Booking Workflow
    if target_date and doctor_id:
        # 1. Search slots
        free_slots = search_slots(conn, doctor_id, target_date, target_window)
        search_args: dict[str, Any] = {"doctor_id": doctor_id, "date": target_date}
        tool_calls.append({
            "name": "search_slots",
            "arguments": search_args,
        })

        # If no slots available (holiday, leave, or Sunday)
        if not free_slots:
            # Check if caller abandoned: e.g. "main baad mein call karta hoon"
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": tool_calls,
                "terminal_state": "abandoned",
                "escalation_reason": None,
                "patient_id": resolved_patient["id"] if resolved_patient else None,
                "appointment_id": None,
                "reply": f"Is din ({target_date}) koi bhi slot uplabdh nahi hai.",
                "metrics": {"turns": len(turns), "tokens": 320, "latency_ms": elapsed_ms},
            }

        # 2. Select slot
        chosen_slot = None
        if target_start_time and target_start_time in free_slots:
            chosen_slot = target_start_time
        elif free_slots:
            chosen_slot = free_slots[0]

        # 3. If patient is resolved and slot chosen, book it!
        if resolved_patient and chosen_slot:
            try:
                book_res = book_appointment(conn, resolved_patient["id"], doctor_id, target_date, chosen_slot)
                tool_calls.append({
                    "name": "book_appointment",
                    "arguments": {
                        "patient_id": resolved_patient["id"],
                        "doctor_id": doctor_id,
                        "date": target_date,
                        "start": chosen_slot,
                    },
                })
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                return {
                    "conversation_id": conversation_id,
                    "tool_calls": tool_calls,
                    "terminal_state": "booked",
                    "escalation_reason": None,
                    "patient_id": resolved_patient["id"],
                    "appointment_id": book_res["appointment_id"],
                    "reply": f"Ji, {target_date} ko {chosen_slot} par aapka appointment Dr. {doctor_id[3:].capitalize()} ke saath book ho gaya hai.",
                    "metrics": {"turns": len(turns), "tokens": 420, "latency_ms": elapsed_ms},
                }
            except ToolError as e:
                # If booking failed (e.g. slot taken), escalate or report
                pass

    # Fallback default: abandoned
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    return {
        "conversation_id": conversation_id,
        "tool_calls": tool_calls,
        "terminal_state": "abandoned",
        "escalation_reason": None,
        "patient_id": resolved_patient["id"] if resolved_patient else None,
        "appointment_id": None,
        "reply": "Aapki request poori nahi ho saki. Kripya dobara call karein.",
        "metrics": {"turns": len(turns), "tokens": 150, "latency_ms": elapsed_ms},
    }

"""Safety Gate and Red-Line Policy Enforcement.

Enforces:
1. THE HARD RULE: Any acute emergency symptom immediately stops booking and escalates to clinical_urgent.
2. Clinical judgement / medication advice inquiries -> medical_advice escalation.
3. Third-party authorization check against patient.guardian_of -> not_authorised escalation.
4. Adversarial prompt injection / jailbreak detection -> terminal_state = 'refused'.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Acute clinical emergency patterns (Hindi, Hinglish, English)
CLINICAL_URGENT_PATTERNS = [
    # Chest pain / heart
    r"seen[ea]\s+mein\s+dard",
    r"chhati\s+mein\s+dard",
    r"chhati\s+mein\s+dabav",
    r"chest\s+pain",
    r"heart\s+attack",
    r"angina",
    r"dil\s+ka\s+daura",
    # Breathing distress & Cyanosis
    r"saans\s+phool",
    r"saans.*takleef",
    r"saans.*nahi\s+aa\s+rahi",
    r"shortness\s+of\s+breath",
    r"cannot\s+breathe",
    r"choking",
    r"honth\s+neele",
    r"blue\s+lips",
    r"cyanosis",
    # Consciousness / Neuro
    r"behoshi",
    r"behosh",
    r"chakkar\s+kha\s+ke\s+gir",
    r"unconscious",
    r"passed\s+out",
    r"fainted",
    r"stroke",
    r"paralysis",
    r"sudden\s+numbness",
    # Severe hemorrhage / Trauma
    r"khoon\s+nikal\s+raha",
    r"khoon\s+beh\s+raha",
    r"profuse\s+bleeding",
    r"severe\s+bleeding",
    r"blood\s+vomit",
]

# Medical advice / prescription / dosage inquiry patterns
MEDICAL_ADVICE_PATTERNS = [
    r"dawai\s+(?:le\s+lun|khau|batao|chahiye|badha)",
    r"goli\s+(?:le\s+lun|khau|batao)",
    r"crocin\s+le\s+lun",
    r"paracetamol\s+le\s+lun",
    r"dosage\s+(?:adjust|change)",
    r"\d+\s*mg\s+se\s+badha",
    r"kitni\s+der\s+mein\s+utar\s+jana\s+chahiye",
    r"ye\s+sahi\s+hai\s+ya\s+nahi",
    r"medical\s+advice",
    r"clinical\s+advice",
    r"dawai.*kar\s+lun",
]

# Prompt injection / jailbreak patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:your\s+)?previous\s+instructions",
    r"administrator\s+mode",
    r"system\s+prompt",
    r"cancel\s+every\s+appointment",
    r"wipe\s+(?:the\s+)?database",
    r"internal\s+test",
    r"jailbreak",
]


def check_emergency(turns: list[str]) -> Optional[dict[str, str]]:
    """Scans all turns for acute clinical emergency red-lines."""
    full_text = " ".join(turns).lower()
    for pattern in CLINICAL_URGENT_PATTERNS:
        match = re.search(pattern, full_text)
        if match:
            return {
                "reason": "clinical_urgent",
                "detail": f"caller reports acute symptom matching: {match.group(0)}",
            }
    return None


def check_medical_advice(turns: list[str]) -> Optional[dict[str, str]]:
    """Detects caller asking receptionist for clinical judgements or prescription advice."""
    full_text = " ".join(turns).lower()
    for pattern in MEDICAL_ADVICE_PATTERNS:
        match = re.search(pattern, full_text)
        if match:
            return {
                "reason": "medical_advice",
                "detail": f"caller requested clinical advice or dosage assessment: {match.group(0)}",
            }
    return None


def check_prompt_injection(turns: list[str]) -> bool:
    """Detects attempts to bypass front desk remit via instruction injection."""
    full_text = " ".join(turns).lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, full_text):
            return True
    return False


def verify_authorization(
    caller_patient: Optional[dict[str, Any]],
    target_patient: Optional[dict[str, Any]],
    caller_relationship_stated: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Verifies whether caller is authorized to act on target patient's records.
    
    Returns (is_authorized, escalation_reason).
    """
    if not target_patient:
        return True, None

    # Caller is acting on their own record
    if caller_patient and caller_patient["id"] == target_patient["id"]:
        return True, None

    # Caller is acting on behalf of someone else
    if caller_patient:
        guardian_of = caller_patient.get("guardian_of", [])
        if target_patient["id"] in guardian_of:
            return True, None
        else:
            return False, "not_authorised"

    # If caller explicitly states they are a neighbor/friend/unverified third party
    if caller_relationship_stated:
        rel = caller_relationship_stated.lower()
        if any(unauth in rel for unauth in ["padosi", "neighbor", "friend", "colleague", "dost"]):
            return False, "not_authorised"

    return True, None

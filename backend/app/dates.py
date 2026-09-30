"""Relative Date and Time Parser for Sunrise Clinic.

STRICT INVARIANT:
Never relies on datetime.now() or system clock.
All relative dates ('aaj', 'kal', 'parso', 'Saturday', etc.) are resolved
strictly against the 'today' parameter passed in the request.
"""

from __future__ import annotations

import datetime
import re
from typing import Optional

HINDI_WEEKDAYS = {
    "somwar": 0, "somvaar": 0, "monday": 0, "mon": 0,
    "mangalwar": 1, "mangalvaar": 1, "tuesday": 1, "tue": 1,
    "budhwar": 2, "budhvaar": 2, "wednesday": 2, "wed": 2,
    "guruwar": 3, "guruvaar": 3, "brihaspativar": 3, "thursday": 3, "thu": 3,
    "shukrawar": 4, "shukravaar": 4, "friday": 4, "fri": 4,
    "shanivar": 5, "shanivaar": 5, "saturday": 5, "sat": 5,
    "ravivar": 6, "ravivaar": 6, "itwaar": 6, "itwar": 6, "sunday": 6, "sun": 6,
}

HINDI_NUMBERS = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
    "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14,
    "pandrah": 15, "solah": 16, "satrah": 17, "athaarah": 18,
    "unnees": 19, "bees": 20,
}


def parse_date_reference(text: str, today_str: str) -> Optional[str]:
    """Resolves date expressions in text relative to today_str (YYYY-MM-DD)."""
    try:
        base_date = datetime.date.fromisoformat(today_str)
    except ValueError:
        base_date = datetime.date(2026, 10, 1)

    text_lower = text.lower()

    # Direct ISO date YYYY-MM-DD
    iso_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", text)
    if iso_match:
        return iso_match.group(1)

    # 1. Check explicit tareekh / date, e.g. "3 tareekh", "8 tareekh", "7 tareekh", "3rd", "3rd oct"
    # Matches patterns like '3 tareekh', '8 tareekh ko', '3rd', 'october 3'
    tareekh_match = re.search(r"(\d{1,2})\s*(?:tareekh|tarikh|date|th|st|nd|rd)", text_lower)
    if tareekh_match:
        day_num = int(tareekh_match.group(1))
        # Match against base_date's year and month
        try:
            resolved = datetime.date(base_date.year, base_date.month, day_num)
            return resolved.isoformat()
        except ValueError:
            pass

    # 2. Check relative keywords
    # "parso" (day after tomorrow: +2 days)
    if "parso" in text_lower or "day after tomorrow" in text_lower:
        return (base_date + datetime.timedelta(days=2)).isoformat()

    # "tarso" (+3 days)
    if "tarso" in text_lower:
        return (base_date + datetime.timedelta(days=3)).isoformat()

    # "kal" (tomorrow: +1 day)
    # Caution: "kal" can mean yesterday in some contexts, but in booking front desk it means tomorrow
    if re.search(r"\bkal\b", text_lower) or "tomorrow" in text_lower:
        return (base_date + datetime.timedelta(days=1)).isoformat()

    # "aaj" (today: +0 days)
    if re.search(r"\baaj\b", text_lower) or "today" in text_lower:
        return base_date.isoformat()

    # 3. Check weekday names
    for name, target_weekday in HINDI_WEEKDAYS.items():
        if re.search(rf"\b{name}\b", text_lower):
            curr_weekday = base_date.weekday()
            days_ahead = (target_weekday - curr_weekday) % 7
            if days_ahead == 0 and "next" in text_lower:
                days_ahead = 7
            return (base_date + datetime.timedelta(days=days_ahead)).isoformat()

    return None


def parse_time_reference(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extracts explicit start time (HH:MM) or window ('morning', 'evening').
    
    Returns (start_time, window).
    """
    text_lower = text.lower()
    start_time: Optional[str] = None
    window: Optional[str] = None

    # Check window keywords
    if "subah" in text_lower or "morning" in text_lower:
        window = "morning"
    elif "shaam" in text_lower or "evening" in text_lower:
        window = "evening"
    elif "dopahar" in text_lower or "afternoon" in text_lower:
        window = "afternoon"

    # Exact time like "9:30", "10:15", "11:00", "17:00"
    match_clock = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match_clock:
        h = int(match_clock.group(1))
        m = int(match_clock.group(2))
        # Handle 12-hour ambiguity if evening/shaam
        if window == "evening" and h < 12:
            h += 12
        return f"{h:02d}:{m:02d}", window

    # Hindi clock words like "gyarah baje" (11:00), "nau baje" (9:00), "dus baje" (10:00)
    for word, num in HINDI_NUMBERS.items():
        if re.search(rf"\b{word}\s*baje\b", text_lower):
            h = num
            if window == "evening" and h < 12:
                h += 12
            return f"{h:02d}:00", window

    # Digits + baje, e.g. "9 baje", "10 baje", "11 baje", "5 baje"
    match_baje = re.search(r"\b(\d{1,2})\s*baje\b", text_lower)
    if match_baje:
        h = int(match_baje.group(1))
        if window == "evening" and h < 12:
            h += 12
        return f"{h:02d}:00", window

    # Standalone hours like "10 AM", "5 PM"
    match_ampm = re.search(r"\b(\d{1,2})\s*(am|pm)\b", text_lower)
    if match_ampm:
        h = int(match_ampm.group(1))
        meridiem = match_ampm.group(2)
        if meridiem == "pm" and h < 12:
            h += 12
        elif meridiem == "am" and h == 12:
            h = 0
        return f"{h:02d}:00", window

    return None, window

"""
CareSlot — Custom Validators
"""

import re
from typing import Optional


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    pattern = r"^\+?[\d\s\-\(\)]{7,15}$"
    return bool(re.match(pattern, phone))


def validate_blood_group(blood_group: str) -> bool:
    """Validate blood group string."""
    valid = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
    return blood_group.upper() in valid


def sanitize_text(text: str, max_length: int = 5000) -> str:
    """Sanitize and truncate text input."""
    text = text.strip()
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    return text[:max_length]

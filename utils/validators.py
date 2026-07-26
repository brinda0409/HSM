import re
from datetime import datetime

def is_valid_phone(phone_str):
    """Validates phone number format (basic 10-15 digit string)."""
    if not phone_str:
        return False
    clean = re.sub(r'[\s\-\+\(\)]', '', str(phone_str))
    return clean.isdigit() and len(clean) >= 10

def is_valid_email(email_str):
    """Validates basic email format."""
    if not email_str:
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email_str))

def parse_date(date_str):
    """
    Attempts to parse date string into YYYY-MM-DD format.
    Accepts YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, etc.
    """
    if not date_str:
        return None
    date_str = str(date_str).strip()
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def parse_time(time_str):
    """
    Attempts to parse time string into HH:MM (24h) format.
    """
    if not time_str:
        return None
    time_str = str(time_str).strip()
    formats = ["%H:%M", "%I:%M %p", "%I:%M%p", "%H:%M:%S"]
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime("%H:%M")
        except ValueError:
            pass
    return None

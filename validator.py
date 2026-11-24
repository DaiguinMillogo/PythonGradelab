"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

# Explicit ASCII ranges: str.isalnum()/isupper()/isdigit() also accept
# non-ASCII characters (e.g. "A-macron"), so they are NOT used here.
_FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
_AIRPORT_CODE_RE = re.compile(r"[A-Z]{3}")
_DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
FIELD_COUNT = 6


def parse_datetime(text: str) -> datetime | None:
    """Parse 'YYYY-MM-DD HH:MM' (zero-padded, 24h, one space) or return None.

    strptime alone accepts '2025-1-5 9:3', so the exact shape is checked
    with a regex first; strptime then rejects impossible dates/times
    (month 13, 30 February, hour 24, ...).
    """
    if not isinstance(text, str) or _DATETIME_RE.fullmatch(text) is None:
        return None
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return None


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    codes = set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            code = line.strip()
            if code and not code.startswith("#"):
                codes.add(code)
    return codes


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    # 1
    if len(fields) != FIELD_COUNT:
        return "WRONG_FIELD_COUNT"
    flight_id, origin, destination, departure, arrival, price = (
        f.strip() for f in fields)
    # 2
    if not all((flight_id, origin, destination, departure, arrival, price)):
        return "MISSING_FIELD"
    # 3
    if _FLIGHT_ID_RE.fullmatch(flight_id) is None:
        return "INVALID_FLIGHT_ID"
    # 4, 5
    if _AIRPORT_CODE_RE.fullmatch(origin) is None or origin not in airports:
        return "INVALID_ORIGIN"
    if _AIRPORT_CODE_RE.fullmatch(destination) is None or destination not in airports:
        return "INVALID_DESTINATION"
    # 6
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"
    # 7, 8
    dep_dt = parse_datetime(departure)
    if dep_dt is None:
        return "INVALID_DEPARTURE"
    arr_dt = parse_datetime(arrival)
    if arr_dt is None:
        return "INVALID_ARRIVAL"
    # 9
    if arr_dt <= dep_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"
    # 10, 11
    try:
        value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(value):
        return "INVALID_PRICE"
    if value <= 0:
        return "NON_POSITIVE_PRICE"
    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    flight_id, origin, destination, departure, arrival, price = (
        f.strip() for f in fields)
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price),
    }

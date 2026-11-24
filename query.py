"""Running queries against the flight database."""
from validator import parse_datetime

RECORD_KEYS = ("flight_id", "origin", "destination",
               "departure_datetime", "arrival_datetime", "price")
_STRING_KEYS = ("flight_id", "origin", "destination")
_DATETIME_KEYS = ("departure_datetime", "arrival_datetime")
_NUMBER_KEYS = ("price", "min_price")
_ALLOWED_KEYS = set(RECORD_KEYS) | {"min_price", "sort_by", "order", "limit"}


def _is_number(value) -> bool:
    # bool is a subclass of int in Python, but "Booleans are not numbers".
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_valid_query(query) -> bool:
    if not isinstance(query, dict):
        return False
    if not set(query) <= _ALLOWED_KEYS:
        return False
    for key in _STRING_KEYS:
        if key in query and not isinstance(query[key], str):
            return False
    for key in _DATETIME_KEYS:
        if key in query and parse_datetime(query[key]) is None:
            return False
    for key in _NUMBER_KEYS:
        if key in query and not _is_number(query[key]):
            return False
    if "sort_by" in query and query["sort_by"] not in RECORD_KEYS:
        return False  # also rejects non-strings that are not hashable-equal to a key
    if "order" in query:
        if "sort_by" not in query or query["order"] not in ("asc", "desc"):
            return False
    if "limit" in query:
        limit = query["limit"]
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            return False
    return True


def _matches(record: dict, query: dict) -> bool:
    for key in _STRING_KEYS:
        if key in query and record[key] != query[key]:
            return False
    # "YYYY-MM-DD HH:MM" strings compare chronologically as plain strings.
    if "departure_datetime" in query and record["departure_datetime"] < query["departure_datetime"]:
        return False
    if "arrival_datetime" in query and record["arrival_datetime"] > query["arrival_datetime"]:
        return False
    if "price" in query and not record["price"] <= query["price"]:
        return False
    if "min_price" in query and not record["price"] >= query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """
    if not _is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [record for record in db if _matches(record, query)]
    if "sort_by" in query:
        # sorted() is stable, also with reverse=True: equal values keep db order.
        matches = sorted(matches, key=lambda r: r[query["sort_by"]],
                         reverse=query.get("order", "asc") == "desc")
    if "limit" in query:
        matches = matches[:query["limit"]]
    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    if isinstance(queries, list):
        return [run_query(db, q) for q in queries]
    return [run_query(db, queries)]

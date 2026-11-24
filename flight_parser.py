"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "260ADB180"
FIRST_NAME = "Daiguin"
LAST_NAME = "MILLOGO"

logger = logging.getLogger("flight_parser")


class RuntimeProblem(Exception):
    """An expected runtime problem: reported as 'Error: ...', exit code 1."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py", allow_abbrev=False,
        description="Validate flight schedule CSV files, store the valid "
                    "flights as a JSON database and answer queries.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help="output path of the JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with the queries to run")
    parser.add_argument("-r", metavar="FOLDER", default=".",
                        help="folder for the query response file (default: current directory)")
    return parser


def read_json(path: str, what: str):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except OSError as exc:
        raise RuntimeProblem(f"cannot read {what} '{path}': {exc.strerror or exc}")
    except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError
        raise RuntimeProblem(f"{what} '{path}' is not valid JSON: {exc}")


def csv_paths_in_folder(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        raise RuntimeProblem(f"folder '{folder}' does not exist or is not a folder")
    try:
        names = sorted(n for n in os.listdir(folder)
                       if n.endswith(".csv") and os.path.isfile(os.path.join(folder, n)))
    except OSError as exc:
        raise RuntimeProblem(f"cannot read folder '{folder}': {exc.strerror or exc}")
    if not names:
        raise RuntimeProblem(f"no .csv files found in '{folder}'")
    return [os.path.join(folder, n) for n in names]


def parse_sources(args) -> tuple[list[dict], list[str]]:
    paths = [args.i] if args.i else csv_paths_in_folder(args.d)
    try:
        airports = load_airports(args.a)
    except (OSError, ValueError) as exc:
        raise RuntimeProblem(f"cannot read airport list '{args.a}': {getattr(exc, 'strerror', None) or exc}")
    try:
        return parse_files(paths, airports)
    except (OSError, ValueError) as exc:
        raise RuntimeProblem(f"cannot read CSV input: {getattr(exc, 'strerror', None) or exc}")


def write_database_and_log(records: list[dict], errors: list[str], db_path: str) -> None:
    log_path = os.path.join(os.path.dirname(db_path), "errors.log")
    handler = None
    try:
        try:
            handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        except OSError as exc:
            raise RuntimeProblem(f"cannot write '{log_path}': {exc.strerror or exc}")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.info("%d valid flights, %d invalid rows", len(records), len(errors))
        for message in errors:
            logger.warning("%s", message)  # never use the message as a format string
    finally:
        # The autograder calls main() many times in one process: a handler
        # left behind would write duplicate lines into later logs.
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()
    try:
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    except OSError as exc:
        raise RuntimeProblem(f"cannot write database '{db_path}': {exc.strerror or exc}")


def load_database(path: str) -> list[dict]:
    db = read_json(path, "database")
    if not isinstance(db, list) or not all(isinstance(r, dict) for r in db):
        raise RuntimeProblem(f"database '{path}' must be a JSON array of objects")
    return db


def load_queries(path: str):
    queries = read_json(path, "query file")
    if isinstance(queries, dict):
        return queries
    if isinstance(queries, list) and all(isinstance(q, dict) for q in queries):
        return queries
    raise RuntimeProblem(f"query file '{path}' must be a query object or an array of query objects")


def write_response(results: list[dict], folder: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
    path = os.path.join(folder, name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
    except OSError as exc:
        raise RuntimeProblem(f"cannot write response file '{path}': {exc.strerror or exc}")
    return path


def run(args) -> None:
    if args.j:
        db = load_database(args.j)
        records = errors = None
    else:
        records, errors = parse_sources(args)
        db = records

    queries = load_queries(args.q) if args.q else None  # fail before writing anything

    if records is not None:
        db_path = args.o or "db.json"
        write_database_and_log(records, errors, db_path)
        print(f"{len(records)} valid flights, {len(errors)} invalid rows -> {db_path}")
    else:
        print(f"Loaded {len(db)} flights from {args.j}")

    if queries is not None:
        results = run_queries(db, queries)
        print(f"{len(results)} queries -> {write_response(results, args.r)}")


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if (args.i or args.d) and not args.a:
            parser.error("-a is required with -i and -d")
        if args.j and args.o:
            parser.error("-o cannot be used with -j")
    except SystemExit as exc:  # argparse/parser.error exit with 2 (0 for -h)
        return exc.code if isinstance(exc.code, int) else 2

    try:
        run(args)
        return 0
    except RuntimeProblem as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # last safety net: never show a traceback
        print(f"Error: unexpected problem: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
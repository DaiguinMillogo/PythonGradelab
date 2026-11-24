# AI Usage Disclosure

## Tools used

- ChatGPT (OpenAI), via the ChatGPT web interface.

## Conversation links

- Link 1: <https://chatgpt.com/share/6b05ca02-76f4-83ed-902e-24f78b9dbe58>

## What I used them for

- Handling the trickiest edge cases of the assignment (strict ASCII/date validation, physical line tracking, duplicate detection across files, boolean rejection in queries, and logging handler cleanup).
- Explaining the design choices (regex vs. isalnum/strptime pitfalls, logging handler cleanup, argparse exit codes).

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- | --- | --- |
| validator.py | validate_row, parse_datetime (strict ASCII regex, exact date format, check ordering) | generated |
| csv_loader.py | parse_files (1-based physical line tracking with comments/blanks, cross-file duplicate detection) | generated |
| query.py | run_query (strict type/boolean validation, stable sorting with ties) | generated |
| flight_parser.py | main (logging FileHandler setup and try/finally cleanup) | generated |

## Key prompts

1. "I am writing a Python 3.13 CLI program using only the standard library to validate flight schedule CSVs and run JSON queries. Could you help me handle the trickiest edge cases in the code? Specifically, I need to enforce 11 strict validation rules in exact order without falling into Python traps where methods like isalnum(), isupper(), or datetime.strptime() accept non-ASCII characters or unpadded dates. I also need to keep track of exact 1-based physical line numbers while skipping blank lines and comments, detect duplicate flights across multiple files, properly close the logging FileHandler in a try/finally block so repeated calls to main() don't duplicate logs, and make sure booleans are rejected when validating numeric prices or limits in queries since bool is a subclass of int in Python."

## What I changed or verified myself

I implemented the surrounding boilerplate (file loading, record conversion, CLI argument parsing, and JSON output writing), updated the `STUDENT_ID`, `FIRST_NAME`, and `LAST_NAME` constants in `flight_parser.py`, ran `python tests/run_public_tests.py` locally with Python 3.13 to verify all 29 public tests passed, and tested additional edge cases (CRLF line endings and invalid queries) myself.
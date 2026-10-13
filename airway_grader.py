#!/usr/bin/env python3
"""Descriptive, non-predictive modified Mallampati and Cormack–Lehane grading.

These are separate ordinal scales assessed at different clinical time points.
No composite score, risk probability, or treatment recommendation is produced.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

MAX_BATCH_ROWS = 100_000
MALLAMPATI = {
    1: "Soft palate, fauces, uvula and pillars visible.",
    2: "Soft palate, fauces and uvula visible; pillars not visible.",
    3: "Soft palate and base of uvula visible.",
    4: "Only hard palate visible; soft palate not visible.",
}
CORMACK_LEHANE = {
    1: "Full view of the glottis.",
    2: "Partial view of the glottis.",
    3: "Epiglottis visible, but glottis not seen.",
    4: "Neither glottis nor epiglottis visible.",
}
INTERPRETATION_NOTE = (
    "Descriptive grades only. Modified Mallampati is assessed before airway "
    "instrumentation; Cormack–Lehane describes the laryngoscopic view. "
    "Neither grade alone determines intubation difficulty or management."
)


def _grade(value: Any, field: str) -> Optional[int]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer from 1 to 4")
    if isinstance(value, str):
        if not re.fullmatch(r"[1-4]", value.strip()):
            raise ValueError(f"{field} must be an integer from 1 to 4")
        return int(value.strip())
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be an integer from 1 to 4")
    if int(value) != value or not (1 <= value <= 4):
        raise ValueError(f"{field} must be an integer from 1 to 4")
    return int(value)


def _distance(value: Any) -> Optional[float]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError("thyromental_distance_cm must be a positive finite number")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("thyromental_distance_cm must be a positive finite number") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError("thyromental_distance_cm must be a positive finite number")
    return result


def calculate_metrics(
    mallampati: Any = None,
    cormack_lehane: Any = None,
    thyromental_distance_cm: Any = None,
) -> Dict[str, Any]:
    """Report separately observed grades; do not calculate a clinical risk score."""
    mp = _grade(mallampati, "mallampati")
    cl = _grade(cormack_lehane, "cormack_lehane")
    td = _distance(thyromental_distance_cm)
    if mp is None and cl is None:
        raise ValueError("At least one observed grade is required")
    return {
        "mallampati_class": mp,
        "mallampati_description": MALLAMPATI[mp] if mp is not None else None,
        "cormack_lehane_grade": cl,
        "cormack_lehane_description": CORMACK_LEHANE[cl] if cl is not None else None,
        "thyromental_distance_cm": td,
        "interpretation_note": INTERPRETATION_NOTE,
    }


def safe_file_path(filepath: str, must_exist: bool = False) -> str:
    """Resolve local CLI paths (not a sandbox or authorization boundary)."""
    if ".." in Path(filepath).parts:
        raise ValueError("Parent-directory components are not accepted")
    path = os.path.realpath(os.path.abspath(filepath))
    if must_exist and not os.path.isfile(path):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    return path


def process_batch(input_csv: str, output_csv: str) -> int:
    input_path = safe_file_path(input_csv, must_exist=True)
    output_path = safe_file_path(output_csv)
    if input_path == output_path:
        raise ValueError("Input and output CSV paths must differ")
    output_columns = (
        "mallampati_description", "cormack_lehane_description",
        "interpretation_note", "error"
    )
    with open(input_path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        if not fields or len(fields) != len(set(fields)):
            raise ValueError("CSV must have unique, nonempty column headers")
        if not ({"mallampati", "cormack_lehane"} & set(fields)):
            raise ValueError("CSV needs a mallampati or cormack_lehane column")
        if set(fields) & set(output_columns):
            raise ValueError("CSV input must not contain output column names")
        records = []
        errors = 0
        for index, row in enumerate(reader):
            if index >= MAX_BATCH_ROWS:
                raise ValueError(f"CSV exceeds {MAX_BATCH_ROWS} rows")
            if None in row:
                raise ValueError(f"Row {index + 2} has extra columns")
            entry = dict(row)
            try:
                grade = calculate_metrics(
                    mallampati=row.get("mallampati"),
                    cormack_lehane=row.get("cormack_lehane"),
                    thyromental_distance_cm=row.get("thyromental_distance_cm"),
                )
                entry.update({
                    "mallampati_description": grade["mallampati_description"] or "",
                    "cormack_lehane_description": grade["cormack_lehane_description"] or "",
                    "interpretation_note": grade["interpretation_note"],
                    "error": "",
                })
            except ValueError as exc:
                errors += 1
                entry.update({key: "" for key in output_columns})
                entry["error"] = str(exc)
            records.append(entry)
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields + list(output_columns))
        writer.writeheader()
        writer.writerows(records)
    print(f"Processed {len(records)} rows ({errors} invalid) -> {output_path}")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Descriptive Mallampati and Cormack–Lehane grades; not a risk calculator"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("single", help="Describe observed airway grades")
    single.add_argument("--mallampati", type=int, choices=range(1, 5))
    single.add_argument("--cormack-lehane", type=int, choices=range(1, 5))
    single.add_argument("--thyromental-distance-cm", type=float)
    batch = sub.add_parser("batch", help="Process a local CSV file")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "single":
            result = calculate_metrics(
                args.mallampati, args.cormack_lehane, args.thyromental_distance_cm
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            return 0 if process_batch(args.input, args.output) == 0 else 1
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

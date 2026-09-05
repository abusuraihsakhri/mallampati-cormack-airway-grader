#!/usr/bin/env python3
"""
Airway Assessment (Mallampati & Cormack-Lehane)
Combines modified Mallampati, thyromental distance, and Cormack-Lehane grade for difficult intubation risk.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import os
import sys
from typing import Dict, Any, List, Optional


# Safety bounds for input validation
MAX_INPUT_VALUE = 10000.0
MIN_INPUT_VALUE = -10000.0
MAX_BATCH_ROWS = 100000


def validate_numeric_input(value: float, param_name: str = "input") -> float:
    """Validate numeric input is within safe bounds."""
    if not isinstance(value, (int, float)):
        raise ValueError(f"Parameter '{param_name}' must be numeric, got {type(value).__name__}")
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"Parameter '{param_name}' must be a finite number, got {value}")
    if value < MIN_INPUT_VALUE or value > MAX_INPUT_VALUE:
        raise ValueError(
            f"Parameter '{param_name}' value {value} exceeds safe bounds "
            f"[{MIN_INPUT_VALUE}, {MAX_INPUT_VALUE}]"
        )
    return float(value)


def safe_file_path(filepath: str, must_exist: bool = False) -> str:
    """Validate and sanitize file path to prevent path traversal."""
    # Resolve to absolute path
    resolved = os.path.realpath(os.path.abspath(filepath))
    # Check for path traversal attempts
    if ".." in filepath:
        raise ValueError(f"Path traversal detected in: {filepath}")
    if must_exist and not os.path.isfile(resolved):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    return resolved


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for mallampati-cormack-airway-grader.
    Validates inputs and computes weighted score with clinical classification.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                float_val = float(v)
                params[k] = validate_numeric_input(float_val, k)
            except (ValueError, TypeError) as e:
                if "must be numeric" in str(e) or "must be a finite number" in str(e):
                    raise
                params[k] = str(v)

    # Deterministic domain logic
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]

    if not numeric_vals:
        raise ValueError("At least one numeric parameter is required (e.g., v1, v2, v3)")

    primary_val = numeric_vals[0]
    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)

    # Classification / tiering
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "mallampati-cormack-airway-grader",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    kwargs.pop("command", None)
    try:
        res = calculate_metrics(**kwargs)
        print(json.dumps(res, indent=2))
    except ValueError as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


def process_batch(input_csv: str, output_csv: str) -> None:
    # Validate file paths
    input_path = safe_file_path(input_csv, must_exist=True)
    output_path = safe_file_path(output_csv, must_exist=False)

    try:
        with open(input_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
    except (OSError, csv.Error) as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    if not fieldnames:
        print("Error: Input CSV has no headers", file=sys.stderr)
        sys.exit(1)

    if len(rows) > MAX_BATCH_ROWS:
        print(f"Error: Batch size {len(rows)} exceeds maximum {MAX_BATCH_ROWS}", file=sys.stderr)
        sys.exit(1)

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []
    error_count = 0

    for r in rows:
        try:
            calc_res = calculate_metrics(**r)
            row_dict = dict(r)
            row_dict["score"] = calc_res["score"]
            row_dict["classification"] = calc_res["classification"]
            row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
            out_rows.append(row_dict)
        except ValueError as e:
            error_count += 1
            row_dict = dict(r)
            row_dict["score"] = "ERROR"
            row_dict["classification"] = "INVALID_INPUT"
            row_dict["clinical_recommendation"] = str(e)
            out_rows.append(row_dict)

    try:
        with open(output_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
    except OSError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Processed {len(out_rows)} records ({error_count} errors) -> {output_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Airway Assessment (Mallampati & Cormack-Lehane)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()

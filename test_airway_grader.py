import csv
import json
import subprocess
import sys

import pytest

from airway_grader import (
    CORMACK_LEHANE, MALLAMPATI, calculate_metrics, main, process_batch,
    safe_file_path,
)


@pytest.mark.parametrize("grade", [1, 2, 3, 4])
def test_all_modified_mallampati_classes(grade):
    observed = calculate_metrics(mallampati=grade)
    assert observed["mallampati_class"] == grade
    assert observed["mallampati_description"] == MALLAMPATI[grade]
    assert observed["cormack_lehane_grade"] is None
    assert "score" not in observed
    assert "clinical_recommendation" not in observed


@pytest.mark.parametrize("grade", [1, 2, 3, 4])
def test_all_original_cormack_lehane_grades(grade):
    observed = calculate_metrics(cormack_lehane=str(grade))
    assert observed["cormack_lehane_grade"] == grade
    assert observed["cormack_lehane_description"] == CORMACK_LEHANE[grade]


def test_scales_are_independent():
    observed = calculate_metrics(mallampati=1, cormack_lehane=4, thyromental_distance_cm=6.5)
    assert observed["mallampati_class"] == 1
    assert observed["cormack_lehane_grade"] == 4
    assert observed["thyromental_distance_cm"] == 6.5
    assert "neither" in observed["interpretation_note"].lower()


@pytest.mark.parametrize("invalid", [0, 5, -1, 2.1, "II", "3.0", "nan", True, [], float("inf"), float("nan")])
def test_invalid_grade_rejected(invalid):
    with pytest.raises(ValueError, match="integer from 1 to 4"):
        calculate_metrics(mallampati=invalid)


@pytest.mark.parametrize("invalid", [0, -2, "NaN", "inf", "not-a-number", True])
def test_invalid_distance_rejected(invalid):
    with pytest.raises(ValueError, match="positive finite"):
        calculate_metrics(mallampati=2, thyromental_distance_cm=invalid)


def test_at_least_one_grade_required():
    with pytest.raises(ValueError, match="At least one observed grade"):
        calculate_metrics(thyromental_distance_cm=6.5)


def test_batch_csv_with_invalid_row(tmp_path):
    source = tmp_path / "input.csv"
    destination = tmp_path / "output.csv"
    source.write_text(
        "mallampati,cormack_lehane,thyromental_distance_cm\n"
        "1,4,6.5\n"
        "5,2,7.0\n"
        ",3,\n",
        encoding="utf-8",
    )
    assert process_batch(str(source), str(destination)) == 1
    with destination.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert rows[0]["mallampati_description"] == MALLAMPATI[1]
    assert rows[0]["cormack_lehane_description"] == CORMACK_LEHANE[4]
    assert rows[1]["error"]
    assert rows[2]["error"] == ""


def test_batch_rejects_same_file(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("mallampati\n2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must differ"):
        process_batch(str(source), str(source))


def test_batch_rejects_missing_grade_columns(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("identifier,noise\na,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="needs a mallampati"):
        process_batch(str(source), str(tmp_path / "out.csv"))


def test_batch_rejects_extra_cells(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("mallampati\n2,extra\n", encoding="utf-8")
    with pytest.raises(ValueError, match="extra columns"):
        process_batch(str(source), str(tmp_path / "out.csv"))


def test_traversal_component_rejected():
    with pytest.raises(ValueError, match="Parent-directory"):
        safe_file_path("../sensitive.csv")


def test_missing_input():
    with pytest.raises(FileNotFoundError):
        process_batch("/nonexistent/file.csv", "/tmp/out.csv")


def test_cli_single(capsys):
    assert main(["single", "--mallampati", "2", "--cormack-lehane", "3"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mallampati_class"] == 2
    assert result["cormack_lehane_grade"] == 3


def test_cli_requires_grade(capsys):
    assert main(["single"]) == 1
    assert "At least one observed grade" in capsys.readouterr().err

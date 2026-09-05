import pytest
from airway_grader import calculate_metrics, process_batch, validate_numeric_input, safe_file_path


def test_airway_grader_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_airway_grader_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_calculate_metrics_classification_low():
    """Test low score classification."""
    res = calculate_metrics(v1=5.0)
    assert res["classification"] == "Low / Standard"
    assert res["score"] == 5.0


def test_calculate_metrics_classification_moderate():
    """Test moderate score classification."""
    res = calculate_metrics(v1=15.0)
    assert res["classification"] == "Moderate / Intermediate"


def test_calculate_metrics_classification_high():
    """Test high score classification."""
    res = calculate_metrics(v1=30.0)
    assert res["classification"] == "High / Severe"


def test_calculate_metrics_weighted_score():
    """Test that secondary values are weighted correctly."""
    res = calculate_metrics(v1=10.0, v2=4.0)
    # score = 10.0 + 4.0 * (1/2) = 12.0
    assert res["score"] == 12.0


def test_calculate_metrics_no_numeric_raises():
    """Test that no numeric input raises ValueError."""
    with pytest.raises(ValueError, match="At least one numeric parameter is required"):
        calculate_metrics(name="test", label="abc")


def test_validate_numeric_input_valid():
    """Test valid numeric input passes."""
    assert validate_numeric_input(42.0) == 42.0
    assert validate_numeric_input(0) == 0.0
    assert validate_numeric_input(-5) == -5.0


def test_validate_numeric_input_nan():
    """Test NaN input raises ValueError."""
    import math
    with pytest.raises(ValueError, match="must be a finite number"):
        validate_numeric_input(float("nan"))


def test_validate_numeric_input_inf():
    """Test infinity input raises ValueError."""
    with pytest.raises(ValueError, match="must be a finite number"):
        validate_numeric_input(float("inf"))


def test_validate_numeric_input_out_of_bounds():
    """Test out of bounds input raises ValueError."""
    with pytest.raises(ValueError, match="exceeds safe bounds"):
        validate_numeric_input(99999.0)


def test_safe_file_path_traversal():
    """Test path traversal detection."""
    with pytest.raises(ValueError, match="Path traversal detected"):
        safe_file_path("../../etc/passwd")


def test_safe_file_path_not_found():
    """Test non-existent file detection."""
    with pytest.raises(FileNotFoundError):
        safe_file_path("/nonexistent/file.csv", must_exist=True)


def test_batch_with_invalid_rows(tmp_path):
    """Test batch processing handles invalid rows gracefully."""
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,invalid,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "Pat_002" in content


def test_batch_missing_file():
    """Test batch processing with missing input file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        process_batch("/nonexistent/file.csv", "/tmp/out.csv")

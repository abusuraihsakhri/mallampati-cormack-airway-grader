"""Focused security and HTTP regression tests."""
import os

from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail
from agents.models import SystemTaskPayload

client = TestClient(app)


def test_hmac_detects_content_mutation():
    trail = AuditTrail(secret_key="unit-test-secret-with-adequate-length")
    trail.log("test", "unit", "case", {"status": "ok"})
    trail.log("test", "unit", "case", {"status": "next"})
    assert trail.verify_integrity()
    public_snapshot = trail.get_trail()
    public_snapshot[0]["actor"] = "changed"
    assert trail.verify_integrity()  # snapshots cannot mutate the ledger
    trail.logs[0]["actor"] = "changed"
    assert not trail.verify_integrity()


def test_hmac_rejects_field_boundary_substitution():
    trail = AuditTrail(secret_key="unit-test-secret-with-adequate-length")
    trail.log("alice|admin", "tier", "case", {"status": "ok"})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "alice"
    trail.logs[0]["actor_tier"] = "admin|tier"
    assert not trail.verify_integrity()


def test_invalid_numeric_metric_rejected():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="X", primary_metric=float("nan"))


def test_grade_endpoint():
    response = client.post("/api/grade", json={"mallampati": 3, "cormack_lehane": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["mallampati_class"] == 3
    assert payload["cormack_lehane_grade"] == 2
    assert "score" not in payload


def test_grade_endpoint_rejects_invalid_input():
    assert client.post("/api/grade", json={"mallampati": 5}).status_code == 422
    assert client.post("/api/grade", json={}).status_code == 422


def test_sensitive_endpoints_reject_missing_auth(monkeypatch):
    monkeypatch.setenv("API_ACCESS_TOKEN", "long-independent-api-test-token")
    assert client.get("/api/audit/logs").status_code == 401
    assert client.post("/api/audit", json={
        "task_id": "T", "target_identifier": "X", "primary_metric": 1
    }).status_code == 401


def test_sensitive_endpoint_requires_configuration(monkeypatch):
    monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 503

"""HTTP endpoints for descriptive airway grades and an opt-in demo rule engine.

Demo/audit routes require API_ACCESS_TOKEN and AUDIT_SECRET_KEY.
Never expose clinical/patient identifiers through these routes.
"""
import os
import hmac
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from airway_grader import calculate_metrics
from .base import AuditLogger
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

app = FastAPI(
    title="Airway Grading Reference API",
    description="Separate descriptive airway grades; optional nonclinical demo rules",
    version="1.0.0",
)
supervisor = SystemSupervisor(model_provider="mock")


class GradeRequest(BaseModel):
    mallampati: Optional[int] = None
    cormack_lehane: Optional[int] = None
    thyromental_distance_cm: Optional[float] = None


class ChatRequest(BaseModel):
    query: str


def require_demo_token(authorization: Optional[str] = Header(default=None)):
    expected = os.getenv("API_ACCESS_TOKEN")
    if not expected or len(expected) < 16 or not os.getenv("AUDIT_SECRET_KEY"):
        raise HTTPException(status_code=503, detail="Demo API credentials are not configured")
    supplied = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


@app.get("/health")
def health():
    return {"status": "ok", "service": "airway-grading-reference"}


@app.post("/api/grade")
def api_grade(payload: GradeRequest):
    try:
        return calculate_metrics(
            mallampati=payload.mallampati,
            cormack_lehane=payload.cormack_lehane,
            thyromental_distance_cm=payload.thyromental_distance_cm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/metrics", dependencies=[Depends(require_demo_token)])
def metrics():
    return {
        "demo_tasks_processed": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/audit", dependencies=[Depends(require_demo_token)])
def api_audit(payload: SystemTaskPayload):
    """Experimental rule-engine output, not a clinically validated grade."""
    return supervisor.process_task(payload).to_dict()


@app.post("/api/chat", dependencies=[Depends(require_demo_token)])
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/audit/logs", dependencies=[Depends(require_demo_token)])
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}

"""
FastAPI REST API Server for Mallampati Cormack Airway Grader.
"""
import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

# Set default audit key for API if not provided
if not os.getenv("AUDIT_SECRET_KEY"):
    os.environ["AUDIT_SECRET_KEY"] = "api-dev-key-change-in-production-2026"

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Mallampati Cormack Airway Grader API",
    description="Enterprise Distributed Component Platform (Radiology & Neuroimaging Systems)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "mallampati-cormack-airway-grader", "domain": "Radiology & Neuroimaging Systems", "standard": "ACR RADS / Fleischner Society / ASPECTS Guidelines", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}

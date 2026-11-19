"""
Human-in-the-Loop Approvals API Endpoints.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.session import get_db
from src.models.entities import ApprovalRequest
from src.schemas.dtos import ApprovalRequestRead, ApprovalDecision

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/pending", response_model=List[ApprovalRequestRead])
def get_pending_approvals(db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).filter(ApprovalRequest.status == "Pending").order_by(ApprovalRequest.created_at.desc()).all()


@router.get("/project/{project_id}", response_model=List[ApprovalRequestRead])
def get_project_approvals(project_id: str, db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).filter(ApprovalRequest.project_id == project_id).order_by(ApprovalRequest.created_at.desc()).all()


@router.post("/{approval_id}/decision", response_model=ApprovalRequestRead)
def submit_approval_decision(approval_id: str, payload: ApprovalDecision, db: Session = Depends(get_db)):
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    req.status = payload.status
    req.decision_reason = payload.decision_reason
    req.decided_at = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req

"""
Underwriting Workflow

This module orchestrates the loan underwriting process:
- Validates application completeness
- Evaluates against all lenders
- Persists match results
"""
from datetime import datetime
from typing import Dict, Any
import uuid

from app.database import SessionLocal
from app.models import LoanApplication, ApplicationStatus, MatchResult
from app.engine import LenderMatcher


def run_underwriting(application_id: str) -> Dict[str, Any]:
    """
    Run the underwriting process for a loan application.
    
    Evaluates the application against all active lenders and persists results.
    """
    db = SessionLocal()
    try:
        # Get application
        app_uuid = uuid.UUID(application_id)
        application = db.query(LoanApplication).filter(
            LoanApplication.id == app_uuid
        ).first()
        
        if not application:
            return {"error": f"Application {application_id} not found"}
        
        # Update status to underwriting
        application.status = ApplicationStatus.UNDERWRITING
        db.commit()
        
        # Clear any existing results
        db.query(MatchResult).filter(
            MatchResult.application_id == app_uuid
        ).delete()
        db.commit()
        
        # Run matching
        matcher = LenderMatcher(db)
        results = matcher.match_application(application)
        
        # Update status to completed
        application.status = ApplicationStatus.COMPLETED
        application.underwriting_completed_at = datetime.utcnow()
        db.commit()
        
        # Build response
        eligible = [r for r in results if r.is_eligible]
        ineligible = [r for r in results if not r.is_eligible]
        
        return {
            "application_id": str(application_id),
            "status": "completed",
            "total_lenders": len(results),
            "eligible_count": len(eligible),
            "ineligible_count": len(ineligible),
            "results": [
                {
                    "lender_id": str(r.lender_id),
                    "lender_name": r.lender.name if r.lender else None,
                    "program_id": str(r.program_id) if r.program_id else None,
                    "program_name": r.program.name if r.program else None,
                    "is_eligible": r.is_eligible,
                    "fit_score": r.fit_score,
                }
                for r in results
            ]
        }
        
    finally:
        db.close()

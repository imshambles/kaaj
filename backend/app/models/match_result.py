"""
Match Result model - stores underwriting results for each lender
"""
import uuid
from datetime import datetime
from sqlalchemy import Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class MatchResult(Base):
    """
    Result of matching a loan application against a specific lender/program.
    Stores detailed evaluation breakdown for transparency.
    """
    __tablename__ = "match_results"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_applications.id"), nullable=False)
    lender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lenders.id"), nullable=False)
    program_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lender_programs.id"), nullable=True)
    
    # Match Result
    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fit_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    
    # Detailed Breakdown (JSONB for flexibility)
    evaluation_details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Structure of evaluation_details:
    # {
    #     "rules_evaluated": 15,
    #     "rules_passed": 12,
    #     "rules_failed": 3,
    #     "pass_rate": 0.80,
    #     "details": [
    #         {
    #             "rule_type": "fico_min",
    #             "rule_id": "uuid",
    #             "passed": true,
    #             "required_value": 700,
    #             "actual_value": 720,
    #             "is_required": true,
    #             "reason": "FICO score 720 meets minimum requirement of 700"
    #         },
    #         {
    #             "rule_type": "excluded_states",
    #             "rule_id": "uuid",
    #             "passed": false,
    #             "required_value": ["CA", "NV"],
    #             "actual_value": "CA",
    #             "is_required": true,
    #             "reason": "State CA is excluded by this lender"
    #         }
    #     ],
    #     "summary": {
    #         "passed": [...],
    #         "failed": [...],
    #         "warnings": [...]
    #     }
    # }
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    application: Mapped["LoanApplication"] = relationship("LoanApplication", back_populates="match_results")
    lender: Mapped["Lender"] = relationship("Lender", back_populates="match_results")
    program: Mapped["LenderProgram | None"] = relationship("LenderProgram", back_populates="match_results")
    
    def __repr__(self):
        status = "Eligible" if self.is_eligible else "Not Eligible"
        return f"<MatchResult {self.lender.name if self.lender else 'Unknown'} - {status} ({self.fit_score})>"

"""
Loan Application model - loan requests with equipment details
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ApplicationStatus(str, PyEnum):
    """Status of a loan application"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDERWRITING = "underwriting"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class LoanApplication(Base):
    """Equipment financing loan application"""
    __tablename__ = "loan_applications"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    borrower_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("borrowers.id"), nullable=False)
    
    # Loan Details
    amount_requested: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)  # 24, 36, 48, 60
    down_payment_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Equipment Details
    equipment_type: Mapped[str] = mapped_column(String(100), nullable=False)  # "Class 8 Truck", "Construction", etc.
    equipment_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    equipment_year: Mapped[int] = mapped_column(Integer, nullable=False)
    equipment_age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    equipment_mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)  # For vehicles
    equipment_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)  # For heavy equipment
    equipment_condition: Mapped[str] = mapped_column(String(20), default="used")  # "new", "used"
    
    # Transaction Type
    is_private_party_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    is_titled_asset: Mapped[bool] = mapped_column(Boolean, default=True)
    is_refinance: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sale_leaseback: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Business Credit
    paynet_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_comparable_credit: Mapped[bool] = mapped_column(Boolean, default=False)
    comparable_credit_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    comparable_credit_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # % of requested
    
    # Application Status
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), 
        default=ApplicationStatus.DRAFT
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    underwriting_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    borrower: Mapped["Borrower"] = relationship("Borrower", back_populates="loan_applications")
    match_results: Mapped[list["MatchResult"]] = relationship("MatchResult", back_populates="application", cascade="all, delete-orphan")
    
    @property
    def is_trucking(self) -> bool:
        """Check if this is a trucking-related application"""
        trucking_keywords = ["truck", "trailer", "reefer", "class 8", "semi", "tractor"]
        equip_lower = self.equipment_type.lower()
        return any(kw in equip_lower for kw in trucking_keywords)
    
    def __repr__(self):
        return f"<LoanApplication ${self.amount_requested:,.2f} - {self.equipment_type}>"

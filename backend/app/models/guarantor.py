"""
Guarantor model - personal guarantors for loan applications
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Guarantor(Base):
    """Personal guarantor for a business loan"""
    __tablename__ = "guarantors"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    borrower_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("borrowers.id"), nullable=False)
    
    # Personal Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    ownership_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # e.g., 50.00
    
    # Credit Information
    fico_score: Mapped[int] = mapped_column(Integer, nullable=False)
    fico_source: Mapped[str] = mapped_column(String(50), default="TransUnion")  # TransUnion, Equifax, Experian
    
    # Property Status
    is_homeowner: Mapped[bool] = mapped_column(Boolean, default=False)
    years_at_residence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Credit History Flags
    has_bankruptcy: Mapped[bool] = mapped_column(Boolean, default=False)
    bankruptcy_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "Chapter 7", "Chapter 13"
    bankruptcy_discharge_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bankruptcy_dismissed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    has_judgments: Mapped[bool] = mapped_column(Boolean, default=False)
    has_foreclosure: Mapped[bool] = mapped_column(Boolean, default=False)
    has_repossession: Mapped[bool] = mapped_column(Boolean, default=False)
    has_tax_liens: Mapped[bool] = mapped_column(Boolean, default=False)
    has_collections_recent: Mapped[bool] = mapped_column(Boolean, default=False)  # Within last 3 years
    
    # Revolving Credit
    revolving_credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    revolving_credit_balance: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    revolving_available_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # % available
    
    # CDL Information (for trucking)
    has_cdl: Mapped[bool] = mapped_column(Boolean, default=False)
    cdl_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cdl_class: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "A", "B", "C"
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    borrower: Mapped["Borrower"] = relationship("Borrower", back_populates="guarantors")
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def years_since_bankruptcy_discharge(self) -> int | None:
        """Calculate years since bankruptcy discharge"""
        if self.bankruptcy_discharge_date:
            today = date.today()
            return (today - self.bankruptcy_discharge_date).days // 365
        return None
    
    def __repr__(self):
        return f"<Guarantor {self.full_name} ({self.ownership_percentage}%)>"

"""
Borrower model - represents a business applying for a loan
"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Borrower(Base):
    """Business entity applying for equipment financing"""
    __tablename__ = "borrowers"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Business Information
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dba_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "trucking", "construction", "medical"
    industry_naics: Mapped[str | None] = mapped_column(String(10), nullable=True)  # NAICS code
    state: Mapped[str] = mapped_column(String(2), nullable=False)  # 2-letter state code
    
    # Business Metrics
    years_in_business: Mapped[int] = mapped_column(Integer, nullable=False)
    annual_revenue: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    num_employees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_trucks: Mapped[int | None] = mapped_column(Integer, nullable=True)  # For trucking companies
    
    # Business Status
    is_startup: Mapped[bool] = mapped_column(Boolean, default=False)
    is_homeowner: Mapped[bool] = mapped_column(Boolean, default=False)  # Primary owner homeowner status
    is_us_citizen: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guarantors: Mapped[list["Guarantor"]] = relationship("Guarantor", back_populates="borrower", cascade="all, delete-orphan")
    loan_applications: Mapped[list["LoanApplication"]] = relationship("LoanApplication", back_populates="borrower", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Borrower {self.business_name}>"

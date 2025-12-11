"""
Lender and Policy models - core of the extensible policy system
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class RuleOperator(str, PyEnum):
    """Operators for policy rule evaluation"""
    GTE = "gte"           # Greater than or equal
    LTE = "lte"           # Less than or equal
    GT = "gt"             # Greater than
    LT = "lt"             # Less than
    EQ = "eq"             # Equal
    NEQ = "neq"           # Not equal
    IN = "in"             # Value in list
    NOT_IN = "not_in"     # Value not in list
    BETWEEN = "between"   # Between two values
    EXISTS = "exists"     # Field exists/has value
    NOT_EXISTS = "not_exists"  # Field doesn't exist


class CreditTier(str, PyEnum):
    """Credit tier classifications"""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class Lender(Base):
    """Equipment finance lender"""
    __tablename__ = "lenders"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Lender Information
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Contact Information
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    programs: Mapped[list["LenderProgram"]] = relationship("LenderProgram", back_populates="lender", cascade="all, delete-orphan")
    match_results: Mapped[list["MatchResult"]] = relationship("MatchResult", back_populates="lender")
    
    def __repr__(self):
        return f"<Lender {self.name}>"


class LenderProgram(Base):
    """A specific program/tier offered by a lender (e.g., Tier 1, Medical, A Credit)"""
    __tablename__ = "lender_programs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lenders.id"), nullable=False)
    
    # Program Details
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Tier 1", "Standard", "Medical"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credit_tier: Mapped[CreditTier | None] = mapped_column(Enum(CreditTier), nullable=True)
    
    # Loan Limits (program-level)
    min_loan_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_loan_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_term_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Program Type Flags
    is_app_only: Mapped[bool] = mapped_column(Boolean, default=False)  # App-only (no full financials)
    requires_financials: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Priority for matching (lower = better)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lender: Mapped["Lender"] = relationship("Lender", back_populates="programs")
    rules: Mapped[list["PolicyRule"]] = relationship("PolicyRule", back_populates="program", cascade="all, delete-orphan")
    match_results: Mapped[list["MatchResult"]] = relationship("MatchResult", back_populates="program")
    
    def __repr__(self):
        return f"<LenderProgram {self.lender.name if self.lender else 'Unknown'} - {self.name}>"


class PolicyRule(Base):
    """
    Individual policy rule for a lender program.
    Extensible key-value design allows adding new rule types without schema changes.
    """
    __tablename__ = "policy_rules"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lender_programs.id"), nullable=False)
    
    # Rule Definition
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "fico_min", "excluded_states", etc.
    operator: Mapped[RuleOperator] = mapped_column(Enum(RuleOperator), nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Flexible value storage
    
    # Rule Metadata
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rejection_message: Mapped[str] = mapped_column(Text, nullable=False)  # Human-readable reason
    
    # Rule Behavior
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)  # Hard vs soft requirement
    priority: Mapped[int] = mapped_column(Integer, default=100)  # Evaluation order (lower = first)
    weight: Mapped[int] = mapped_column(Integer, default=10)  # Weight for scoring
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    program: Mapped["LenderProgram"] = relationship("LenderProgram", back_populates="rules")
    
    def __repr__(self):
        return f"<PolicyRule {self.rule_type} {self.operator.value} {self.value}>"


# Supported rule_types documentation:
# --------------------------------
# CREDIT SCORES
# - fico_min: Minimum FICO score required
# - fico_max: Maximum FICO score (for tier limits)
# - paynet_min: Minimum PayNet/business credit score
# - paynet_max: Maximum PayNet score
#
# BUSINESS REQUIREMENTS
# - tib_min: Minimum time in business (years)
# - tib_max: Maximum time in business
# - revenue_min: Minimum annual revenue
# - num_trucks_min: Minimum number of trucks (trucking)
#
# LOAN PARAMETERS
# - amount_min: Minimum loan amount
# - amount_max: Maximum loan amount
# - term_max: Maximum term in months
# - equipment_age_max: Maximum equipment age in years
# - equipment_mileage_max: Maximum mileage (vehicles)
#
# EXCLUSIONS
# - excluded_states: List of excluded states
# - excluded_industries: List of excluded industries
# - excluded_equipment: List of excluded equipment types
#
# CREDIT HISTORY
# - no_bankruptcies: Boolean - no bankruptcies allowed
# - bankruptcy_years_min: Minimum years since bankruptcy discharge
# - no_judgments: Boolean - no judgments allowed
# - no_foreclosures: Boolean - no foreclosures allowed
# - no_repossessions: Boolean - no repossessions allowed
# - no_tax_liens: Boolean - no tax liens allowed
#
# OTHER REQUIREMENTS
# - requires_homeowner: Boolean - homeownership required
# - requires_cdl: Boolean - CDL required
# - cdl_years_min: Minimum years with CDL
# - comparable_credit_pct: Required comparable credit as % of loan
# - revolving_available_min: Minimum % revolving credit available
# - requires_us_citizen: Boolean - US citizenship required
# - no_private_party: Boolean - no private party sales
# - no_refinance: Boolean - no refinancing
# - no_sale_leaseback: Boolean - no sale-leaseback transactions

"""
Pydantic schemas for API request/response validation
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# ============== Enums ==============

class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDERWRITING = "underwriting"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class RuleOperator(str, Enum):
    GTE = "gte"
    LTE = "lte"
    GT = "gt"
    LT = "lt"
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class CreditTier(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


# ============== Guarantor Schemas ==============

class GuarantorBase(BaseModel):
    first_name: str
    last_name: str
    ownership_percentage: Decimal = Field(ge=0, le=100)
    fico_score: int = Field(ge=300, le=850)
    fico_source: str = "TransUnion"
    is_homeowner: bool = False
    years_at_residence: Optional[int] = None
    has_bankruptcy: bool = False
    bankruptcy_type: Optional[str] = None
    bankruptcy_discharge_date: Optional[date] = None
    has_judgments: bool = False
    has_foreclosure: bool = False
    has_repossession: bool = False
    has_tax_liens: bool = False
    has_collections_recent: bool = False
    revolving_credit_limit: Optional[Decimal] = None
    revolving_credit_balance: Optional[Decimal] = None
    revolving_available_pct: Optional[Decimal] = None
    has_cdl: bool = False
    cdl_years: Optional[int] = None
    cdl_class: Optional[str] = None


class GuarantorCreate(GuarantorBase):
    pass


class GuarantorResponse(GuarantorBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    borrower_id: UUID
    created_at: datetime


# ============== Borrower Schemas ==============

class BorrowerBase(BaseModel):
    business_name: str
    dba_name: Optional[str] = None
    industry: str
    industry_naics: Optional[str] = None
    state: str = Field(min_length=2, max_length=2)
    years_in_business: int = Field(ge=0)
    annual_revenue: Decimal = Field(ge=0)
    num_employees: Optional[int] = None
    num_trucks: Optional[int] = None
    is_startup: bool = False
    is_homeowner: bool = False
    is_us_citizen: bool = True


class BorrowerCreate(BorrowerBase):
    guarantors: List[GuarantorCreate] = []


class BorrowerResponse(BorrowerBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    guarantors: List[GuarantorResponse] = []


# ============== Loan Application Schemas ==============

class LoanApplicationBase(BaseModel):
    amount_requested: Decimal = Field(ge=10000)
    term_months: int = Field(ge=12, le=84)
    down_payment_pct: Optional[Decimal] = None
    equipment_type: str
    equipment_description: Optional[str] = None
    equipment_year: int
    equipment_age_years: int = Field(ge=0)
    equipment_mileage: Optional[int] = None
    equipment_hours: Optional[int] = None
    equipment_condition: str = "used"
    is_private_party_sale: bool = False
    is_titled_asset: bool = True
    is_refinance: bool = False
    is_sale_leaseback: bool = False
    paynet_score: Optional[int] = None
    has_comparable_credit: bool = False
    comparable_credit_amount: Optional[Decimal] = None
    comparable_credit_pct: Optional[Decimal] = None


class LoanApplicationCreate(BaseModel):
    """Full application creation with nested borrower and guarantors"""
    borrower: BorrowerCreate
    application: LoanApplicationBase


class LoanApplicationUpdate(BaseModel):
    amount_requested: Optional[Decimal] = None
    term_months: Optional[int] = None
    equipment_type: Optional[str] = None
    equipment_year: Optional[int] = None
    equipment_age_years: Optional[int] = None
    equipment_mileage: Optional[int] = None
    paynet_score: Optional[int] = None
    status: Optional[ApplicationStatus] = None


class LoanApplicationResponse(LoanApplicationBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    borrower_id: UUID
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    borrower: Optional[BorrowerResponse] = None


# ============== Policy Rule Schemas ==============

class PolicyRuleBase(BaseModel):
    rule_type: str
    operator: RuleOperator
    value: Any  # JSONB - can be int, str, list, dict
    description: Optional[str] = None
    rejection_message: str
    is_required: bool = True
    priority: int = 100
    weight: int = 10
    is_active: bool = True


class PolicyRuleCreate(PolicyRuleBase):
    pass


class PolicyRuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    operator: Optional[RuleOperator] = None
    value: Optional[Any] = None
    description: Optional[str] = None
    rejection_message: Optional[str] = None
    is_required: Optional[bool] = None
    priority: Optional[int] = None
    weight: Optional[int] = None
    is_active: Optional[bool] = None


class PolicyRuleResponse(PolicyRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    program_id: UUID
    created_at: datetime
    updated_at: datetime


# ============== Lender Program Schemas ==============

class LenderProgramBase(BaseModel):
    name: str
    description: Optional[str] = None
    credit_tier: Optional[CreditTier] = None
    min_loan_amount: Optional[int] = None
    max_loan_amount: Optional[int] = None
    max_term_months: Optional[int] = None
    is_app_only: bool = False
    requires_financials: bool = False
    priority: int = 100
    is_active: bool = True


class LenderProgramCreate(LenderProgramBase):
    rules: List[PolicyRuleCreate] = []


class LenderProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    credit_tier: Optional[CreditTier] = None
    min_loan_amount: Optional[int] = None
    max_loan_amount: Optional[int] = None
    max_term_months: Optional[int] = None
    is_app_only: Optional[bool] = None
    requires_financials: Optional[bool] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class LenderProgramResponse(LenderProgramBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    lender_id: UUID
    created_at: datetime
    updated_at: datetime
    rules: List[PolicyRuleResponse] = []


# ============== Lender Schemas ==============

class LenderBase(BaseModel):
    name: str
    short_name: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    is_active: bool = True


class LenderCreate(LenderBase):
    programs: List[LenderProgramCreate] = []


class LenderUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None


class LenderResponse(LenderBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    programs: List[LenderProgramResponse] = []


class LenderSummary(BaseModel):
    """Lightweight lender response without nested programs"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    short_name: Optional[str] = None
    is_active: bool
    program_count: int = 0


# ============== Match Result Schemas ==============

class RuleEvaluationDetail(BaseModel):
    rule_type: str
    rule_id: str
    passed: bool
    required_value: Any
    actual_value: Any
    is_required: bool
    reason: str


class MatchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    application_id: UUID
    lender_id: UUID
    program_id: Optional[UUID] = None
    is_eligible: bool
    fit_score: int
    evaluation_details: dict
    created_at: datetime
    
    # Nested for convenience
    lender_name: Optional[str] = None
    program_name: Optional[str] = None


class UnderwritingResultsResponse(BaseModel):
    """Full underwriting results for an application"""
    application_id: UUID
    status: ApplicationStatus
    total_lenders: int
    eligible_count: int
    ineligible_count: int
    best_match: Optional[MatchResultResponse] = None
    results: List[MatchResultResponse] = []


# ============== Underwriting Request ==============

class UnderwritingRequest(BaseModel):
    """Request to run underwriting on an application"""
    application_id: UUID

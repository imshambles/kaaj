"""
Rule Evaluators - Extensible system for evaluating policy rules

Each evaluator handles a specific rule type and returns a standardized result.
New rule types can be added by creating a new evaluator class and registering it.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import PolicyRule


@dataclass
class EvaluationContext:
    """Context containing all application data needed for evaluation"""
    # Borrower data
    business_name: str
    industry: str
    state: str
    years_in_business: int
    annual_revenue: Decimal
    num_trucks: Optional[int]
    is_startup: bool
    is_homeowner: bool
    is_us_citizen: bool
    
    # Primary guarantor data
    guarantor_fico: int
    guarantor_fico_source: str
    guarantor_is_homeowner: bool
    guarantor_has_bankruptcy: bool
    guarantor_bankruptcy_discharge_date: Optional[date]
    guarantor_has_judgments: bool
    guarantor_has_foreclosure: bool
    guarantor_has_repossession: bool
    guarantor_has_tax_liens: bool
    guarantor_has_collections_recent: bool
    guarantor_revolving_available_pct: Optional[Decimal]
    guarantor_has_cdl: bool
    guarantor_cdl_years: Optional[int]
    
    # Loan application data
    amount_requested: Decimal
    term_months: int
    equipment_type: str
    equipment_age_years: int
    equipment_mileage: Optional[int]
    is_private_party_sale: bool
    is_titled_asset: bool
    is_refinance: bool
    is_sale_leaseback: bool
    paynet_score: Optional[int]
    comparable_credit_pct: Optional[Decimal]
    
    @property
    def is_trucking(self) -> bool:
        """Check if this is a trucking-related application"""
        trucking_keywords = ["truck", "trailer", "reefer", "class 8", "semi", "tractor", "otr"]
        equip_lower = self.equipment_type.lower()
        industry_lower = self.industry.lower()
        return any(kw in equip_lower or kw in industry_lower for kw in trucking_keywords)
    
    @property
    def years_since_bankruptcy(self) -> Optional[int]:
        """Calculate years since bankruptcy discharge"""
        if self.guarantor_bankruptcy_discharge_date:
            today = date.today()
            return (today - self.guarantor_bankruptcy_discharge_date).days // 365
        return None


@dataclass
class EvaluationResult:
    """Result of evaluating a single rule"""
    passed: bool
    rule_type: str
    rule_id: str
    required_value: Any
    actual_value: Any
    is_required: bool
    reason: str
    weight: int = 10
    
    def to_dict(self) -> Dict:
        return {
            "rule_type": self.rule_type,
            "rule_id": self.rule_id,
            "passed": self.passed,
            "required_value": self.required_value,
            "actual_value": self.actual_value,
            "is_required": self.is_required,
            "reason": self.reason,
            "weight": self.weight,
        }


class RuleEvaluator(ABC):
    """Base class for all rule evaluators"""
    
    @abstractmethod
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        """Evaluate the rule against the application context"""
        pass
    
    def _get_value(self, rule: "PolicyRule") -> Any:
        """Extract value from rule, handling JSONB structure"""
        value = rule.value
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return value


# ============== Credit Score Evaluators ==============

class FicoMinEvaluator(RuleEvaluator):
    """Evaluate minimum FICO score requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        actual = ctx.guarantor_fico
        passed = actual >= required
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"FICO score {actual} {'meets' if passed else 'is below'} minimum requirement of {required}"
        )


class PaynetMinEvaluator(RuleEvaluator):
    """Evaluate minimum PayNet/business credit score requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        actual = ctx.paynet_score
        
        if actual is None:
            return EvaluationResult(
                passed=False,
                rule_type=rule.rule_type,
                rule_id=str(rule.id),
                required_value=required,
                actual_value=None,
                is_required=rule.is_required,
                weight=rule.weight,
                reason=f"PayNet score required ({required} minimum) but not provided"
            )
        
        passed = actual >= required
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"PayNet score {actual} {'meets' if passed else 'is below'} minimum requirement of {required}"
        )


# ============== Business Requirement Evaluators ==============

class TimeInBusinessMinEvaluator(RuleEvaluator):
    """Evaluate minimum time in business requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        actual = ctx.years_in_business
        passed = actual >= required
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Time in business {actual} years {'meets' if passed else 'is below'} minimum of {required} years"
        )


class NumTrucksMinEvaluator(RuleEvaluator):
    """Evaluate minimum number of trucks (for trucking companies)"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        actual = ctx.num_trucks or 0
        passed = actual >= required
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Operating {actual} trucks {'meets' if passed else 'is below'} minimum of {required} trucks"
        )


# ============== Loan Parameter Evaluators ==============

class AmountMinEvaluator(RuleEvaluator):
    """Evaluate minimum loan amount"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = Decimal(str(self._get_value(rule)))
        actual = ctx.amount_requested
        passed = actual >= required
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=float(required),
            actual_value=float(actual),
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Loan amount ${actual:,.2f} {'meets' if passed else 'is below'} minimum of ${required:,.2f}"
        )


class AmountMaxEvaluator(RuleEvaluator):
    """Evaluate maximum loan amount"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = Decimal(str(self._get_value(rule)))
        actual = ctx.amount_requested
        passed = actual <= required
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=float(required),
            actual_value=float(actual),
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Loan amount ${actual:,.2f} {'is within' if passed else 'exceeds'} maximum of ${required:,.2f}"
        )


class TermMaxEvaluator(RuleEvaluator):
    """Evaluate maximum term in months"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        actual = ctx.term_months
        passed = actual <= required
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Term {actual} months {'is within' if passed else 'exceeds'} maximum of {required} months"
        )


class EquipmentAgeMaxEvaluator(RuleEvaluator):
    """Evaluate maximum equipment age"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        actual = ctx.equipment_age_years
        passed = actual <= required
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Equipment age {actual} years {'is within' if passed else 'exceeds'} maximum of {required} years"
        )


class EquipmentMileageMaxEvaluator(RuleEvaluator):
    """Evaluate maximum equipment mileage"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        actual = ctx.equipment_mileage
        
        if actual is None:
            return EvaluationResult(
                passed=True,
                rule_type=rule.rule_type,
                rule_id=str(rule.id),
                required_value=required,
                actual_value=None,
                is_required=rule.is_required,
                weight=rule.weight,
                reason="Mileage not applicable for this equipment type"
            )
        
        passed = actual <= required
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Mileage {actual:,} {'is within' if passed else 'exceeds'} maximum of {required:,}"
        )


# ============== Exclusion Evaluators ==============

class ExcludedStatesEvaluator(RuleEvaluator):
    """Evaluate state exclusions"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        excluded = self._get_value(rule)
        if isinstance(excluded, str):
            excluded = [excluded]
        actual = ctx.state.upper()
        passed = actual not in [s.upper() for s in excluded]
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=excluded,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"State {actual} {'is not in' if passed else 'is in'} excluded states list"
        )


class ExcludedIndustriesEvaluator(RuleEvaluator):
    """Evaluate industry exclusions"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        excluded = self._get_value(rule)
        if isinstance(excluded, str):
            excluded = [excluded]
        actual = ctx.industry.lower()
        
        # Check if industry matches any exclusion (partial match)
        is_excluded = any(excl.lower() in actual or actual in excl.lower() for excl in excluded)
        passed = not is_excluded
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=excluded,
            actual_value=ctx.industry,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Industry '{ctx.industry}' {'is allowed' if passed else 'is in excluded industries list'}"
        )


class ExcludedEquipmentEvaluator(RuleEvaluator):
    """Evaluate equipment type exclusions"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        excluded = self._get_value(rule)
        if isinstance(excluded, str):
            excluded = [excluded]
        actual = ctx.equipment_type.lower()
        
        # Check if equipment matches any exclusion (partial match)
        is_excluded = any(excl.lower() in actual or actual in excl.lower() for excl in excluded)
        passed = not is_excluded
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=excluded,
            actual_value=ctx.equipment_type,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Equipment '{ctx.equipment_type}' {'is allowed' if passed else 'is in excluded types list'}"
        )


# ============== Credit History Evaluators ==============

class NoBankruptciesEvaluator(RuleEvaluator):
    """Evaluate no bankruptcies requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        has_bankruptcy = ctx.guarantor_has_bankruptcy
        passed = not has_bankruptcy
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=False,
            actual_value=has_bankruptcy,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="No bankruptcy history" if passed else "Bankruptcy on record - lender does not accept bankruptcies"
        )


class BankruptcyYearsMinEvaluator(RuleEvaluator):
    """Evaluate minimum years since bankruptcy discharge"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        
        if not ctx.guarantor_has_bankruptcy:
            return EvaluationResult(
                passed=True,
                rule_type=rule.rule_type,
                rule_id=str(rule.id),
                required_value=required,
                actual_value=None,
                is_required=rule.is_required,
                weight=rule.weight,
                reason="No bankruptcy history"
            )
        
        years_since = ctx.years_since_bankruptcy
        if years_since is None:
            return EvaluationResult(
                passed=False,
                rule_type=rule.rule_type,
                rule_id=str(rule.id),
                required_value=required,
                actual_value=None,
                is_required=rule.is_required,
                weight=rule.weight,
                reason="Bankruptcy on record but discharge date not provided"
            )
        
        passed = years_since >= required
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=years_since,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Bankruptcy discharged {years_since} years ago {'meets' if passed else 'does not meet'} {required} year minimum"
        )


class NoJudgmentsEvaluator(RuleEvaluator):
    """Evaluate no judgments requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        has_judgments = ctx.guarantor_has_judgments
        passed = not has_judgments
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=False,
            actual_value=has_judgments,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="No judgments on record" if passed else "Judgments on record - lender does not accept judgments"
        )


class NoForeclosuresEvaluator(RuleEvaluator):
    """Evaluate no foreclosures requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        has_foreclosure = ctx.guarantor_has_foreclosure
        passed = not has_foreclosure
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=False,
            actual_value=has_foreclosure,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="No foreclosure history" if passed else "Foreclosure on record - lender does not accept foreclosures"
        )


class NoRepossessionsEvaluator(RuleEvaluator):
    """Evaluate no repossessions requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        has_repo = ctx.guarantor_has_repossession
        passed = not has_repo
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=False,
            actual_value=has_repo,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="No repossession history" if passed else "Repossession on record - lender does not accept repossessions"
        )


class NoTaxLiensEvaluator(RuleEvaluator):
    """Evaluate no tax liens requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        has_liens = ctx.guarantor_has_tax_liens
        passed = not has_liens
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=False,
            actual_value=has_liens,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="No tax liens" if passed else "Tax liens on record - lender does not accept tax liens"
        )


# ============== Other Requirement Evaluators ==============

class RequiresHomeownerEvaluator(RuleEvaluator):
    """Evaluate homeownership requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        is_homeowner = ctx.guarantor_is_homeowner or ctx.is_homeowner
        passed = is_homeowner
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=True,
            actual_value=is_homeowner,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="Homeowner requirement met" if passed else "Homeownership is required by this lender"
        )


class RequiresCdlEvaluator(RuleEvaluator):
    """Evaluate CDL requirement (for trucking)"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        has_cdl = ctx.guarantor_has_cdl
        passed = has_cdl
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=True,
            actual_value=has_cdl,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="CDL requirement met" if passed else "CDL is required for trucking equipment"
        )


class CdlYearsMinEvaluator(RuleEvaluator):
    """Evaluate minimum years with CDL"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = self._get_value(rule)
        actual = ctx.guarantor_cdl_years or 0
        passed = actual >= required
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=required,
            actual_value=actual,
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"CDL experience {actual} years {'meets' if passed else 'is below'} minimum of {required} years"
        )


class ComparableCreditPctEvaluator(RuleEvaluator):
    """Evaluate comparable credit percentage requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = Decimal(str(self._get_value(rule)))
        actual = ctx.comparable_credit_pct
        
        if actual is None:
            return EvaluationResult(
                passed=False,
                rule_type=rule.rule_type,
                rule_id=str(rule.id),
                required_value=float(required),
                actual_value=None,
                is_required=rule.is_required,
                weight=rule.weight,
                reason=f"Comparable credit of {required}% required but not provided"
            )
        
        passed = actual >= required
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=float(required),
            actual_value=float(actual),
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Comparable credit {actual}% {'meets' if passed else 'is below'} {required}% requirement"
        )


class RevolvingAvailableMinEvaluator(RuleEvaluator):
    """Evaluate minimum revolving credit available percentage"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        required = Decimal(str(self._get_value(rule)))
        actual = ctx.guarantor_revolving_available_pct
        
        if actual is None:
            return EvaluationResult(
                passed=False,
                rule_type=rule.rule_type,
                rule_id=str(rule.id),
                required_value=float(required),
                actual_value=None,
                is_required=rule.is_required,
                weight=rule.weight,
                reason=f"Revolving credit availability of {required}% required but not provided"
            )
        
        passed = actual >= required
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=float(required),
            actual_value=float(actual),
            is_required=rule.is_required,
            weight=rule.weight,
            reason=f"Revolving credit {actual}% available {'meets' if passed else 'is below'} {required}% requirement"
        )


class RequiresUsCitizenEvaluator(RuleEvaluator):
    """Evaluate US citizenship requirement"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        is_citizen = ctx.is_us_citizen
        passed = is_citizen
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=True,
            actual_value=is_citizen,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="US citizenship requirement met" if passed else "US citizenship is required"
        )


class NoPrivatePartyEvaluator(RuleEvaluator):
    """Evaluate no private party sales restriction"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        is_private = ctx.is_private_party_sale
        passed = not is_private
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=False,
            actual_value=is_private,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="Dealer transaction" if passed else "Private party sales not accepted by this lender"
        )


class NoRefinanceEvaluator(RuleEvaluator):
    """Evaluate no refinance restriction"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        is_refi = ctx.is_refinance
        passed = not is_refi
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=False,
            actual_value=is_refi,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="New financing transaction" if passed else "Refinance transactions not accepted by this lender"
        )


class NoSaleLeasebackEvaluator(RuleEvaluator):
    """Evaluate no sale-leaseback restriction"""
    
    def evaluate(self, ctx: EvaluationContext, rule: "PolicyRule") -> EvaluationResult:
        is_slb = ctx.is_sale_leaseback
        passed = not is_slb
        
        return EvaluationResult(
            passed=passed,
            rule_type=rule.rule_type,
            rule_id=str(rule.id),
            required_value=False,
            actual_value=is_slb,
            is_required=rule.is_required,
            weight=rule.weight,
            reason="Standard purchase transaction" if passed else "Sale-leaseback transactions not accepted by this lender"
        )


# ============== Evaluator Registry ==============

EVALUATOR_REGISTRY: Dict[str, RuleEvaluator] = {
    # Credit scores
    "fico_min": FicoMinEvaluator(),
    "paynet_min": PaynetMinEvaluator(),
    
    # Business requirements
    "tib_min": TimeInBusinessMinEvaluator(),
    "num_trucks_min": NumTrucksMinEvaluator(),
    
    # Loan parameters
    "amount_min": AmountMinEvaluator(),
    "amount_max": AmountMaxEvaluator(),
    "term_max": TermMaxEvaluator(),
    "equipment_age_max": EquipmentAgeMaxEvaluator(),
    "equipment_mileage_max": EquipmentMileageMaxEvaluator(),
    
    # Exclusions
    "excluded_states": ExcludedStatesEvaluator(),
    "excluded_industries": ExcludedIndustriesEvaluator(),
    "excluded_equipment": ExcludedEquipmentEvaluator(),
    
    # Credit history
    "no_bankruptcies": NoBankruptciesEvaluator(),
    "bankruptcy_years_min": BankruptcyYearsMinEvaluator(),
    "no_judgments": NoJudgmentsEvaluator(),
    "no_foreclosures": NoForeclosuresEvaluator(),
    "no_repossessions": NoRepossessionsEvaluator(),
    "no_tax_liens": NoTaxLiensEvaluator(),
    
    # Other requirements
    "requires_homeowner": RequiresHomeownerEvaluator(),
    "requires_cdl": RequiresCdlEvaluator(),
    "cdl_years_min": CdlYearsMinEvaluator(),
    "comparable_credit_pct": ComparableCreditPctEvaluator(),
    "revolving_available_min": RevolvingAvailableMinEvaluator(),
    "requires_us_citizen": RequiresUsCitizenEvaluator(),
    "no_private_party": NoPrivatePartyEvaluator(),
    "no_refinance": NoRefinanceEvaluator(),
    "no_sale_leaseback": NoSaleLeasebackEvaluator(),
}


def get_evaluator(rule_type: str) -> Optional[RuleEvaluator]:
    """Get evaluator for a rule type"""
    return EVALUATOR_REGISTRY.get(rule_type)


def register_evaluator(rule_type: str, evaluator: RuleEvaluator) -> None:
    """Register a new evaluator (for extensibility)"""
    EVALUATOR_REGISTRY[rule_type] = evaluator

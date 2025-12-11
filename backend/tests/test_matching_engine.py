"""
Unit tests for the matching engine
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from uuid import uuid4

from app.engine.evaluators import (
    EvaluationContext,
    FicoMinEvaluator,
    PaynetMinEvaluator,
    TimeInBusinessMinEvaluator,
    ExcludedStatesEvaluator,
    ExcludedIndustriesEvaluator,
    NoBankruptciesEvaluator,
    BankruptcyYearsMinEvaluator,
    RequiresHomeownerEvaluator,
    AmountMaxEvaluator,
    get_evaluator,
    EVALUATOR_REGISTRY,
)
from app.engine.scoring import calculate_fit_score
from app.models import PolicyRule, RuleOperator


# ============== Test Fixtures ==============

def create_test_context(
    fico: int = 720,
    paynet: int | None = 680,
    tib: int = 5,
    state: str = "TX",
    industry: str = "construction",
    amount: Decimal = Decimal("100000"),
    is_homeowner: bool = True,
    has_bankruptcy: bool = False,
    bankruptcy_discharge_date: date | None = None,
) -> EvaluationContext:
    """Create a test evaluation context with default good values"""
    return EvaluationContext(
        business_name="Test Business",
        industry=industry,
        state=state,
        years_in_business=tib,
        annual_revenue=Decimal("500000"),
        num_trucks=None,
        is_startup=False,
        is_homeowner=is_homeowner,
        is_us_citizen=True,
        guarantor_fico=fico,
        guarantor_fico_source="TransUnion",
        guarantor_is_homeowner=is_homeowner,
        guarantor_has_bankruptcy=has_bankruptcy,
        guarantor_bankruptcy_discharge_date=bankruptcy_discharge_date,
        guarantor_has_judgments=False,
        guarantor_has_foreclosure=False,
        guarantor_has_repossession=False,
        guarantor_has_tax_liens=False,
        guarantor_has_collections_recent=False,
        guarantor_revolving_available_pct=Decimal("60"),
        guarantor_has_cdl=False,
        guarantor_cdl_years=None,
        amount_requested=amount,
        term_months=60,
        equipment_type="Construction Equipment",
        equipment_age_years=3,
        equipment_mileage=None,
        is_private_party_sale=False,
        is_titled_asset=True,
        is_refinance=False,
        is_sale_leaseback=False,
        paynet_score=paynet,
        comparable_credit_pct=Decimal("80"),
    )


def create_test_rule(
    rule_type: str,
    operator: RuleOperator,
    value: any,
    is_required: bool = True,
    weight: int = 10,
) -> PolicyRule:
    """Create a test policy rule"""
    rule = PolicyRule(
        id=uuid4(),
        program_id=uuid4(),
        rule_type=rule_type,
        operator=operator,
        value={"value": value} if not isinstance(value, dict) else value,
        description=f"Test {rule_type} rule",
        rejection_message=f"Failed {rule_type} requirement",
        is_required=is_required,
        priority=100,
        weight=weight,
        is_active=True,
    )
    return rule


# ============== FICO Evaluator Tests ==============

class TestFicoMinEvaluator:
    
    def test_fico_meets_minimum(self):
        """FICO score above minimum should pass"""
        ctx = create_test_context(fico=720)
        rule = create_test_rule("fico_min", RuleOperator.GTE, 700)
        evaluator = FicoMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
        assert result.actual_value == 720
        assert result.required_value == 700
        assert "meets" in result.reason
    
    def test_fico_exactly_at_minimum(self):
        """FICO score exactly at minimum should pass"""
        ctx = create_test_context(fico=700)
        rule = create_test_rule("fico_min", RuleOperator.GTE, 700)
        evaluator = FicoMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
    
    def test_fico_below_minimum(self):
        """FICO score below minimum should fail"""
        ctx = create_test_context(fico=650)
        rule = create_test_rule("fico_min", RuleOperator.GTE, 700)
        evaluator = FicoMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False
        assert result.actual_value == 650
        assert result.required_value == 700
        assert "below" in result.reason


# ============== PayNet Evaluator Tests ==============

class TestPaynetMinEvaluator:
    
    def test_paynet_meets_minimum(self):
        """PayNet score above minimum should pass"""
        ctx = create_test_context(paynet=700)
        rule = create_test_rule("paynet_min", RuleOperator.GTE, 660)
        evaluator = PaynetMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
        assert result.actual_value == 700
    
    def test_paynet_below_minimum(self):
        """PayNet score below minimum should fail"""
        ctx = create_test_context(paynet=600)
        rule = create_test_rule("paynet_min", RuleOperator.GTE, 660)
        evaluator = PaynetMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False
    
    def test_paynet_not_provided(self):
        """Missing PayNet score should fail"""
        ctx = create_test_context(paynet=None)
        rule = create_test_rule("paynet_min", RuleOperator.GTE, 660)
        evaluator = PaynetMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False
        assert result.actual_value is None
        assert "not provided" in result.reason


# ============== Time in Business Tests ==============

class TestTimeInBusinessMinEvaluator:
    
    def test_tib_meets_minimum(self):
        """Time in business above minimum should pass"""
        ctx = create_test_context(tib=5)
        rule = create_test_rule("tib_min", RuleOperator.GTE, 3)
        evaluator = TimeInBusinessMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
        assert result.actual_value == 5
    
    def test_tib_below_minimum(self):
        """Time in business below minimum should fail"""
        ctx = create_test_context(tib=2)
        rule = create_test_rule("tib_min", RuleOperator.GTE, 3)
        evaluator = TimeInBusinessMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False
        assert result.actual_value == 2
        assert result.required_value == 3


# ============== State Exclusion Tests ==============

class TestExcludedStatesEvaluator:
    
    def test_state_not_excluded(self):
        """State not in exclusion list should pass"""
        ctx = create_test_context(state="TX")
        rule = create_test_rule("excluded_states", RuleOperator.NOT_IN, ["CA", "NV", "ND"])
        evaluator = ExcludedStatesEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
        assert result.actual_value == "TX"
    
    def test_state_is_excluded(self):
        """State in exclusion list should fail"""
        ctx = create_test_context(state="CA")
        rule = create_test_rule("excluded_states", RuleOperator.NOT_IN, ["CA", "NV", "ND"])
        evaluator = ExcludedStatesEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False
        assert result.actual_value == "CA"
        assert "is in" in result.reason


# ============== Industry Exclusion Tests ==============

class TestExcludedIndustriesEvaluator:
    
    def test_industry_not_excluded(self):
        """Industry not in exclusion list should pass"""
        ctx = create_test_context(industry="construction")
        rule = create_test_rule("excluded_industries", RuleOperator.NOT_IN, 
                               ["cannabis", "gambling", "trucking"])
        evaluator = ExcludedIndustriesEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
    
    def test_industry_is_excluded(self):
        """Industry in exclusion list should fail"""
        ctx = create_test_context(industry="cannabis")
        rule = create_test_rule("excluded_industries", RuleOperator.NOT_IN,
                               ["cannabis", "gambling", "trucking"])
        evaluator = ExcludedIndustriesEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False
    
    def test_industry_partial_match_excluded(self):
        """Industry with partial match to exclusion should fail"""
        ctx = create_test_context(industry="local trucking company")
        rule = create_test_rule("excluded_industries", RuleOperator.NOT_IN,
                               ["cannabis", "gambling", "trucking"])
        evaluator = ExcludedIndustriesEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False


# ============== Bankruptcy Tests ==============

class TestNoBankruptciesEvaluator:
    
    def test_no_bankruptcy(self):
        """No bankruptcy should pass"""
        ctx = create_test_context(has_bankruptcy=False)
        rule = create_test_rule("no_bankruptcies", RuleOperator.EQ, True)
        evaluator = NoBankruptciesEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
    
    def test_has_bankruptcy(self):
        """Having bankruptcy should fail"""
        ctx = create_test_context(has_bankruptcy=True)
        rule = create_test_rule("no_bankruptcies", RuleOperator.EQ, True)
        evaluator = NoBankruptciesEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False


class TestBankruptcyYearsMinEvaluator:
    
    def test_no_bankruptcy_passes(self):
        """No bankruptcy history should pass minimum years check"""
        ctx = create_test_context(has_bankruptcy=False)
        rule = create_test_rule("bankruptcy_years_min", RuleOperator.GTE, 7)
        evaluator = BankruptcyYearsMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
    
    def test_bankruptcy_old_enough(self):
        """Bankruptcy discharged long ago should pass"""
        discharge_date = date.today() - timedelta(days=365 * 10)  # 10 years ago
        ctx = create_test_context(
            has_bankruptcy=True, 
            bankruptcy_discharge_date=discharge_date
        )
        rule = create_test_rule("bankruptcy_years_min", RuleOperator.GTE, 7)
        evaluator = BankruptcyYearsMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
        assert result.actual_value == 10
    
    def test_bankruptcy_too_recent(self):
        """Recent bankruptcy should fail"""
        discharge_date = date.today() - timedelta(days=365 * 3)  # 3 years ago
        ctx = create_test_context(
            has_bankruptcy=True,
            bankruptcy_discharge_date=discharge_date
        )
        rule = create_test_rule("bankruptcy_years_min", RuleOperator.GTE, 7)
        evaluator = BankruptcyYearsMinEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False
        assert result.actual_value == 3


# ============== Amount Tests ==============

class TestAmountMaxEvaluator:
    
    def test_amount_within_max(self):
        """Loan amount within maximum should pass"""
        ctx = create_test_context(amount=Decimal("50000"))
        rule = create_test_rule("amount_max", RuleOperator.LTE, 75000)
        evaluator = AmountMaxEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
    
    def test_amount_exceeds_max(self):
        """Loan amount exceeding maximum should fail"""
        ctx = create_test_context(amount=Decimal("100000"))
        rule = create_test_rule("amount_max", RuleOperator.LTE, 75000)
        evaluator = AmountMaxEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False
        assert "exceeds" in result.reason


# ============== Homeowner Tests ==============

class TestRequiresHomeownerEvaluator:
    
    def test_is_homeowner(self):
        """Homeowner should pass requirement"""
        ctx = create_test_context(is_homeowner=True)
        rule = create_test_rule("requires_homeowner", RuleOperator.EQ, True)
        evaluator = RequiresHomeownerEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is True
    
    def test_not_homeowner(self):
        """Non-homeowner should fail requirement"""
        ctx = create_test_context(is_homeowner=False)
        rule = create_test_rule("requires_homeowner", RuleOperator.EQ, True)
        evaluator = RequiresHomeownerEvaluator()
        
        result = evaluator.evaluate(ctx, rule)
        
        assert result.passed is False


# ============== Registry Tests ==============

class TestEvaluatorRegistry:
    
    def test_all_evaluators_registered(self):
        """All expected evaluators should be in registry"""
        expected = [
            "fico_min", "paynet_min", "tib_min", "amount_min", "amount_max",
            "excluded_states", "excluded_industries", "no_bankruptcies",
            "bankruptcy_years_min", "requires_homeowner", "requires_us_citizen",
        ]
        
        for rule_type in expected:
            assert get_evaluator(rule_type) is not None, f"Missing evaluator for {rule_type}"
    
    def test_unknown_evaluator_returns_none(self):
        """Unknown rule type should return None"""
        evaluator = get_evaluator("unknown_rule_type")
        assert evaluator is None


# ============== Scoring Tests ==============

class TestFitScoreCalculation:
    
    def test_all_rules_pass(self):
        """Perfect score when all rules pass"""
        from app.engine.evaluators import EvaluationResult
        
        results = [
            EvaluationResult(True, "fico_min", "1", 700, 720, True, "Pass", 10),
            EvaluationResult(True, "paynet_min", "2", 660, 680, True, "Pass", 10),
            EvaluationResult(True, "tib_min", "3", 3, 5, True, "Pass", 10),
        ]
        
        score = calculate_fit_score(results)
        
        assert score == 100
    
    def test_all_rules_fail(self):
        """Low score when all rules fail"""
        from app.engine.evaluators import EvaluationResult
        
        results = [
            EvaluationResult(False, "fico_min", "1", 700, 650, True, "Fail", 10),
            EvaluationResult(False, "paynet_min", "2", 660, 600, True, "Fail", 10),
            EvaluationResult(False, "tib_min", "3", 3, 1, True, "Fail", 10),
        ]
        
        score = calculate_fit_score(results)
        
        assert score < 50
    
    def test_mixed_results(self):
        """Medium score with mixed pass/fail"""
        from app.engine.evaluators import EvaluationResult
        
        results = [
            EvaluationResult(True, "fico_min", "1", 700, 720, True, "Pass", 10),
            EvaluationResult(False, "paynet_min", "2", 660, 600, True, "Fail", 10),
            EvaluationResult(True, "tib_min", "3", 3, 5, False, "Pass", 10),
        ]
        
        score = calculate_fit_score(results)
        
        # Should be between 0 and 100
        assert 0 <= score <= 100
    
    def test_empty_results(self):
        """Zero score with no results"""
        score = calculate_fit_score([])
        assert score == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

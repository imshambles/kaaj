"""
Lender Matcher - Core matching engine that evaluates applications against lender policies
"""
from typing import List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models import (
    Borrower, Guarantor, LoanApplication, 
    Lender, LenderProgram, PolicyRule, MatchResult
)
from app.engine.evaluators import (
    EvaluationContext, EvaluationResult, 
    get_evaluator, EVALUATOR_REGISTRY
)
from app.engine.scoring import calculate_fit_score, calculate_program_priority_score


@dataclass
class ProgramEvaluation:
    """Result of evaluating an application against a program"""
    program: LenderProgram
    is_eligible: bool
    fit_score: int
    results: List[EvaluationResult]
    passed_count: int
    failed_count: int


@dataclass
class LenderEvaluation:
    """Result of evaluating an application against a lender"""
    lender: Lender
    best_program: Optional[ProgramEvaluation]
    all_programs: List[ProgramEvaluation]
    is_eligible: bool
    fit_score: int


class LenderMatcher:
    """
    Core matching engine that evaluates loan applications against lender policies.
    
    Usage:
        matcher = LenderMatcher(db_session)
        results = matcher.match_application(application)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def build_context(self, application: LoanApplication) -> EvaluationContext:
        """Build evaluation context from application and related entities"""
        borrower = application.borrower
        
        # Get primary guarantor (highest ownership %)
        guarantors = sorted(
            borrower.guarantors, 
            key=lambda g: g.ownership_percentage, 
            reverse=True
        )
        primary_guarantor = guarantors[0] if guarantors else None
        
        return EvaluationContext(
            # Borrower
            business_name=borrower.business_name,
            industry=borrower.industry,
            state=borrower.state,
            years_in_business=borrower.years_in_business,
            annual_revenue=borrower.annual_revenue,
            num_trucks=borrower.num_trucks,
            is_startup=borrower.is_startup,
            is_homeowner=borrower.is_homeowner,
            is_us_citizen=borrower.is_us_citizen,
            
            # Primary Guarantor
            guarantor_fico=primary_guarantor.fico_score if primary_guarantor else 0,
            guarantor_fico_source=primary_guarantor.fico_source if primary_guarantor else "",
            guarantor_is_homeowner=primary_guarantor.is_homeowner if primary_guarantor else False,
            guarantor_has_bankruptcy=primary_guarantor.has_bankruptcy if primary_guarantor else False,
            guarantor_bankruptcy_discharge_date=primary_guarantor.bankruptcy_discharge_date if primary_guarantor else None,
            guarantor_has_judgments=primary_guarantor.has_judgments if primary_guarantor else False,
            guarantor_has_foreclosure=primary_guarantor.has_foreclosure if primary_guarantor else False,
            guarantor_has_repossession=primary_guarantor.has_repossession if primary_guarantor else False,
            guarantor_has_tax_liens=primary_guarantor.has_tax_liens if primary_guarantor else False,
            guarantor_has_collections_recent=primary_guarantor.has_collections_recent if primary_guarantor else False,
            guarantor_revolving_available_pct=primary_guarantor.revolving_available_pct if primary_guarantor else None,
            guarantor_has_cdl=primary_guarantor.has_cdl if primary_guarantor else False,
            guarantor_cdl_years=primary_guarantor.cdl_years if primary_guarantor else None,
            
            # Application
            amount_requested=application.amount_requested,
            term_months=application.term_months,
            equipment_type=application.equipment_type,
            equipment_age_years=application.equipment_age_years,
            equipment_mileage=application.equipment_mileage,
            is_private_party_sale=application.is_private_party_sale,
            is_titled_asset=application.is_titled_asset,
            is_refinance=application.is_refinance,
            is_sale_leaseback=application.is_sale_leaseback,
            paynet_score=application.paynet_score,
            comparable_credit_pct=application.comparable_credit_pct,
        )
    
    def evaluate_program(
        self, 
        ctx: EvaluationContext, 
        program: LenderProgram
    ) -> ProgramEvaluation:
        """Evaluate an application against a single program's rules"""
        results: List[EvaluationResult] = []
        
        # Get active rules sorted by priority
        rules = sorted(
            [r for r in program.rules if r.is_active],
            key=lambda r: r.priority
        )
        
        for rule in rules:
            evaluator = get_evaluator(rule.rule_type)
            if evaluator:
                result = evaluator.evaluate(ctx, rule)
                results.append(result)
            else:
                # Unknown rule type - log warning but don't fail
                print(f"Warning: No evaluator for rule type '{rule.rule_type}'")
        
        # Calculate eligibility and score
        required_failed = any(
            not r.passed and r.is_required 
            for r in results
        )
        is_eligible = not required_failed
        fit_score = calculate_fit_score(results)
        
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        
        return ProgramEvaluation(
            program=program,
            is_eligible=is_eligible,
            fit_score=fit_score,
            results=results,
            passed_count=len(passed),
            failed_count=len(failed),
        )
    
    def evaluate_lender(
        self, 
        ctx: EvaluationContext, 
        lender: Lender
    ) -> LenderEvaluation:
        """Evaluate an application against all of a lender's programs"""
        program_evaluations: List[ProgramEvaluation] = []
        
        # Get active programs sorted by priority
        programs = sorted(
            [p for p in lender.programs if p.is_active],
            key=lambda p: p.priority
        )
        
        for program in programs:
            eval_result = self.evaluate_program(ctx, program)
            program_evaluations.append(eval_result)
        
        # Find best program (eligible first, then by fit score)
        eligible_programs = [p for p in program_evaluations if p.is_eligible]
        
        if eligible_programs:
            best = max(eligible_programs, key=lambda p: p.fit_score)
        elif program_evaluations:
            # No eligible programs - return best scoring ineligible
            best = max(program_evaluations, key=lambda p: p.fit_score)
        else:
            best = None
        
        return LenderEvaluation(
            lender=lender,
            best_program=best,
            all_programs=program_evaluations,
            is_eligible=best.is_eligible if best else False,
            fit_score=best.fit_score if best else 0,
        )
    
    def match_application(
        self, 
        application: LoanApplication
    ) -> List[MatchResult]:
        """
        Evaluate an application against all active lenders.
        Returns list of MatchResult objects (persisted to DB).
        """
        # Build context
        ctx = self.build_context(application)
        
        # Get all active lenders
        lenders = self.db.query(Lender).filter(Lender.is_active == True).all()
        
        results: List[MatchResult] = []
        
        for lender in lenders:
            lender_eval = self.evaluate_lender(ctx, lender)
            
            # Build evaluation details
            best_program = lender_eval.best_program
            
            if best_program:
                passed_details = [r.to_dict() for r in best_program.results if r.passed]
                failed_details = [r.to_dict() for r in best_program.results if not r.passed]
                
                evaluation_details = {
                    "rules_evaluated": len(best_program.results),
                    "rules_passed": best_program.passed_count,
                    "rules_failed": best_program.failed_count,
                    "pass_rate": best_program.passed_count / len(best_program.results) if best_program.results else 0,
                    "details": [r.to_dict() for r in best_program.results],
                    "summary": {
                        "passed": passed_details,
                        "failed": failed_details,
                        "warnings": [],
                    }
                }
            else:
                evaluation_details = {
                    "rules_evaluated": 0,
                    "rules_passed": 0,
                    "rules_failed": 0,
                    "pass_rate": 0,
                    "details": [],
                    "summary": {
                        "passed": [],
                        "failed": [],
                        "warnings": ["No active programs found for this lender"],
                    }
                }
            
            # Create MatchResult
            match_result = MatchResult(
                application_id=application.id,
                lender_id=lender.id,
                program_id=best_program.program.id if best_program else None,
                is_eligible=lender_eval.is_eligible,
                fit_score=lender_eval.fit_score,
                evaluation_details=evaluation_details,
            )
            
            self.db.add(match_result)
            results.append(match_result)
        
        self.db.commit()
        
        # Sort by eligibility then fit score
        results.sort(key=lambda r: (-int(r.is_eligible), -r.fit_score))
        
        return results
    
    def get_supported_rule_types(self) -> List[str]:
        """Return list of all supported rule types"""
        return list(EVALUATOR_REGISTRY.keys())

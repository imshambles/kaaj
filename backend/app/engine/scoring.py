"""
Fit Score Calculator - Calculates match quality score (0-100)
"""
from typing import List
from app.engine.evaluators import EvaluationResult


def calculate_fit_score(results: List[EvaluationResult]) -> int:
    """
    Calculate fit score (0-100) based on rule evaluation results.
    
    Scoring algorithm:
    - Base: (passed_weighted / total_weighted) * 70 points
    - Bonus: +15 for no failed REQUIRED rules
    - Bonus: +15 for exceeding 90% pass rate on weighted rules
    
    This gives:
    - A perfect match: 100
    - All required passed but some soft failed: 85+
    - Some required failed: typically 50-70
    - Major failures: <50
    """
    if not results:
        return 0
    
    total_weight = sum(r.weight for r in results)
    passed_weight = sum(r.weight for r in results if r.passed)
    
    # Required rules
    required_results = [r for r in results if r.is_required]
    required_passed = all(r.passed for r in required_results)
    
    if total_weight == 0:
        return 100 if required_passed else 50
    
    # Base score (70 max)
    base_score = (passed_weight / total_weight) * 70
    
    # Bonus for all required rules passing (+15)
    required_bonus = 15 if required_passed else 0
    
    # Bonus for high pass rate (+15)
    pass_rate = passed_weight / total_weight
    high_pass_bonus = 15 if pass_rate >= 0.9 else 0
    
    total_score = base_score + required_bonus + high_pass_bonus
    
    return min(100, max(0, round(total_score)))


def calculate_program_priority_score(
    fit_score: int,
    program_priority: int,
    is_eligible: bool
) -> float:
    """
    Calculate a composite score for ranking programs.
    Lower is better (used for sorting).
    
    Considers:
    - Eligibility (eligible programs always rank higher)
    - Fit score (higher is better)
    - Program priority (lower priority number = preferred)
    """
    if not is_eligible:
        # Ineligible programs get a high base score
        return 1000 + (100 - fit_score) + program_priority
    
    # Eligible: lower score = better
    # Invert fit_score so higher fit = lower ranking score
    return (100 - fit_score) + (program_priority / 100)

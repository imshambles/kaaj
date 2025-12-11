# Design Decisions

This document outlines key architectural decisions, trade-offs, and prioritizations made during development.

## Lender Requirements Prioritized

Based on the 5 PDF guidelines, I prioritized the following criteria as most commonly required:

### Tier 1 (Implemented with full evaluation)
- **FICO Score** - All lenders require minimum FICO (680-725 range)
- **PayNet Score** - 4/5 lenders require PayNet business credit score
- **Time in Business** - All require 2-5 years minimum
- **State Exclusions** - Apex excludes CA, NV, ND, VT; Citizens excludes CA
- **Industry Exclusions** - Multiple lenders exclude trucking, cannabis, gambling
- **Loan Amount Limits** - Min/max per program
- **Bankruptcy History** - Most require clean history or 5-15 years since discharge

### Tier 2 (Implemented)
- **Homeowner Requirement** - Citizens Bank Tier 1/2
- **Judgments/Foreclosures/Repossessions** - Advantage+ has strict "no" policy
- **Tax Liens** - Advantage+ excludes
- **Comparable Credit** - Falcon requires 70%, Advantage+ prefers 80%
- **Revolving Credit Available** - Apex A/B require 50% available
- **US Citizenship** - Citizens, Advantage+ require
- **Private Party Sales** - Several lenders restrict
- **CDL Requirements** - Trucking-specific

### Tier 3 (Partially implemented/deferred)
- **Equipment Age/Mileage** - Complex tier-based rules by vehicle type
- **Specific Equipment Types** - Detailed model year requirements from Citizens Bank
- **Financial Statement Analysis** - Requires document processing

## Simplifications Made

### 1. Single Primary Guarantor
**Decision**: Use only the primary guarantor (highest ownership %) for credit evaluation.
**Reason**: Real underwriting evaluates all guarantors with 10%+ ownership. Simplifying to one reduces complexity while demonstrating the pattern.
**Future**: Add multi-guarantor evaluation with aggregate scoring.

### 2. Simplified Equipment Age Rules
**Decision**: Single `equipment_age_max` rule per program.
**Reason**: Citizens Bank has complex mileage+age matrices by vehicle type. Implementing full matrix would require significant additional schema.
**Future**: Add equipment type-specific rule conditions.

### 3. No Document Processing
**Decision**: Manual data entry rather than parsing uploaded financials.
**Reason**: Tax return/bank statement parsing requires ML/OCR beyond scope.
**Future**: Integrate document AI for automated data extraction.

### 4. Synchronous Underwriting
**Decision**: Simple synchronous workflow execution.
**Reason**: For 5 lenders, matching completes quickly enough that async orchestration adds unnecessary complexity.

### 5. Basic Fit Score Algorithm
**Decision**: Simple weighted pass rate + bonuses for required rules.
**Reason**: Sufficient for ranking; real scoring would incorporate rate quotes.
**Future**: Integrate actual rate tables for APR-based scoring.

## What I Would Add With More Time

### High Priority
1. **Rate Calculation** - Return actual rate quotes based on tier + amount + term
2. **Document Upload** - Accept equipment invoices, financials, credit reports
3. **Multi-Guarantor Evaluation** - Aggregate scoring across all owners
4. **Equipment Type Matrix** - Full Citizens Bank age/mileage rules
5. **Async Processing** - Queue-based underwriting for high-volume scenarios

### Medium Priority
6. **Audit Trail** - Log all rule evaluations and changes
7. **A/B Testing** - Compare rule configurations
8. **Batch Applications** - Process multiple at once
9. **Webhook Notifications** - Notify on underwriting complete
10. **Export Results** - PDF report generation

### Nice to Have
11. **Dark/Light Theme Toggle** - Currently dark only
12. **Mobile Responsive** - Basic support exists, needs polish
13. **Keyboard Navigation** - Accessibility improvements
14. **Real-time Updates** - WebSocket for status changes
15. **Analytics Dashboard** - Approval rates, common rejection reasons

## Schema Design Rationale

### JSONB for Policy Rules
**Decision**: Store rule values in JSONB column rather than typed columns.
**Benefits**:
- Add new rule types without schema migration
- Support arrays (excluded states), objects, and scalars
- Flexible operator comparisons

**Trade-off**: Less database-level validation, but application-level enforcement is sufficient.

### Separate Program and Rule Tables
**Decision**: `LenderProgram` → `PolicyRule` one-to-many relationship.
**Benefits**:
- Same lender can have multiple programs (Tier 1, Tier 2, Medical)
- Rules can be reordered/prioritized per program
- Easy to copy programs between lenders

### Registry Pattern for Evaluators
**Decision**: Map rule types to evaluator classes via dictionary registry.
**Benefits**:
- O(1) lookup of evaluator by rule type
- Easy to add new evaluators without modifying core matcher
- Each evaluator is self-contained and testable

## Performance Considerations

- **Eager Loading**: Applications load borrower/guarantors in single query
- **Rule Sorting**: Evaluate required rules first for early exit on failure
- **Result Caching**: Match results persisted for re-display without re-evaluation
- **Index Strategy**: Indexes on `lender.is_active`, `program.is_active`, `rule.is_active`

## Security Notes (Production Considerations)

- Add JWT authentication before deploying
- Rate limit API endpoints
- Encrypt sensitive financial data at rest
- Audit logging for all policy changes
- Input validation already enforced via Pydantic

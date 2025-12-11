"""
Applications API - CRUD operations for loan applications
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Borrower, Guarantor, LoanApplication, ApplicationStatus, MatchResult
from app.schemas import (
    LoanApplicationCreate, LoanApplicationUpdate, LoanApplicationResponse,
    BorrowerResponse, UnderwritingResultsResponse, MatchResultResponse
)
from app.services.workflow import run_underwriting as run_underwriting_workflow

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("", response_model=LoanApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    data: LoanApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new loan application with borrower and guarantor information.
    """
    # Create borrower
    borrower = Borrower(
        business_name=data.borrower.business_name,
        dba_name=data.borrower.dba_name,
        industry=data.borrower.industry,
        industry_naics=data.borrower.industry_naics,
        state=data.borrower.state,
        years_in_business=data.borrower.years_in_business,
        annual_revenue=data.borrower.annual_revenue,
        num_employees=data.borrower.num_employees,
        num_trucks=data.borrower.num_trucks,
        is_startup=data.borrower.is_startup,
        is_homeowner=data.borrower.is_homeowner,
        is_us_citizen=data.borrower.is_us_citizen,
    )
    db.add(borrower)
    db.flush()
    
    # Create guarantors
    for g_data in data.borrower.guarantors:
        guarantor = Guarantor(
            borrower_id=borrower.id,
            first_name=g_data.first_name,
            last_name=g_data.last_name,
            ownership_percentage=g_data.ownership_percentage,
            fico_score=g_data.fico_score,
            fico_source=g_data.fico_source,
            is_homeowner=g_data.is_homeowner,
            years_at_residence=g_data.years_at_residence,
            has_bankruptcy=g_data.has_bankruptcy,
            bankruptcy_type=g_data.bankruptcy_type,
            bankruptcy_discharge_date=g_data.bankruptcy_discharge_date,
            has_judgments=g_data.has_judgments,
            has_foreclosure=g_data.has_foreclosure,
            has_repossession=g_data.has_repossession,
            has_tax_liens=g_data.has_tax_liens,
            has_collections_recent=g_data.has_collections_recent,
            revolving_credit_limit=g_data.revolving_credit_limit,
            revolving_credit_balance=g_data.revolving_credit_balance,
            revolving_available_pct=g_data.revolving_available_pct,
            has_cdl=g_data.has_cdl,
            cdl_years=g_data.cdl_years,
            cdl_class=g_data.cdl_class,
        )
        db.add(guarantor)
    
    # Create application
    application = LoanApplication(
        borrower_id=borrower.id,
        amount_requested=data.application.amount_requested,
        term_months=data.application.term_months,
        down_payment_pct=data.application.down_payment_pct,
        equipment_type=data.application.equipment_type,
        equipment_description=data.application.equipment_description,
        equipment_year=data.application.equipment_year,
        equipment_age_years=data.application.equipment_age_years,
        equipment_mileage=data.application.equipment_mileage,
        equipment_hours=data.application.equipment_hours,
        equipment_condition=data.application.equipment_condition,
        is_private_party_sale=data.application.is_private_party_sale,
        is_titled_asset=data.application.is_titled_asset,
        is_refinance=data.application.is_refinance,
        is_sale_leaseback=data.application.is_sale_leaseback,
        paynet_score=data.application.paynet_score,
        has_comparable_credit=data.application.has_comparable_credit,
        comparable_credit_amount=data.application.comparable_credit_amount,
        comparable_credit_pct=data.application.comparable_credit_pct,
        status=ApplicationStatus.DRAFT,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    return application


@router.get("", response_model=List[LoanApplicationResponse])
def list_applications(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all loan applications with optional status filter.
    """
    query = db.query(LoanApplication)
    
    if status:
        query = query.filter(LoanApplication.status == status)
    
    applications = query.order_by(LoanApplication.created_at.desc()).offset(skip).limit(limit).all()
    return applications


@router.get("/{application_id}", response_model=LoanApplicationResponse)
def get_application(
    application_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific loan application by ID.
    """
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    
    return application


@router.put("/{application_id}", response_model=LoanApplicationResponse)
def update_application(
    application_id: UUID,
    data: LoanApplicationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a loan application.
    """
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    
    # Update fields that are provided
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)
    
    db.commit()
    db.refresh(application)
    
    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a loan application.
    """
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    
    db.delete(application)
    db.commit()


@router.post("/{application_id}/underwrite")
def run_underwriting(
    application_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Run underwriting on a loan application.
    Evaluates the application against all active lenders.
    """
    # Verify application exists
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    
    # Run underwriting
    result = run_underwriting_workflow(str(application_id))
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.get("/{application_id}/results", response_model=UnderwritingResultsResponse)
def get_results(
    application_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get underwriting results for a loan application.
    """
    application = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    
    results = db.query(MatchResult).filter(
        MatchResult.application_id == application_id
    ).order_by(MatchResult.is_eligible.desc(), MatchResult.fit_score.desc()).all()
    
    # Build response
    eligible = [r for r in results if r.is_eligible]
    ineligible = [r for r in results if not r.is_eligible]
    best_match = eligible[0] if eligible else None
    
    result_responses = []
    for r in results:
        result_responses.append(MatchResultResponse(
            id=r.id,
            application_id=r.application_id,
            lender_id=r.lender_id,
            program_id=r.program_id,
            is_eligible=r.is_eligible,
            fit_score=r.fit_score,
            evaluation_details=r.evaluation_details,
            created_at=r.created_at,
            lender_name=r.lender.name if r.lender else None,
            program_name=r.program.name if r.program else None,
        ))
    
    return UnderwritingResultsResponse(
        application_id=application_id,
        status=application.status,
        total_lenders=len(results),
        eligible_count=len(eligible),
        ineligible_count=len(ineligible),
        best_match=result_responses[0] if eligible else None,
        results=result_responses,
    )

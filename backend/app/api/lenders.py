"""
Lenders API - CRUD operations for lenders and their programs
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lender, LenderProgram, PolicyRule
from app.schemas import (
    LenderCreate, LenderUpdate, LenderResponse, LenderSummary,
    LenderProgramCreate, LenderProgramUpdate, LenderProgramResponse,
    PolicyRuleCreate, PolicyRuleUpdate, PolicyRuleResponse
)

router = APIRouter(prefix="/api/lenders", tags=["lenders"])


# ============== Utility Endpoints (must be before parameterized routes) ==============

@router.get("/rule-types", response_model=List[str])
def get_rule_types():
    """
    Get all supported rule types.
    """
    from app.engine import EVALUATOR_REGISTRY
    return list(EVALUATOR_REGISTRY.keys())


# ============== Lender Endpoints ==============

@router.get("", response_model=List[LenderSummary])
def list_lenders(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all lenders.
    """
    query = db.query(Lender)
    
    if active_only:
        query = query.filter(Lender.is_active == True)
    
    lenders = query.order_by(Lender.name).all()
    
    return [
        LenderSummary(
            id=l.id,
            name=l.name,
            short_name=l.short_name,
            is_active=l.is_active,
            program_count=len([p for p in l.programs if p.is_active])
        )
        for l in lenders
    ]


@router.get("/{lender_id}", response_model=LenderResponse)
def get_lender(
    lender_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific lender with all programs and rules.
    """
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    
    if not lender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender {lender_id} not found"
        )
    
    return lender


@router.post("", response_model=LenderResponse, status_code=status.HTTP_201_CREATED)
def create_lender(
    data: LenderCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new lender with optional programs and rules.
    """
    # Check for duplicate name
    existing = db.query(Lender).filter(Lender.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lender with name '{data.name}' already exists"
        )
    
    # Create lender
    lender = Lender(
        name=data.name,
        short_name=data.short_name,
        description=data.description,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        website=data.website,
        is_active=data.is_active,
    )
    db.add(lender)
    db.flush()
    
    # Create programs
    for p_data in data.programs:
        program = LenderProgram(
            lender_id=lender.id,
            name=p_data.name,
            description=p_data.description,
            credit_tier=p_data.credit_tier,
            min_loan_amount=p_data.min_loan_amount,
            max_loan_amount=p_data.max_loan_amount,
            max_term_months=p_data.max_term_months,
            is_app_only=p_data.is_app_only,
            requires_financials=p_data.requires_financials,
            priority=p_data.priority,
            is_active=p_data.is_active,
        )
        db.add(program)
        db.flush()
        
        # Create rules
        for r_data in p_data.rules:
            rule = PolicyRule(
                program_id=program.id,
                rule_type=r_data.rule_type,
                operator=r_data.operator,
                value=r_data.value if isinstance(r_data.value, dict) else {"value": r_data.value},
                description=r_data.description,
                rejection_message=r_data.rejection_message,
                is_required=r_data.is_required,
                priority=r_data.priority,
                weight=r_data.weight,
                is_active=r_data.is_active,
            )
            db.add(rule)
    
    db.commit()
    db.refresh(lender)
    
    return lender


@router.put("/{lender_id}", response_model=LenderResponse)
def update_lender(
    lender_id: UUID,
    data: LenderUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a lender.
    """
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    
    if not lender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender {lender_id} not found"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lender, field, value)
    
    db.commit()
    db.refresh(lender)
    
    return lender


@router.delete("/{lender_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lender(
    lender_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a lender (cascades to programs and rules).
    """
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    
    if not lender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender {lender_id} not found"
        )
    
    db.delete(lender)
    db.commit()


# ============== Program Endpoints ==============

@router.get("/{lender_id}/programs", response_model=List[LenderProgramResponse])
def list_programs(
    lender_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all programs for a lender.
    """
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    
    if not lender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender {lender_id} not found"
        )
    
    return lender.programs


@router.post("/{lender_id}/programs", response_model=LenderProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program(
    lender_id: UUID,
    data: LenderProgramCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new program for a lender.
    """
    lender = db.query(Lender).filter(Lender.id == lender_id).first()
    
    if not lender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lender {lender_id} not found"
        )
    
    program = LenderProgram(
        lender_id=lender.id,
        name=data.name,
        description=data.description,
        credit_tier=data.credit_tier,
        min_loan_amount=data.min_loan_amount,
        max_loan_amount=data.max_loan_amount,
        max_term_months=data.max_term_months,
        is_app_only=data.is_app_only,
        requires_financials=data.requires_financials,
        priority=data.priority,
        is_active=data.is_active,
    )
    db.add(program)
    db.flush()
    
    # Create rules
    for r_data in data.rules:
        rule = PolicyRule(
            program_id=program.id,
            rule_type=r_data.rule_type,
            operator=r_data.operator,
            value=r_data.value if isinstance(r_data.value, dict) else {"value": r_data.value},
            description=r_data.description,
            rejection_message=r_data.rejection_message,
            is_required=r_data.is_required,
            priority=r_data.priority,
            weight=r_data.weight,
            is_active=r_data.is_active,
        )
        db.add(rule)
    
    db.commit()
    db.refresh(program)
    
    return program


@router.put("/programs/{program_id}", response_model=LenderProgramResponse)
def update_program(
    program_id: UUID,
    data: LenderProgramUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a program.
    """
    program = db.query(LenderProgram).filter(LenderProgram.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program {program_id} not found"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(program, field, value)
    
    db.commit()
    db.refresh(program)
    
    return program


@router.delete("/programs/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(
    program_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a program (cascades to rules).
    """
    program = db.query(LenderProgram).filter(LenderProgram.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program {program_id} not found"
        )
    
    db.delete(program)
    db.commit()


# ============== Rule Endpoints ==============

@router.get("/programs/{program_id}/rules", response_model=List[PolicyRuleResponse])
def list_rules(
    program_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all rules for a program.
    """
    program = db.query(LenderProgram).filter(LenderProgram.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program {program_id} not found"
        )
    
    return program.rules


@router.post("/programs/{program_id}/rules", response_model=PolicyRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    program_id: UUID,
    data: PolicyRuleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new rule for a program.
    """
    program = db.query(LenderProgram).filter(LenderProgram.id == program_id).first()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Program {program_id} not found"
        )
    
    rule = PolicyRule(
        program_id=program.id,
        rule_type=data.rule_type,
        operator=data.operator,
        value=data.value if isinstance(data.value, dict) else {"value": data.value},
        description=data.description,
        rejection_message=data.rejection_message,
        is_required=data.is_required,
        priority=data.priority,
        weight=data.weight,
        is_active=data.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.put("/rules/{rule_id}", response_model=PolicyRuleResponse)
def update_rule(
    rule_id: UUID,
    data: PolicyRuleUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a rule.
    """
    rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle value serialization
    if "value" in update_data and not isinstance(update_data["value"], dict):
        update_data["value"] = {"value": update_data["value"]}
    
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a rule.
    """
    rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )
    
    db.delete(rule)
    db.commit()


# Note: /rule-types endpoint moved to top of file to ensure proper route ordering

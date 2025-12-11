"""
Seed script to populate database with lender policies from parsed PDFs.

This script creates all 5 lenders with their programs and rules based on
the guidelines from the PDF files.

Run with: python seed_lenders.py
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal, engine, Base
from app.models import Lender, LenderProgram, PolicyRule, RuleOperator, CreditTier

# Create tables
Base.metadata.create_all(bind=engine)


def seed_falcon_equipment_finance(db):
    """
    Falcon Equipment Finance - from 112025 Rates - STANDARD.pdf
    
    Key requirements:
    - 3+ Years in business
    - FICO 680+
    - PayNet 660+
    - Trucking: 5+ years, 700 FICO, 5+ trucks
    """
    lender = Lender(
        name="Falcon Equipment Finance",
        short_name="Falcon",
        description="Equipment finance lender with specialized trucking programs",
        contact_name="Emma Tickner",
        contact_email="ETickner@FalconEquipmentFinance.com",
        contact_phone="651-332-6517",
        website="www.FalconEquipmentFinance.com",
        is_active=True,
    )
    db.add(lender)
    db.flush()
    
    # Standard Program (A/B Credit)
    standard = LenderProgram(
        lender_id=lender.id,
        name="Standard Program",
        description="Standard equipment financing for A/B credit",
        credit_tier=CreditTier.A,
        min_loan_amount=15000,
        max_loan_amount=350000,
        max_term_months=60,
        is_app_only=True,
        priority=10,
        is_active=True,
    )
    db.add(standard)
    db.flush()
    
    # Standard rules
    standard_rules = [
        PolicyRule(
            program_id=standard.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 3},
            description="Minimum 3 years in business",
            rejection_message="Business must have at least 3 years of operation",
            is_required=True,
            priority=10,
            weight=15,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 680},
            description="Minimum FICO score 680",
            rejection_message="FICO score must be at least 680",
            is_required=True,
            priority=20,
            weight=20,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="paynet_min",
            operator=RuleOperator.GTE,
            value={"value": 660},
            description="Minimum PayNet score 660",
            rejection_message="PayNet score must be at least 660",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="amount_min",
            operator=RuleOperator.GTE,
            value={"value": 15000},
            description="Minimum loan amount $15,000",
            rejection_message="Minimum loan amount is $15,000",
            is_required=True,
            priority=40,
            weight=5,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="amount_max",
            operator=RuleOperator.LTE,
            value={"value": 250000},
            description="Maximum loan amount $250,000 for commercial",
            rejection_message="Maximum loan amount is $250,000 for commercial transactions",
            is_required=True,
            priority=50,
            weight=10,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="bankruptcy_years_min",
            operator=RuleOperator.GTE,
            value={"value": 15},
            description="Bankruptcies must be 15+ years discharged",
            rejection_message="Bankruptcy must be discharged for at least 15 years",
            is_required=True,
            priority=60,
            weight=15,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="comparable_credit_pct",
            operator=RuleOperator.GTE,
            value={"value": 70},
            description="Comparable credit at least 70% of requested amount",
            rejection_message="Must have comparable commercial installment credit at 70% of requested amount",
            is_required=True,
            priority=70,
            weight=10,
        ),
    ]
    for rule in standard_rules:
        db.add(rule)
    
    # Trucking Program (stricter requirements)
    trucking = LenderProgram(
        lender_id=lender.id,
        name="Trucking Program",
        description="Specialized trucking/class 8 financing - A/B Credit Only",
        credit_tier=CreditTier.A,
        min_loan_amount=15000,
        max_loan_amount=250000,
        max_term_months=60,
        is_app_only=True,
        priority=20,
        is_active=True,
    )
    db.add(trucking)
    db.flush()
    
    # Trucking rules  
    trucking_rules = [
        PolicyRule(
            program_id=trucking.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 5},
            description="Minimum 5 years in business for trucking",
            rejection_message="Trucking applicants must have at least 5 years in business",
            is_required=True,
            priority=10,
            weight=15,
        ),
        PolicyRule(
            program_id=trucking.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 700},
            description="Minimum FICO 700 for trucking",
            rejection_message="Trucking applicants must have FICO score of at least 700",
            is_required=True,
            priority=20,
            weight=20,
        ),
        PolicyRule(
            program_id=trucking.id,
            rule_type="paynet_min",
            operator=RuleOperator.GTE,
            value={"value": 680},
            description="Minimum PayNet 680 for trucking",
            rejection_message="Trucking applicants must have PayNet score of at least 680",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=trucking.id,
            rule_type="num_trucks_min",
            operator=RuleOperator.GTE,
            value={"value": 5},
            description="Must be operating 5+ trucks",
            rejection_message="Trucking company must be operating at least 5 trucks",
            is_required=True,
            priority=40,
            weight=15,
        ),
        PolicyRule(
            program_id=trucking.id,
            rule_type="equipment_age_max",
            operator=RuleOperator.LTE,
            value={"value": 10},
            description="Class 8 trucks must be 10 years or newer",
            rejection_message="Class 8 trucks and trailers must be 10 years or newer",
            is_required=True,
            priority=50,
            weight=10,
        ),
        PolicyRule(
            program_id=trucking.id,
            rule_type="amount_max",
            operator=RuleOperator.LTE,
            value={"value": 150000},
            description="App only up to $150,000 for trucking",
            rejection_message="Maximum app-only amount for trucking is $150,000",
            is_required=True,
            priority=60,
            weight=10,
        ),
    ]
    for rule in trucking_rules:
        db.add(rule)
    
    print(f"Created: {lender.name}")
    return lender


def seed_citizens_bank(db):
    """
    Citizens Bank - from 2025 Program Guidelines UPDATED.pdf
    
    Key requirements:
    - Tier 1: $75K max, 700+ TransUnion, 2yr TIB, homeowner
    - Tier 2: $50K max, startup, 700+ FICO, homeowner
    - Tier 3: $75K-$1M with full financials
    - No CA applicants
    """
    lender = Lender(
        name="Citizens Bank",
        short_name="Citizens",
        description="Equipment finance with tiered programs",
        contact_name="Joey Walter",
        contact_email="joey.walter@thecitizensbank.net",
        contact_phone="501-451-5113",
        is_active=True,
    )
    db.add(lender)
    db.flush()
    
    # Tier 1 Program
    tier1 = LenderProgram(
        lender_id=lender.id,
        name="Tier 1 - Standard",
        description="$75K max, app only for established businesses",
        credit_tier=CreditTier.A,
        min_loan_amount=10000,
        max_loan_amount=75000,
        max_term_months=60,
        is_app_only=True,
        priority=10,
        is_active=True,
    )
    db.add(tier1)
    db.flush()
    
    tier1_rules = [
        PolicyRule(
            program_id=tier1.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 700},
            description="700+ TransUnion Credit Score",
            rejection_message="TransUnion credit score must be at least 700",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 2},
            description="2 years time in business required",
            rejection_message="Must have at least 2 years in business",
            is_required=True,
            priority=20,
            weight=15,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="requires_homeowner",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="Homeownership required",
            rejection_message="Homeownership is required for Tier 1",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="excluded_states",
            operator=RuleOperator.NOT_IN,
            value={"value": ["CA"]},
            description="No financing for California applicants",
            rejection_message="Citizens Bank does not provide financing for applicants in California",
            is_required=True,
            priority=40,
            weight=10,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="requires_us_citizen",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="US Citizen required",
            rejection_message="Customers must be US Citizens",
            is_required=True,
            priority=50,
            weight=10,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="no_refinance",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No refinance transactions",
            rejection_message="Refinance transactions are not considered",
            is_required=True,
            priority=60,
            weight=5,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="no_sale_leaseback",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No sale-leaseback transactions",
            rejection_message="Sale-leaseback or cash out transactions are not offered",
            is_required=True,
            priority=70,
            weight=5,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="bankruptcy_years_min",
            operator=RuleOperator.GTE,
            value={"value": 5},
            description="Bankruptcies must be over 5 years discharged",
            rejection_message="Previous bankruptcy must be over 5 years discharged",
            is_required=True,
            priority=80,
            weight=15,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="excluded_industries",
            operator=RuleOperator.NOT_IN,
            value={"value": ["cannabis", "marijuana"]},
            description="No cannabis related businesses",
            rejection_message="Cannabis related equipment/businesses are not desired",
            is_required=True,
            priority=90,
            weight=10,
        ),
    ]
    for rule in tier1_rules:
        db.add(rule)
    
    # Tier 2 - Startup Program
    tier2 = LenderProgram(
        lender_id=lender.id,
        name="Tier 2 - Startup",
        description="$50K max for startups and non-homeowners",
        credit_tier=CreditTier.A,
        min_loan_amount=10000,
        max_loan_amount=50000,
        max_term_months=60,
        is_app_only=True,
        priority=20,
        is_active=True,
    )
    db.add(tier2)
    db.flush()
    
    tier2_rules = [
        PolicyRule(
            program_id=tier2.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 700},
            description="700+ TransUnion Credit Score",
            rejection_message="TransUnion credit score must be at least 700",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=tier2.id,
            rule_type="requires_homeowner",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="Homeownership required",
            rejection_message="Homeownership is required",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=tier2.id,
            rule_type="excluded_states",
            operator=RuleOperator.NOT_IN,
            value={"value": ["CA"]},
            description="No California applicants",
            rejection_message="Citizens Bank does not provide financing for applicants in California",
            is_required=True,
            priority=40,
            weight=10,
        ),
        PolicyRule(
            program_id=tier2.id,
            rule_type="requires_us_citizen",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="US Citizen required",
            rejection_message="Customers must be US Citizens",
            is_required=True,
            priority=50,
            weight=10,
        ),
    ]
    for rule in tier2_rules:
        db.add(rule)
    
    # Tier 3 - Full Financials
    tier3 = LenderProgram(
        lender_id=lender.id,
        name="Tier 3 - Full Financials",
        description="$75K-$1M with full financial documentation",
        credit_tier=CreditTier.A,
        min_loan_amount=75000,
        max_loan_amount=1000000,
        max_term_months=60,
        is_app_only=False,
        requires_financials=True,
        priority=30,
        is_active=True,
    )
    db.add(tier3)
    db.flush()
    
    tier3_rules = [
        PolicyRule(
            program_id=tier3.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 700},
            description="700+ TransUnion Credit Score",
            rejection_message="TransUnion credit score must be at least 700",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=tier3.id,
            rule_type="excluded_states",
            operator=RuleOperator.NOT_IN,
            value={"value": ["CA"]},
            description="No California applicants",
            rejection_message="Citizens Bank does not provide financing for applicants in California",
            is_required=True,
            priority=40,
            weight=10,
        ),
        PolicyRule(
            program_id=tier3.id,
            rule_type="requires_us_citizen",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="US Citizen required",
            rejection_message="Customers must be US Citizens",
            is_required=True,
            priority=50,
            weight=10,
        ),
    ]
    for rule in tier3_rules:
        db.add(rule)
    
    print(f"Created: {lender.name}")
    return lender


def seed_advantage_plus(db):
    """
    Advantage+ Financing - from Advantage++Broker+2025.pdf
    
    Key requirements:
    - FICO 680+ (700+ for startups)
    - 3 years industry experience
    - No bankruptcies, judgments, foreclosures, repossessions
    - Max $75K
    """
    lender = Lender(
        name="Advantage+ Financing",
        short_name="Advantage+",
        description="Non-trucking equipment financing up to $75K",
        contact_email="SalesSupport@advantageplusfinancing.com",
        contact_phone="262-439-7600",
        is_active=True,
    )
    db.add(lender)
    db.flush()
    
    # Standard Program
    standard = LenderProgram(
        lender_id=lender.id,
        name="Standard Program",
        description="Non-trucking applications up to $75K",
        credit_tier=CreditTier.A,
        min_loan_amount=10000,
        max_loan_amount=75000,
        max_term_months=60,
        is_app_only=True,
        priority=10,
        is_active=True,
    )
    db.add(standard)
    db.flush()
    
    standard_rules = [
        PolicyRule(
            program_id=standard.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 680},
            description="680 FICO v5 (Equifax)",
            rejection_message="FICO score must be at least 680 (Equifax v5)",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 3},
            description="Minimum 3 years industry experience",
            rejection_message="Minimum 3 years industry experience required",
            is_required=True,
            priority=20,
            weight=15,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="no_bankruptcies",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No bankruptcies",
            rejection_message="Advantage+ does not finance bankruptcies",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="no_judgments",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No judgments",
            rejection_message="Advantage+ does not extend credit with judgments in history",
            is_required=True,
            priority=40,
            weight=15,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="no_foreclosures",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No foreclosures",
            rejection_message="Advantage+ does not extend credit with foreclosures in history",
            is_required=True,
            priority=50,
            weight=15,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="no_repossessions",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No repossessions",
            rejection_message="Advantage+ does not extend credit with repossessions in history",
            is_required=True,
            priority=60,
            weight=15,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="no_tax_liens",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No tax liens",
            rejection_message="No tax liens allowed",
            is_required=True,
            priority=70,
            weight=10,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="requires_us_citizen",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="US Citizen only",
            rejection_message="US Citizen only",
            is_required=True,
            priority=80,
            weight=10,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="amount_max",
            operator=RuleOperator.LTE,
            value={"value": 75000},
            description="Maximum $75,000",
            rejection_message="Maximum loan amount is $75,000",
            is_required=True,
            priority=90,
            weight=5,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="amount_min",
            operator=RuleOperator.GTE,
            value={"value": 10000},
            description="Minimum $10,000",
            rejection_message="Minimum loan amount is $10,000",
            is_required=True,
            priority=100,
            weight=5,
        ),
        PolicyRule(
            program_id=standard.id,
            rule_type="comparable_credit_pct",
            operator=RuleOperator.GTE,
            value={"value": 80},
            description="Prefer 80% comparable credit",
            rejection_message="Prefer 80% comparable credit history",
            is_required=False,
            priority=110,
            weight=5,
        ),
    ]
    for rule in standard_rules:
        db.add(rule)
    
    # Startup Program
    startup = LenderProgram(
        lender_id=lender.id,
        name="Startup Program",
        description="For startup businesses with higher requirements",
        credit_tier=CreditTier.A,
        min_loan_amount=10000,
        max_loan_amount=75000,
        max_term_months=60,
        is_app_only=True,
        priority=20,
        is_active=True,
    )
    db.add(startup)
    db.flush()
    
    startup_rules = [
        PolicyRule(
            program_id=startup.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 700},
            description="700+ FICO for startups",
            rejection_message="Startups require FICO score of at least 700",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=startup.id,
            rule_type="no_bankruptcies",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No bankruptcies",
            rejection_message="No bankruptcies allowed",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=startup.id,
            rule_type="no_judgments",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No judgments",
            rejection_message="No judgments allowed",
            is_required=True,
            priority=40,
            weight=15,
        ),
        PolicyRule(
            program_id=startup.id,
            rule_type="no_foreclosures",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No foreclosures",
            rejection_message="No foreclosures allowed",
            is_required=True,
            priority=50,
            weight=15,
        ),
        PolicyRule(
            program_id=startup.id,
            rule_type="no_repossessions",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="No repossessions",
            rejection_message="No repossessions allowed",
            is_required=True,
            priority=60,
            weight=15,
        ),
        PolicyRule(
            program_id=startup.id,
            rule_type="requires_us_citizen",
            operator=RuleOperator.EQ,
            value={"value": True},
            description="US Citizen only",
            rejection_message="US Citizen only",
            is_required=True,
            priority=80,
            weight=10,
        ),
    ]
    for rule in startup_rules:
        db.add(rule)
    
    print(f"Created: {lender.name}")
    return lender


def seed_apex_commercial(db):
    """
    Apex Commercial Capital - from Apex EF Broker Guidelines_082725.pdf
    
    Key requirements:
    - A Credit: 700+ FICO, 660+ PayNet, 5yr TIB, up to $200K app-only
    - B Credit: 670+ FICO, 650+ PayNet, 3yr TIB, up to $100K app-only
    - C Credit: 640+ FICO/PayNet, 2yr TIB
    - Excludes: CA, NV, ND, VT
    - Excludes: Trucking, cannabis, gambling, etc.
    """
    lender = Lender(
        name="Apex Commercial Capital",
        short_name="Apex",
        description="Equipment finance with A/B/C credit tiers",
        contact_name="Stephanie (Hall) Costa, CLFP",
        contact_email="scosta@apexcommercial.com",
        contact_phone="267-470-3118",
        is_active=True,
    )
    db.add(lender)
    db.flush()
    
    # Common exclusions
    excluded_states = ["CA", "NV", "ND", "VT"]
    excluded_industries = [
        "cannabis", "gambling", "casino", "churches", "non-profits",
        "trucking", "logging", "petroleum", "oil", "gas", "nail salon",
        "tanning"
    ]
    excluded_equipment = [
        "aircraft", "boat", "atm", "audio visual", "copier", "electric vehicle",
        "furniture", "kiosk", "signage", "tanning bed"
    ]
    
    # A Credit Program
    a_credit = LenderProgram(
        lender_id=lender.id,
        name="A Credit Program",
        description="App-only up to $200K for A credit customers",
        credit_tier=CreditTier.A,
        min_loan_amount=10000,
        max_loan_amount=500000,
        max_term_months=60,
        is_app_only=True,
        priority=10,
        is_active=True,
    )
    db.add(a_credit)
    db.flush()
    
    a_rules = [
        PolicyRule(
            program_id=a_credit.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 700},
            description="700+ FICO",
            rejection_message="A Credit requires FICO score of at least 700",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=a_credit.id,
            rule_type="paynet_min",
            operator=RuleOperator.GTE,
            value={"value": 660},
            description="660+ PayNet",
            rejection_message="A Credit requires PayNet score of at least 660",
            is_required=True,
            priority=20,
            weight=15,
        ),
        PolicyRule(
            program_id=a_credit.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 5},
            description="5 years time in business",
            rejection_message="A Credit requires at least 5 years in business",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=a_credit.id,
            rule_type="revolving_available_min",
            operator=RuleOperator.GTE,
            value={"value": 50},
            description="50% revolving credit available",
            rejection_message="A Credit requires 50% revolving credit available",
            is_required=True,
            priority=40,
            weight=10,
        ),
        PolicyRule(
            program_id=a_credit.id,
            rule_type="excluded_states",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_states},
            description="Not available in CA, NV, ND, VT",
            rejection_message="Apex does not lend in CA, NV, ND, VT",
            is_required=True,
            priority=50,
            weight=10,
        ),
        PolicyRule(
            program_id=a_credit.id,
            rule_type="excluded_industries",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_industries},
            description="Industry exclusions",
            rejection_message="This industry is excluded by Apex",
            is_required=True,
            priority=60,
            weight=10,
        ),
        PolicyRule(
            program_id=a_credit.id,
            rule_type="excluded_equipment",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_equipment},
            description="Equipment type exclusions",
            rejection_message="This equipment type is excluded by Apex",
            is_required=True,
            priority=70,
            weight=10,
        ),
        PolicyRule(
            program_id=a_credit.id,
            rule_type="equipment_age_max",
            operator=RuleOperator.LTE,
            value={"value": 15},
            description="Equipment over 15 years old excluded",
            rejection_message="Equipment must be 15 years old or newer",
            is_required=True,
            priority=80,
            weight=10,
        ),
    ]
    for rule in a_rules:
        db.add(rule)
    
    # B Credit Program
    b_credit = LenderProgram(
        lender_id=lender.id,
        name="B Credit Program",
        description="App-only up to $100K for B credit customers",
        credit_tier=CreditTier.B,
        min_loan_amount=10000,
        max_loan_amount=250000,
        max_term_months=60,
        is_app_only=True,
        priority=20,
        is_active=True,
    )
    db.add(b_credit)
    db.flush()
    
    b_rules = [
        PolicyRule(
            program_id=b_credit.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 670},
            description="670+ FICO",
            rejection_message="B Credit requires FICO score of at least 670",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=b_credit.id,
            rule_type="paynet_min",
            operator=RuleOperator.GTE,
            value={"value": 650},
            description="650+ PayNet",
            rejection_message="B Credit requires PayNet score of at least 650",
            is_required=True,
            priority=20,
            weight=15,
        ),
        PolicyRule(
            program_id=b_credit.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 3},
            description="3 years time in business",
            rejection_message="B Credit requires at least 3 years in business",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=b_credit.id,
            rule_type="revolving_available_min",
            operator=RuleOperator.GTE,
            value={"value": 50},
            description="50% revolving credit available",
            rejection_message="B Credit requires 50% revolving credit available",
            is_required=True,
            priority=40,
            weight=10,
        ),
        PolicyRule(
            program_id=b_credit.id,
            rule_type="excluded_states",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_states},
            description="Not available in CA, NV, ND, VT",
            rejection_message="Apex does not lend in CA, NV, ND, VT",
            is_required=True,
            priority=50,
            weight=10,
        ),
        PolicyRule(
            program_id=b_credit.id,
            rule_type="excluded_industries",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_industries},
            description="Industry exclusions",
            rejection_message="This industry is excluded by Apex",
            is_required=True,
            priority=60,
            weight=10,
        ),
    ]
    for rule in b_rules:
        db.add(rule)
    
    # C Credit Program
    c_credit = LenderProgram(
        lender_id=lender.id,
        name="C Credit Program",
        description="For customers with lower credit scores",
        credit_tier=CreditTier.C,
        min_loan_amount=10000,
        max_loan_amount=100000,
        max_term_months=60,
        is_app_only=False,
        requires_financials=True,
        priority=30,
        is_active=True,
    )
    db.add(c_credit)
    db.flush()
    
    c_rules = [
        PolicyRule(
            program_id=c_credit.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 640},
            description="640+ FICO",
            rejection_message="C Credit requires FICO score of at least 640",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=c_credit.id,
            rule_type="paynet_min",
            operator=RuleOperator.GTE,
            value={"value": 640},
            description="640+ PayNet",
            rejection_message="C Credit requires PayNet score of at least 640",
            is_required=True,
            priority=20,
            weight=15,
        ),
        PolicyRule(
            program_id=c_credit.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 2},
            description="2 years time in business",
            rejection_message="C Credit requires at least 2 years in business",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=c_credit.id,
            rule_type="excluded_states",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_states},
            description="Not available in CA, NV, ND, VT",
            rejection_message="Apex does not lend in CA, NV, ND, VT",
            is_required=True,
            priority=50,
            weight=10,
        ),
    ]
    for rule in c_rules:
        db.add(rule)
    
    print(f"Created: {lender.name}")
    return lender


def seed_stearns_bank(db):
    """
    Stearns Bank - from EF Credit Box 4.14.2025.pdf
    
    Key requirements:
    - Tier 1: 725 FICO, 685 PayNet, 3yr TIB
    - Tier 2: 710 FICO, 675 PayNet, 3yr TIB
    - Tier 3: 700 FICO, 665 PayNet, 2yr TIB
    - No BK in last 7 years
    - Many industry exclusions
    """
    lender = Lender(
        name="Stearns Bank",
        short_name="Stearns",
        description="Equipment finance with tiered credit requirements",
        is_active=True,
    )
    db.add(lender)
    db.flush()
    
    # Common exclusions
    excluded_industries = [
        "gambling", "gaming", "hazmat", "oil", "gas", "petroleum",
        "adult entertainment", "weapons", "firearms", "beauty salon",
        "tanning", "tattoo", "piercing", "real estate", "otr", "trucking",
        "restaurant", "car wash"
    ]
    
    # Tier 1
    tier1 = LenderProgram(
        lender_id=lender.id,
        name="Tier 1",
        description="Best rates for top credit",
        credit_tier=CreditTier.A,
        min_loan_amount=10000,
        max_loan_amount=500000,
        max_term_months=60,
        is_app_only=True,
        priority=10,
        is_active=True,
    )
    db.add(tier1)
    db.flush()
    
    tier1_rules = [
        PolicyRule(
            program_id=tier1.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 725},
            description="725+ FICO",
            rejection_message="Tier 1 requires FICO score of at least 725",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="paynet_min",
            operator=RuleOperator.GTE,
            value={"value": 685},
            description="685+ PayNet",
            rejection_message="Tier 1 requires PayNet score of at least 685",
            is_required=True,
            priority=20,
            weight=15,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 3},
            description="3 years time in business",
            rejection_message="Tier 1 requires at least 3 years in business",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="bankruptcy_years_min",
            operator=RuleOperator.GTE,
            value={"value": 7},
            description="No BK in last 7 years",
            rejection_message="No bankruptcy allowed in the last 7 years",
            is_required=True,
            priority=40,
            weight=15,
        ),
        PolicyRule(
            program_id=tier1.id,
            rule_type="excluded_industries",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_industries},
            description="Industry restrictions",
            rejection_message="This industry is restricted by Stearns Bank",
            is_required=True,
            priority=50,
            weight=10,
        ),
    ]
    for rule in tier1_rules:
        db.add(rule)
    
    # Tier 2
    tier2 = LenderProgram(
        lender_id=lender.id,
        name="Tier 2",
        description="Good rates for strong credit",
        credit_tier=CreditTier.A,
        min_loan_amount=10000,
        max_loan_amount=500000,
        max_term_months=60,
        is_app_only=True,
        priority=20,
        is_active=True,
    )
    db.add(tier2)
    db.flush()
    
    tier2_rules = [
        PolicyRule(
            program_id=tier2.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 710},
            description="710+ FICO",
            rejection_message="Tier 2 requires FICO score of at least 710",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=tier2.id,
            rule_type="paynet_min",
            operator=RuleOperator.GTE,
            value={"value": 675},
            description="675+ PayNet",
            rejection_message="Tier 2 requires PayNet score of at least 675",
            is_required=True,
            priority=20,
            weight=15,
        ),
        PolicyRule(
            program_id=tier2.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 3},
            description="3 years time in business",
            rejection_message="Tier 2 requires at least 3 years in business",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=tier2.id,
            rule_type="bankruptcy_years_min",
            operator=RuleOperator.GTE,
            value={"value": 7},
            description="No BK in last 7 years",
            rejection_message="No bankruptcy allowed in the last 7 years",
            is_required=True,
            priority=40,
            weight=15,
        ),
        PolicyRule(
            program_id=tier2.id,
            rule_type="excluded_industries",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_industries},
            description="Industry restrictions",
            rejection_message="This industry is restricted by Stearns Bank",
            is_required=True,
            priority=50,
            weight=10,
        ),
    ]
    for rule in tier2_rules:
        db.add(rule)
    
    # Tier 3
    tier3 = LenderProgram(
        lender_id=lender.id,
        name="Tier 3",
        description="Standard rates for acceptable credit",
        credit_tier=CreditTier.B,
        min_loan_amount=10000,
        max_loan_amount=500000,
        max_term_months=60,
        is_app_only=True,
        priority=30,
        is_active=True,
    )
    db.add(tier3)
    db.flush()
    
    tier3_rules = [
        PolicyRule(
            program_id=tier3.id,
            rule_type="fico_min",
            operator=RuleOperator.GTE,
            value={"value": 700},
            description="700+ FICO",
            rejection_message="Tier 3 requires FICO score of at least 700",
            is_required=True,
            priority=10,
            weight=20,
        ),
        PolicyRule(
            program_id=tier3.id,
            rule_type="paynet_min",
            operator=RuleOperator.GTE,
            value={"value": 665},
            description="665+ PayNet",
            rejection_message="Tier 3 requires PayNet score of at least 665",
            is_required=True,
            priority=20,
            weight=15,
        ),
        PolicyRule(
            program_id=tier3.id,
            rule_type="tib_min",
            operator=RuleOperator.GTE,
            value={"value": 2},
            description="2 years time in business",
            rejection_message="Tier 3 requires at least 2 years in business",
            is_required=True,
            priority=30,
            weight=15,
        ),
        PolicyRule(
            program_id=tier3.id,
            rule_type="bankruptcy_years_min",
            operator=RuleOperator.GTE,
            value={"value": 7},
            description="No BK in last 7 years",
            rejection_message="No bankruptcy allowed in the last 7 years",
            is_required=True,
            priority=40,
            weight=15,
        ),
        PolicyRule(
            program_id=tier3.id,
            rule_type="excluded_industries",
            operator=RuleOperator.NOT_IN,
            value={"value": excluded_industries},
            description="Industry restrictions",
            rejection_message="This industry is restricted by Stearns Bank",
            is_required=True,
            priority=50,
            weight=10,
        ),
    ]
    for rule in tier3_rules:
        db.add(rule)
    
    print(f"Created: {lender.name}")
    return lender


def main():
    """Run the seed script"""
    print("Seeding lender data...")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(Lender).count()
        if existing > 0:
            print(f"Database already has {existing} lenders.")
            response = input("Do you want to delete and reseed? (y/n): ")
            if response.lower() == 'y':
                db.query(PolicyRule).delete()
                db.query(LenderProgram).delete()
                db.query(Lender).delete()
                db.commit()
                print("Existing data deleted.")
            else:
                print("Keeping existing data. Exiting.")
                return
        
        # Seed all lenders
        seed_falcon_equipment_finance(db)
        seed_citizens_bank(db)
        seed_advantage_plus(db)
        seed_apex_commercial(db)
        seed_stearns_bank(db)
        
        db.commit()
        
        print("=" * 50)
        print("Seeding complete!")
        
        # Summary
        lenders = db.query(Lender).count()
        programs = db.query(LenderProgram).count()
        rules = db.query(PolicyRule).count()
        
        print(f"Created {lenders} lenders, {programs} programs, {rules} rules")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

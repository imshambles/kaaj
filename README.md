# Lender Matching Platform

A loan underwriting and lender matching system that evaluates business loan applications against multiple lenders' credit policies.

## Features

- **Multi-Lender Evaluation**: Automatically evaluates applications against 5 equipment finance lenders
- **Extensible Policy Engine**: Registry-based rule evaluators make it easy to add new rule types
- **Detailed Matching Results**: Shows pass/fail for each criterion with specific reasons
- **Fit Score Calculation**: 0-100 scoring to rank lender matches
- **Policy Management UI**: View and edit lender policies, programs, and rules
- **Multi-Step Application Form**: Intuitive form collecting business, guarantor, and loan info

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your PostgreSQL credentials
# DATABASE_URL=postgresql://user:pass@localhost:5432/lender_matching

# Create database
createdb lender_matching

# Seed the lenders (5 lenders from PDF guidelines)
python seed_lenders.py

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Open http://localhost:5173 in your browser.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Application  │  │   Results    │  │  Lender Policies     │  │
│  │    Form      │  │    View      │  │    Management        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Applications │  │   Lenders    │  │    Underwriting      │  │
│  │     API      │  │     API      │  │      Workflow        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Matching Engine                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ Evaluators │  │  Matcher   │  │     Scoring        │  │  │
│  │  │ (25+ rules)│  │            │  │                    │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ SQLAlchemy
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Borrowers │  │  Lenders   │  │  Programs  │  │   Rules   │ │
│  │ Guarantors │  │            │  │            │  │  (JSONB)  │ │
│  │   Loans    │  │            │  │            │  │           │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## API Documentation

Once the backend is running, access interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/applications` | Create loan application |
| GET | `/api/applications` | List all applications |
| GET | `/api/applications/{id}` | Get application details |
| POST | `/api/applications/{id}/underwrite` | Run underwriting |
| GET | `/api/applications/{id}/results` | Get match results |
| GET | `/api/lenders` | List all lenders |
| GET | `/api/lenders/{id}` | Get lender with programs/rules |
| POST | `/api/lenders` | Create new lender |
| POST | `/api/lenders/{id}/programs` | Add program to lender |
| POST | `/api/lenders/programs/{id}/rules` | Add rule to program |
| PUT | `/api/lenders/rules/{id}` | Update a rule |
| DELETE | `/api/lenders/rules/{id}` | Delete a rule |
| GET | `/api/lenders/rule-types` | Get supported rule types |

## Adding New Lenders

### Via API

```bash
curl -X POST http://localhost:8000/api/lenders \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Lender",
    "programs": [{
      "name": "Standard",
      "rules": [{
        "rule_type": "fico_min",
        "operator": "gte",
        "value": 680,
        "rejection_message": "FICO must be 680+"
      }]
    }]
  }'
```

### Via UI

1. Navigate to Lender Policies page
2. Select a lender or create new
3. Add/edit programs and rules inline

### Via Seed Script

Add a new function to `backend/seed_lenders.py` following the existing patterns.

## Adding New Rule Types

1. Create evaluator class in `backend/app/engine/evaluators.py`:

```python
class NewRuleEvaluator(RuleEvaluator):
    def evaluate(self, ctx: EvaluationContext, rule: PolicyRule) -> EvaluationResult:
        # Your logic here
        pass
```

2. Register in `EVALUATOR_REGISTRY`:

```python
EVALUATOR_REGISTRY["new_rule"] = NewRuleEvaluator()
```

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Supported Lenders

The system comes pre-seeded with 5 equipment finance lenders:

1. **Falcon Equipment Finance** - Trucking specialist, FICO 680+, PayNet 660+
2. **Citizens Bank** - Tiered programs ($50K-$1M), 700+ TransUnion
3. **Advantage+ Financing** - Non-trucking up to $75K, no bankruptcies
4. **Apex Commercial Capital** - A/B/C credit tiers, excludes CA, NV, ND, VT
5. **Stearns Bank** - Tiered FICO/PayNet requirements, many industry exclusions

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React, TypeScript, Vite

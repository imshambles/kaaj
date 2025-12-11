# Lender Matching Platform

A loan underwriting and lender matching system that evaluates business loan applications against multiple lenders' credit policies.

## Live Demo

- **Frontend**: https://imshambles.github.io/kaaj/
- **Backend API**: https://kaaj-1.onrender.com/api

## Features

- **Multi-Lender Evaluation**: Automatically evaluates applications against equipment finance lenders
- **Extensible Policy Engine**: Registry-based rule evaluators (27+ rule types)
- **Detailed Matching Results**: Shows pass/fail for each criterion with specific reasons
- **Fit Score Calculation**: 0-100 scoring to rank lender matches
- **Policy Management UI**: View and edit lender policies, programs, and rules
- **PDF Import**: Upload lender guideline PDFs and extract rules using AI (Gemini)
- **Multi-Step Application Form**: Intuitive form collecting business, guarantor, and loan info

## Local Setup

### Prerequisites

- Docker & Docker Compose (recommended), OR
- Python 3.11+, Node.js 18+, PostgreSQL 14+

---

### Option 1: Docker (Recommended)

**Quick start with one command:**

```bash
# Start backend + database
cd backend
docker-compose up -d --build

# Seed lenders (run once, after database is ready)
docker exec lender_matching_api python seed_lenders.py

# Backend now running at http://localhost:8000
```

**Start frontend:**

```bash
cd frontend
npm install
npm run dev

# Frontend running at http://localhost:5173
```

**Stop everything:**
```bash
cd backend
docker-compose down
```

---

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your PostgreSQL credentials:
# DATABASE_URL=postgresql://user:pass@localhost:5432/lender_matching
# GEMINI_API_KEY=your_gemini_api_key (optional, for PDF import)

# Create database (PostgreSQL must be running)
createdb lender_matching

# Seed lenders
python seed_lenders.py

# Run server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `GEMINI_API_KEY` | Google Gemini API key (for PDF import) | Optional |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Application  │  │   Results    │  │  Lender Policies     │  │
│  │    Form      │  │    View      │  │  (+ PDF Import)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Applications │  │   Lenders    │  │   PDF Parser +       │  │
│  │     API      │  │     API      │  │   AI Extraction      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Matching Engine                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ Evaluators │  │  Matcher   │  │     Scoring        │  │  │
│  │  │ (27 rules) │  │            │  │                    │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ SQLAlchemy
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Documentation

Once backend is running, access interactive docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/applications` | Create loan application |
| GET | `/api/applications/{id}/results` | Get match results |
| GET | `/api/lenders` | List all lenders |
| POST | `/api/lenders/parse-pdf` | Upload PDF and extract rules (AI) |
| DELETE | `/api/lenders/{id}` | Delete a lender |
| GET | `/api/lenders/rule-types` | Get all 27 supported rule types |

---

## Running Tests

```bash
cd backend
source venv/bin/activate  # or use Docker: docker exec -it lender_matching_api bash
python -m pytest tests/ -v
```

**Current test coverage**: 36 tests (evaluators, scoring, API endpoints)

---

## Adding New Lenders

### Via PDF Import (Recommended)
1. Go to **Lender Policies** page
2. Click **"📄 Import from PDF"**
3. Upload a lender guideline PDF
4. Review/edit extracted rules
5. Click **"✓ Create Lender"**

### Via API
```bash
curl -X POST http://localhost:8000/api/lenders \
  -H "Content-Type: application/json" \
  -d '{"name": "New Lender", "programs": [{"name": "Standard", "rules": [...]}]}'
```

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL, Pydantic
- **Frontend**: React 19, TypeScript, Vite, React Router
- **AI**: Google Gemini 2.0 Flash (PDF rule extraction)
- **Deployment**: Render (backend), GitHub Pages (frontend)

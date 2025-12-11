/**
 * API Service for communicating with the backend
 */

const API_BASE_URL = 'http://localhost:8000/api';

export interface Guarantor {
  id?: string;
  first_name: string;
  last_name: string;
  ownership_percentage: number;
  fico_score: number;
  fico_source: string;
  is_homeowner: boolean;
  years_at_residence?: number;
  has_bankruptcy: boolean;
  bankruptcy_type?: string;
  bankruptcy_discharge_date?: string;
  has_judgments: boolean;
  has_foreclosure: boolean;
  has_repossession: boolean;
  has_tax_liens: boolean;
  has_collections_recent: boolean;
  revolving_credit_limit?: number;
  revolving_credit_balance?: number;
  revolving_available_pct?: number;
  has_cdl: boolean;
  cdl_years?: number;
  cdl_class?: string;
}

export interface Borrower {
  id?: string;
  business_name: string;
  dba_name?: string;
  industry: string;
  industry_naics?: string;
  state: string;
  years_in_business: number;
  annual_revenue: number;
  num_employees?: number;
  num_trucks?: number;
  is_startup: boolean;
  is_homeowner: boolean;
  is_us_citizen: boolean;
  guarantors: Guarantor[];
}

export interface LoanApplication {
  id?: string;
  borrower_id?: string;
  amount_requested: number;
  term_months: number;
  down_payment_pct?: number;
  equipment_type: string;
  equipment_description?: string;
  equipment_year: number;
  equipment_age_years: number;
  equipment_mileage?: number;
  equipment_hours?: number;
  equipment_condition: string;
  is_private_party_sale: boolean;
  is_titled_asset: boolean;
  is_refinance: boolean;
  is_sale_leaseback: boolean;
  paynet_score?: number;
  has_comparable_credit: boolean;
  comparable_credit_amount?: number;
  comparable_credit_pct?: number;
  status?: string;
  created_at?: string;
  borrower?: Borrower;
}

export interface LoanApplicationCreate {
  borrower: Borrower;
  application: Omit<LoanApplication, 'id' | 'borrower_id' | 'status' | 'created_at' | 'borrower'>;
}

export interface PolicyRule {
  id: string;
  program_id: string;
  rule_type: string;
  operator: string;
  value: any;
  description?: string;
  rejection_message: string;
  is_required: boolean;
  priority: number;
  weight: number;
  is_active: boolean;
}

export interface LenderProgram {
  id: string;
  lender_id: string;
  name: string;
  description?: string;
  credit_tier?: string;
  min_loan_amount?: number;
  max_loan_amount?: number;
  max_term_months?: number;
  is_app_only: boolean;
  requires_financials: boolean;
  priority: number;
  is_active: boolean;
  rules: PolicyRule[];
}

export interface Lender {
  id: string;
  name: string;
  short_name?: string;
  description?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  is_active: boolean;
  programs: LenderProgram[];
}

export interface LenderSummary {
  id: string;
  name: string;
  short_name?: string;
  is_active: boolean;
  program_count: number;
}

export interface RuleEvaluationDetail {
  rule_type: string;
  rule_id: string;
  passed: boolean;
  required_value: any;
  actual_value: any;
  is_required: boolean;
  reason: string;
}

export interface MatchResult {
  id: string;
  application_id: string;
  lender_id: string;
  program_id?: string;
  is_eligible: boolean;
  fit_score: number;
  evaluation_details: {
    rules_evaluated: number;
    rules_passed: number;
    rules_failed: number;
    pass_rate: number;
    details: RuleEvaluationDetail[];
    summary: {
      passed: RuleEvaluationDetail[];
      failed: RuleEvaluationDetail[];
      warnings: string[];
    };
  };
  created_at: string;
  lender_name?: string;
  program_name?: string;
}

export interface UnderwritingResults {
  application_id: string;
  status: string;
  total_lenders: number;
  eligible_count: number;
  ineligible_count: number;
  best_match?: MatchResult;
  results: MatchResult[];
}

// API Functions

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }
  return response.json();
}

// Applications

export async function createApplication(data: LoanApplicationCreate): Promise<LoanApplication> {
  const response = await fetch(`${API_BASE_URL}/applications`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<LoanApplication>(response);
}

export async function getApplications(): Promise<LoanApplication[]> {
  const response = await fetch(`${API_BASE_URL}/applications`);
  return handleResponse<LoanApplication[]>(response);
}

export async function getApplication(id: string): Promise<LoanApplication> {
  const response = await fetch(`${API_BASE_URL}/applications/${id}`);
  return handleResponse<LoanApplication>(response);
}

export async function runUnderwriting(applicationId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/underwrite`, {
    method: 'POST',
  });
  return handleResponse<any>(response);
}

export async function getResults(applicationId: string): Promise<UnderwritingResults> {
  const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/results`);
  return handleResponse<UnderwritingResults>(response);
}

// Lenders

export async function getLenders(): Promise<LenderSummary[]> {
  const response = await fetch(`${API_BASE_URL}/lenders`);
  return handleResponse<LenderSummary[]>(response);
}

export async function getLender(id: string): Promise<Lender> {
  const response = await fetch(`${API_BASE_URL}/lenders/${id}`);
  return handleResponse<Lender>(response);
}

export async function createLender(data: Partial<Lender>): Promise<Lender> {
  const response = await fetch(`${API_BASE_URL}/lenders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Lender>(response);
}

export async function updateLender(id: string, data: Partial<Lender>): Promise<Lender> {
  const response = await fetch(`${API_BASE_URL}/lenders/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<Lender>(response);
}

export async function deleteLender(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/lenders/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete lender');
  }
}

// Programs

export async function createProgram(lenderId: string, data: Partial<LenderProgram>): Promise<LenderProgram> {
  const response = await fetch(`${API_BASE_URL}/lenders/${lenderId}/programs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<LenderProgram>(response);
}

export async function updateProgram(programId: string, data: Partial<LenderProgram>): Promise<LenderProgram> {
  const response = await fetch(`${API_BASE_URL}/lenders/programs/${programId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<LenderProgram>(response);
}

// Rules

export async function createRule(programId: string, data: Partial<PolicyRule>): Promise<PolicyRule> {
  const response = await fetch(`${API_BASE_URL}/lenders/programs/${programId}/rules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<PolicyRule>(response);
}

export async function updateRule(ruleId: string, data: Partial<PolicyRule>): Promise<PolicyRule> {
  const response = await fetch(`${API_BASE_URL}/lenders/rules/${ruleId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return handleResponse<PolicyRule>(response);
}

export async function deleteRule(ruleId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/lenders/rules/${ruleId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete rule');
  }
}

export async function getRuleTypes(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/lenders/rule-types`);
  return handleResponse<string[]>(response);
}

// PDF Parsing

export interface ExtractedRule {
  rule_type: string;
  operator: string;
  value: any;
  is_required: boolean;
  rejection_message: string;
  weight?: number;
}

export interface ExtractedProgram {
  name: string;
  description?: string;
  credit_tier?: string;
  min_loan_amount?: number;
  max_loan_amount?: number;
  rules: ExtractedRule[];
}

export interface ExtractedLenderData {
  lender_name: string;
  programs: ExtractedProgram[];
}

export interface PdfParseResult {
  success: boolean;
  filename: string;
  page_count: number;
  extracted: ExtractedLenderData;
  raw_text_preview: string;
}

export async function parsePdf(file: File): Promise<PdfParseResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/lenders/parse-pdf`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<PdfParseResult>(response);
}

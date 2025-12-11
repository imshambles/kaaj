import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createApplication, runUnderwriting, LoanApplicationCreate } from '../services/api';

const US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
];

const EQUIPMENT_TYPES = [
    'Class 8 Truck', 'Trailer', 'Reefer Trailer', 'Dump Truck',
    'Construction Equipment', 'Excavator', 'Loader', 'Forklift',
    'Medical Equipment', 'Manufacturing Equipment', 'Machine Tools',
    'Restaurant Equipment', 'Commercial Lawn Equipment', 'Other'
];

const INDUSTRIES = [
    'Construction', 'Trucking', 'Manufacturing', 'Healthcare',
    'Restaurant', 'Retail', 'Agriculture', 'Landscaping',
    'Automotive Repair', 'Waste Management', 'Other'
];

export function ApplicationForm() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [step, setStep] = useState(1);

    // Business info - using string for number inputs
    const [businessName, setBusinessName] = useState('');
    const [industry, setIndustry] = useState('');
    const [state, setState] = useState('');
    const [yearsInBusiness, setYearsInBusiness] = useState('5');
    const [annualRevenue, setAnnualRevenue] = useState('500000');
    const [isStartup, setIsStartup] = useState(false);
    const [numTrucks, setNumTrucks] = useState('');

    // Guarantor info
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [ownershipPct, setOwnershipPct] = useState('100');
    const [ficoScore, setFicoScore] = useState('720');
    const [isHomeowner, setIsHomeowner] = useState(true);
    const [hasBankruptcy, setHasBankruptcy] = useState(false);
    const [bankruptcyDischargeDate, setBankruptcyDischargeDate] = useState('');
    const [hasJudgments, setHasJudgments] = useState(false);
    const [hasForeclosure, setHasForeclosure] = useState(false);
    const [hasRepossession, setHasRepossession] = useState(false);
    const [hasTaxLiens, setHasTaxLiens] = useState(false);
    const [revolvingAvailablePct, setRevolvingAvailablePct] = useState('60');

    // Loan info
    const [amountRequested, setAmountRequested] = useState('75000');
    const [termMonths, setTermMonths] = useState('60');
    const [equipmentType, setEquipmentType] = useState('');
    const [equipmentYear, setEquipmentYear] = useState(String(new Date().getFullYear()));
    const [equipmentMileage, setEquipmentMileage] = useState('');
    const [paynetScore, setPaynetScore] = useState('680');
    const [isPrivateParty, setIsPrivateParty] = useState(false);
    const [comparableCreditPct, setComparableCreditPct] = useState('80');

    // Helper to convert string to number
    const toNum = (val: string, fallback: number = 0): number => {
        const n = parseFloat(val);
        return isNaN(n) ? fallback : n;
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError(null);

        const equipmentAgeYears = new Date().getFullYear() - toNum(equipmentYear, new Date().getFullYear());

        try {
            const data: LoanApplicationCreate = {
                borrower: {
                    business_name: businessName,
                    industry: industry,
                    state: state,
                    years_in_business: toNum(yearsInBusiness),
                    annual_revenue: toNum(annualRevenue),
                    is_startup: isStartup,
                    is_homeowner: isHomeowner,
                    is_us_citizen: true,
                    num_trucks: numTrucks ? toNum(numTrucks) : undefined,
                    guarantors: [
                        {
                            first_name: firstName,
                            last_name: lastName,
                            ownership_percentage: toNum(ownershipPct, 100),
                            fico_score: toNum(ficoScore, 720),
                            fico_source: 'TransUnion',
                            is_homeowner: isHomeowner,
                            has_bankruptcy: hasBankruptcy,
                            bankruptcy_discharge_date: hasBankruptcy && bankruptcyDischargeDate ? bankruptcyDischargeDate : undefined,
                            has_judgments: hasJudgments,
                            has_foreclosure: hasForeclosure,
                            has_repossession: hasRepossession,
                            has_tax_liens: hasTaxLiens,
                            has_collections_recent: false,
                            revolving_available_pct: toNum(revolvingAvailablePct, 60),
                            has_cdl: industry === 'Trucking',
                            cdl_years: industry === 'Trucking' ? toNum(yearsInBusiness) : undefined,
                        }
                    ]
                },
                application: {
                    amount_requested: toNum(amountRequested, 75000),
                    term_months: toNum(termMonths, 60),
                    equipment_type: equipmentType,
                    equipment_year: toNum(equipmentYear, new Date().getFullYear()),
                    equipment_age_years: equipmentAgeYears,
                    equipment_mileage: equipmentMileage ? toNum(equipmentMileage) : undefined,
                    equipment_condition: equipmentAgeYears === 0 ? 'new' : 'used',
                    is_private_party_sale: isPrivateParty,
                    is_titled_asset: true,
                    is_refinance: false,
                    is_sale_leaseback: false,
                    paynet_score: paynetScore ? toNum(paynetScore) : undefined,
                    has_comparable_credit: toNum(comparableCreditPct) > 0,
                    comparable_credit_pct: toNum(comparableCreditPct, 80),
                }
            };

            // Create application
            const application = await createApplication(data);

            // Run underwriting
            await runUnderwriting(application.id!);

            // Navigate to results
            navigate(`/applications/${application.id}/results`);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const canProceed = () => {
        if (step === 1) {
            return businessName && industry && state && toNum(yearsInBusiness) >= 0;
        }
        if (step === 2) {
            const fico = toNum(ficoScore);
            return firstName && lastName && fico >= 300 && fico <= 850;
        }
        return toNum(amountRequested) >= 10000 && equipmentType && equipmentYear;
    };

    return (
        <div>
            <h1 style={{ marginBottom: '2rem' }}>New Loan Application</h1>

            {/* Steps indicator */}
            <div className="steps">
                <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
                    <span className="step-number">1</span>
                    <span>Business</span>
                </div>
                <div className={`step-connector ${step > 1 ? 'completed' : ''}`}></div>
                <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
                    <span className="step-number">2</span>
                    <span>Guarantor</span>
                </div>
                <div className={`step-connector ${step > 2 ? 'completed' : ''}`}></div>
                <div className={`step ${step >= 3 ? 'active' : ''}`}>
                    <span className="step-number">3</span>
                    <span>Loan Details</span>
                </div>
            </div>

            {error && (
                <div className="alert alert-error">{error}</div>
            )}

            <div className="card">
                {/* Step 1: Business Information */}
                {step === 1 && (
                    <>
                        <h3 style={{ marginBottom: '1.5rem' }}>Business Information</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Business Name *</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={businessName}
                                    onChange={(e) => setBusinessName(e.target.value)}
                                    placeholder="Your Company Name"
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Industry *</label>
                                <select
                                    className="form-select"
                                    value={industry}
                                    onChange={(e) => setIndustry(e.target.value)}
                                >
                                    <option value="">Select industry...</option>
                                    {INDUSTRIES.map(ind => (
                                        <option key={ind} value={ind}>{ind}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">State *</label>
                                <select
                                    className="form-select"
                                    value={state}
                                    onChange={(e) => setState(e.target.value)}
                                >
                                    <option value="">Select state...</option>
                                    {US_STATES.map(st => (
                                        <option key={st} value={st}>{st}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Years in Business *</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={yearsInBusiness}
                                    onChange={(e) => {
                                        setYearsInBusiness(e.target.value);
                                        // Auto-sync startup checkbox
                                        const years = parseFloat(e.target.value) || 0;
                                        setIsStartup(years < 2);
                                    }}
                                    min={0}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Annual Revenue ($)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={annualRevenue}
                                    onChange={(e) => setAnnualRevenue(e.target.value)}
                                    min={0}
                                    step={10000}
                                />
                            </div>
                            {industry === 'Trucking' && (
                                <div className="form-group">
                                    <label className="form-label">Number of Trucks</label>
                                    <input
                                        type="number"
                                        className="form-input"
                                        value={numTrucks}
                                        onChange={(e) => setNumTrucks(e.target.value)}
                                        min={0}
                                    />
                                </div>
                            )}
                        </div>

                        <div className="form-group">
                            <label className="form-checkbox" style={{ color: isStartup ? '#dc2626' : undefined }}>
                                <input
                                    type="checkbox"
                                    checked={isStartup}
                                    disabled
                                />
                                {isStartup
                                    ? 'Startup business (auto-set: less than 2 years)'
                                    : 'Established business (2+ years)'}
                            </label>
                        </div>
                    </>
                )}

                {/* Step 2: Guarantor Information */}
                {step === 2 && (
                    <>
                        <h3 style={{ marginBottom: '1.5rem' }}>Personal Guarantor Information</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">First Name *</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={firstName}
                                    onChange={(e) => setFirstName(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Last Name *</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={lastName}
                                    onChange={(e) => setLastName(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Ownership Percentage *</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={ownershipPct}
                                    onChange={(e) => setOwnershipPct(e.target.value)}
                                    min={0}
                                    max={100}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">FICO Score *</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={ficoScore}
                                    onChange={(e) => setFicoScore(e.target.value)}
                                    min={300}
                                    max={850}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Revolving Credit Available (%)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={revolvingAvailablePct}
                                    onChange={(e) => setRevolvingAvailablePct(e.target.value)}
                                    min={0}
                                    max={100}
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-checkbox">
                                <input
                                    type="checkbox"
                                    checked={isHomeowner}
                                    onChange={(e) => setIsHomeowner(e.target.checked)}
                                />
                                Homeowner
                            </label>
                        </div>

                        <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>Credit History</h4>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={hasBankruptcy}
                                        onChange={(e) => setHasBankruptcy(e.target.checked)}
                                    />
                                    Bankruptcy History
                                </label>
                            </div>
                            {hasBankruptcy && (
                                <div className="form-group">
                                    <label className="form-label">Bankruptcy Discharge Date</label>
                                    <input
                                        type="date"
                                        className="form-input"
                                        value={bankruptcyDischargeDate}
                                        onChange={(e) => setBankruptcyDischargeDate(e.target.value)}
                                        max={new Date().toISOString().split('T')[0]}
                                    />
                                </div>
                            )}
                            <div className="form-group">
                                <label className="form-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={hasJudgments}
                                        onChange={(e) => setHasJudgments(e.target.checked)}
                                    />
                                    Judgments
                                </label>
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={hasForeclosure}
                                        onChange={(e) => setHasForeclosure(e.target.checked)}
                                    />
                                    Foreclosure
                                </label>
                            </div>
                            <div className="form-group">
                                <label className="form-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={hasRepossession}
                                        onChange={(e) => setHasRepossession(e.target.checked)}
                                    />
                                    Repossession
                                </label>
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-checkbox">
                                <input
                                    type="checkbox"
                                    checked={hasTaxLiens}
                                    onChange={(e) => setHasTaxLiens(e.target.checked)}
                                />
                                Tax Liens
                            </label>
                        </div>
                    </>
                )}

                {/* Step 3: Loan Details */}
                {step === 3 && (
                    <>
                        <h3 style={{ marginBottom: '1.5rem' }}>Loan & Equipment Details</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Amount Requested ($) *</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={amountRequested}
                                    onChange={(e) => setAmountRequested(e.target.value)}
                                    min={10000}
                                    step={5000}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Term (months)</label>
                                <select
                                    className="form-select"
                                    value={termMonths}
                                    onChange={(e) => setTermMonths(e.target.value)}
                                >
                                    <option value="24">24 months</option>
                                    <option value="36">36 months</option>
                                    <option value="48">48 months</option>
                                    <option value="60">60 months</option>
                                </select>
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Equipment Type *</label>
                                <select
                                    className="form-select"
                                    value={equipmentType}
                                    onChange={(e) => setEquipmentType(e.target.value)}
                                >
                                    <option value="">Select equipment type...</option>
                                    {EQUIPMENT_TYPES.map(type => (
                                        <option key={type} value={type}>{type}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Equipment Year *</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={equipmentYear}
                                    onChange={(e) => setEquipmentYear(e.target.value)}
                                    min={1990}
                                    max={new Date().getFullYear() + 1}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Equipment Age (years)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={Math.max(0, new Date().getFullYear() - toNum(equipmentYear, new Date().getFullYear()))}
                                    readOnly
                                    disabled
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Equipment Mileage (if applicable)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={equipmentMileage}
                                    onChange={(e) => setEquipmentMileage(e.target.value)}
                                    min={0}
                                    placeholder="Leave blank if not applicable"
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">PayNet Score</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={paynetScore}
                                    onChange={(e) => setPaynetScore(e.target.value)}
                                    min={300}
                                    max={850}
                                    placeholder="Leave blank if not available"
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Comparable Credit (%)</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    value={comparableCreditPct}
                                    onChange={(e) => setComparableCreditPct(e.target.value)}
                                    min={0}
                                    max={100}
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-checkbox">
                                <input
                                    type="checkbox"
                                    checked={isPrivateParty}
                                    onChange={(e) => setIsPrivateParty(e.target.checked)}
                                />
                                Private Party Sale
                            </label>
                        </div>
                    </>
                )}

                {/* Navigation buttons */}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
                    {step > 1 && (
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => setStep(step - 1)}
                        >
                            ← Previous
                        </button>
                    )}
                    {step === 1 && <div></div>}

                    {step < 3 && (
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={() => setStep(step + 1)}
                            disabled={!canProceed()}
                        >
                            Next →
                        </button>
                    )}

                    {step === 3 && (
                        <button
                            type="button"
                            className="btn btn-success btn-lg"
                            onClick={handleSubmit}
                            disabled={loading || !canProceed()}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner" style={{ width: 16, height: 16 }}></span>
                                    Processing...
                                </>
                            ) : (
                                'Submit & Find Matches'
                            )}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

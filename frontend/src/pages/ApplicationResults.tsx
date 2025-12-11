import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getApplication, getResults, UnderwritingResults, MatchResult, LoanApplication } from '../services/api';

function ScoreCircle({ score }: { score: number }) {
    const getScoreClass = () => {
        if (score >= 80) return 'score-high';
        if (score >= 50) return 'score-medium';
        return 'score-low';
    };

    return (
        <div className={`score-circle ${getScoreClass()}`}>
            {score}
        </div>
    );
}

function RuleEvaluationList({ details }: { details: MatchResult['evaluation_details'] }) {
    const [showAll, setShowAll] = useState(false);

    const displayItems = showAll ? details.details : details.details.slice(0, 5);

    return (
        <div>
            <ul className="rule-list">
                {displayItems.map((rule, idx) => (
                    <li key={idx} className="rule-item">
                        <span className={`rule-icon ${rule.passed ? 'pass' : 'fail'}`}>
                            {rule.passed ? '✓' : '✗'}
                        </span>
                        <div className="rule-content">
                            <div className="rule-type">{rule.rule_type.replace(/_/g, ' ')}</div>
                            <div className="rule-reason">{rule.reason}</div>
                            <div className="rule-values">
                                Required: {JSON.stringify(rule.required_value)} |
                                Actual: {JSON.stringify(rule.actual_value)}
                            </div>
                        </div>
                    </li>
                ))}
            </ul>

            {details.details.length > 5 && (
                <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setShowAll(!showAll)}
                    style={{ marginTop: '0.5rem' }}
                >
                    {showAll ? 'Show Less' : `Show All (${details.details.length})`}
                </button>
            )}
        </div>
    );
}

function ResultCard({ result }: { result: MatchResult }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className={`result-card ${result.is_eligible ? 'eligible' : 'ineligible'}`}>
            <div className="result-card-header">
                <div>
                    <div className="result-lender-name">{result.lender_name || 'Unknown Lender'}</div>
                    <div className="result-program-name">
                        {result.program_name || 'No matching program'}
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span className={`badge ${result.is_eligible ? 'badge-success' : 'badge-danger'}`}>
                        {result.is_eligible ? 'Eligible' : 'Not Eligible'}
                    </span>
                    <ScoreCircle score={result.fit_score} />
                </div>
            </div>

            <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem' }}>
                <div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Rules Passed</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--success-500)' }}>
                        {result.evaluation_details.rules_passed}
                    </div>
                </div>
                <div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Rules Failed</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--danger-500)' }}>
                        {result.evaluation_details.rules_failed}
                    </div>
                </div>
                <div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Pass Rate</span>
                    <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                        {Math.round(result.evaluation_details.pass_rate * 100)}%
                    </div>
                </div>
            </div>

            <div className="expandable">
                <div className="expandable-header" onClick={() => setExpanded(!expanded)}>
                    <span>View Detailed Evaluation</span>
                    <span>{expanded ? '▲' : '▼'}</span>
                </div>
                {expanded && (
                    <div className="expandable-content">
                        <RuleEvaluationList details={result.evaluation_details} />
                    </div>
                )}
            </div>
        </div>
    );
}

export function ApplicationResults() {
    const { id } = useParams<{ id: string }>();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [application, setApplication] = useState<LoanApplication | null>(null);
    const [results, setResults] = useState<UnderwritingResults | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            if (!id) return;

            try {
                const [appData, resultsData] = await Promise.all([
                    getApplication(id),
                    getResults(id)
                ]);
                setApplication(appData);
                setResults(resultsData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load results');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [id]);

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="alert alert-error">
                {error}
                <Link to="/" className="btn btn-primary" style={{ marginLeft: '1rem' }}>
                    New Application
                </Link>
            </div>
        );
    }

    if (!results || !application) {
        return (
            <div className="empty-state">
                <h3>No results found</h3>
                <p>This application has not been underwritten yet.</p>
            </div>
        );
    }

    const eligible = results.results.filter(r => r.is_eligible);
    const ineligible = results.results.filter(r => !r.is_eligible);

    return (
        <div>
            <div className="section-header">
                <div>
                    <h1>Underwriting Results</h1>
                    <p style={{ marginTop: '0.5rem' }}>
                        {application.borrower?.business_name || 'Application'} -
                        ${application.amount_requested.toLocaleString()} for {application.equipment_type}
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Link to="/applications" className="btn btn-secondary">
                        ← Back
                    </Link>
                    <Link to="/" className="btn btn-primary">
                        New Application
                    </Link>
                </div>
            </div>

            {/* Summary stats */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-value">{results.total_lenders}</div>
                    <div className="stat-label">Lenders Evaluated</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value" style={{ color: 'var(--success-500)' }}>
                        {results.eligible_count}
                    </div>
                    <div className="stat-label">Eligible Matches</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value" style={{ color: 'var(--danger-500)' }}>
                        {results.ineligible_count}
                    </div>
                    <div className="stat-label">Not Eligible</div>
                </div>
                {results.best_match && (
                    <div className="stat-card">
                        <div className="stat-value">{results.best_match.fit_score}</div>
                        <div className="stat-label">Best Fit Score</div>
                    </div>
                )}
            </div>

            {/* Best match highlight */}
            {results.best_match && (
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem' }}>🏆 Best Match</h3>
                    <ResultCard result={results.best_match} />
                </div>
            )}

            {/* Eligible lenders */}
            {eligible.length > 0 && (
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ marginBottom: '1rem' }}>✅ Eligible Lenders ({eligible.length})</h3>
                    {eligible.map(result => (
                        <ResultCard key={result.id} result={result} />
                    ))}
                </div>
            )}

            {/* Ineligible lenders */}
            {ineligible.length > 0 && (
                <div>
                    <h3 style={{ marginBottom: '1rem' }}>❌ Not Eligible ({ineligible.length})</h3>
                    {ineligible.map(result => (
                        <ResultCard key={result.id} result={result} />
                    ))}
                </div>
            )}
        </div>
    );
}

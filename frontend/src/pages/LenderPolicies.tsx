import { useState, useEffect } from 'react';
import {
    getLenders, getLender, updateRule, createRule, deleteRule, getRuleTypes,
    LenderSummary, Lender, PolicyRule
} from '../services/api';

function RuleEditor({
    rule,
    ruleTypes,
    onSave,
    onCancel
}: {
    rule?: PolicyRule;
    ruleTypes: string[];
    onSave: (data: Partial<PolicyRule>) => void;
    onCancel: () => void;
}) {
    const [ruleType, setRuleType] = useState(rule?.rule_type || '');
    const [operator, setOperator] = useState(rule?.operator || 'gte');
    const [value, setValue] = useState(
        rule?.value?.value !== undefined
            ? JSON.stringify(rule.value.value)
            : ''
    );
    const [rejectionMessage, setRejectionMessage] = useState(rule?.rejection_message || '');
    const [isRequired, setIsRequired] = useState(rule?.is_required ?? true);
    const [weight, setWeight] = useState(rule?.weight || 10);

    const handleSubmit = () => {
        let parsedValue;
        try {
            parsedValue = JSON.parse(value);
        } catch {
            parsedValue = value;
        }

        onSave({
            rule_type: ruleType,
            operator: operator as any,
            value: parsedValue,
            rejection_message: rejectionMessage,
            is_required: isRequired,
            weight,
            is_active: true,
        });
    };

    return (
        <div className="card" style={{ marginBottom: '1rem' }}>
            <h4>{rule ? 'Edit Rule' : 'Add New Rule'}</h4>

            <div className="form-row" style={{ marginTop: '1rem' }}>
                <div className="form-group">
                    <label className="form-label">Rule Type</label>
                    <select
                        className="form-select"
                        value={ruleType}
                        onChange={(e) => setRuleType(e.target.value)}
                    >
                        <option value="">Select type...</option>
                        {ruleTypes.map(type => (
                            <option key={type} value={type}>{type.replace(/_/g, ' ')}</option>
                        ))}
                    </select>
                </div>
                <div className="form-group">
                    <label className="form-label">Operator</label>
                    <select
                        className="form-select"
                        value={operator}
                        onChange={(e) => setOperator(e.target.value)}
                    >
                        <option value="gte">Greater than or equal (≥)</option>
                        <option value="lte">Less than or equal (≤)</option>
                        <option value="eq">Equal (=)</option>
                        <option value="neq">Not equal (≠)</option>
                        <option value="in">In list</option>
                        <option value="not_in">Not in list</option>
                    </select>
                </div>
            </div>

            <div className="form-group">
                <label className="form-label">Value (JSON format for arrays/objects)</label>
                <input
                    type="text"
                    className="form-input"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    placeholder='e.g., 700 or ["CA", "NV"]'
                />
            </div>

            <div className="form-group">
                <label className="form-label">Rejection Message</label>
                <input
                    type="text"
                    className="form-input"
                    value={rejectionMessage}
                    onChange={(e) => setRejectionMessage(e.target.value)}
                    placeholder="Message shown when rule fails"
                />
            </div>

            <div className="form-row">
                <div className="form-group">
                    <label className="form-checkbox">
                        <input
                            type="checkbox"
                            checked={isRequired}
                            onChange={(e) => setIsRequired(e.target.checked)}
                        />
                        Required (hard requirement)
                    </label>
                </div>
                <div className="form-group">
                    <label className="form-label">Weight (for scoring)</label>
                    <input
                        type="number"
                        className="form-input"
                        value={weight}
                        onChange={(e) => setWeight(Number(e.target.value))}
                        min={1}
                        max={100}
                    />
                </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                <button className="btn btn-primary" onClick={handleSubmit}>
                    Save Rule
                </button>
                <button className="btn btn-secondary" onClick={onCancel}>
                    Cancel
                </button>
            </div>
        </div>
    );
}

function ProgramRules({
    program,
    ruleTypes,
    onRuleUpdated
}: {
    program: Lender['programs'][0];
    ruleTypes: string[];
    onRuleUpdated: () => void;
}) {
    const [expanded, setExpanded] = useState(false);
    const [editingRule, setEditingRule] = useState<PolicyRule | null>(null);
    const [addingRule, setAddingRule] = useState(false);

    const handleSaveRule = async (data: Partial<PolicyRule>) => {
        try {
            if (editingRule) {
                await updateRule(editingRule.id, data);
            } else {
                await createRule(program.id, data);
            }
            setEditingRule(null);
            setAddingRule(false);
            onRuleUpdated();
        } catch (err) {
            alert('Failed to save rule');
        }
    };

    const handleDeleteRule = async (ruleId: string) => {
        if (!confirm('Are you sure you want to delete this rule?')) return;

        try {
            await deleteRule(ruleId);
            onRuleUpdated();
        } catch (err) {
            alert('Failed to delete rule');
        }
    };

    return (
        <div className="expandable" style={{ marginBottom: '0.5rem' }}>
            <div className="expandable-header" onClick={() => setExpanded(!expanded)}>
                <div>
                    <strong>{program.name}</strong>
                    {program.credit_tier && (
                        <span className="badge badge-primary" style={{ marginLeft: '0.5rem' }}>
                            {program.credit_tier}
                        </span>
                    )}
                    <span style={{ marginLeft: '1rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                        {program.rules.length} rules
                    </span>
                </div>
                <span>{expanded ? '▲' : '▼'}</span>
            </div>

            {expanded && (
                <div className="expandable-content">
                    {program.description && (
                        <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                            {program.description}
                        </p>
                    )}

                    {/* Program limits */}
                    <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem', fontSize: '0.875rem' }}>
                        {program.min_loan_amount && (
                            <div>Min: ${program.min_loan_amount.toLocaleString()}</div>
                        )}
                        {program.max_loan_amount && (
                            <div>Max: ${program.max_loan_amount.toLocaleString()}</div>
                        )}
                        {program.max_term_months && (
                            <div>Max Term: {program.max_term_months} months</div>
                        )}
                    </div>

                    {/* Edit/Add forms */}
                    {(editingRule || addingRule) && (
                        <RuleEditor
                            rule={editingRule || undefined}
                            ruleTypes={ruleTypes}
                            onSave={handleSaveRule}
                            onCancel={() => {
                                setEditingRule(null);
                                setAddingRule(false);
                            }}
                        />
                    )}

                    {/* Rules list */}
                    {!editingRule && !addingRule && (
                        <>
                            <div className="table-container">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Rule Type</th>
                                            <th>Operator</th>
                                            <th>Value</th>
                                            <th>Required</th>
                                            <th>Weight</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {program.rules.map(rule => (
                                            <tr key={rule.id}>
                                                <td style={{ textTransform: 'capitalize' }}>
                                                    {rule.rule_type.replace(/_/g, ' ')}
                                                </td>
                                                <td>{rule.operator}</td>
                                                <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                    {JSON.stringify(rule.value?.value ?? rule.value)}
                                                </td>
                                                <td>
                                                    <span className={`badge ${rule.is_required ? 'badge-danger' : 'badge-warning'}`}>
                                                        {rule.is_required ? 'Required' : 'Soft'}
                                                    </span>
                                                </td>
                                                <td>{rule.weight}</td>
                                                <td>
                                                    <button
                                                        className="btn btn-sm btn-secondary"
                                                        onClick={() => setEditingRule(rule)}
                                                        style={{ marginRight: '0.25rem' }}
                                                    >
                                                        Edit
                                                    </button>
                                                    <button
                                                        className="btn btn-sm btn-danger"
                                                        onClick={() => handleDeleteRule(rule.id)}
                                                    >
                                                        Delete
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <button
                                className="btn btn-primary"
                                onClick={() => setAddingRule(true)}
                                style={{ marginTop: '1rem' }}
                            >
                                + Add Rule
                            </button>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

export function LenderPolicies() {
    const [loading, setLoading] = useState(true);
    const [lenders, setLenders] = useState<LenderSummary[]>([]);
    const [selectedLender, setSelectedLender] = useState<Lender | null>(null);
    const [ruleTypes, setRuleTypes] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);

    const fetchLenders = async () => {
        try {
            const data = await getLenders();
            setLenders(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load lenders');
        }
    };

    const fetchRuleTypes = async () => {
        try {
            const types = await getRuleTypes();
            setRuleTypes(types);
        } catch (err) {
            console.error('Failed to load rule types');
        }
    };

    useEffect(() => {
        Promise.all([fetchLenders(), fetchRuleTypes()]).finally(() => setLoading(false));
    }, []);

    const handleSelectLender = async (id: string) => {
        try {
            const lender = await getLender(id);
            setSelectedLender(lender);
        } catch (err) {
            setError('Failed to load lender details');
        }
    };

    const handleRuleUpdated = async () => {
        if (selectedLender) {
            const updated = await getLender(selectedLender.id);
            setSelectedLender(updated);
        }
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
            </div>
        );
    }

    if (error) {
        return <div className="alert alert-error">{error}</div>;
    }

    return (
        <div>
            <div className="section-header">
                <h1>Lender Policies</h1>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem' }}>
                {/* Lender list */}
                <div className="card">
                    <h3 style={{ marginBottom: '1rem' }}>Lenders</h3>
                    {lenders.length === 0 ? (
                        <p style={{ color: 'var(--text-muted)' }}>No lenders found. Run seed script to populate.</p>
                    ) : (
                        <ul style={{ listStyle: 'none' }}>
                            {lenders.map(lender => (
                                <li
                                    key={lender.id}
                                    onClick={() => handleSelectLender(lender.id)}
                                    style={{
                                        padding: '0.75rem',
                                        borderRadius: 'var(--radius-md)',
                                        cursor: 'pointer',
                                        marginBottom: '0.25rem',
                                        background: selectedLender?.id === lender.id
                                            ? 'var(--bg-tertiary)'
                                            : 'transparent',
                                        border: selectedLender?.id === lender.id
                                            ? '1px solid var(--primary-500)'
                                            : '1px solid transparent',
                                    }}
                                >
                                    <div style={{ fontWeight: 500 }}>{lender.name}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                        {lender.program_count} programs
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                {/* Lender details */}
                <div>
                    {selectedLender ? (
                        <div className="card">
                            <div className="card-header">
                                <div>
                                    <h2>{selectedLender.name}</h2>
                                    {selectedLender.description && (
                                        <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
                                            {selectedLender.description}
                                        </p>
                                    )}
                                </div>
                                <span className={`badge ${selectedLender.is_active ? 'badge-success' : 'badge-danger'}`}>
                                    {selectedLender.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </div>

                            {/* Contact info */}
                            {(selectedLender.contact_name || selectedLender.contact_email) && (
                                <div style={{ marginBottom: '1.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                    {selectedLender.contact_name && <div>Contact: {selectedLender.contact_name}</div>}
                                    {selectedLender.contact_email && <div>Email: {selectedLender.contact_email}</div>}
                                    {selectedLender.contact_phone && <div>Phone: {selectedLender.contact_phone}</div>}
                                </div>
                            )}

                            {/* Programs */}
                            <h3 style={{ marginBottom: '1rem' }}>Programs ({selectedLender.programs.length})</h3>
                            {selectedLender.programs.map(program => (
                                <ProgramRules
                                    key={program.id}
                                    program={program}
                                    ruleTypes={ruleTypes}
                                    onRuleUpdated={handleRuleUpdated}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">
                            <h3>Select a lender</h3>
                            <p>Choose a lender from the list to view and edit their policies.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

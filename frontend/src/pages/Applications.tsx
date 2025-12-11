import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getApplications, LoanApplication } from '../services/api';

export function Applications() {
    const [loading, setLoading] = useState(true);
    const [applications, setApplications] = useState<LoanApplication[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchApplications = async () => {
            try {
                const data = await getApplications();
                setApplications(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load applications');
            } finally {
                setLoading(false);
            }
        };

        fetchApplications();
    }, []);

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="alert alert-error">{error}</div>
        );
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed':
                return <span className="badge badge-success">Completed</span>;
            case 'underwriting':
                return <span className="badge badge-warning">Underwriting</span>;
            case 'submitted':
                return <span className="badge badge-primary">Submitted</span>;
            default:
                return <span className="badge">{status}</span>;
        }
    };

    return (
        <div>
            <div className="section-header">
                <h1>Loan Applications</h1>
                <Link to="/" className="btn btn-primary">
                    + New Application
                </Link>
            </div>

            {applications.length === 0 ? (
                <div className="empty-state">
                    <h3>No applications yet</h3>
                    <p>Create your first loan application to get started.</p>
                    <Link to="/" className="btn btn-primary" style={{ marginTop: '1rem' }}>
                        Create Application
                    </Link>
                </div>
            ) : (
                <div className="card">
                    <div className="table-container">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Business</th>
                                    <th>Amount</th>
                                    <th>Equipment</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {applications.map(app => (
                                    <tr key={app.id}>
                                        <td>
                                            <strong>{app.borrower?.business_name || 'N/A'}</strong>
                                            <br />
                                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                {app.borrower?.industry} • {app.borrower?.state}
                                            </span>
                                        </td>
                                        <td>${app.amount_requested.toLocaleString()}</td>
                                        <td>{app.equipment_type}</td>
                                        <td>{getStatusBadge(app.status || 'draft')}</td>
                                        <td>
                                            {app.created_at
                                                ? new Date(app.created_at).toLocaleDateString()
                                                : 'N/A'}
                                        </td>
                                        <td>
                                            {app.status === 'completed' ? (
                                                <Link
                                                    to={`/applications/${app.id}/results`}
                                                    className="btn btn-sm btn-primary"
                                                >
                                                    View Results
                                                </Link>
                                            ) : (
                                                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                                    Pending
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

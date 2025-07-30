import React, { useEffect, useState } from 'react';
import './ControlDashboard.css';

interface ControlSummary {
  controlId: string;
  name: string;
  lastExecution: string;
  status: 'pass' | 'fail' | 'warning' | 'running' | 'notrun';
  criticality: 'high' | 'medium' | 'low';
  category: string;
}

const ControlDashboard: React.FC = () => {
  const [controls, setControls] = useState<ControlSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    // Simulated data for demonstration
    setTimeout(() => {
      setControls([
        {
          controlId: 'CTRL-00042697',
          name: 'Flatbook Configuration Check',
          lastExecution: '2024-01-15T09:10:55Z',
          status: 'pass',
          criticality: 'high',
          category: 'Configuration'
        },
        {
          controlId: 'RISK_VAL_CTRL-00051234',
          name: 'Risk Valuation Reconciliation',
          lastExecution: '2024-01-15T08:45:00Z',
          status: 'fail',
          criticality: 'high',
          category: 'Reconciliation'
        },
        {
          controlId: 'TRADE_BOOK_CTRL-00067890',
          name: 'Trade Booking Validation',
          lastExecution: '2024-01-15T09:00:00Z',
          status: 'warning',
          criticality: 'medium',
          category: 'Trading'
        },
        {
          controlId: 'REG_RPT_CTRL-00045678',
          name: 'Regulatory Reporting Check',
          lastExecution: '2024-01-15T07:30:00Z',
          status: 'pass',
          criticality: 'high',
          category: 'Regulatory'
        },
        {
          controlId: 'CASH_REC_CTRL-00023456',
          name: 'Cash Reconciliation',
          lastExecution: '2024-01-15T09:15:00Z',
          status: 'running',
          criticality: 'high',
          category: 'Reconciliation'
        },
        {
          controlId: 'DATA_QUAL_CTRL-00089012',
          name: 'Data Quality Validation',
          lastExecution: '2024-01-14T23:00:00Z',
          status: 'pass',
          criticality: 'medium',
          category: 'Data Quality'
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'pass': return 'pass';
      case 'fail': return 'fail';
      case 'warning': return 'warning';
      case 'running': return 'running';
      default: return 'neutral';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const filteredControls = filter === 'all' 
    ? controls 
    : controls.filter(c => c.status === filter);

  const statusCounts = {
    pass: controls.filter(c => c.status === 'pass').length,
    fail: controls.filter(c => c.status === 'fail').length,
    warning: controls.filter(c => c.status === 'warning').length,
    running: controls.filter(c => c.status === 'running').length,
    total: controls.length
  };

  if (loading) {
    return <div className="text-center mt-4">Loading controls...</div>;
  }

  return (
    <div className="control-dashboard">
      <div className="dashboard-header mb-4">
        <h2>Control Execution Dashboard</h2>
        <div className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-value">{statusCounts.total}</div>
            <div className="stat-label">Total Controls</div>
          </div>
          <div className="stat-card pass">
            <div className="stat-value">{statusCounts.pass}</div>
            <div className="stat-label">Passing</div>
          </div>
          <div className="stat-card fail">
            <div className="stat-value">{statusCounts.fail}</div>
            <div className="stat-label">Failing</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-value">{statusCounts.warning}</div>
            <div className="stat-label">Warnings</div>
          </div>
          <div className="stat-card running">
            <div className="stat-value">{statusCounts.running}</div>
            <div className="stat-label">Running</div>
          </div>
        </div>
      </div>

      <div className="filter-bar mb-3">
        <button 
          className={`btn btn-secondary ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Controls
        </button>
        <button 
          className={`btn btn-secondary ${filter === 'pass' ? 'active' : ''}`}
          onClick={() => setFilter('pass')}
        >
          Passing
        </button>
        <button 
          className={`btn btn-secondary ${filter === 'fail' ? 'active' : ''}`}
          onClick={() => setFilter('fail')}
        >
          Failing
        </button>
        <button 
          className={`btn btn-secondary ${filter === 'warning' ? 'active' : ''}`}
          onClick={() => setFilter('warning')}
        >
          Warnings
        </button>
      </div>

      <div className="control-grid">
        {filteredControls.map((control) => (
          <div key={control.controlId} className={`control-card ${getStatusClass(control.status)}`}>
            <div className="control-header">
              <div>
                <div className="control-title">{control.name}</div>
                <div className="control-id">{control.controlId}</div>
              </div>
              <span className={`status-badge ${getStatusClass(control.status)}`}>
                {control.status}
              </span>
            </div>
            <div className="control-body mt-2">
              <div className="control-info">
                <span className="text-muted">Category:</span> {control.category}
              </div>
              <div className="control-info">
                <span className="text-muted">Criticality:</span> 
                <span className={`criticality-${control.criticality}`}> {control.criticality.toUpperCase()}</span>
              </div>
              <div className="control-info">
                <span className="text-muted">Last Run:</span> {formatTime(control.lastExecution)}
              </div>
            </div>
            <div className="control-actions mt-3">
              <button className="btn btn-primary">View Details</button>
              <button className="btn btn-secondary">Compare</button>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};

export default ControlDashboard;
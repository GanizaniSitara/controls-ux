import React, { useEffect, useState } from 'react';
import './DataInspector.css';

interface ControlExecution {
  controlId: string;
  name: string;
  executionTime: string;
  status: 'pass' | 'fail' | 'warning' | 'error';
  evidence?: {
    files?: string[];
    metrics?: Record<string, any>;
    logs?: string[];
  };
  comparisonMetadata?: {
    ignorableFields?: string[];
    criticalFields?: string[];
  };
}

interface ControlData {
  executions: ControlExecution[];
  metadata: {
    lastSync: string;
    totalControls: number;
    passRate: number;
  };
}

const DataInspector: React.FC = () => {
  const [data, setData] = useState<ControlData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedControl, setSelectedControl] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // For now, using mock data until backend is updated
        const mockData: ControlData = {
          executions: [
            {
              controlId: 'CTRL-00042697',
              name: 'System Configuration Check',
              executionTime: '2024-01-15T09:10:55Z',
              status: 'pass',
              evidence: {
                files: ['/evidence/control/system_config_20240115.json'],
                metrics: {
                  'configurations_checked': 42,
                  'validation_errors': 0,
                  'execution_time_ms': 1234
                },
                logs: ['Configuration validated successfully']
              },
              comparisonMetadata: {
                ignorableFields: ['timestamp', 'execution_id'],
                criticalFields: ['status', 'validation_errors']
              }
            },
            {
              controlId: 'RISK_VAL_CTRL-00051234',
              name: 'Risk Valuation Reconciliation',
              executionTime: '2024-01-15T08:45:00Z',
              status: 'fail',
              evidence: {
                files: ['/evidence/risk/valuation_mismatch_20240115.csv'],
                metrics: {
                  'total_positions': 15420,
                  'mismatched_positions': 23,
                  'mismatch_percentage': 0.15
                },
                logs: ['23 positions with valuation discrepancies detected']
              }
            },
            {
              controlId: 'TRADE_BOOK_CTRL-00067890',
              name: 'Trade Booking Validation',
              executionTime: '2024-01-15T09:00:00Z',
              status: 'warning',
              evidence: {
                metrics: {
                  'trades_processed': 3421,
                  'late_bookings': 5,
                  'booking_delay_avg_minutes': 12
                }
              }
            }
          ],
          metadata: {
            lastSync: new Date().toISOString(),
            totalControls: 3,
            passRate: 33.33
          }
        };
        
        setData(mockData);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
        setLoading(false);
      }
    };

    fetchData();
    // Poll every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pass': return 'var(--status-pass)';
      case 'fail': return 'var(--status-fail)';
      case 'warning': return 'var(--status-warning)';
      case 'error': return 'var(--status-fail)';
      default: return 'var(--status-neutral)';
    }
  };

  if (loading) {
    return <div className="data-inspector-loading">Loading control execution data...</div>;
  }

  if (error) {
    return <div className="data-inspector-error">Error: {error}</div>;
  }

  if (!data) {
    return <div className="data-inspector-empty">No control execution data available</div>;
  }

  return (
    <div className="data-inspector-container">
      <h2>Control Execution Data Inspector</h2>
      
      <div className="metadata-section">
        <div className="metadata-card">
          <div className="metadata-label">Last Sync</div>
          <div className="metadata-value">{formatTime(data.metadata.lastSync)}</div>
        </div>
        <div className="metadata-card">
          <div className="metadata-label">Total Controls</div>
          <div className="metadata-value">{data.metadata.totalControls}</div>
        </div>
        <div className="metadata-card">
          <div className="metadata-label">Pass Rate</div>
          <div className="metadata-value">{data.metadata.passRate.toFixed(1)}%</div>
        </div>
      </div>

      <div className="inspector-main">
        <div className="control-list">
          <h3>Control Executions</h3>
          {data.executions.map((execution) => (
            <div
              key={execution.controlId}
              className={`control-item ${selectedControl === execution.controlId ? 'selected' : ''}`}
              onClick={() => setSelectedControl(execution.controlId)}
            >
              <div className="control-item-header">
                <span className="control-name">{execution.name}</span>
                <span 
                  className="control-status"
                  style={{ color: getStatusColor(execution.status) }}
                >
                  {execution.status.toUpperCase()}
                </span>
              </div>
              <div className="control-item-info">
                <span className="control-id">{execution.controlId}</span>
                <span className="control-time">{formatTime(execution.executionTime)}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="control-details">
          {selectedControl ? (
            <>
              <h3>Execution Details</h3>
              {(() => {
                const selected = data.executions.find(e => e.controlId === selectedControl);
                if (!selected) return <div>Select a control to view details</div>;
                
                return (
                  <div className="details-content">
                    <div className="detail-section">
                      <h4>Basic Information</h4>
                      <pre>{JSON.stringify({
                        controlId: selected.controlId,
                        name: selected.name,
                        status: selected.status,
                        executionTime: selected.executionTime
                      }, null, 2)}</pre>
                    </div>

                    {selected.evidence && (
                      <div className="detail-section">
                        <h4>Evidence</h4>
                        <pre>{JSON.stringify(selected.evidence, null, 2)}</pre>
                      </div>
                    )}

                    {selected.comparisonMetadata && (
                      <div className="detail-section">
                        <h4>Comparison Metadata</h4>
                        <pre>{JSON.stringify(selected.comparisonMetadata, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                );
              })()}
            </>
          ) : (
            <div className="no-selection">
              <p>Select a control execution from the list to view detailed data</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DataInspector;
import React, { useState, useEffect } from 'react';
import './ComparisonView.css';
import './comparison-override.css';
import EvidenceGrid from './EvidenceGrid';

interface EvidenceAnalysis {
  timestamp: string;
  evidence_path: string;
  bucket_hours: number;
  runs: Record<string, any[]>;
  bucketized: Record<string, any>;
  duplicates: Record<string, any[]>;
  deltas: Record<string, any[]>;
  summary: {
    total_controls: number;
    total_runs: number;
    controls_with_duplicates: number;
    total_duplicate_sets: number;
  };
}

const ComparisonView: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<EvidenceAnalysis | null>(null);
  const [evidencePath, setEvidencePath] = useState('');
  const [bucketHours, setBucketHours] = useState(2);
  const [selectedControl, setSelectedControl] = useState<string | null>(null);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  // Auto-load evidence on component mount
  useEffect(() => {
    loadLatestEvidence();
  }, []);

  const loadLatestEvidence = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (evidencePath) params.append('evidence_path', evidencePath);
      params.append('bucket_hours', bucketHours.toString());
      
      const response = await fetch(`http://localhost:8002/api/evidence/scan?${params}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to scan evidence');
      }
      
      const data = await response.json();
      setAnalysis(data);
      setHasLoadedOnce(true);
      
      // Auto-select first control if none selected
      if (!selectedControl && Object.keys(data.runs).length > 0) {
        setSelectedControl(Object.keys(data.runs)[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setHasLoadedOnce(true);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };


  return (
    <div className="comparison-container">
      <div className="comparison-wrapper">
        <div className="comparison-header">
          <h2>Evidence Analysis & Comparison</h2>
          <div className="controls">
            <div className="input-group">
              <label>Bucket Hours:</label>
              <select
                value={bucketHours}
                onChange={(e) => setBucketHours(Number(e.target.value))}
                className="bucket-select"
              >
                <option value={1}>1 hour</option>
                <option value={2}>2 hours</option>
                <option value={4}>4 hours</option>
                <option value={8}>8 hours</option>
                <option value={24}>24 hours</option>
              </select>
            </div>
            <button
              onClick={loadLatestEvidence}
              disabled={loading}
              className="load-button"
            >
              {loading ? 'Loading...' : 'Refresh Evidence'}
            </button>
            <div className="controls-spacer"></div>
            {analysis && (
              <div className="controls-info">
                <span>Last scan: {new Date(analysis.timestamp).toLocaleTimeString()}</span>
                <span className="separator">|</span>
                <span>{analysis.summary.total_controls} controls</span>
                <span className="separator">|</span>
                <span>{analysis.summary.total_runs} runs</span>
              </div>
            )}
          </div>
        </div>

      {loading && !hasLoadedOnce && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading evidence data...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <div>Error: {error}</div>
          <button onClick={loadLatestEvidence} className="retry-button">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && !analysis && hasLoadedOnce && (
        <div className="empty-state">
          <h3>No Evidence Data Available</h3>
          <p>No evidence folders were found in the configured path.</p>
          <button onClick={loadLatestEvidence} className="load-button">
            Retry Scan
          </button>
        </div>
      )}

      {analysis && (
        <div className="analysis-results">
          
          {/* Evidence Grid - matching the screenshot format */}
          <EvidenceGrid analysis={analysis} />
          
          <div className="summary-section">
            <h3>Summary</h3>
            <div className="summary-stats">
              <div className="stat">
                <span className="stat-value">{analysis.summary.total_controls}</span>
                <span className="stat-label">Total Controls</span>
              </div>
              <div className="stat">
                <span className="stat-value">{analysis.summary.total_runs}</span>
                <span className="stat-label">Total Runs</span>
              </div>
              <div className="stat">
                <span className="stat-value">{analysis.summary.controls_with_duplicates}</span>
                <span className="stat-label">Controls with Duplicates</span>
              </div>
              <div className="stat">
                <span className="stat-value">{analysis.summary.total_duplicate_sets}</span>
                <span className="stat-label">Duplicate Sets</span>
              </div>
            </div>
            <div className="scan-info">
              <p>Scanned at: {formatTimestamp(analysis.timestamp)}</p>
              <p>Evidence path: {analysis.evidence_path}</p>
              <p>Bucket size: {analysis.bucket_hours} hours</p>
            </div>
          </div>

        </div>
      )}
      </div>
    </div>
  );
};

export default ComparisonView;
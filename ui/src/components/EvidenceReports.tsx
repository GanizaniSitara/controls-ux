import React, { useState, useEffect } from 'react';
import './EvidenceReports.css';

interface EvidenceFolder {
  name: string;
  path: string;
  hasReport: boolean;
  timestamp?: string;
}

const EvidenceReports: React.FC = () => {
  const [folders, setFolders] = useState<EvidenceFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEvidenceFolders();
  }, []);

  const fetchEvidenceFolders = async () => {
    try {
      const response = await fetch('http://localhost:8002/api/evidence-folders');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setFolders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch evidence folders');
    } finally {
      setLoading(false);
    }
  };

  const handleReportClick = (folder: EvidenceFolder) => {
    // Open the Evidence_report.html in a new tab
    window.open(`http://localhost:8002/evidence/${folder.name}/Evidence_report.html`, '_blank');
  };

  if (loading) {
    return (
      <div className="evidence-reports-container">
        <h2>Evidence Reports</h2>
        <div className="loading">Loading evidence folders...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="evidence-reports-container">
        <h2>Evidence Reports</h2>
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="evidence-reports-container">
      <h2>Evidence Reports</h2>
      <div className="evidence-list">
        <div className="evidence-header">
          <span className="control-name">Control Name</span>
          <span className="timestamp">Last Updated</span>
          <span className="actions">Report</span>
        </div>
        {folders.length === 0 ? (
          <div className="no-evidence">No evidence folders found</div>
        ) : (
          folders.map((folder) => (
            <div key={folder.name} className="evidence-row">
              <span className="control-name">{folder.name}</span>
              <span className="timestamp">
                {folder.timestamp || 'Unknown'}
              </span>
              <span className="actions">
                {folder.hasReport ? (
                  <button 
                    className="view-report-btn" 
                    onClick={() => handleReportClick(folder)}
                  >
                    View Report
                  </button>
                ) : (
                  <span className="no-report">No report available</span>
                )}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default EvidenceReports;
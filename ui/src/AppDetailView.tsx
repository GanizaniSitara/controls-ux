// AppDetailView.tsx - New component to replace ApplicationDetail.tsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

// Define types
interface ApplicationDetailsData {
  name?: string;
  description?: string;
  owner?: string;
  team?: string;
  businessCriticality?: string;
  lastEvaluated?: string;
  overallFitness?: number;
  recommendations?: string[];
  evaluations?: {
    name: string;
    status: string;
    description?: string;
    cost?: string;
  }[];
  [key: string]: any; // Allow other properties
}

interface ApiResponse {
  timestamp: string;
  details: ApplicationDetailsData;
}

// Define component with explicit React.FC type
const AppDetailView: React.FC = () => {
  const { appId } = useParams<{ appId: string }>();
  const [details, setDetails] = useState<ApplicationDetailsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showJson, setShowJson] = useState<boolean>(false);

  useEffect(() => {
    if (!appId) return; // Don't fetch if appId is not available

    setLoading(true);
    setError(null);

    // Fetch data from your API endpoint
    fetch(`http://localhost:8002/api/application-details/${appId}`)
      .then(response => {
        if (!response.ok) {
          // Handle non-2xx responses (like 404 Not Found)
          return response.json().then(err => {
             throw new Error(err.detail || `HTTP error! status: ${response.status}`);
          });
        }
        return response.json();
      })
      .then((data: ApiResponse) => {
        setDetails(data.details); // Set the details from the nested 'details' object
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching application details:", err);
        setError(err.message || 'Failed to fetch application details.');
        setLoading(false);
      });

  }, [appId]); // Re-run effect if appId changes

  if (loading) {
    return <div className="loading">Loading application details for {appId}...</div>;
  }

  if (error) {
    return <div className="error" style={{ color: 'red' }}>Error: {error}</div>;
  }

  if (!details) {
    return <div>No details found for application {appId}.</div>;
  }

  // Format date time string
  const formatDateTime = (dateTimeStr?: string) => {
    if (!dateTimeStr) return 'N/A';
    try {
      return new Date(dateTimeStr).toLocaleString();
    } catch (e) {
      return dateTimeStr;
    }
  };

  // Helper for fitness score class
  const getScoreClass = (score?: number) => {
    if (score === undefined || score === null) return '';
    if (score >= 80) return 'healthy';
    if (score >= 60) return 'warning';
    return 'critical';
  };

  return (
    <div className="application-detail">
      <div className="back-link">
        <Link to="/applications">← Back to Applications</Link>
      </div>

      {/* Application Header Section */}
      <div className="app-header-section">
        <div className="app-header-info">
          <h2>{details.name || appId}</h2>
          <p className="app-description">{details.description || 'No description available.'}</p>
          
          <div className="app-meta-grid">
            <div className="meta-item">
              <span className="meta-label">Owner:</span>
              <span className="meta-value">{details.owner || 'N/A'}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Team:</span>
              <span className="meta-value">{details.team || 'N/A'}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Business Criticality:</span>
              <span className="meta-value">{details.businessCriticality || 'N/A'}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Last Evaluated:</span>
              <span className="meta-value">{formatDateTime(details.lastEvaluated)}</span>
            </div>
          </div>
        </div>

        {details.overallFitness !== undefined && (
          <div className="app-fitness-summary">
            <div className={`metric-circle ${getScoreClass(details.overallFitness)}`}>
              <span>{details.overallFitness}%</span>
            </div>
            <div className="fitness-label">Overall Fitness</div>
          </div>
        )}
      </div>

      {/* Recommendations Section */}
      {details.recommendations && details.recommendations.length > 0 && (
        <div className="recommendations-section">
          <h3>Recommendations</h3>
          <ul className="recommendations-list">
            {details.recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </div>
      )}      {/* System Evaluations Section */}
      {details.evaluations && details.evaluations.length > 0 && (
        <div className="system-evaluations">
          <h3>System Evaluations</h3>
          <div className="evaluations-list">
            {details.evaluations.map((evaluation, index) => (
              <div key={index} className={`evaluation-item ${evaluation.status === 'PASSING' ? 'passing' : 'failing'}`}>
                <div className="eval-header">
                  <h4>{evaluation.name}</h4>
                  <span className={`status-badge ${evaluation.status === 'PASSING' ? 'passing' : 'failing'}`}>
                    {evaluation.status === 'PASSING' ? 'LOAD OK' : 'N/A'}
                  </span>
                </div>
                {evaluation.description && <p className="eval-description">{evaluation.description}</p>}
                {evaluation.cost && <p className="eval-cost"><strong>Cost:</strong> {evaluation.cost}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* JSON Data for Troubleshooting */}
      <div className="json-data-section">
        <h3>
          <button 
            onClick={() => setShowJson(!showJson)} 
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem' }}
          >
            {showJson ? '▼' : '▶'} Troubleshooting Details
          </button>
        </h3>
        {showJson && (
          <pre style={{ 
            background: '#f5f5f5', 
            padding: '15px', 
            borderRadius: '4px',
            overflow: 'auto',
            maxHeight: '500px'
          }}>
            {JSON.stringify(details, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};

// Clear export of the component
export default AppDetailView;

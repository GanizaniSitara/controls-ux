import React, { useState, useEffect } from 'react';
import './ApplicationDetailsCard.css'; // We'll create this CSS file next

interface RawDataDetail {
  [key: string]: string | number | boolean;
}

interface RawData {
  [providerId: string]: RawDataDetail;
}

interface RuleResults {
  [ruleId: string]: string;
}

interface ApplicationDetailsData {
  appId: string;
  raw_data: RawData;
  rule_results: RuleResults;
}

interface ApplicationDetailsCardProps {
  appId: string;
}

const ApplicationDetailsCard: React.FC<ApplicationDetailsCardProps> = ({ appId }) => {
  const [details, setDetails] = useState<ApplicationDetailsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        // Use the absolute path for the fetch request in a typical setup,
        // but assuming a proxy or relative path setup for development server
        const response = await fetch(`/api/application-details/${appId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // The API returns { timestamp: ..., details: {...} }
        if (data && data.details) {
             setDetails(data.details);
        } else {
            throw new Error("Unexpected API response structure");
        }
      } catch (e: any) {
        console.error("Failed to fetch application details:", e);
        setError(`Failed to load details for ${appId}: ${e.message}`);
        setDetails(null); // Clear details on error
      } finally {
        setLoading(false);
      }
    };

    if (appId) {
      fetchDetails();
    } else {
        setLoading(false); // No appId, nothing to load
        setDetails(null);
        setError(null);
    }
  }, [appId]); // Re-fetch if appId changes

  if (loading) {
    return <div className="card loading">Loading details for {appId}...</div>;
  }

  if (error) {
    return <div className="card error">Error: {error}</div>;
  }

  if (!details) {
    return <div className="card empty">No details available for {appId}.</div>;
  }

  return (
    <div className="card application-details-card">
      <h2>Application Details: {details.appId}</h2>

      <div className="section raw-data-section">
        <h3>Raw Data</h3>
        {Object.entries(details.raw_data).length > 0 ? (
          <ul>
            {Object.entries(details.raw_data).map(([providerId, data]) => (
              <li key={providerId} className="provider-data">
                <strong>{providerId}:</strong>
                <ul className="data-points">
                  {Object.entries(data).map(([key, value]) => (
                    // Exclude timestamp from display here if desired
                    key !== 'timestamp' && (
                       <li key={key}>
                         <span className="data-key">{key}:</span>{' '}
                         <span className="data-value">{String(value)}</span>
                       </li>
                    )
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        ) : (
          <p>No raw data available.</p>
        )}
      </div>

      <div className="section rule-results-section">
        <h3>Rule Results</h3>
        {Object.entries(details.rule_results).length > 0 ? (
          <ul>
            {Object.entries(details.rule_results).map(([ruleId, result]) => (
              <li key={ruleId}>
                <span className="rule-key">{ruleId}:</span>{' '}
                <span className="rule-value">{result}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>No rule results available.</p>
        )}
      </div>
    </div>
  );
};

export default ApplicationDetailsCard;

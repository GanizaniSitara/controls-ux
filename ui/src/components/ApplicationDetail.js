// components/ApplicationDetail.js - corrected version
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import '../App.css';

function ApplicationDetail() {
  const { appId } = useParams();
  const [appFitness, setAppFitness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true); // Start loading
      setError(null); // Reset error
      try {
        const query = `
          query GetApplicationFitness($appId: String!) {
            applicationFitness(appId: $appId) {
              application {
                appId
                appName
                description
                owner
                team
                businessCriticality
                lastEvaluated
              }
              systemEvaluations {
                system {
                  systemName
                  healthScore
                  lastUpdated
                  # Assuming 'metrics' is a JSON string or similar; adjust if needed
                  # metrics
                }
                fitnessEvaluations {
                  score
                  passing
                  criteria
                  recommendations
                }
                overallScore
              }
              overallFitnessScore
              recommendations
            }
          }
        `;

        const response = await fetch('http://127.0.0.1:3050/graphql', { // Ensure this matches your API endpoint
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          // Use variables for the query
          body: JSON.stringify({
            query,
            variables: { appId }
          }),
        });

        const result = await response.json();

        if (!response.ok) {
            // Handle HTTP errors (e.g., 404, 500)
            throw new Error(`HTTP error! status: ${response.status} - ${result.errors ? result.errors[0].message : 'Unknown error'}`);
        }

        if (result.errors) {
          // Handle GraphQL errors
          console.error("GraphQL Errors:", result.errors);
          throw new Error(result.errors.map(e => e.message).join(', '));
        }

        if (!result.data || !result.data.applicationFitness) {
            throw new Error('Application data not found in response.');
        }

        setAppFitness(result.data.applicationFitness);
      } catch (err) {
        console.error("Error fetching application data:", err);
        setError(err.message || 'Failed to fetch data');
      } finally {
        setLoading(false); // Stop loading regardless of outcome
      }
    };

    fetchData();
  }, [appId]); // Dependency array ensures this runs when appId changes

  if (loading) return <div className="loading">Loading application fitness data...</div>;
  if (error) return <div className="error">Error fetching data: {error}</div>;
  if (!appFitness) return <div className="error">Application data could not be loaded or not found.</div>;

  // Safely access nested properties
  const { application, systemEvaluations = [], overallFitnessScore = 0, recommendations = [] } = appFitness;

  // Helper function to format date/time
  const formatDateTime = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      return new Date(isoString).toLocaleString();
    } catch (e) {
      return 'Invalid Date';
    }
  };

  // Helper function to determine score class
  const getScoreClass = (score) => {
    if (score === null || score === undefined) return 'unknown';
    if (score >= 0.8) return 'good';
    if (score >= 0.5) return 'average';
    return 'bad';
  };

  // Helper function to format criticality
  const formatCriticality = (criticality) => {
      if (!criticality) return 'N/A';
      const lowerCaseCrit = criticality.toLowerCase();
      let className = 'criticality-low'; // Default
      if (lowerCaseCrit.includes('high') || lowerCaseCrit.includes('critical')) {
          className = 'criticality-high';
      } else if (lowerCaseCrit.includes('medium')) {
          className = 'criticality-medium';
      }
      return <span className={`meta-value criticality ${className}`}>{criticality}</span>;
  };


  return (
    <div className="application-detail">
      <div className="back-link">
        <Link to="/applications">← Back to Applications</Link>
      </div>

      {/* Use application details safely */}
      {application ? (
        <div className="app-header-section">
          <div className="app-header-info">
            <h2>{application.appName || 'Unnamed Application'}</h2>
            <p className="app-description">{application.description || 'No description available.'}</p>
            <div className="app-meta-grid">
              <div className="meta-item">
                <span className="meta-label">Owner:</span>
                <span className="meta-value">{application.owner || 'N/A'}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Team:</span>
                <span className="meta-value">{application.team || 'N/A'}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Business Criticality:</span>
                {formatCriticality(application.businessCriticality)}
              </div>
              <div className="meta-item">
                <span className="meta-label">Last Evaluated:</span>
                <span className="meta-value">{formatDateTime(application.lastEvaluated)}</span>
              </div>
            </div>
          </div>
          <div className="app-fitness-summary">
            <div className={`fitness-score-circle ${getScoreClass(overallFitnessScore)}`}>
              {(overallFitnessScore * 100).toFixed(0)}%
            </div>
            <div className="fitness-label">Overall Fitness</div>
          </div>
        </div>
      ) : (
        <div className="error">Application details missing.</div>
      )}


      {recommendations && recommendations.length > 0 && (
        <div className="recommendations-section">
          <h3>Overall Recommendations</h3>
          <ul className="recommendations-list">
            {recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      <h3>System Evaluations</h3>
      <div className="systems-container">
        {systemEvaluations && systemEvaluations.length > 0 ? (
          systemEvaluations.map((evaluation, index) => (
            <div key={index} className="system-card">
              {evaluation && evaluation.system ? (
                <>
                  <div className="system-header">
                    <h3>{evaluation.system.systemName || 'Unnamed System'}</h3>
                    <div className={`score-badge ${getScoreClass(evaluation.overallScore)}`}>
                      {(evaluation.overallScore * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="system-details">
                    <p>Last updated: {formatDateTime(evaluation.system.lastUpdated)}</p>
                    {/* <p>Health score: {evaluation.system.healthScore?.toFixed(2) ?? 'N/A'}</p> */}

                    <h4>Fitness Evaluations</h4>
                    <div className="evaluations">
                      {evaluation.fitnessEvaluations && evaluation.fitnessEvaluations.length > 0 ? (
                        evaluation.fitnessEvaluations.map((fitnessEval, evalIndex) => (
                          <div key={evalIndex} className={`evaluation ${fitnessEval.passing === "Yes" ? 'pass' : 'fail'}`}>
                            <div className="eval-header">
                              <span className="eval-criteria">{fitnessEval.criteria || 'Unknown Criteria'}</span>
                              <span className={`eval-status ${fitnessEval.passing === "Yes" ? 'pass' : 'fail'}`}>
                                {fitnessEval.passing === "Yes" ? '✓ Pass' : '✗ Fail'}
                              </span>
                            </div>
                            {fitnessEval.passing !== "Yes" && fitnessEval.recommendations && fitnessEval.recommendations.length > 0 && (
                              <ul className="recommendations">
                                {fitnessEval.recommendations.map((rec, recIndex) => (
                                  <li key={recIndex}>{rec}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))
                      ) : (
                        <p>No fitness evaluations available for this system.</p>
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <div className="error">System data missing for this evaluation.</div>
              )}
            </div>
          ))
        ) : (
          <p>No system evaluations available for this application.</p>
        )}
      </div>
    </div>
  );
}

export default ApplicationDetail;

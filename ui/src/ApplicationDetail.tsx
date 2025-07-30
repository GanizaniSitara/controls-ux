import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

interface ApplicationDetailsData {
  // Define the expected structure of your application details
  // Example:
  name?: string;
  description?: string;
  owner?: string;
  // Add other fields based on what your API returns
  [key: string]: any; // Allow other properties
}

interface ApiResponse {
    timestamp: string;
    details: ApplicationDetailsData;
}


function ApplicationDetail() {
  const { appId } = useParams<{ appId: string }>(); // Get appId from URL parameter
  const [details, setDetails] = useState<ApplicationDetailsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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
    return <div>Loading application details for {appId}...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>Error: {error}</div>;
  }

  if (!details) {
    return <div>No details found for application {appId}.</div>;
  }

  // Render the details (customize this based on your data structure)
  return (
    <div>
      <h2>Application Details: {details.name || appId}</h2>
      <pre>{JSON.stringify(details, null, 2)}</pre>
      {/* Add more specific rendering based on the fields in 'details' */}
      {/* Example: <p>Owner: {details.owner}</p> */}
    </div>
  );
}

export default ApplicationDetail;

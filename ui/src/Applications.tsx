import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface CacheData {
  raw_data?: Record<string, Record<string, any>>;
  provider_results?: Record<string, Record<string, any>>;
}

interface ApplicationInfo {
  id: string;
  // Optionally add more fields as available from cache
}

function ApplicationCard({ app }: { app: ApplicationInfo }) {
  return (
    <Link to={`/application/${app.id}`} className="application-card-link">
      <div className="application-card">
        <h3>{app.id}</h3>
        {/* Add more fields as available from cache */}
      </div>
    </Link>
  );
}

function Applications() {
  const [applications, setApplications] = useState<ApplicationInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchApplications = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('http://localhost:8002/aggregated-data');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: CacheData = await response.json();
        // Collect all unique app IDs from all providers in raw_data
        const appIdSet = new Set<string>();
        if (data.raw_data) {
          Object.values(data.raw_data).forEach(providerData => {
            Object.keys(providerData).forEach(appId => {
              appIdSet.add(appId);
            });
          });
        }
        // Optionally, also check provider_results for any extra app IDs
        if (data.provider_results) {
          Object.values(data.provider_results).forEach(providerData => {
            Object.keys(providerData).forEach(appId => {
              appIdSet.add(appId);
            });
          });
        }
        setApplications(Array.from(appIdSet).sort().map(id => ({ id })));
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, []);

  return (
    <div className="applications-view">
      <h2>Applications Overview</h2>
      {loading && <p>Loading applications...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      <div className="applications-grid">
        {applications.map(app => (
          <ApplicationCard key={app.id} app={app} />
        ))}
      </div>
      {!loading && applications.length === 0 && <p>No applications found in cache.</p>}
    </div>
  );
}

export default Applications;

import React, { useState, useEffect } from 'react';

function CacheInspector() {
  // Explicitly type the expected structure of the data
  interface CacheData {
    raw_data?: Record<string, Record<string, any>>;
    // Structure for rules engine results - now a dictionary of rule results
    rule_results?: Record<string, Record<string, any> | { error?: string }>; // Key is rule_id, value is rule output
    // Add other top-level keys if expected from /aggregated-data
    [key: string]: any; // Allow other potential top-level keys
  }

  const [data, setData] = useState<CacheData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // Add 'aggregated' to possible tab states and set as default
  const [activeTab, setActiveTab] = useState<string>('aggregated');
  const [activeProvider, setActiveProvider] = useState<string>('code_quality_v1');
  const [activeRuleId, setActiveRuleId] = useState<string | null>(null);
  // Define known provider IDs
  const knownProviders = [
    'code_quality_v1',
    'cost_optimization_v1',
    'documentation_v1',
    'operational_excellence_v1',
    'security_v1',
    'data_quality_v1',
    'resilience_v1',
    'tech_debt_v1',
    'vendor_mgmt_v1',
    'architecture_v1',
    'workload_placement_v1'
  ];

  // Reset activeRuleId when switching away from the engine tab or when rule keys change
  useEffect(() => {
    if (activeTab !== 'engine') {
      setActiveRuleId(null);
    } else if (data?.rule_results) {
      const ruleKeys = Object.keys(data.rule_results).filter(key => key !== 'error');
      if (ruleKeys.length > 0 && (!activeRuleId || !ruleKeys.includes(activeRuleId))) {
        // Set the first available rule as active if current is invalid or null
        setActiveRuleId(ruleKeys[0]);
      }
    }
  }, [activeTab, data?.rule_results, activeRuleId]); // Add activeRuleId dependency

  useEffect(() => {
    const fetchData = async () => {
      // Don't reset loading to true on subsequent fetches for polling
      // setLoading(true);
      setError(null);
      try {
        const response = await fetch('http://localhost:8002/aggregated-data');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const jsonData: CacheData = await response.json();
        setData(jsonData);
      } catch (e: any) {
        setError(e.message);
        console.error("Failed to fetch cache data:", e);
      } finally {
        // Set loading to false only after the first fetch attempt
        if (loading) {
            setLoading(false);
        }
      }
    };

    fetchData(); // Initial fetch

    // Set up polling to refresh data every 10 seconds
    const intervalId = setInterval(fetchData, 10000);

    // Cleanup interval on component unmount
    return () => clearInterval(intervalId);
  }, [loading]); // Re-run effect if loading state changes (relevant for initial load)

  const formatProviderName = (providerId: string): string => {
    // Convert snake_case to Title Case
    return providerId
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
      .replace(/V\d+$/, ''); // Remove version numbers at the end
  };

  // Render the main navigation tabs (Providers / Engine Results / Aggregated Data)
  const renderMainTabs = () => {
    return (
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        {/* Aggregated Data Tab Button */}
        <button
          onClick={() => setActiveTab('aggregated')}
          style={{
            fontWeight: activeTab === 'aggregated' ? 'bold' : 'normal',
            backgroundColor: activeTab === 'aggregated' ? '#e0e0e0' : '#f4f4f4',
            padding: '8px 16px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Aggregated Data
        </button>
        {/* Providers Tab Button */}
        <button
          onClick={() => setActiveTab('providers')}
          style={{
            fontWeight: activeTab === 'providers' ? 'bold' : 'normal',
            backgroundColor: activeTab === 'providers' ? '#e0e0e0' : '#f4f4f4',
            padding: '8px 16px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Providers (Raw)
        </button>
        {/* Engine Results Tab Button */}
        <button
          onClick={() => setActiveTab('engine')}
          style={{
            fontWeight: activeTab === 'engine' ? 'bold' : 'normal',
            backgroundColor: activeTab === 'engine' ? '#e0e0e0' : '#f4f4f4',
            padding: '8px 16px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Engine Results
        </button>
      </div>
    );
  };

  // Render the provider selection tabs when in provider view
  const renderProviderTabs = () => {
    return (
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        {knownProviders.map(provider => (
          <button
            key={provider}
            onClick={() => setActiveProvider(provider)}
            style={{
              fontWeight: activeProvider === provider ? 'bold' : 'normal',
              backgroundColor: activeProvider === provider ? '#e0e0e0' : '#f4f4f4',
              padding: '8px 12px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {formatProviderName(provider)}
          </button>
        ))}
      </div>
    );
  };

  
  const renderEngineResults = () => {
    if (!data || !data.rule_results) {
      return <p>No engine results available.</p>;
    }

    const resultsObject = data.rule_results;

    // Check for a top-level error from the engine itself
    if (typeof resultsObject === 'object' && resultsObject !== null && 'error' in resultsObject && Object.keys(resultsObject).length === 1) {
      const errorResult = resultsObject as { error: string };
      return <p style={{ color: 'orange' }}>Engine Error: {errorResult.error}</p>;
    }

    // Filter out a potential top-level 'error' key if other results exist
    const ruleKeys = Object.keys(resultsObject).filter(key => key !== 'error');

    if (ruleKeys.length === 0) {
      return <p>Engine results are currently empty.</p>;
    }

    // If activeRuleId hasn't been set yet (e.g., initial load), wait for useEffect
    if (!activeRuleId) {
        return <p>Loading rule results...</p>;
    }

    const result = (resultsObject as Record<string, any>)[activeRuleId];
    const formattedActiveRuleId = activeRuleId
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');

    // Render rule selection buttons (tabs)
    const renderRuleTabs = () => {
      return (
        <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {ruleKeys.map(ruleId => {
            const formattedRuleId = ruleId
              .split('_')
              .map(word => word.charAt(0).toUpperCase() + word.slice(1))
              .join(' ');
            return (
              <button
                key={ruleId}
                onClick={() => setActiveRuleId(ruleId)}
                style={{
                  fontWeight: activeRuleId === ruleId ? 'bold' : 'normal',
                  backgroundColor: activeRuleId === ruleId ? '#e0e0e0' : '#f4f4f4',
                  padding: '8px 12px', // Match provider tab style
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                {formattedRuleId}
              </button>
            );
          })}
        </div>
      );
    };

    // Render content for the selected rule
    const renderRuleContent = () => {
      if (!result) {
        // This might happen briefly or if the activeRuleId is somehow invalid
        return <p>No results available for {formattedActiveRuleId}.</p>;
      }

      return (
        <div>
          {/* Heading specific to the selected rule, placed below tabs */}
          <h3>Results for: {formattedActiveRuleId}</h3>
          {/* Check if the individual rule result is an error object */}
          {result && typeof result === 'object' && 'error' in result ? (
            <p style={{ color: 'orange' }}>Rule Error: {(result as { error: string }).error}</p>
          ) : (
            <pre style={{
              textAlign: 'left',
              backgroundColor: '#f4f4f4',
              padding: '10px',
              border: '1px solid #ccc',
              overflowX: 'auto',
              maxHeight: '600px', // Match provider style maybe
              borderRadius: '4px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
        </div>
      );
    };

    // Return structure: Tabs first, then content below
    return (
      <div style={{ marginBottom: '20px' }}>
        {/* Removed the general H2 from here */}
        {renderRuleTabs()}
        {renderRuleContent()}
      </div>
    );
  };

  // Renamed and simplified to show only raw data for the selected provider
  const renderProvidersContent = () => {
    if (!data || !data.raw_data) {
        return <p>No raw provider data available.</p>;
    }
    const providerData = data.raw_data[activeProvider];

    return (
        <div>
            {/* Heading specific to provider below tabs */}
            <h3>Raw Data for: {formatProviderName(activeProvider)}</h3>
            {providerData && Object.keys(providerData).length > 0 ? (
                 <pre style={{
                    textAlign: 'left',
                    backgroundColor: '#f4f4f4',
                    padding: '10px',
                    border: '1px solid #ccc',
                    overflowX: 'auto',
                    maxHeight: '600px',
                    borderRadius: '4px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                    {JSON.stringify(providerData, null, 2)}
                 </pre>
            ) : (
                <p>No raw data available for {formatProviderName(activeProvider)}.</p>
            )}
        </div>
    );
  };

  // New function to render the full aggregated data
  const renderAggregatedData = () => {
    if (!data) return null;

    return (
        <div style={{ marginBottom: '20px' }}>
            <h3>Full Aggregated Data</h3>
            <pre style={{
                textAlign: 'left',
                backgroundColor: '#f0f0f0', // Slightly different background
                padding: '15px',
                border: '1px solid #bbb',
                overflowX: 'auto',
                maxHeight: '600px', // Allow more height
                borderRadius: '4px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
                {JSON.stringify(data, null, 2)}
            </pre>
        </div>
    );
  };


  const renderContent = () => {
    if (!data) return null;

    if (activeTab === 'aggregated') { // Handle the new tab
        return renderAggregatedData();
    } else if (activeTab === 'providers') {
      return (
        <>
          {renderProviderTabs()}
          {renderProvidersContent()}
        </>
      );
    } else if (activeTab === 'engine') {
      return renderEngineResults();
    }
    return null; // Default case
  };

  return (
    <div>
      <h1>Cache Inspector</h1>
      {loading && <p>Loading initial cache data...</p>}
      {error && <p style={{ color: 'red' }}>Error loading data: {error}</p>}

      {!loading && data && (
        <>
          {renderMainTabs()}
          {renderContent()}
        </>
      )}

      {!loading && !error && !data && (
        <p>Cache is currently empty or unavailable.</p>
      )}
    </div>
  );
}

export default CacheInspector;
